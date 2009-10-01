#! /usr/bin/env python
import csv
import sys 
from itertools import islice
from modifiedtestcase import *
from sampler import make_sample_generator, make_outage_generator, read
from newprocess import make_sample_simulator
from pymisc import *

# ---------------------------------------------------------------------------- #
# solved_outages :: dict(name = probability), int -> [[T]]
#         T ::= count, result, descritions, Nfail, fail1, ..., failN
def solved_outages(components,iterations):
    outage_database = n_unique(make_outage_generator(components),iterations)
    simulate = make_sample_simulator()
    results = map(simulate,outage_database)
    
    processed_database = []
    for res,(fails,count) in zip(results,outage_database.items()):
        processed_database.append([count] + list(res) + [len(fails)] + list(fails))
    return processed_database

# ---------------------------------------------------------------------------- #
# remove_failed :: [[T]] -> [[T]]
#         T ::= count, result, descritions, Nfail, fail1, ..., failN
def remove_failed(processed_database):
    """remove all the ones that don't load flow"""
    def killer(item):
        return item[1]
    return filter(killer,processed_database)

# ---------------------------------------------------------------------------- #
# run :: str, int, int -> None
def run(network_file_name,num_base_cases,num_samples):
    """Generate base cases and sample each of those
    then simulate the results.
    """
    
    print "# Sampling", network_file_name
    print "# Base Cases", num_base_cases
    print "# Samples", num_samples
    print 

    # read in the list of components and their probability of failure 
    components = read(open(network_file_name))

    # get 100 solved base cases
    outage_database = solved_outages(components,num_base_cases)

    # remove all the ones that don't load flow
    outage_database = remove_failed(outage_database)

    # prepare the sampler 
    sampler = make_sample_generator(components)

    # prepare the simulator
    simulate = make_sample_simulator()

    # sample each of these 1000 times
    for N,base_case in enumerate(outage_database):

        # extract the base case item that have failed
        base_fail_set = set(base_case[4:])

        print 
        csv_print(["# processing " + str(N)] + list(base_fail_set))

        # grab 1000 samples
        n_samples = islice(sampler,num_samples)
        
        # combine with the base_case
        contingincies = [base_fail_set|sample for sample in n_samples]

        # remove duplicates
        contingincy_database = reduce(countedadd,contingincies,{})

        # simulate each contingency 
        results = map(simulate,contingincy_database)

        for result,(fails,count) in zip(results,contingincy_database.items()):
            infoline = [count] + list(result) + [len(fails)] + list(fails)
            csv_print(infoline)


# run("rts.net",1,10000)

def main ():
    from optparse import OptionParser

    parser = OptionParser("e.g. python main.py rts.net 100 1000000", 
                          version="1-Oct-09 by James Brooks")
    (options, args) = parser.parse_args()

    if len(args) != 3:
        parser.error("expected 3 arguments got " + str(len(args)))

    retval = run(args[0], int(args[1]), int(args[2]))
    sys.exit(retval)

if __name__ == "__main__":
    main()
