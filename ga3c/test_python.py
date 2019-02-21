import numpy as np
import random as rd
from GuardingTerritoryGame import Target

def pwr(x, y):
    return x ** y

def add(x, y):
    return x + y

dispatcher = { 'pwr' : pwr, 'add' : add}
def call_func(func, x, y):
    try:
        return dispatcher[func](x, y)
    except:
        return "Invalid function"

print(call_func('add', 2, 3))
