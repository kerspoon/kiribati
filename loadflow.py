#! /usr/bin/env python

import csv
import string
import StringIO
import subprocess
import sys 
import unittest

from misc import EnsureEqual, Ensure, EnsureNotEqual, EnsureIn, Error
from modifiedtestcase import ModifiedTestCase

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

        self.line_losses = 0
        
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

                # calcluaste line losses
                if row[3].strip() != "":
                    self.line_losses += float(row[3])
                if row[7].strip() != "":
                    self.line_losses -= float(row[7])
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

        # fix power mismatch
        names = {}
        powers = []
        load_powers = []

        min_limit = []
        max_limit = []

        for name, value in self.busbars.items():
            if name not in killlist:
                if value[3].strip() != "":
                    names[name] = len(powers)
                    powers.append(float(value[3]))
                    min_limit.append(0) # no minimum level for a generator
                    max_limit.append(float(self.limits_checker.gen_limit[name]))
                if value[7].strip() != "":
                    load_powers.append(float(value[7]))

        # mismatch is sum(load_power) + line_losses - sum(gen_power) after: fix mismatch, bus_level and killed.
        mismatch = (sum(load_powers) * scenario.bus_level) + self.line_losses - sum(powers)
        fixed_powers = fix_mismatch(mismatch, powers, min_limit, max_limit)
        # line for `main.py test` to check with notes.
        # print "mismatch", 8550 - (sum(load_powers) * scenario.bus_level), 8997.9-sum(fixed_powers)

        # ignore everything in killlist, print the rest
        for (name, value) in self.busbars.items():
            if name not in buskill:
                # don't modify self
                new_value = value[:]

                # if we have a load power - times it by the bus_level
                if new_value[7].strip() != "":
                    new_value[7] = str(float(new_value[7]) * scenario.bus_level)

                # if we have a new generator power get it from fix mismatch
                if name in names:
                    new_value[3] = str(fixed_powers[names[name]])

                # print it out
                # print len(new_value), " ".join(new_value)

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
        try: 
            proc = subprocess.Popen('./loadflow -i10000 -t -y',
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    stdin=subprocess.PIPE
                                    )

            try:
                self.lfgenerator(proc.stdin, sample)
            except Error, e:
                # stop the comms
                proc.kill()
                outs, errs = proc.communicate()
                # remove `,` from message
                return (False, ''.join(c for c in e.msg if c not in ','))

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

        except Exception, e:
            # stop the comms
            proc.kill()
            outs, errs = proc.communicate()
            return (False, "other error " + ''.join(c for c in e.msg if c not in ','))


#==============================================================================
#
#==============================================================================


def fix_mismatch(mismatch, power, min_limit, max_limit):
    """
    func fix_mismatch :: Real, [Real], [Real], [Real] -> [Real]
    
    change the total generated power by `mismatch`.
    Do this based upon current power of each generator
    taking into account its limits.
    Returns a list of new generator powers
    """

    EnsureEqual(len(power), len(min_limit))
    EnsureEqual(len(power), len(max_limit))

    if mismatch == 0:
        return power
    
    done = [False for _ in range(len(power))]
    result = [0.0 for _ in range(len(power))]
     
    def find_limit_max(m):
        """find the index of the first generator that will
        be limited. or None """
        for n in range(len(done)):
            if (not done[n]) and (power[n] * m > max_limit[n]):
                return n
        return None
     
    def find_limit_min(m):
        """find the index of the first generator that will
        be limited. or None """
        for n in range(len(done)):
            if (not done[n]) and (power[n] * m < min_limit[n]):
                return n
        return None

    Ensure(sum(min_limit) < sum(power) + mismatch < sum(max_limit),
           "mismatch of %f is outside limits (%f < %f < %f)" % (mismatch, sum(min_limit), sum(power) + mismatch , sum(max_limit)))

    # print "mismatch\t%f" % mismatch
    # print "total gen\t%f" % sum(power)
    # print "total min gen\t%f" % sum(min_limit)
    # print "total max gen\t%f" % sum(max_limit)
    # print "-"*10
    # print "power\t%s" % as_csv(power,"\t")
    # print "min_limit\t%s" % as_csv(min_limit,"\t")
    # print "max_limit\t%s" % as_csv(max_limit,"\t")
    # if mismatch > 0:
    #     print as_csv([b-a for a,b in zip(power, max_limit)], "\t")
    #     print sum(max_limit) - sum(power)
    # else:
    #     print as_csv([b-a for a,b in zip(power, min_limit)], "\t")
    #     print sum(power) - sum(min_limit)
        

    # deal with each generator that will be limited
    while True:
        Ensure(not all(done), "programmer error")

        # print "fix_mismatch", len([1 for x in done if x])

        total_gen = sum(power[i] for i in range(len(done)) if not done[i])
        EnsureNotEqual(total_gen, 0)
        
        multiplier = 1.0 + (mismatch / total_gen)

        # we shouldn't really care about the miltiplier as long as 
        # the limits are being met should we?
        Ensure(0 <= multiplier <= 5, "vague sanity check")

        if mismatch < 0:
            idx_gen = find_limit_min(multiplier)
            if idx_gen is None:
                break

            # print "generator hit min limit:", idx_gen
            result[idx_gen] = min_limit[idx_gen]
            mismatch -= result[idx_gen] - power[idx_gen]
            done[idx_gen] = True
        else:
            idx_gen = find_limit_max(multiplier)
            if idx_gen is None:
                break

            # print "generator hit max limit:", idx_gen
            result[idx_gen] = max_limit[idx_gen]
            mismatch -= result[idx_gen] - power[idx_gen]
            done[idx_gen] = True

    # deal with all the other generators 
    # knowing that none of them will limit
    for idx in range(len(power)):
        if not done[idx]:
            # print "set generator", idx
            result[idx] = power[idx] * multiplier
            mismatch -= result[idx] - power[idx]
            done[idx] = True
  
    # check nothing is out of limits 
    for idx in range(len(power)):
        Ensure(power[idx] == 0 or (min_limit[idx] <= power[idx] <= max_limit[idx]),
               "Power (%d) out of limit (%f<=%f<=%f)" % (idx,
                                                         min_limit[idx],
                                                         power[idx],
                                                         max_limit[idx]))
    Ensure(mismatch < 0.001, "should be much mismatch left after fixing it")
    Ensure(all(done), "should have fixed everything")
    
    return result


#==============================================================================
#
#==============================================================================


class Test_fix_mismatch(ModifiedTestCase):

    def test_1(self):
        p_list = [1, 1, 1, 1, 1]
        max_list = [2, 2, 2, 2, 2]
        min_list = [-2, -2, -2, -2, -2]

        res = fix_mismatch(0, p_list, min_list, max_list)
        self.assertAlmostEqualList(res, p_list)
      
    def test_2(self):
        p_list = [1, 1]
        max_list = [2, 2]
        min_list = [-2, -2]

        res = fix_mismatch(1.0, p_list, min_list, max_list)
        self.assertAlmostEqualList(res, [1.5, 1.5])

    def test_3(self):
        p_list = [1, 0, 1]
        max_list = [2, 2, 2]
        min_list = [-2, -2, -2]
        res = fix_mismatch(1.0, p_list, min_list, max_list)
        self.assertAlmostEqualList(res, [1.5, 0, 1.5])

    def test_4(self):
        p_list = [2, 4]
        max_list = [8, 8]
        min_list = [-8, -8]
        res = fix_mismatch(3.0, p_list, min_list, max_list)
        self.assertAlmostEqualList(res, [3, 6])

    def test_5(self):
        p_list = [2, 4]
        max_list = [8, 5]
        min_list = [-8, -5]
        res = fix_mismatch(3.0, p_list, min_list, max_list)
        self.assertAlmostEqualList(res, [4, 5])

    def test_6(self):
        p_list = [1, 1]
        max_list = [2, 2]
        min_list = [-2, -2]

        res = fix_mismatch(-1.0, p_list, min_list, max_list)
        self.assertAlmostEqualList(res, [0.5, 0.5])

    def test_7(self):
        p_list = [1, 0, 1]
        max_list = [2, 2, 2]
        min_list = [-2, -2, -2]
        res = fix_mismatch(-1.0, p_list, min_list, max_list)
        self.assertAlmostEqualList(res, [0.5, 0, 0.5])

    def test_8(self):
        p_list = [2, 4]
        max_list = [8, 8]
        min_list = [-8, -8]
        res = fix_mismatch(-3.0, p_list, min_list, max_list)
        self.assertAlmostEqualList(res, [1, 2])

    def test_9(self):
        p_list = [2, 4]
        max_list = [8, 5]
        min_list = [-1, 3]
        res = fix_mismatch(-3.0, p_list, min_list, max_list)
        self.assertAlmostEqualList(res, [0, 3])


#==============================================================================
#
#==============================================================================


if __name__ == '__main__':
    unittest.main()
