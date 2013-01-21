#! /usr/bin/env python
# http://code.activestate.com/recipes/190465/

"""xpermutations.py
Generators for calculating a) the permutations of a sequence and
b) the combinations and selections of a number of elements from a
sequence. Uses Python 2.2 generators.

Similar solutions found also in comp.lang.python

Keywords: generator, combination, permutation, selection

See also: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/105962
See also: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66463
See also: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66465
"""


# ---------------------------------------------------------------------------- #
# combinations :: [T], int -> ([T])
def combinations(items, n):
    if n == 0:
        yield []
    else:
        for i in xrange(len(items)):
            for cc in combinations(items[:i] + items[i + 1:], n - 1):
                yield [items[i]] + cc


# ---------------------------------------------------------------------------- #
# uniqueCombinations :: [T], int -> ([T])
def uniqueCombinations(items, n):
    if n == 0:
        yield []
    else:
        for i in xrange(len(items)):
            for cc in uniqueCombinations(items[i + 1:], n - 1):
                yield [items[i]] + cc


# ---------------------------------------------------------------------------- #
# selections :: [T], int -> ([T])
def selections(items, n):
    if n == 0:
        yield []
    else:
        for i in xrange(len(items)):
            for ss in selections(items, n - 1):
                yield [items[i]] + ss


# ---------------------------------------------------------------------------- #
# permutations :: [T] -> ([T])
def permutations(items):
    return combinations(items, len(items))


# ---------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------- #

def examples():
    print "Permutations of 'love'"
    for p in permutations(['l', 'o', 'v', 'e']):
        print ''.join(p)

    print
    print "Combinations of 2 letters from 'love'"
    for c in combinations(['l', 'o', 'v', 'e'], 2):
        print ''.join(c)

    print
    print "Unique Combinations of 2 letters from 'love'"
    for uc in uniqueCombinations(['l', 'o', 'v', 'e'], 2):
        print ''.join(uc)

    print
    print "Selections of 2 letters from 'love'"
    for s in selections(['l', 'o', 'v', 'e'], 2):
        print ''.join(s)

    print
    print map(''.join, list(permutations('done')))
