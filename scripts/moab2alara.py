#! /usr/bin/env python

# The input to this script is the MOAB file (h5m) from mmGridGen.

# Written by: Amir Jaber

from itaps import iBase,iMesh
from optparse import OptionParser

def parser():
    parser = OptionParser(usage="usage: %prog <in> [options]")
    parser.add_option("-o", "--output",
                      action="store", dest="output", default="alara_geom",
                      help="Name of generated ALARA input file, default: %default")
    return parser.parse_args()

def moab2alara(mesh, filename):
    # Write ALARA geometry card to file
    filename.write('geometry rectangular\n\n')
    
    mats = mesh.getTagHandle("MATS")
    dims = mesh.getTagHandle("GRID_DIMS")
    fracs = mesh.getTagHandle("FRACTIONS")
    matID = list(mats[mesh.rootSet])
    
    # To be redone later to allow for coarse/fine meshes
    dimID = list(dims[mesh.rootSet])
    numzones=(dimID[0]*dimID[1]*dimID[2])
    elementvolume = float(1)/numzones
    
    voxels = mesh.getEntities(iBase.Type.region)
#    filename.write(str(fracs[voxels]))

# Write ALARA volume card to file
    filename.write('volume\n')
    for i in range(len(voxels)) :
         zonename='\t'+str(elementvolume)+'\t'+'zone_'+str(i)+'\n'
         filename.write(zonename)
    filename.write('end\n\n')

# Write ALARA mat_loading card to file
    filename.write('mat_loading\n')
    for i in range(len(voxels)) :
         zonemats=list(fracs[voxels][i])
         if zonemats[0] == 1.0:
             matname='\t'+'zone_'+str(i)+'\t'+'void'+'\n'
             filename.write(matname)  
         else :
             matname='\t'+'zone_'+str(i)+'\t'+'mix_'+str(i)+'\n'
             filename.write(matname)
    filename.write('end\n\n')
     
# Write ALARA mixture definitions to file
    nummats=len(matID)
    for i in range(len(voxels)) :
        zonemats=list(fracs[voxels][i])
        if zonemats[0] != 1.0 :  
            mixname='mixture'+'\t'+'mix_'+str(i)+'\n'
            filename.write(mixname)
            for j in range(nummats):
                   if zonemats[j] != 0 :
                       mixdef='\tmaterial\t'+'mat_'+str(matID[j])+'\t'+\
                       str(1)+'\t'+str(float(zonemats[j]))+'\n'
                       filename.write(mixdef)
                   else :
                       continue
            filename.write('end\n\n')
        else :
            continue
    filename.close()

    return
        
def main() :
    (options, args)= parser()
    alara_input = open(options.output, 'w')

    mesh = iMesh.Mesh()
    print "Read "+args[0]
    mesh.load(args[0])
    moab2alara(mesh, alara_input)  
    print "Wrote "+options.output

if __name__=='__main__':
    main()