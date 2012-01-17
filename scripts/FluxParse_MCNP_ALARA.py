#!/usr/bin/env python
######################################################################
#FluxParse_MCNP_ALARA
######################################################################
#This python script is used for converting a raw MCNP mesh tally output 
#file into an ALARA input file.
#
#The script takes 3 command line arguments: the path of the input file,
#the path of the outpile file, and the normalization factor.
#
# Created by Elliott Biondo, Biondo@wisc.edu, working under Professor 
# Paul Wilson, University of Wisconsin, Madison
######################################################################

import sys

#Option Parser
from optparse import OptionParser

def FindFirstLine(InputLines):#Finding # of lines to skip
    TableHeading ='   Energy         '
    n=1 #number of lines in mcnp file header
    HeaderLine=InputLines[0][:64]
    while HeaderLine != TableHeading:
          n=n+1
          HeaderLine=InputLines[n][:18]
    print 'Skipping Header:', n, 'lines'
    m=n+1 #first line of values
    return m

def CountDelineations(m):
    #Finding number or Z deliniations
    z=1
    while InputLines[m][36:41] != InputLines[m+z][36:41]:
        z=z+1
    #Finding number of Y delinations
    y=1
    while InputLines[m][26:31] != InputLines[m+z*y][26:31]:
        y=y+1
    #Finding number of X deliniations
    x=1
    while InputLines[m][16:21] != InputLines[m+z*y*x][16:21]:
        x=x+1
    print 'Spacial Deliniations: (',x,',',y,',',z,')'

def MeshPointCount(m):#Counting Number of Meshpoints
    j=1 #initialising # of points
    while InputLines[j+m-1][:11] == InputLines[j+m][:11]:
          j=j+1
    print 'Mesh points found:', j
    return j

def EnergyGroupCount(m, j):#finding number of energy groups
    k=(len(InputLines)-j-m)/j #number of energy groups
    print 'Energy bins found:', k
    return k

def PrintLowtoHigh(m, j, k, Norm):#Printing values to output file
    #Initial normailization factor from command line argument
    for t in range(0, j):
        pointoutput=''
        for s in range(0,k):
           pointoutput+=str(float(InputLines[m+s*j + t][42:53])*Norm)+' '
           if (s+1)%8 == 0 & s != (k-1):
               pointoutput+='\n'
        Output.write(pointoutput + '\n\n')
    print 'File creation sucessful'

def PrintHightoLow(m, j, k, Norm):
    #Initial normailization factor from command line argument
    for t in range(0, j):
        pointoutput=''
        for s in range(k-1,-1,-1):
           pointoutput+=str(float(InputLines[m+s*j + t][42:53])*Norm)+' '
           if (s+1)%8 == 0 & s != (k-1):
               pointoutput+='\n'
        Output.write(pointoutput + '\n\n')
    print 'File creation sucessful'

def CloseFiles(): #Closes input and output files
    Input.close()
    Output.close()

#Execute functions
if __name__=='__main__':
    parser = OptionParser()
    parser.add_option('-b', action='store_true', dest='backwardbool', default=False, help="print fluxes in decreasing energy")
    (opts, args) = parser.parse_args()
    Input=open(args[0], "r")#opens MCNP input file (first specified)
    Output=file(args[1], "w")
    InputLines=Input.readlines() 
    m=FindFirstLine(InputLines)
    CountDelineations(m)
    j=MeshPointCount(m)
    k=EnergyGroupCount(m,j)
    if opts.backwardbool==False:
        PrintLowtoHigh(m,j,k,float(args[2])
    else:
        PrintHightoLow(m,j,k,float(args[2])
    CloseFiles()

