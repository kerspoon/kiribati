
# This checks that the loadflow results are in limits. 
# 
# All you really want to do with this is call 
#   limitChecker = Limits()
#   limitsChecker.check(loadflow_stdout)

import csv
import string

def skiplines(infile,n):
    for x in range(n):
        infile.readline()


def cleanup_output(infile):
    skiplines(infile,5)
    result = []

    while True:
        line = infile.readline()
        cols = string.split(line)
        if len(cols) == 0: break 

        Vm = float(cols[6])
        result.append(["B", cols[1], Vm] )

    skiplines(infile,2)

    while True:
        line = infile.readline()
        cols = string.split(line)
        if len(cols) == 0: break 

        P1 = float(cols[len(cols)-4])
        P2 = float(cols[len(cols)-2])
        P  = max (abs(P1),abs(P2))

        result.append(["L", cols[0] , cols[1] , P] )

    return result

class Limits:
    """min_volt, max_volt, line_limit_type, line_limits"""

    def __init__(self, limitsfile, min_volt=0.9, max_volt=1.1, line_limit_type=1):
        self.min_volt = min_volt
        self.max_volt = max_volt
        self.line_limit_type = line_limit_type
        self.readlimits(limitsfile)

    def readlimits(self, limitsfile):
        self.line_limit = {}
        self.gen_limit = {}
        reader  = csv.reader(limitsfile)
        for row in reader:
            if row[0].strip() == "line":
                self.line_limit[(row[2].strip() , row[3].strip())] = row[4:]
            elif row[0].strip() == "gen":
                self.gen_limit[row[1].strip()] = row[2].strip()
            else:
                raise "expected 'line' got '" + row[0] + "'"

    def businlimit(self, row):
        if not (self.min_volt < float(row[2]) < self.max_volt):
            # print "BUS-LIMIT," , row[1] , "," , row[2]
            return False
        return True

    def lineinlimit(self, row):
        name = (row[1], row[2])
        if name in self.line_limit:
            lim = self.line_limit[name]
            limit = float(lim[self.line_limit_type])
            P = float(row[3])

            if P > limit:
                # print "LINE-LIMIT,", row[1], ",", row[2], ",", P, ",", limit
                return False
        else:
            pass # it's probably a generator interconnect
        return True

    def check(self, loadflow_output):
        cleaned_loadflow_output = cleanup_output(loadflow_output)
        failcount = 0
        for row in cleaned_loadflow_output:
            if row[0] == "B":
                if not self.businlimit(row):
                    failcount += 1
            elif row[0] == "L":
                if not self.lineinlimit(row):
                    failcount += 1
            else:
                raise "expected 'L' or 'B' got '" + row[0] + "'"
        return failcount
