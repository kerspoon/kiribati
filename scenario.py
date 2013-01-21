import sampler
import misc
from buslevel import quantised_05, random_bus_forecast, actual_load2
from collections import defaultdict
from modifiedtestcase import ModifiedTestCase
import unittest
from StringIO import StringIO
from combinations import uniqueCombinations


def outage_scenario_generator(net_file):
    outage_generator = sampler.make_outage_generator(sampler.read(net_file))
    for kill_list in outage_generator:
        yield Scenario("outage", quantised_05(random_bus_forecast()), kill_list)


def failure_scenario_generator(net_file):
    sample_generator = sampler.make_sample_generator(sampler.read(net_file))
    for kill_list in sample_generator:
        yield Scenario("failure", quantised_05(actual_load2(1.0)), kill_list)


def n_minus_x_generator(x, net_file):
    for kill_list in uniqueCombinations(sampler.read(net_file).keys(), x):
        yield 1, Scenario("n-x", 1.0, kill_list)


def stream_scenario_generator(in_stream):
    for line in in_stream:
        split_line = line.split(", ")
        scenario = scenario_from_csv(", ".join(split_line[1:]))
        yield int(split_line[0]), scenario


def generate_n_unique(generator, num):
    batch = defaultdict(int)
    for scenario in generator:
        if len(batch) >= num:
            break
        batch[str(scenario)] += 1

    new_batch = []
    for scenario, n in batch.items():
        new_batch.append((n, scenario_from_csv(scenario)))
    return new_batch


def scenario_from_csv(text):
    items = [x.strip() for x in text.split(", ")]
    # TODO test this
    scenario = Scenario(items[0], float(items[3]), items[4:])
    if items[1] == "None":
        scenario.result = None
    else:
        scenario.result = (items[1] == "True")
    scenario.result_reason = items[2]
    return scenario


def input_scenario(in_stream):
    return list(stream_scenario_generator(in_stream))


def output_scenario(batch, out_stream):
    for n, scenario in batch:
        out_stream.write(str(n) + ", " + str(scenario) + "\n")


def combine_scenarios(one, other):
    return Scenario("combined", one.bus_level * other.bus_level, one.kill_list | other.kill_list)


class Scenario:
    """one possible state a base case could be in"""

    def __init__(self, scenario_type, bus_level, kill_list):
        self.scenario_type = scenario_type
        self.result = None
        self.result_reason = ""
        self.bus_level = bus_level
        self.kill_list = frozenset(kill_list)

    def __str__(self):
        return misc.as_csv([self.scenario_type, self.result, self.result_reason, self.bus_level] + list(self.kill_list), ", ")


#==============================================================================
#
#==============================================================================


class TestRead(ModifiedTestCase):

    def util_readwrite_match(self, inp):
        batch = list(input_scenario(StringIO(inp)))
        stream = StringIO()
        output_scenario(batch, stream)
        self.assertEqual(stream.getvalue(), inp)

    def test_1(self):
        self.util_readwrite_match("""1, outage, False, bad, 0.55, G49, G32, G22, G12\n""")
        self.util_readwrite_match("""999, failure, True, ok, 1.0\n""")
        self.util_readwrite_match("""999, combined, None, ok, 0.01, A1\n""")
        self.util_readwrite_match("""1, combined, False, component out of limits, 0.525, G31, G66\n""")

#==============================================================================
#
#==============================================================================


if __name__ == '__main__':
    unittest.main()
