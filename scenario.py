 

def outage_scenario_generator(net_file):
	outage_generator = sampler.make_outage_generator(sampler.read(net_file))
	for kill_list in outage_generator:
		yield Scenario("outage", quantised_05(random_bus_forecast()), kill_list)

def failure_scenario_generator(net_file):
	sample_generator = sampler.make_sample_generator(sampler.read(net_file))
	for kill_list in sample_generator:
		yield Scenario("outage", quantised_05(actual_load2(1.0)), kill_list)


class Scenario:
    """one possible state a base case could be in"""

    def __init__(self, scenario_type, bus_level, kill_list):
    	self.scenario_type = scenario_type
    	self.count = 1
    	self.result = None
    	self.result_reason = ""
    	self.bus_level = bus_level
    	self.kill_list = kill_list

    def __str__(self):
    	return ", ".join([self.count, self.scenario_type, self.result, self.result_reason, self.bus_level] + self.kill_list)

