#! /usr/bin/env python
import csv
import sys 

def main_outage(num, out_stream):
    gen = outage_scenario_generator(open("rts.net"))

    batch = dict()

    for scenario in gen:
        if len(batch) >= num:
            break
        if scenario in batch:
            batch[scenario] += 1
        else:
            batch[scenario] = 1

    for scenario in batch:
        out_stream.write(str(scenario))

def main_simulate(in_stream):
    pass

def main_failure(num, in_stream):
    pass

def main ():
    from optparse import OptionParser

    parser = OptionParser("e.g. python main.py rts.net 100 1000000", 
                          version="1-Oct-09 by James Brooks")
    (options, args) = parser.parse_args()

    if len(args) <= 1:
        parser.error("expected more arguments")

    in_stream = False

    if args[0] == "outage":
        if len(args) != 2:
            parser.error("expected 2 arguments got " + str(len(args)))
        num = int(args[1])
        retval = main_outage(num)

    elif args[0] == "simulate":
        if len(args) != 1:
            parser.error("expected 1 argument got " + str(len(args)))
        retval = main_simulate(in_stream)

    elif args[0] == "failure":
        if len(args) != 2:
            parser.error("expected 2 arguments got " + str(len(args)))
        num = int(args[1])
        retval = main_failure(num, in_stream)

    else:
        parser.error("expected [outage, simulate, failure] got " + str(args[0]))
    
    sys.exit(retval)

if __name__ == "__main__":
    main()

