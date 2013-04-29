import random
from modifiedtestcase import ModifiedTestCase
import unittest
from collections import defaultdict

if False:
    unscheduleable = ["G3", "G7", "G9", "G16", "G25", "G31", "G67",
                      "G73", "G75", "G82", "G91", "G97"]
else:
    unscheduleable = ["G3", "G7", "G9", "G16", "G25", "G31", "G67", "G73",
                      "G75", "G82", "G91", "G97", "G4", "G8", "G10", "G17",
                      "G26", "G32", "G68", "G74", "G76", "G83", "G92", "G98"]


num_wind = len(unscheduleable)
prob_raw = [1, 4, 10, 22, 29, 19, 19, 10, 4]
prob_cum = [sum(prob_raw[:n]) for n in range(1, len(prob_raw)+1)]


def gen_forecast():
    # random between 60 and 140 with probability of each bucket as in prob_raw
    choice = random.randint(0, sum(prob_raw)-1)
    for n, cum in enumerate(prob_cum):
        if choice < cum:
            return n*10+60
    return 140


def random_forecasts():
    return [1 for _ in range(num_wind)]


def random_forecast_errors():
    return [gen_forecast() for _ in range(num_wind)]


#==============================================================================
#
#==============================================================================


class TestRead(ModifiedTestCase):

    def test_1(self):
        buckets_sizes = [60, 70, 80, 90, 100, 110, 120, 130, 140]
        buckets = defaultdict(int)
        for _ in xrange(1000000):
            rfe = random_forecast_errors()
            self.assertEqual(len(rfe), num_wind)
            self.assertLessThan(max(rfe), 141)
            self.assertGreaterThan(min(rfe), 59)
            self.assertEqual(
                len(list(1 for x in rfe if (x not in buckets_sizes))), 0)
            for x in rfe:
                buckets[x] += 1

        buckets_size = float(sum(buckets.values()))
        raw_size = float(sum(prob_raw))

        expected = []
        actual = []

        # print "bucket\texpect\tactual"
        for n, chunk in enumerate(buckets_sizes):
            expected.append(prob_raw[n]/raw_size)
            actual.append(buckets[chunk]/buckets_size)
            # print str(chunk) + "\t",
            # print str(int(prob_raw[n]/raw_size*10000)) + "\t",
            # print str(int(buckets[chunk]/buckets_size*10000)) + "\t"

        # it's fails this all the time but I think it is close enough to the
        # real thing.
        self.assertAlmostEqualList(expected, actual)


#==============================================================================
#
#==============================================================================


if __name__ == '__main__':
    unittest.main()
