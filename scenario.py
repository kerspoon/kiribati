import sampler
import misc
from buslevel import quantised_05, random_bus_forecast, actual_load2

def outage_scenario_generator(net_file):
	outage_generator = sampler.make_outage_generator(sampler.read(net_file))
	for kill_list in outage_generator:
		yield Scenario("outage", quantised_05(random_bus_forecast()), kill_list)

def failure_scenario_generator(net_file):
	sample_generator = sampler.make_sample_generator(sampler.read(net_file))
	for kill_list in sample_generator:
		yield Scenario("outage", quantised_05(actual_load2(1.0)), kill_list)


def scenario_from_csv(text):
    items = text.split(", ")
    # TODO test this
    return Scenario(items[0], items[1], items[2], items[3], items[4:])

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

