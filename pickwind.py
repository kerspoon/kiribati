
"""
Pick from the load flow (not installed capacity) of the starting base case (so
  it is the same for each MCS base-case).

Pick so that You can double the number of itentical generating units on each
bus that are to become 'wind powered'. This is to up the installed capacity
to 20% without changing where the wind farms are.
"""

from loadflow import Loadflow
import string
import random

lf = Loadflow(open("rts.lf"), None)

raw_gens = [x for x in lf.busbars.values() if x[2].strip().startswith("G")]
total_power = sum(float(x[3].strip()) for x in raw_gens)


class Gen(object):
    """docstring for Gen"""
    def __init__(self, name):
        super(Gen, self).__init__()
        self.name = name

    def __str__(self):
        # return string.join(["Gen", self.name, self.bus, str(self.power)], ", ")
        return str(self.power)

gens = []

for raw_gen in raw_gens:
    name = raw_gen[2].strip()
    gen = Gen(name)
    gen.bus = lf.branches["X" + name][4].strip()
    gen.power = float(raw_gen[3].strip())
    gens.append(gen)

print "total power", total_power

busses = dict()

for g in gens:
    if g.bus not in busses:
        busses[g.bus] = []
    busses[g.bus].append(g)


for n, b in busses.items():
    print n + "," + string.join([str(y) for y in b], ",")


included = set()
included_power = 0


for _ in xrange(1, 100):
    b = random.choice(list(busses))
    if b in included:
        continue
    if len(busses[b]) < 2:
        continue

    # print [str(y) for y in busses[b]]

    included.add(b)
    #print included




# end
