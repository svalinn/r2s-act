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
parser = OptionParser()
parser.add_option('-b', action='store_true', dest='backwardbool', default=False, help="print fluxes in decreasing energy")
(opts, args) = parser.parse_args()

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

def PrintLowtoHigh(m, j, k):#Printing values to output file
    Norm=float(sys.argv[3])
    #Initial normailization factor from command line argument
    for t in range(0, j):
        pointoutput=''
        for s in range(0,k):
           pointoutput+=str(float(InputLines[m+s*j + t][42:53])*Norm)+' '
           if (s+1)%8 == 0 & s != (k-1):
               pointoutput+='\n'
        Output.write(pointoutput + '\n\n')
    print 'File creation sucessful'

def PrintHightoLow(m, j, k):
    Norm=float(sys.argv[3])
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

def check_meshpoints(MeshtalInputLines, m, j, k, mesh):
    voxels = mesh.getEntities(iBase.Type.region)
    if j !=len(voxels):
        print >>sys.stderr, 'Number of meshtal points does not match number of mesh points'
        sys.exit(1)

    #find number of data points in InputLines
    l=0 #number of datapoints
    while MeshtalInputLines[m+l][:11] != '   Total   ':
        l=l+1
    print l
    if l != (j*k) :
        print >>sys.stderr, 'Number of data points does not equal meshpoints*energy groups'
        sys.exit(1)

#Execute functions
if __name__=='__main__':
    Input=open(sys.argv[1], "r")#opens MCNP input file (first specified)
    Output=file(sys.argv[2], "w")
    InputLines=Input.readlines() 
    m=FindFirstLine(InputLines)
    CountDelineations(m)
    j=MeshPointCount(m)
    k=EnergyGroupCount(m,j)
    check_input(options.Norm, options.volume)
    if opts.backwardbool==False:
        PrintLowtoHigh(m,j,k)
    else:
        PrintHightoLow(m,j,k)
    CloseFiles()

