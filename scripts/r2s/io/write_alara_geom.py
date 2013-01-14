#!/usr/bin/env python

import sys
import re
import operator

from itaps import iBase, iMesh, iMeshExtensions
from r2s.scdmesh import ScdMesh

def _create_mixture_tuple( v ):
    """Create a tuple from a sequence of numbers

    Performs rounding to get tuples that can be compared to 
    some level of precision.
    """
    return tuple( [ round(x, 6) for x in v ] )

def create_mixture_definitions( scdmesh ):
    """Return a list of unique materials tagged onto the mesh by mmgrid.

    Returns a tuple (unique_mixtures, mat_tags)

    unique_mixtures is a dictionary mapping mixture tuples (created through
    create_mixture_tuple) to lists.  The first element in the list is a
    unique integer ID for the mixtures; the rest of the elements
    are the hex handles that participate in that mixture.

    mat_tags is a list of the material tags from the input mesh.  This list
    is ordered in the same order as the mixture tuples.
    """

    # Get the list of materials in the mesh-- should be changed in the future
    # to use a solution that does not involve string parsing.

    # The material tags are a subset of all the tags on a hex of the scdmesh
    # Pick the hex at minimum (i,j,k)
    tags = scdmesh.imesh.getAllTags( scdmesh.getHex( *(scdmesh.dims[:3]) ))
    # material tags have the name format 'mat{int}_rho{float}'
    mat_tags = [t for t in tags if re.match('^mat[0-9]+_rho[0-9\-\.eE]+$', t.name)]
    # Void is always the first material, so put it at the list's beginning
    mat_tags = [ scdmesh.imesh.getTagHandle('matVOID') ] + mat_tags
            
    unique_mixtures = dict()

    voxcount = 0
    for voxel in scdmesh.iterateHex('xyz'):
        voxcount += 1
        fracs = [ t[voxel] for t in mat_tags ]
        mixture = _create_mixture_tuple( fracs )
        if mixture[0] == 1: # a void material
            continue
        if mixture not in unique_mixtures:
            unique_mixtures[mixture] = [len(unique_mixtures),voxel]
        else:
            unique_mixtures[mixture].append(voxel)

    print len(unique_mixtures), 'unique mixtures in', voxcount, 'voxels'
    return unique_mixtures, mat_tags

def write_zones( scdmesh, output_file ):
    """Write the volume / zone lines to the ALARA geometry output"""
    output_file.write('geometry rectangular\n\n')

    output_file.write('volume\n')
    for idx, vol in enumerate(scdmesh.iterateHexVolumes('xyz')):
        output_file.write('\t{0}\tzone_{1}\n'.format(vol,idx))
    output_file.write('end\n\n')


def write_mixtures( mixtures, mat_tags, name_dict, output_file ):
    """Write the mixture lines to the ALARA geometry output"""
    for mixture, voxels in sorted( mixtures.iteritems(), 
                                   key=operator.itemgetter(1,0) ):
        # voxels[0] is the unique mixture ID
        output_file.write('mixture\tmix_{0}\n'.format(voxels[0]))
        for idx, m in enumerate(mixture[1:], start=1):
            if m == 0: continue 
            material_name = mat_tags[idx].name
            if material_name in name_dict:
                material_name = name_dict[material_name]
            output_file.write('\tmaterial\t{0}\t1\t{1}\n'.format(material_name,m))
        output_file.write('end\n\n')
    output_file.write('mixture pseudo_void\n\tmaterial\tpseudo_void\t1\t1\nend\n\n')

def write_mat_loading( scdmesh, mat_tags, mixtures, output_file):
    """Write the mat_loading information to the ALARA geometry output"""
    output_file.write('mat_loading\n')

    for idx, voxel in enumerate(scdmesh.iterateHex('xyz')):
        fracs = [t[voxel] for t in mat_tags]
        mixture = _create_mixture_tuple(fracs)
        if mixture[0] == 1: # a void material
            output_file.write('\tzone_{0}\tpseudo_void\n'.format(idx))
        else:
            mix_id = mixtures[mixture][0]
            output_file.write('\tzone_{0}\tmix_{1}\n'.format(idx,mix_id))
    output_file.write('end\n\n')

def write_alara_geom( filename, scdmesh, namedict={} ):
    """Given a structured mesh with mmgrid tags, write an ALARA geometry"""
    mixtures, mat_tags = create_mixture_definitions( scdmesh )

    with open(filename,'w') as output_file:
        write_zones( scdmesh, output_file )
        write_mixtures( mixtures, mat_tags, namedict, output_file )
        write_mat_loading( scdmesh, mat_tags, mixtures, output_file )

def main():

    mesh = ScdMesh.fromFile( sys.argv[1] )
    write_alara_geom( 'alara_geom', mesh )

if __name__ == '__main__':
    main()
