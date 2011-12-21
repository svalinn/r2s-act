#! /usr/bin/env python

# The input to this script is a mesh file output from mmGridGen.
# This script writes a file with the ALARA input for the geometry and mixing 
# definition (volume, mat_loading, and mixture definitions). 
# This user must specfiy the path to the input file, path of the output file
# on the command line, and the total volume of the geometry.  

# Written by: Amir Jaber

from itaps import iBase,iMesh
import re
import sys

def meshReader( filename ):
    nmfile = open("matFracs_results", 'w')
    mesh = iMesh.Mesh()
    mesh.load( filename )
    volFracs = {}
    cell = []
    j=0
    fracs=mesh.getTagHandle("FRACTIONS")
    errors=mesh.getTagHandle("ERRORS")
    mats=mesh.getTagHandle("MATS")  
    dims=mesh.getTagHandle("GRID_DIMS")
    
    nmfile.write("Materials "+re.sub("[\[\]\,]","",str(mats[mesh.rootSet]))+"\n")
    nmfile.write("Dimensions "+re.sub("[\[\]\,]","",str(dims[mesh.rootSet]))+"\n")
    for i in mesh.getEntities(iBase.Type.region) :
        volFracs[j]=fracs[i]
        for i in volFracs.values() :  
            volFracs[j]=list(i)
        nmfile.write(re.sub("[\[\]\,]","",str(volFracs[j]))+"\n")
        j=j+1
    nmfile.close()
    return 
  
def make_alara(output_filename, geom_volume):
     # Open input file, read input, and create output file
     input = open("matFracs_results", 'r')
     readinp = input.readlines()
     alara_input = open(output_filename, 'w')
     
     # Determine order of material IDs
     matID = readinp[0].strip().split()
     del matID[0]
     matID=map(int ,matID)
     nummats=len(matID)
     print 'Materials order: ', matID

     # Determine intervals of mesh 
     dimID = readinp[1].strip().split()
     del dimID[0]
     dimID=map(int ,dimID)
     print 'Number of xyz intervals: ', dimID
     
     # Calculate volume per mesh element assuming equal volume for all elements
     totalvolume = geom_volume
     try : 
          float(totalvolume)
     except :
          print >>sys.stderr, "Invalid entry for volume."
          sys.exit(1)
     numzones=(dimID[0]*dimID[1]*dimID[2])
     elementvolume = float(totalvolume)/numzones
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
                     mixdef='\tmaterial\t'+'mat_'+str(matID[j])+'\t'+\
                     str(1)+'\t'+str(float(zonemats[j]))+'\n'
                     alara_input.write(mixdef)
            alara_input.write('end\n\n')
     input.close()
     alara_input.close()
     return

if __name__=='__main__':
     meshReader(sys.argv[1])
     make_alara(sys.argv[2],sys.argv[3])
	