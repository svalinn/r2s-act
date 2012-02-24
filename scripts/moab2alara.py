#! /usr/bin/env python

# The input to this script is the MOAB file (h5m) from mmGridGen.

# Written by: Amir Jaber

from itaps import iBase,iMesh
from optparse import OptionParser
from numpy import ones

def parser():
    parser = OptionParser(usage="usage: %prog <in> [options]")
    parser.add_option("-r", "--round",
                      action="store", dest="round", default="6",
                      help="Number of decimal places to round volume fractions, default: %default")
    parser.add_option("-o", "--output",
                      action="store", dest="output", default="alara_geom",
                      help="Name of generated ALARA input file, default: %default")
    return parser.parse_args()

def moab2alara(mesh, filename, numround):
  # Write ALARA geometry card to file
    filename.write('geometry rectangular\n\n')
    
    mats = mesh.getTagHandle("MATS")
    dims = mesh.getTagHandle("GRID_DIMS")
    fracs = mesh.getTagHandle("FRACTIONS")
    matID = list(mats[mesh.rootSet])
    voxels = mesh.getEntities(iBase.Type.region)

  # To be redone later to allow for coarse/fine meshes
    dimID = list(dims[mesh.rootSet])
    numzones=(dimID[0]*dimID[1]*dimID[2])
    elementvolume = float(1)/numzones 

  # Write ALARA volume card to file
    filename.write('volume\n')
    for i in range(len(voxels)) :
         zonename='\t'+str(elementvolume)+'\t'+'zone_'+str(i)+'\n'
         filename.write(zonename)
    filename.write('end\n\n')
     
  # Write ALARA mixture definitions to file
    nummats=len(matID)
    count=0
    list1 = list(ones(len(voxels)))
    for i in range(len(voxels)) :
        zonemats=list(fracs[voxels][i])
        if round(zonemats[0],1) != 1.0 :
            zonemats_i=map(lambda x: round(x ,int(numround)), list(fracs[voxels][i]))
            for k in range(len(voxels)) :
                zonemats_k=map(lambda x: round(x ,int(numround)), list(fracs[voxels][k]))
                
                if (zonemats_i == zonemats_k):
                    if (list1[k] == 1) :
                        mixname='mixture'+'\t'+'mix_'+str(k)+'\n'
                        filename.write(mixname)
                        count = count + 1
                        list1[k] = 2;
                        for j in range(1,nummats): # start from [1] because [0] is void fraction
                           if zonemats[j] != 0 :
                                mixdef='\tmaterial\t'+'mat_'+str(matID[j])+'\t'+\
                                str(1)+'\t'+str(round(zonemats[j],int(numround)))+'\n'
                                filename.write(mixdef)
                           else :

                               continue
                        filename.write('end\n\n')
                        break;

                    break;

        else :
            continue
    print str(count)+' mixtures defined'

  # Write ALARA mat_loading card to file
    filename.write('mat_loading\n')
#    list1 = list(ones(len(voxels)))
    for i in range(len(voxels)) :
         zonemats=list(fracs[voxels][i])
         if round(zonemats[0],1) == 1.0:
             matname='\t'+'zone_'+str(i)+'\t'+'void'+'\n'
             filename.write(matname)  
         else :
             filename.write('\t'+'zone_'+str(i))
             zonemats_i=map(lambda x: round(x ,int(numround)), list(fracs[voxels][i]))
             for k in range(len(voxels)) :
                zonemats_k=map(lambda x: round(x ,int(numround)), list(fracs[voxels][k]))
                
                if (zonemats_i == zonemats_k):
                    mixname='\t'+'mix_'+str(k)+'\n'
                    filename.write(mixname)
                    break;
                                   
    filename.write('end\n\n')   
    filename.close()

    return
        
def main() :
    (options, args)= parser()
    alara_input = open(options.output, 'w')
    mesh = iMesh.Mesh()
    print "Read "+args[0]
    mesh.load(args[0])
    moab2alara(mesh, alara_input, options.round)  
    print "Wrote "+options.output
    return

if __name__=='__main__':
    main()
