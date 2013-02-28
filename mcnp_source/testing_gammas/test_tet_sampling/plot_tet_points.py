#! /usr/bin/env python

import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

from optparse import OptionParser

def randrange(n, vmin, vmax):
    return (vmax-vmin)*np.random.rand(n) + vmin

def plot(file):
    """
    """

    fig = plt.figure()

    ax = fig.add_subplot(111, projection='3d')

    xs = list()
    ys = list()
    zs = list()

    tetX = list()
    tetY = list()
    tetZ = list()

    with open(file, 'r') as fr:
        for cnt in xrange(4):
            line = fr.readline()
            lineparts = line.split()
            tetX.append(float(lineparts[0]))
            tetY.append(float(lineparts[1]))
            tetZ.append(float(lineparts[2]))
        
        while line:
            try:
                line = fr.readline()
                lineparts = line.split()
                xs.append(float(lineparts[0]))
                ys.append(float(lineparts[1]))
                zs.append(float(lineparts[2]))
            except IndexError:
                print "bad line:", line

    (c, m) = ('r', 'o')
    ax.scatter(tetX, tetY, tetZ, c=c, marker=m)

    (c, m) = ('b', '.')
    ax.scatter(xs, ys, zs, c=c, marker=m)

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

    plt.show()


def main():
    """
    """
    usage = "usage: %prog datafile [options]"
    parser = OptionParser(usage)

    #
    #parser.add_option("-o","--output",action="store",dest="output", \
    #        default="gammas",help="Option specifies the name of the 'gammas'" \
    #        "file. Default: %default")

    (options, args) = parser.parse_args()

    plot(args[0])


if __name__ == "__main__":
    main()
