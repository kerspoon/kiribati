#! /usr/bin/env python

import csv
import string
import StringIO
import subprocess
import sampler
import buslevel
from pymisc import *

class Limits:
    """min_volt, max_volt, line_limit_type, line_limits"""

    def __init__(self,limits="rts.lim", min_volt=0.9, max_volt=1.1, line_limit_type=1):
        self.limits = limits
        self.min_volt = min_volt
        self.max_volt = max_volt
        self.line_limit_type = line_limit_type
        self.readlimits(open(limits))

    def readlimits(self,limitsfile):
        self.line_limit = {}
        reader  = csv.reader(limitsfile)
        for row in reader:
            if row[0].strip() == "line":
                self.line_limit[(row[2].strip() , row[3].strip())] = row[4:]
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

    def check(self, cleaned_loadflow_output):
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

class Loadflow:
    """a load flow file
    
    title = string
    header = csv(...)
    busbars  = dict(bus-name, bus-row)
    branches = dict(branch-name, branch-row)

    where:
        bus-name = branch-name = string
        bus-row = csv(type, zone, name, pg, qg, vm, va, pl,ql, qmin, qmax, slope )
        branch-row = csv(Type, Code, Zone1, Zone2, Bus1, Bus2, Circuit, R, X, B, Ratio, Phase, Sr, Control, MinTap, MaxTap, TapStep)
     """

    def __init__(self,loadflowstream):
        """read in data from a text file"""
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

    def get_lfgenerator(self):
        def inner(output):
            csvwriter = csv.writer(output)

            # the title
            csvwriter.writerow([self.title])

            # header
            csvwriter.writerow(self.header)

            # busbars
            for (name, value) in self.busbars.items():
                csvwriter.writerow(value)

            # branches
            for (name, value) in self.branches.items():
                csvwriter.writerow(value)

        return inner


def simulate(limits, lfgenerator):
    """run the simulator and return the result"""
        
    proc = subprocess.Popen('./loadflow -i10000 -t -y',
                            shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            stdin=subprocess.PIPE
                            )
    lfgenerator(proc.stdin)
    so, se = proc.communicate()
    
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

    res = limits.check(cleaned)
    if res == 0:
        return (True,"ok")
    else:
        return (False,"component out of limits")

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


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

def load_scenarios(stream):
    """load from text. return [Scenario(...)]"""
    scenarioReader = csv.reader(stream, delimiter=' ', quotechar="'")

    scenarios = []
    linenum = None 
    
    name = None 
    base = None
    faillist = None
    loadlevel = None 
    result = None

    for line in scenarioReader:
        # print line 
        if len(line) >= 2 and line[0].strip() =="[Scenario]":
            if linenum == 6:
                scenarios.append(Scenario(name, base, faillist, loadlevel, {}, result))
            else:
                assert linenum == None 
            name = line[1]
            base = line[2]
            linenum = 1
        elif linenum == 2:
            # print "faillist"
            faillist = set(line)
        elif linenum == 3:
            # print "loadlevel"
            loadlevel = line[0]
        elif linenum == 4:
            # print "genlevels"
            assert len(line) == 0
        elif linenum == 5:
            if len(line) == 2:
                result = (line[0], line[1])
            else:
                assert len(line) == 0
        else:
            raise Exception("error")
        linenum += 1
    return scenarios

def gen_scenarios(iterations):
    """generate N scenarios"""

    loadflow = Loadflow(open("rts.lf"))
    components = sampler.read(open("rts.net"))

    faillist = n_unique(sampler.make_outage_generator(components),iterations)
    loadlevel = [buslevel.random_bus_forecast() for x in range(iterations)]

    return [Scenario("sc"+str(n),loadflow,fl,ll,{}) for n,fl,ll in zip(range(iterations),faillist,loadlevel)]

def solve_scenarios(scenarios):
    """all simulated"""

    limit = Limits()
    for scenario in scenarios:
        scenario.simulate(limit)
    return None

def save_scenarios(scenarios, output):
    """save to an output stream whether that have been simulated or not """

    for scenario in scenarios:
        output.write(str(scenario))
    pass 

class Scenario:
    """one possible state a base case could be in
    id = String
    base = Loadflow | Loadflow.filename
    outages = set(bus-name | branch-name)
    load-level = float[0, inf]
    gen-level = dict(gen-name, float[0, inf])
    where:
        gen-name = string
    """

    def __init__(self, name, lf, faillist, loadlevel, genlevels = {}, result = None):
        self.name = name 
        self.loadflow = lf
        self.faillist  = faillist 
        self.loadlevel = loadlevel 
        self.genlevels = genlevels 
        self.result = result
        assert genlevels == {}

    def simulate(self,limit):
        self.result = simulate(limit, self.get_lfgenerator())

    def get_lfgenerator(self):
        def inner(output):
            # 1. find all in the set killlist & loadflow.branches.keys
            # 2. find all in the set killlist & loadflow.busbars.keys
            # 3. kill all the generator linking lines
            #    i.e. kill lines 'X + 2.'

            lf = self.loadflow

            killlist = set([x.strip() for x in self.faillist])
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

                    # print value 
                    if value[7].strip() != "":
                        value[7] = str(float(value[7]) * self.loadlevel)
                    if value[2] in self.genlevels:
                        value[3] = str(float(value[3]) * self.genlevels[value[2]])

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
             
        return inner

    def __str__(self):
        # text =  "[Scenario] " + self.name + " '" + self.loadflow.title + "'\n"
        text =  "[Scenario] " + self.name + " '" + "rts.lf" + "'\n"
        text += as_csv(self.faillist," ") + "\n"
        text += str(self.loadlevel) + "\n"
        for name, value in self.genlevels.items():
            text += name + "=" + str(value) + " " 
        text += "\n"
        if self.result:
            text += str(self.result[0]) + " " + str(self.result[1]) + "\n"
        else:
            text += "\n"
        return text 

# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

def gen_scenario_samples(iterations, scenario):
    """generate N scenario-samples"""
    
    loadflow = Loadflow(open("rts.lf"))
    components = sampler.read(open("rts.net"))

    loadlevel = [buslevel.actual_load2(scenario.loadlevel) for x in range(iterations)]
    faillist = n_unique(sampler.make_sample_generator(components),iterations)
    faillist = zip(faillist,[scenario.faillist for x in range(iterations)])

    # TODO change to ScenarioSample
    return [Scenario("ss"+str(n),loadflow,fl,ll,{}) for n,fl,ll in zip(range(iterations),faillist,loadlevel)]

def solve_scenario_samples(scenariosamples):
    """all simulated"""

    limit = Limits() # TODO set limits properly
    for scenariosample in scenariosamples:
        scenariosample.simulate(limit)
    return None

def gather_scenarios_data(scenariosamples):

    info = {}

    def inner(result_desc):
        if result_desc in info:
            info[result_desc] += 1
        else:
            info[result_desc] = 1

    results = [inner(sample.result[1]) for sample in scenariosamples if not sample.result[0]]

    # for name,val in info:
    #     baaad
        
    return  info
    
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------

def gen_solve_and_save_scenarios(iterations=100, filename="scenarios.csv"):
    scenarios = gen_scenarios(iterations)
    solve_scenarios(scenarios)
    save_scenarios(scenarios, open(filename,"w"))

def load_sample_solve_and_save(iterations=1000, infile="scenarios.csv", outfile="samples.csv"):
    scenarios = load_scenarios(open(infile))
    
    output = open(outfile,"w")

    for scenario in scenarios:
        if scenario.results[0]:
            scenariosamples = gen_scenario_samples(iterations, scenario)
            solve_scenario_samples(scenariosamples)
            output.write(str(gather_scenarios_data(scenariosamples)))
        else:
            output.write("failed scenario")


# >>> iterations = 400
# >>> scenarios = tmp.gen_scenarios(iterations)
# >>> tmp.solve_scenarios(scenarios)
# >>> print tmp.gather_scenarios_data(scenarios)
# {'divergence': 325, 'component out of limits': 74}
