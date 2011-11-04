#!/user/bin/env python
######################################################################
#FluxParse_MCNP_ALARA
######################################################################
#This python script is used for converting a raw MCNP mesh tally output file
#into an ALARA input file.
#
#The script takes 3 command line arguments: the path of the input file,
#the path of the outpile file, and the normalization factor.
#
# Created by Elliott Biondo, Biondo@wisc.edu, working under Professor 
# Paul Wilson, University of Wisconsin, Madison
######################################################################

import sys
Input=open(sys.argv[1], "r")     #opens MCNP input file (first specified)
Output=file(sys.argv[2], "w")
InputLines=Input.readlines()

#Finding # of lines to skip
TableHeading ='   Energy         '
n=1 #number of lines in mcnp file header
HeaderLine=InputLines[0][:64]
while HeaderLine != TableHeading:
          n=n+1
          HeaderLine=InputLines[n][:18]
print 'Skipping Header:', n, 'lines'
m=n+1 #first line of values
#print 'First line of Table: X=',InputLines[m][16:20]

#Counting Number of Meshpoints
j=1 #initialising # of points
while InputLines[j+n][:11] == InputLines[j+1+n][:11]:
          j=j+1
print 'Mesh points found:', j

#finding number of energy groups
k=(len(InputLines)-j-m)/j #number of energy groups
print 'Energy bins found:', k

#Printing values to output file
Norm=float(sys.argv[3])
#Initial normailization factor from command line argument
for t in range(0, j):
          pointoutput=''
          for s in range(0,k):
                   pointoutput+=str(float(InputLines[m+s*j + t][42:53])*Norm)+'\n'
          Output.write(pointoutput + '\n')
	
print 'File creation sucessful'
Input.close()
Output.close()
