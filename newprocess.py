#! /usr/bin/env python

import csv
import string
import StringIO
import subprocess
import sys 

"""start with a sample, create a stream to put into loadflow.exe, 
run the loadflow, analyse the output stream to see if it is an 
acceptable system. return result,description. where result is 
zero for success and description is a text block."""

# we could since there arn't that many save the tests that fail to a file!

class Loadflow(object):
    """Read in a loadflow file"""
    def __init__(self, loadflowstream):
        self.busbars  = {}
        self.branches = {}
        
        x = 0 # enumerate would mess up on comment lines 
        for row in csv.reader(loadflowstream):
            if len(row) == 0 or row[0][0] == '#':
                continue
            x += 1
            if x == 1 :
                self.title = row[0]
            elif x == 2 :
                numbus = int(row[0])
                self.header = row
            elif x < numbus+3:
                busname = row[2].strip()
                self.busbars[busname] = row
            else:
                branchname = row[1].strip()
                self.branches[branchname] = row



def lfgenerator(lf, output, killlist):
    """from the loadflow kill everything in the killlist 
    and save resulting loadlow to writer. lf is the baseloadflow"""

    # 1. find all in the set killlist & loadflow.branches.keys
    # 2. find all in the set killlist & loadflow.busbars.keys
    # 3. kill all the generator linking lines
    #    i.e. kill lines 'X + 2.'

    killlist = set([x.strip() for x in killlist])
    allbranches = set(lf.branches.keys())
    allbusses = set(lf.busbars.keys())

    branchkill = allbranches & killlist
    buskill    = allbusses & killlist
    assert(branchkill | buskill == killlist)

    # kill lines on dead busbars
    deadlines = []
    for (name,value) in lf.branches.items():
        if name in branchkill or value[4].strip() in buskill or value[5].strip() in buskill: 
            deadlines += [name]
    deadlines = set(deadlines)

    # print "killlist", killlist
    # print "deadlines", deadlines
    # print "branchkill", branchkill
    # print "buskill", buskill

    branchkill |= deadlines
    assert(branchkill <= allbranches)
    assert(buskill <= allbusses)

    csvwriter = csv.writer(output)

    # the title
    csvwriter.writerow([lf.title])

    # remembering to change the number of bus and line
    numbus  = int(lf.header[0]) - len(buskill)
    numline = int(lf.header[1]) - len(branchkill)
    csvwriter.writerow([numbus, numline] + lf.header[2:])

    # make sure there is a slack bus 
    newslackbus = None

    def is_slack_bus(busline):
        return int(busline[0]) == 2

    slackbuslines = filter(is_slack_bus, lf.busbars.values())
    assert(len(slackbuslines) == 1)
    slackbus = slackbuslines[0][2].strip()

    if slackbus in buskill:
        for item in ["G13","G14"]:
            if item not in buskill:
                newslackbus = item 
                break
        if newslackbus == None:
            # print "failed to find a replacement slackbus"
            # print "guess I have to just ignore it"
            # print "it will fail the simulation"
            pass 

    # ignore everything in killlist, print the rest
    for (name, value) in lf.busbars.items():
        if name not in buskill:
            if name != newslackbus:
                csvwriter.writerow(value)
            else:
                csvwriter.writerow(["2"] + value[1:])

    # same with the branches
    # remember to kill lines on dead busbars 
    for (name,value) in lf.branches.items():
        if name not in branchkill:
            if value[4].strip() not in buskill and value[5].strip() not in buskill: 
                csvwriter.writerow(value)

def skiplines(infile,n):
    for x in range(n):
        infile.readline()

# TODO why on earth don't we use busbar variable 
def businlimit(busbar,row,min_volt,max_volt):
    if not (min_volt < float(row[2]) < max_volt):
        # print "BUS-LIMIT," , row[1] , "," , row[2]
        return False
    return True

def lineinlimit(line_limit,row,line_limit_type):
    name = (row[1], row[2])
    if name in line_limit:
        lim = line_limit[name]
        limit = float(lim[line_limit_type])
        P   = float(row[3])

        if P > limit:
            # print "LINE-LIMIT,", row[1], ",", row[2], ",", P, ",", limit
            return False
    else:
        pass # it's probably a generator interconnect
    return True

def check(limits,input,min_volt,max_volt,line_limit_type):
    (busbar , line) = limits
    failcount = 0
    for row in input:
        if row[0] == "B":
            if not businlimit(busbar,row,min_volt,max_volt):
                failcount += 1
        elif row[0] == "L":
            if not lineinlimit(line,row,line_limit_type):
                failcount += 1
        else:
            raise "expected 'L' or 'B' got '" + row[0] + "'"
    
    return failcount


def readlimits(limitsfile):
    busbar = {}
    line = {}
    
    reader  = csv.reader(limitsfile)
    for row in reader:
        if row[0].strip() == "line":
            line[(row[2].strip() , row[3].strip())] = row[4:]
        else:
            raise "expected 'line' got '" + row[0] + "'"

    return (busbar, line)

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

def make_sample_simulator(baself="rts.lf", limits="rts.lim", 
                          min_volt=0.9, max_volt=1.1, line_limit_type=1):
    
    baself = Loadflow(open(baself))
    limits = readlimits(open(limits))

    def dothis(sample):
        return process(sample, baself, limits, min_volt, 
                       max_volt, line_limit_type)
    return dothis

def process(sample, baself, limits, min_volt, max_volt, line_limit_type):
    
    proc = subprocess.Popen('./loadflow -i10000 -t -y',
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            stdin=subprocess.PIPE
                            )
    lfgenerator(baself, proc.stdin, sample)
    so, se = proc.communicate()


    # print "\n\n\nSE\n\n\n"
    # print se

    # print "\n\n\nSO\n\n\n"
    # print so
    # return

    err_lines = se.splitlines()
    errstart = err_lines[0].strip()

    if len(err_lines) == 4:
        ok = True
        ok &= err_lines[0].startswith("Time :-")
        ok &= err_lines[1].startswith("(sec)")
        ok &= err_lines[2].startswith("Jacobian Matrix:")
        ok &= err_lines[3].startswith("Best Maximum Mismatch :")
        if not ok:
            return (False,"unexpected 4: " + errstart)
    else:
        if len(err_lines) == 1 and errstart.startswith("error: no slack bus defined"):
            return (False,"no slack bus")
        if len(err_lines) >= 1 and errstart.startswith("warning 1: stop - divergence"):
            return (False,"divergence")
        if len(err_lines) >= 1 and errstart.startswith("error: zero diagonal element"):
            return (False,"islanded")
        return (False,"unexpected: " + errstart)

    cleaned = cleanup_output(StringIO.StringIO(so))

    res = check(limits,cleaned,min_volt,max_volt,line_limit_type)
    if res == 0:
        return (True,"ok")
    else:
        return (False,"component out of limits")

    assert(False)

def examples():
    # baself="rts.lf" 
    # limits="rts.lim" 
    # min_volt=0.9
    # max_volt=1.1
    # line_limit_type=1
    # baself = Loadflow(open(baself))
    # limits = readlimits(open(limits))
    # sample = []
    # sample += ['107', '113', '123']
    # lfgenerator(baself, sys.stdout, sample)
    # print process(sample, baself, limits, min_volt,  max_volt, line_limit_type)

    prc = make_sample_simulator()
    print prc([' G12'])
    print prc([' 108']) # THIS SHOULD SURELY FAIL !!!
    print prc([' 113','107','123'])
    print prc(['107','123'])
# examples()

# make_sample_simulator()(['not-here'])
