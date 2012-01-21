#!/usr/bin/env python
#This is the second version of FluxParse, which uses an array of numbers 
#instead of using a readlines()

import linecache
from optparse import OptionParser
import sys

#use for lines in filename
def find_first_line(meshtal):
    table_heading ='   Energy         '
    n=1
    line=linecache.getline(meshtal, 1)
    while line[0:18] != table_heading :
        n=n+1
        line=linecache.getline(meshtal, n)
    m=n+1
    print 'Skipping Header:', n, 'lines'  
    return m

def meshtal_to_array(meshtal, m):
    n=m
    line=linecache.getline(meshtal, n)
    array = []
    while line[:11] != '   Total   ' :
        array.append([float(line[2:11]),float(line[14:21]),float(line[24:31]),
                                        float(line[34:41]),float(line[42:53])])
        n=n+1
        line=linecache.getline(meshtal, n)
    return array

def count_mesh_points(array) :
    j=1
    while abs(array[j][0]/array[0][0] - 1) < 0.0001 :
        j=j+1
    print 'Mesh points found:', j
    return j

def count_energy_bins(array):
    k=1
    for n in range(0,len(array)-1):
        if abs(array[n][0]/array[n+1][0] -1) > 0.00001 :
            k=k+1
    print 'Energy bins found:', k
    return k

def count_data_points(array):
    l=len(array)
    print 'Total data points found:', l
    return l

def count_delinations(array) :
    #Finding number or Z deliniations
    z=1
    while abs(array[1][3]-array[z+1][3])>0.001:
        z=z+1
        #Finding number of Y delinations
    y=1
    while abs(array[1][2]-array[1+z*y][2])>0.001:
        y=y+1
    #Finding number of X deliniations
    x=1
    while abs(array[1][1]-array[1+z*y*x][1])>0.001:
        x=x+1
    print 'Spacial Deliniations: (',x,',',y,',',z,')'
    return(x, y, z)

def check_meshtal_data(l, j, k, x, y, z) :
    if l != (j*k) :
        print >>sys.stderr, 'Number of data points does not equal meshpoints*energy groups'
        sys.exit(1)
    if x*y*z != j :
        print >>sys.stderr, 'Number of mesh points does not equal x*y*z'
        sys.exit(1)

def print_fluxin(array, j, k, norm, output_file, backwardbool):
    output=file(output_file, 'w')
    for t in range(0, j):
        pointoutput=''
        if backwardbool==False :
            a=0
            b=k
            c=1
        else :
            a=k-1
            b=-1
            c=-1
        for s in range(a, b, c):
           pointoutput+=str((array[s*j + t][4])*norm)+' '
           
           if (s+1)%8 == 0 & s != (k-1):
               pointoutput+='\n'
        output.write(pointoutput + '\n\n')
    print output_file, 'created sucessfully'
     
if __name__=='__main__':
    print 'Parsing meshtal file'
    parser = OptionParser()
    parser.add_option('-b', action='store_true', dest='backwardbool', default=False, help="Print fluxes in decreasing energy")
    parser.add_option('-o', dest='output_file', default='ALARAflux.in', help="Name of output file")
    (opts, args) = parser.parse_args()
    m=find_first_line(args[0])
    array=meshtal_to_array(args[0],m)
    j=count_mesh_points(array)
    k=count_energy_bins(array)
    l=count_data_points(array)
    x,y,z=count_delinations(array)
    check_meshtal_data(l, j, k, x, y, z)
    norm=float(args[1])
    print_fluxin(array, j, k, norm, opts.output_file, opts.backwardbool)


