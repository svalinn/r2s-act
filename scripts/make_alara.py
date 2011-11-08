#! /usr/bin/env python

# The input to this script is the output from mmGridGen's meshReader.
# This script writes a file with the ALARA input for the geometry and mixing 
# definition (volume, mat_loading, and mixture definitions). 
# This user must specfiy the path to the input file and path of the output file
# on the command line. The program will prompt for the user to enter the total 
# volume of the geometry  

# Written by: Amir Jaber 

import sys
# Open input file, read input, and create output file
input = open(sys.argv[1], 'r')
readinp = input.readlines()
alara_input = open(sys.argv[2], 'w')

# Determine order of material IDs
matID = readinp[0].strip().split()
del matID[0]
for i in range(0,len(matID)):
    matID[i]=int(matID[i])
nummats=len(matID)
print 'Materials order: ', matID

# Determine intervals of mesh 
dimID = readinp[1].strip().split()
del dimID[0]
for i in range(0,len(dimID)):
    dimID[i]=int(dimID[i])
print 'Number of xyz intervals: ', dimID

# Calculate volume per mesh element assuming equal volume for all elements
totalvolume = float(raw_input('Enter the volume: '))
numzones=(dimID[0]*dimID[1]*dimID[2])
elementvolume = totalvolume/numzones
print 'Volume per mesh element: ', elementvolume

# Write ALARA geometry card to file
alara_input.write('geometry rectangular\n\n')

# Write ALARA volume card to file
alara_input.write('volume\n')
for i in range(1,numzones+1):
    zonename='\t'+str(elementvolume)+'\t'+'zone_'+str(i)+'\n'
    alara_input.write(zonename)
alara_input.write('end\n\n')

# Write ALARA mat_loading card to file
alara_input.write('mat_loading\n')
for i in range(1,numzones+1):
    zonemats=readinp[i+1].strip().split()
    if float(zonemats[0])==1.0:
        matname='\t'+'zone_'+str(i)+'\t'+'void'+'\n'
            alara_input.write(matname)  
    else:
        matname='\t'+'zone_'+str(i)+'\t'+'mix_'+str(i)+'\n'
            alara_input.write(matname)
alara_input.write('end\n\n')

# Write ALARA mixture definitions to file
for i in range(1,numzones+1):
    zonemats=readinp[i+1].strip().split()
    if float(zonemats[0])==1.0:
        continue
    else:
        mixname='mixture'+'\t'+'mix_'+str(i)+'\n'
        alara_input.write(mixname)
        for j in range(1,nummats):
            mixdef='\t'+'mat_'+str(matID[j])+'\t'+str(float(zonemats[j]))+'\n'
            alara_input.write(mixdef)
        alara_input.write('end\n\n')


