import misc

from modifiedtestcase import ModifiedTestCase
import unittest
from StringIO import StringIO

# This file is to take a two sets of summary files and find a common set of id number for the cases so they can be compared.
#
# First file:
#
#   id, load-level, ...kill-list...
#    1, 0.7, G17, G85, G4, G13, G10,
#    2, 0.6, G31, G22, G34, G57, G56, G72, A8, G78,
#    3, 0.4, G17, G76, G57, G9,
#    4, 0.6, G19, G82, G41, G68, G71, G91, C25-1, G66, G89,
#
# Second File:
#
#  num-fail, count, type, result, reason, load-level, ...kill-list...
#   14, 1, outage, TRUE, ok, 0.4, G17, G76, G57, G9
#   23, 1, outage, TRUE, ok, 0.7, G17, G85, G4, G13, G10
#   12, 1, outage, TRUE, ok, 0.6, G19, G82, G41, G68, G71, G91, C25-1, G66, G89
#   19, 1, outage, TRUE, ok, 0.6, G31, G22, G34, G57, G56, G72, A8, G78
#
# Output
#
#  id, num-fail, result, reason
#   3, 14, TRUE, ok
#   1, 23, TRUE, ok
#   4, 12, TRUE, ok
#   2, 19, TRUE, ok
#


def scenario_from_csv(items):
    return Scenario(float(items[0]), items[1:])


class Scenario:
    """one possible state a base case could be in"""

    def __init__(self, bus_level, kill_list):
        self.bus_level = bus_level
        self.kill_list = frozenset(kill_list)
        assert 0 <= self.bus_level <= 1

    def __str__(self):
        return misc.as_csv([self.bus_level] + list(self.kill_list), ", ")

    def __eq__(self, other):
        return self.bus_level == other.bus_level and self.kill_list == other.kill_list

    def __hash__(self):
        return hash((self.bus_level, self.kill_list))


def main(infilea, infileb, outfile):
    summary = dict()

    for line in infilea:
        # id, ...rest..
        items = [x.strip() for x in line.split(", ")]
        scen_id = int(items[0])
        scenario = scenario_from_csv(items[1:])
        summary[scenario] = (scen_id, 0, "NONE", "")

    # for k, v in summary.items():
    #     print str(k) + misc.as_csv(v, ", ")

    for line in infileb:
        # num-fail, count, type, result, reason, ..rest..
        # 1313  1    outage TRUE     ok 0.7  G17     G85     G4  G13     G10
        items = [x.strip() for x in line.split(", ")]

        num_fail = int(items[0])
        assert 0 <= num_fail <= 10000000
        result = items[3]
        assert result in set(["TRUE", "FALSE", "NONE"])
        reason = items[4]

        scenario = scenario_from_csv(items[5:])

        # print str(scenario)
        # for k, v in summary.items():
        #     print str(k)
        #     print scenario == k, str(scenario) == str(k)

        assert scenario in summary.keys(), str(scenario)
        assert summary[scenario][1] == 0, str(scenario)

        scen_id = summary[scenario][0]
        info = (scen_id, num_fail, result, reason)
        summary[scenario] = info

    for scenario, info in summary.items():
        outfile.write(misc.as_csv(info, ", ") + "\n")


#==============================================================================
#
#==============================================================================


class TestRead(ModifiedTestCase):

    def test_1(self):

        filea = StringIO("""1, 0.7, G17, G85, G4, G13, G10
2, 0.6, G31, G22, G34, G57, G56, G72, A8, G78
3, 0.4, G17, G76, G57, G9
4, 0.6, G19, G82, G41, G68, G71, G91, C25-1, G66, G89""")

        fileb = StringIO("""14, 1, outage, TRUE, ok, 0.4, G17, G76, G57, G9
23, 1, outage, TRUE, ok, 0.7, G17, G85, G4, G13, G10
12, 1, outage, TRUE, ok, 0.6, G19, G82, G41, G68, G71, G91, C25-1, G66, G89
19, 1, outage, TRUE, ok, 0.6, G31, G22, G34, G57, G56, G72, A8, G78""")

        expected = """3, 14, TRUE, ok
1, 23, TRUE, ok
4, 12, TRUE, ok
2, 19, TRUE, ok
"""

        stream = StringIO()

        main(filea, fileb, stream)

        self.assertEqual(stream.getvalue(), expected)


#==============================================================================
#
#==============================================================================

if __name__ == "__main__":
    unittest.main()
    main()
