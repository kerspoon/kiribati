#! /usr/bin/env python
import csv
import sys 
from itertools import islice

# ---------------------------------------------------------------------------- #
# countedadd :: {set(T)=int}, set(T) -> {set(T)=int}
def countedadd(database,sample):
    """remove all duplicates by adding to a database"""
    if frozenset(sample) in database:
        database[frozenset(sample)] += 1
    else:
        database[frozenset(sample)] = 1
    return database

# ---------------------------------------------------------------------------- #
# n_unique :: (set(T)), int, {set(T)=int} -> {frozenset(T)=int}
def n_unique(func,iterations,database={}):
    """grab N from the generator 'func' and remove the duplicates"""
    smp = islice(func,iterations)
    return reduce(countedadd,smp,database)

# ---------------------------------------------------------------------------- #
# as_csv :: [T], str -> str
def as_csv(iterable,sep = ", "):
    """a string of each item seperated by commas"""
    iterable = list(iterable)
    res = ""
    if len(iterable) == 0:
        return ""
    for item in iterable[:-1]:
        res += str(item) + sep
    return res + str(iterable[len(iterable)-1])

# ---------------------------------------------------------------------------- #
# csv_print :: [T], str -> None
def csv_print(iterable,sep = ", "):
    """print each item seperated by commas"""
    print as_csv(iterable,sep)

# ---------------------------------------------------------------------------- #
# dict_inc :: [T1 = T2], T1, T2 -> None
def dict_inc(dictionary,key,value):
    """increment a value in a dictionary
    or set it if not already done"""
    if key in dictionary:
        dictionary[key] += value
    else:
        dictionary[key] = value
        
# ---------------------------------------------------------------------------- #
# dict_get :: [T1 = T2], T1, T2 -> T2 
def dict_get(dictionary,key,default=0):
    """get a value from a dict or return default"""
    if key in dictionary:
        return dictionary[key]
    else:
        return default

# ---------------------------------------------------------------------------- #
# dict_sort_by_values :: {T1 = T2} -> [(T1, T2)]
def dict_sort_by_values(dictionary):
    def by_values(first,second):
        return cmp(second[1],first[1])
    return sorted(dictionary.items(), by_values)

# ---------------------------------------------------------------------------- #
# each_with_each_other [T], (T, T -> None) -> None
def each_with_each_other(iterable,func):
    for N,first in enumerate(iterable):
        for second in iterable[N+1:]:
            func(first,second)


# ---------------------------------------------------------------------------- #
# ---------------------------------------------------------------------------- #

def TEST_dict_sort_by_values():
    print dict_sort_by_values(dict(a=2,b=1,c=7,d=0))
# TEST_dict_sort_by_values()

def TEST_each_with_each_other():
    def testprint(first,second):
        print first, second
    each_with_each_other([1,2,3,4,5],testprint)
# TEST_each_with_each_other()

