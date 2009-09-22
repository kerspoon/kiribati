#! /usr/bin/env python
from combinations import uniqueCombinations
from sampler import read
from newprocess import make_sample_simulator
from math import factorial
from pymisc import csv_print


def examples():

    network_file_name = "rts.net"

    # read in the list of components and their probability of failure 
    components = read(open(network_file_name))

    N1 = list(uniqueCombinations(components.keys(),1))
    N2 = list(uniqueCombinations(components.keys(),2))

    def comb(n,k):
        return factorial(n) / (factorial(n-k) * factorial(k))

    print "length of components", len(components) 
    print "length of N-1", len(N1)
    print
    print "length of N-2", len(N2)

    assert(len(N1) == len(components))
    assert(len(N2) == comb(len(components),2))

def solveN1(network_file_name="rts.net"):
    
    print 
    print("# processing N-1")

    network_file_name = "rts.net"

    # read in the list of components and their probability of failure 
    components = read(open(network_file_name))

    # prepare the simulator
    simulate = make_sample_simulator()

    # grab the samples
    n_samples = list(uniqueCombinations(components.keys(),1))

    # simulate each sample 
    results = map(simulate,n_samples)

    for result,fails in zip(results,n_samples):
        infoline = [1] + list(result) + [len(fails)] + list(fails)
        csv_print(infoline)
solveN1()
