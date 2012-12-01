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

    def __init__(self, loadflowstream, limits_checker):
        self.busbars  = {}
        self.branches = {}
        self.limits_checker = limits_checker
        
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

    def lfgenerator(self, output, scenario):
        """from the loadflow kill everything in the killlist 
        and save resulting loadlow to writer."""

        # 1. find all in the set killlist & loadflow.branches.keys
        # 2. find all in the set killlist & loadflow.busbars.keys
        # 3. kill all the generator linking lines
        #    i.e. kill lines 'X + 2.'

        killlist = set([x.strip() for x in scenario.kill_list])
        allbranches = set(self.branches.keys())
        allbusses = set(self.busbars.keys())

        branchkill = allbranches & killlist
        buskill    = allbusses & killlist
        assert(branchkill | buskill == killlist)

        # kill lines on dead busbars
        deadlines = []
        for (name,value) in self.branches.items():
            if name in branchkill or value[4].strip() in buskill or value[5].strip() in buskill: 
                deadlines += [name]
        deadlines = set(deadlines)

        # if we have killed a generator connecting line, kill its generator
        special_kill = set()
        for name in deadlines:
            if name.startswith("XG"):
                special_kill |= set([name[1:]])
        buskill |= special_kill

        # print "killlist", killlist
        # print "deadlines", deadlines
        # print "branchkill", branchkill
        # print "buskill", buskill

        branchkill |= deadlines
        assert(branchkill <= allbranches)
        assert(buskill <= allbusses)

        csvwriter = csv.writer(output)

        # the title
        csvwriter.writerow([self.title])

        # remembering to change the number of bus and line
        numbus  = int(self.header[0]) - len(buskill)
        numline = int(self.header[1]) - len(branchkill)
        csvwriter.writerow([numbus, numline] + self.header[2:])

        # make sure there is a slack bus 
        newslackbus = None

        def is_slack_bus(busline):
            return int(busline[0]) == 2

        slackbuslines = filter(is_slack_bus, self.busbars.values())
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
        for (name, value) in self.busbars.items():
            if name not in buskill:
                new_value = value[:]
                if new_value[7].strip() != "":
                    new_value[7] = str(float(new_value[7]) * scenario.bus_level)

                if name != newslackbus:
                    csvwriter.writerow(new_value)
                else:
                    csvwriter.writerow(["2"] + new_value[1:])

        # same with the branches
        # remember to kill lines on dead busbars 
        for (name,value) in self.branches.items():
            if name not in branchkill:
                if value[4].strip() not in buskill and value[5].strip() not in buskill:
                    csvwriter.writerow(value)

    def check_limits(self, output):
        return self.limits_checker.check(output)

    def simulate(self, sample):
        
        proc = subprocess.Popen('./loadflow -i10000 -t -y',
                                shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE
                                )

        self.lfgenerator(proc.stdin, sample)
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

        res = self.check_limits(StringIO.StringIO(so))
        if res == 0:
            return (True, "ok")
        else:
            return (False, "component out of limits")

