#! /usr/bin/env python
#import unittest
#import StringIO
import csv
import math
import sys 
from modifiedtestcase import *
from pymisc import *

# probability_failure :: real(>0) -> real(0,1)
def probability_failure(failrate):
    """returns the probability of a component 
    failing given the failure rate"""
    assert(failrate >= 0)
    time = 1.0
    res = math.exp( - failrate * time )
    assert(0 <= res <= 1)
    return res

# probability_outage :: real(>0), real(>0) -> real(0,1)
def probability_outage(mttf, mttr):
    """returns the probability of a component 
    being on outage given the mean time to fail
    and restore"""
    assert(mttf >= 0)
    assert(mttr >= 0)
    res = mttf / (mttf + mttr)
    assert(0 <= res <= 1)
    return res

# read_branch :: [str] -> (str, real(>0), real(>0), real(>0)) | None
def read_branch(line):
    ReadAssert(line[0].strip() == "line", "line type incorrect")
    name = line[1].strip()
    if line[4].strip() == "-1" or line[5].strip() == '-1':
        return None
    ReadAssert(float(line[4]) != 0,"cannot have zero fail rate")
    failrate = float(line[4]) / (24.0 * 365.0)
    mttf = ((24.0 * 365.0)/ float(line[4]))
    mttr = float(line[5])
    ReadAssert(len(name) != 0,"zero length name")
    ReadAssert(failrate > 0,"failrate must be real greater than zero")
    ReadAssert(mttf > 0,"mttf must be real greater than zero")
    ReadAssert(mttr > 0,"mttr must be real greater than zero")
    return (name, failrate, mttf, mttr)

# read_gen :: [str] -> (str, real(>0), real(>0), real(>0)) | None
def read_gen(line):
    ReadAssert(line[0].strip() == "gen", "line type incorrect")
    name = line[1].strip()
    if line[3].strip() == "-1" or line[4].strip() == "-1":
        return None
    ReadAssert(float(line[3]) != 0,"cannot have zero mttf")
    failrate = 1.0 / float(line[3])
    mttf = float(line[3])
    mttr = float(line[4])
    ReadAssert(len(name) != 0,"zero length name")
    ReadAssert(failrate > 0,"failrate must be real greater than zero")
    ReadAssert(mttf > 0,"mttf must be real greater than zero")
    ReadAssert(mttr > 0,"mttr must be real greater than zero")
    return (name, failrate, mttf, mttr)

# read_bus :: [str] -> (str, real(>0), real(>0), real(>0)) | None
def read_bus(line):
    ReadAssert(line[0].strip() == "bus", "line type incorrect")
    ReadAssert(len(line) == 2,"busbars must have 2 columns")
    name = line[1].strip()

    BUS_FAIL_RATE = 0.025
    BUS_REPAIR_RATE = 13

    failrate = BUS_FAIL_RATE / (24.0 * 365.0)
    mttf = (24.0 * 365.0) / BUS_FAIL_RATE
    mttr = BUS_REPAIR_RATE
    ReadAssert(len(name) != 0,"zero length name")
    ReadAssert(failrate > 0,"failrate must be real greater than zero")
    ReadAssert(mttf > 0,"mttf must be real greater than zero")
    ReadAssert(mttr > 0,"mttr must be real greater than zero")
    return (name, failrate, mttf, mttr)

# read :: file_handler -> dict(name = probability)
#         name ::= str
#         probability ::= (real(0,1),real(0,1))
def read (infile):
    """processes a file into name, probability for 
    each component"""
    components = {}
    for row in csv.reader(infile):
        if len(row) <= 1:
            continue
        linetype = row[0].strip()
        if linetype == 'line':
            readinfo = read_branch(row)
        elif linetype == 'gen':
            readinfo = read_gen(row)
        elif linetype == 'bus':
            readinfo = read_bus(row)
        else:
            continue # probably a comment 
        if readinfo != None:
            name, failrate, mttf, mttr = readinfo
            components[name] = (probability_failure(failrate),
                                probability_outage(mttf,mttr))

    for name,(pfail,pout) in components.items():
        ReadAssert(len(name.strip()) != 0,"zero length name")
        ReadAssert(0 <= pfail <= 1,"probability must be real bewteen zero and one")
        ReadAssert(0 <= pout <= 1,"probability must be real bewteen zero and one")
    return components

# sample_failures :: dict(name = probability), (Real(0,1) -> Bool) -> set(name)
#         name ::= str
#         probability ::= (real(0,1),real(0,1))
# 
# this is the join slowest function of the program, 
# along with running the load flow program
def sample_failures(components, rnd):
    # return set([ name for name,(pfail,pout) in components.items() if rnd(pfail)])
    return set([name for name,(pfail,pout) in components.items() if random.random() > pfail])
    # res = set()
    # for name,(pfail,pout) in components.items():
    #     if random.random() > pfail:
    #       res.add(name)
    # return res

# get_crow :: None -> dict(str = str)
def get_crow():
    return { 'A12-1' : "A13-2",
             'A13-2' : "A12-1",
             'A18'   : "A20",
             'A20'   : "A18",
             'A25-1' : "A25-2",
             'A25-2' : "A25-1",
             'A30'   : "A34",
             'A34'   : "A30",
             'A31-1' : "A31-2",
             'A31-2' : "A31-1",
             'A32-1' : "A32-2",
             'A32-2' : "A32-1",
             'A33-1' : "A33-2",
             'A33-2' : "A33-1",
             'B12-1' : "B13-2",
             'B13-2' : "B12-1",
             'B18'   : "B20",
             'B20'   : "B18",
             'B25-1' : "B25-2",
             'B25-2' : "B25-1",
             'B30'   : "B34",
             'B34'   : "B30",
             'B31-1' : "B31-2",
             'B31-2' : "B31-1",
             'B32-1' : "B32-2",
             'B32-2' : "B32-1",
             'B33-1' : "B33-2",
             'B33-2' : "B33-1",
             'C12-1' : "C13-2",
             'C13-2' : "C12-1",
             'C18'   : "C20",
             'C20'   : "C18",
             'C25-1' : "C25-2",
             'C25-2' : "C25-1",
             'C30'   : "C34",
             'C34'   : "C30",
             'C31-1' : "C31-2",
             'C31-2' : "C31-1",
             'C32-1' : "C32-2",
             'C32-2' : "C32-1",
             'C33-1' : "C33-2",
             'C33-2' : "C33-1"}

# crow_failures :: set(str), (Real(0,1) -> Bool) -> set(str)
def crow_failures(failures,rnd):
    crow = get_crow()
    return set([crow[component] for component in failures if component in crow and rnd(1-0.075)])

# sample_outages :: dict(name = probability), (Real(0,1) -> Bool)-> set(name)
#         name ::= str
#         probability ::= (real(0,1),real(0,1))
def sample_outages(components, rnd):
    return set([name for name, (pfail, pout) in components.items() if rnd(pout)])

# ---------------------------------------------------------------------------- #
# make_outage_generator :: dict(name = probability) :: (set(str))
#         name ::= str
#         probability ::= (real(0,1),real(0,1))
def make_outage_generator(components):
    """a generator function that makes outages"""
    while(True):
        outages = sample_outages(components,rnd_random)
        yield outages | crow_failures(outages,rnd_random)

# ---------------------------------------------------------------------------- #
# make_sample_generator :: dict(name = probability) -> (set(str))
#         name ::= str
#         probability ::= (real(0,1),real(0,1))
def make_sample_generator(components):
    """a generator function that makes samples"""
    while(True):
        failures = sample_failures(components,rnd_random)
        yield failures | crow_failures(failures,rnd_random)

# ---------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------- #

class Tester_ReadBranch(ModifiedTestCase):
    def test_calc(self):
        def inner(num):
            line = "line, AB3, 0, 0, nan, 50, 0".split(",")
            line[4] = str(num)
            name, rate, mttf, mttr = read_branch(line)
            self.assertAlmostEqual(rate,num/(24.0 * 365.0))
        try_with = [.1, .4, .6, .8, 1, 1.5, 2, 10]
        for num in try_with:
            inner(num)

    def test_a(self):
        line = "".split(",")
        self.assertRaisesEx(ReadError, read_branch, line, exc_args=(("line type incorrect",)))
    def test_b(self):
        line = "line, AB3, 0, 0, .5, 50, 0".split(",")
        name, rate, mttf, mttr = read_branch(line)
        self.assertEqual(name,"AB3")
        self.assertAlmostEqual(rate,0.5/(24.0 * 365.0))
    def test_c(self):
        line = "gen, G1, 0, 0, 0, U20".split(",")
        self.assertRaisesEx(ReadError, read_branch, line, exc_args=(("line type incorrect",)))
    def test_d(self):
        line = "line, , 0, 0, 0.5, 50, 0".split(",")
        self.assertRaisesEx(ReadError, read_branch, line, exc_args=(("zero length name",)))

class Tester_ReadGen(ModifiedTestCase):
    """
    read generator testing functions.
    """
    def test_a(self):
        line = "".split(",")
        self.assertRaisesEx(ReadError, read_gen, line, exc_args=(("line type incorrect",)))
    def test_b(self):
        line = "gen, G1, 0, 1000, 100, U20".split(",")
        name, rate, mttf, mttr = read_gen(line)
        self.assertEqual(name,"G1")
        self.assertAlmostEqual(rate,1.0/1000)
    def test_c(self):
        line = "line, AB3, 0, 0, .5, 0, 0".split(",")
        self.assertRaisesEx(ReadError, read_gen, line, exc_args=(("line type incorrect",)))
    def test_d(self):
        line = "gen, , 0, 1000, 50 , 0, 0".split(",")
        self.assertRaisesEx(ReadError, read_gen, line, exc_args=(("zero length name",)))
    def test_calc(self):
        def inner(num):
            line = "gen, G1, 0, nan, 50, U20".split(",")
            line[3] = str(num)
            name, rate, mttf, mttr = read_gen(line)
            self.assertAlmostEqual(rate,1.0/num)
        try_with = [.1, .4, .6, .8, 1, 1.5, 2, 10, 25, 100, 1000, 2500]
        for num in try_with:
            inner(num)

class Tester_ReadBus(ModifiedTestCase):
    def test_a(self):
        line = "".split(",")
        self.assertRaisesEx(ReadError, read_bus, line, exc_args=(("line type incorrect",)))
    def test_b(self):
        line = "bus, 101".split(",")
        name, rate, mttf, mttr = read_bus(line)
        self.assertEqual(name,"101")
        self.assertAlmostEqual(rate,0.025 / (24.0 * 365.0))
        self.assertAlmostEqual(mttf,(24.0 * 365.0)/ 0.025)
        self.assertAlmostEqual(mttr,13)
    def test_c(self):
        line = "bus, ".split(",")
        self.assertRaisesEx(ReadError, read_bus, line, exc_args=(("zero length name",)))
        

class Tester_Probability(ModifiedTestCase):
    """
    probability testing functions.
    """
    pass 

class Tester_Read(ModifiedTestCase):
    def test_a(self):
        components = read(mockfile(""))
        self.assertEqual(len(components),0)
    def test_b(self):
        components = read(mockfile("""
        gen, G1, 0, 1000, 100, U20"""))
        self.assertEqual(set(components), set(["G1"]))
        self.assertAlmostEqual(components.values()[0][0],0.99900,5)

class Tester_Sample_Failures(ModifiedTestCase):
    def test_a(self):
        components = {'A1':(0.5,1), 'A2':(0.7,1), 'A3':(0.9,1)}
        self.assertEqual(set(sample_failures(components,rnd_True)), set(components))

    def test_b(self):
        components = {'A1':(0.5,1), 'A2':(0.7,1), 'A3':(0.9,1)}
        self.assertEqual(len(sample_failures(components,rnd_False)), 0)

    def test_c(self):
        components = {'A1':(0,1), 'A2':(0,1), 'A3':(0,1), 'A3':(0,1), 'A4':(0,1)}
        rnd = Generate_rnd_sequence([0.28, 0.72, 0.96, 0.37, 0.08, 
                            0.65, 0.05, 0.36, 0.00, 0.66])
        self.assertEqual(set(sample_failures(components,rnd)), set(components))
    
    def test_d(self):
        components = {'A1':(1,1), 'A2':(1,1), 'A3':(1,1), 'A3':(1,1), 'A4':(1,1)}
        rnd = Generate_rnd_sequence([0.28, 0.72, 0.96, 0.37, 0.08, 
                            0.65, 0.05, 0.36, 0.00, 0.66])
        self.assertEqual(len(sample_failures(components,rnd)), 0)

    def test_e(self):
        components = {'A1':(0.5,1), 'A2':(0.5,1), 'A3':(0.5,1), 'A3':(0.5,1), 'A4':(0.5,1)}
        rnd = Generate_rnd_sequence([0.28, 0.72, 0.96, 0.37, 0.08, 
                            0.65, 0.05, 0.36, 0.00, 0.66])
        self.assertEqual(set(sample_failures(components,rnd)), set("A2 A3".split()))

    def test_f(self):
        prob = 0.5
        components = {}
        for x in range(10000):
            components["A" + str(x)] = (prob,1)

        for x in range(10):
            # this is a 'fuzzy test' it may 
            # fail sometimes but should pass 
            # most of the time.

            sampled_num = len(sample_failures(components,rnd_random))
            expected_num = len(components)*(1-prob)
            allowed_mismatch = 1 + len(components)/80

            message = "expected " + str(expected_num) 
            message += ' got ' + str(sampled_num) 
            message += " allowed-mismatch " + str(allowed_mismatch)

            # print message
            self.assert_(abs(sampled_num - expected_num)  < allowed_mismatch, message)

    def test_g(self):
        prob = 0.8
        components = {}
        for x in range(10000):
            components["A" + str(x)] = (prob,1)

        for x in range(10):
            # this is a 'fuzzy test' it may 
            # fail sometimes but should pass 
            # most of the time.

            sampled_num = len(sample_failures(components,rnd_random))
            expected_num = len(components)*(1-prob)
            allowed_mismatch = 1 + len(components)/80

            message = "expected " + str(expected_num) 
            message += ' got ' + str(sampled_num) 
            message += " allowed-mismatch " + str(allowed_mismatch)

            # print message
            self.assert_(abs(sampled_num - expected_num)  < allowed_mismatch, message)

class test_crow_failures(ModifiedTestCase):
    def test_a(self):
        failures = set(['A18','A20','A30'])
        matches = set(['A20','A18','A34'])
        self.assertEqual(crow_failures(failures,rnd_True), matches)

    def test_b(self):
        failures = set(['A18','A20','A30','ZZZ'])
        self.assertEqual(len(crow_failures(failures,rnd_False)), 0)

    def test_c(self):
        failures = set(['A18','A20','A30','ZZZ'])
        matches = set(['A20','A18','A34'])
        self.assertEqual(crow_failures(failures,rnd_True), matches)

    def test_d(self):
        prob = 1-0.075
        rnd = Generate_rnd_sequence([prob+0.001])
        failures = set(['A18'])
        matches = set(['A20'])
        self.assertEqual(crow_failures(failures,rnd), matches)

    def test_e(self):
        prob = 1-0.075
        rnd = Generate_rnd_sequence([prob-0.001])
        failures = set(['A18'])
        matches = set([])
        self.assertEqual(crow_failures(failures,rnd), matches)

    def test_f(self):
        prob = 1-0.075
        failures = set(get_crow())
        sampled_num = 0 
        repeat_count = 1000
        for x in range(repeat_count):
            # this is a 'fuzzy test' it may 
            # fail sometimes but should pass 
            # most of the time.

            sampled_num += len(crow_failures(failures,rnd_random))

        expected_num = len(failures)*(1-prob)*repeat_count
        allowed_mismatch = 80

        message = "expected " + str(expected_num) 
        message += ' got ' + str(sampled_num) 
        message += " allowed-mismatch " + str(allowed_mismatch)
        # print message
        
        self.assert_(abs(sampled_num - expected_num) < allowed_mismatch, message)

def examples(n=100):
    components = read(open("rts.net"))
    sampler = make_sample_generator(components)
    for ctg in n_unique(sampler,n):
           csv_print(ctg,", ")

if __name__ == '__main__':
    unittest.main()
    examples(100)

