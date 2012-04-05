#! /usr/bin/env python

# The input to this script is the MOAB file (h5m) from mmGridGen.

# Written by: Amir Jaber

from itaps import iBase,iMesh
from optparse import OptionParser
from numpy import ones
import operator

def parser():
    parser = OptionParser(usage="usage: %prog <in> -v VOLUME [options]")
    parser.add_option("-v", "--volume",
                      action="store", dest="volume", default=1,
                      help="Total volume of mesh geometry")
    parser.add_option("-r", "--round",
                      action="store", dest="round", default="6",
                      help="Number of decimal places to round volume fractions, default: %default")
    parser.add_option("-o", "--output",
                      action="store", dest="output", default="alara_geom",
                      help="Name of generated ALARA input file, default: %default")
    return parser.parse_args()

def moab2alara(mesh, filename, numround, total_volume):
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
    elementvolume = float(total_volume)/numzones 

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

    def create_mixture_tuple( v ):
        return tuple( [ round(x, int(numround)) for x in fracs[v]] )

    # unique_mixtures maps mixture tuples (see below) to lists of hex handles
    # that participate in those mixtures.  However, the first item in each list
    # is a unique id for that mixture.  Thus:
    # unique_mixture[ (mixture_tuple) ] = [ ID, handle, handle, ... ]
    unique_mixtures = dict()
    for v in voxels :
        
        zonemats=list(fracs[v])
        # if material 1 (void) is not 1.0
        if round(zonemats[0],1) != 1.0 :
            zonemats_i = create_mixture_tuple( v )
            if zonemats_i not in unique_mixtures:
                unique_mixtures[zonemats_i] = [len(unique_mixtures),v] 
            else:
                unique_mixtures[zonemats_i].append(v)

    for mixture, voxel_members in sorted( unique_mixtures.iteritems(), 
                                   key = operator.itemgetter(1,0) ):
        # voxels[0] is a unique mixture ID
        filename.write('mixture\tmix_{0}\n'.format(voxel_members[0])) 
        for idx, m in enumerate(mixture[1:]):
            if m == 0: continue
            mixdef = ('\tmaterial\t'+'mat_'+str(matID[idx+1])+'\t'+
                       str(1)+'\t'+str(round(m,int(numround)))+'\n')
            filename.write(mixdef) 
        filename.write('end\n\n')

    count = len(unique_mixtures)
    print count, 'mixtures defined'

  # Write ALARA mat_loading card to file
    filename.write('mat_loading\n')
    for idx, v in enumerate(voxels):
        zonemats=list(fracs[v])
        # if material 1 (void) is 1.0
        if round(zonemats[0],1) == 1.0 :
            filename.write('\tzone_{0}\tvoid\n'.format( idx ))
        else:
            zonemats_i =  create_mixture_tuple( v )
            mat_voxel_list = unique_mixtures[ zonemats_i ]
            mat_id = mat_voxel_list[0]
            filename.write('\tzone_{0}\tmix_{1}\n'.format(idx,mat_id))
                                   
    filename.write('end\n\n')   
    filename.close()

    return
        
def main() :
    (options, args)= parser()
    alara_input = open(options.output, 'w')
    mesh = iMesh.Mesh()
    print "Read "+args[0]
    mesh.load(args[0])
    moab2alara(mesh, alara_input, options.round, options.volume)  
    print "Wrote "+options.output
    return

if __name__=='__main__':
    main()
