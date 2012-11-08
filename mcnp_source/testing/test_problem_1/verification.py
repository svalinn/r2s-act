#! /usr/bin/env python

# This script plots the contents of source_debug
# Specifically a scatter plot of x,y coordinates of started particles is made

from pylab import *

with open("source_debug", 'r') as fr:
    x = list()
    y = list()
    
    for line in fr:
        lineparts = line.split()
        x.append(float(lineparts[0]))
        y.append(float(lineparts[1]))

scatter(x,y)
show()
