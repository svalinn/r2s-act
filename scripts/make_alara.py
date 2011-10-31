#! /usr/bin/env python

# mmGridGen to ALARA
# Written by: Amir Jaber
# 10/27/2011

# Open file and read input
# inputfile = raw_input('Enter the input file name: ')
# input = open(inputfile, 'r')
input = open('matFracs_results.txt', 'r')
readinp = input.readlines()

# Determine order of material IDs
matID = readinp[0].strip().split()
del matID[0]
for i in range(0,len(matID)):
	matID[i]=int(matID[i])
nummats=len(matID)
print 'Materials order: ', matID

# Determine dimensions of mesh 
dimID = readinp[1].strip().split()
del dimID[0]
for i in range(0,len(dimID)):
	dimID[i]=int(dimID[i])
print 'Number of xyz dimensions: ', dimID

# Calculate volume per mesh element
totalvolume = float(raw_input('Enter the volume: '))
numzones=(dimID[0]*dimID[1]*dimID[2])
elementvolume = totalvolume/numzones
print 'Volume per mesh element: ', elementvolume

# Create file to write ALARA input into
alara_input = open('alara_input', 'w')

# Write ALARA volume card to file
alara_input.write('volume\n')
for i in range(1,numzones+1):
	zonename='\t'+str(elementvolume)+'\t'+'zone_'+str(i)+'\n'
	alara_input.write(zonename)
alara_input.write('end\n\n')

# Write ALARA mat_loading card to file
alara_input.write('mat_loading\n')
for i in range(1,numzones+1):
	matname='\t'+'zone_'+str(i)+'\t'+'mix_'+str(i)+'\n'
      	alara_input.write(matname)
alara_input.write('end\n\n')

# Write ALARA mixture definitions to file
for i in range(1,numzones+1):
	mixname='mixture'+'\t'+'mix_'+str(i)+'\n'
	alara_input.write(mixname)
	for j in range(1,nummats):
		zonemats=readinp[i+1].strip().split()
		mixdef='\t'+'mat_'+str(matID[j])+'\t'+str(float(zonemats[j]))+'\n'
		alara_input.write(mixdef)
	alara_input.write('end\n\n')









