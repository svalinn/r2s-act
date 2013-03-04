#!/usr/bin/env python

import sys
import re
import operator

from itaps import iBase, iMesh, iMeshExtensions
from r2s.scdmesh import ScdMesh

from numpy import cross, dot, sqrt
from numpy.linalg import det

def _create_mixture_tuple(v):
    """Create a tuple from a sequence of numbers

    Performs rounding to get tuples that can be compared to 
    some level of precision.

    Parameters
    ----------
    v : list of floats
        List of floats to be set to a fixed precision.

    Returns
    -------
    ... : tuple
        ...
    """
    return tuple( [ round(x, 6) for x in v ] )


def _distance(v):
    return sqrt(v[0]**2 + v[1]**2 + v[2]**2)


def _tet_volume(coords):
    return abs(det( [coords[0]-coords[1],
                     coords[1]-coords[2],
                     coords[2]-coords[3]] )) / 6


def _hex_volume(coords):
    # assumes not-quite logical vertex ordering
    def subvolume(a, b, c, d, e):
        base = ( _distance(cross(b-a, d-a)) +
                 _distance(cross(c-a, d-a)) ) / 2
        norm = cross(b-a, c-a)
        norm = norm / _distance(norm)
        height = abs(dot(norm, e-a))
        return base*height / 3

    return subvolume(coords[0], coords[1], coords[3], coords[2], coords[7]) + \
           subvolume(coords[0], coords[1], coords[4], coords[5], coords[7]) + \
           subvolume(coords[1], coords[2], coords[5], coords[6], coords[7])


def _calc_volume(mesh, voxel):
    """Calculates the volume of a hexahedral or tetrahedral voxel
    
    Parameters
    ----------
    mesh : iMesh.Mesh object
        Mesh object that includes voxel
    voxel : iBase.Type.Region entity
        Entity handle for the voxel for which volume is being found

    Returns
    -------
    volume : float
        Volume of the voxel

    Notes
    -----
    Code adapted from:
    http://pythonhosted.org/PyTAPS/tutorial/example.html?highlight=volume
    """
    topo = mesh.getEntTopo(voxel)
    curr = mesh.getVtxCoords(mesh.getEntAdj(voxel, iBase.Type.vertex))

    if topo == iMesh.Topology.tetrahedron:
        volume = _tet_volume(curr)
    elif topo == iMesh.Topology.hexahedron:
        volume = _hex_volume(curr)
    else:
        print "Bad voxel; Topo:{0} Voxel:{1} Coords:{2}".format(
                topo, voxel, curr)
        assert(False)
    return volume


def create_mixture_definitions(mesh):
    """Return a list of unique materials tagged onto the mesh.

    unique_mixtures is a dictionary mapping mixture tuples (created through
    _create_mixture_tuple) to lists.  The first element in the list is a
    unique integer ID for the mixtures; the rest of the elements
    are the hex handles that participate in that mixture.

    mat_tags is a list of the material tags from the input mesh.  This list
    is ordered in the same order as the mixture tuples.

    Parameters
    ----------
    mesh : ScdMesh object or iMesh.Mesh object
        Mesh object to read materials data from

    Returns
    -------
    ... : tuple
        A tuple of the list of mixtures and tag handles list;
        i.e. (unique_mixtures, mat_tags)

    Notes
    -----
    It is assumed that the mesh has the 'matVOID' tag.
    """

    # Get the list of materials in the mesh-- should be changed in the future
    # to use a solution that does not involve string parsing.

    if isinstance(mesh, ScdMesh):
        # The material tags are a subset of all the tags on a hex of the scdmesh
        # Pick the hex at minimum (i,j,k)
        voxels = [v for v in mesh.iterateHex('xyz')]
        tags = mesh.imesh.getAllTags( mesh.getHex( *(mesh.dims[:3]) ))
        void_tag = [mesh.imesh.getTagHandle('matVOID')]
    else:
        # Grab volume entities on mesh, then grab tags off the first one
        voxels = [v for v in \
                mesh.iterate(iBase.Type.region, iMesh.Topology.all)]
        tags = mesh.getAllTags(voxels[0])
        void_tag = [mesh.getTagHandle('matVOID')]
        print "Got {0} voxels from mesh.".format(len(voxels))

    # material tags have the name format 'mat{int}_rho{float}'
    mat_tags = [t for t in tags if \
            re.match('^mat[0-9]+_rho[0-9\-\.eE]+$', t.name)]
    # Void is always the first material, so put it at the list's beginning
    mat_tags = void_tag + mat_tags
            
    unique_mixtures = dict()

    for voxel in voxels:
        fracs = [t[voxel] for t in mat_tags]
        mixture = _create_mixture_tuple(fracs)
        if mixture[0] == 1: # a void material
            continue
        if mixture not in unique_mixtures:
            unique_mixtures[mixture] = [len(unique_mixtures), voxel]
        else:
            unique_mixtures[mixture].append(voxel)

    print "{0} unique mixtures in {1} voxels".format( \
            len(unique_mixtures), len(voxels))
    return (unique_mixtures, mat_tags)


def write_zones(mesh, output_file):
    """Write the volume and zone lines to the ALARA geometry output

    Parameters
    ----------
    mesh : ScdMesh object or iMesh.Mesh object
        Mesh object to read materials data from
    output_file : file object
        Opened file for writing contents of ALARA geometry 
    """

    output_file.write('geometry rectangular\n\n')
    output_file.write('volume\n')
    
    if isinstance(mesh, ScdMesh):
        for idx, vol in enumerate(mesh.iterateHexVolumes('xyz')):
            output_file.write("\t{0}\tzone_{1}\n".format(vol, idx))
    else:
        for idx, voxel in enumerate( \
                mesh.iterate(iBase.Type.region, iMesh.Topology.all)):
            vol =  _calc_volume(mesh, voxel)
            output_file.write("\t{0}\tzone_{1}\n".format(vol, idx))

    output_file.write('end\n\n')


def write_mixtures(mixtures, mat_tags, name_dict, output_file):
    """Write the mixture lines to the ALARA geometry output

    Parameters
    ----------
    mixtures : ???
        ...
    mat_tags : list of iMesh.Tag entities
        ...
    name_dict : dictionary (optional?)
        Dictionary of names for material compositions
    output_file : file object
        Opened file for writing contents of ALARA geometry 
    """
    for mixture, voxels in sorted( mixtures.iteritems(), 
                                   key=operator.itemgetter(1,0) ):
        # voxels[0] is the unique mixture ID
        output_file.write("mixture\tmix_{0}\n".format(voxels[0]))
        for idx, m in enumerate(mixture[1:], start=1):
            if m == 0: continue 
            material_name = mat_tags[idx].name
            if material_name in name_dict:
                material_name = name_dict[material_name]
            output_file.write("\tmaterial\t{0}\t1\t{1}\n".format(
                material_name,m))
        output_file.write('end\n\n')

    # Finally add pseudo void material
    output_file.write(
            "mixture pseudo_void\n\tmaterial\tpseudo_void\t1\t1\nend\n\n")


def write_mat_loading(mesh, mat_tags, mixtures, output_file):
    """Write the mat_loading information to the ALARA geometry output

    Parameters
    ----------
    mesh : ScdMesh object or iMesh.Mesh object
        Mesh object to read materials data from
    mat_tags : ...
        ...
    mixtures : ...
        ...
    output_file : file object
        Opened file for writing contents of ALARA geometry 
    """

    output_file.write('mat_loading\n')

    # Get correct iterator
    if isinstance(mesh, ScdMesh):
        voxels_iterator = mesh.iterateHex('xyz')
    else:
        voxels_iterator = mesh.iterate(iBase.Type.region, iMesh.Topology.all)

    for idx, voxel in enumerate(voxels_iterator):
        fracs = [t[voxel] for t in mat_tags]
        mixture = _create_mixture_tuple(fracs)
        if mixture[0] == 1: # a void material
            output_file.write('\tzone_{0}\tpseudo_void\n'.format(idx))
        else:
            mix_id = mixtures[mixture][0]
            output_file.write('\tzone_{0}\tmix_{1}\n'.format(idx,mix_id))
    output_file.write('end\n\n')


def write_alara_geom(filename, mesh, namedict={}):
    """Given a mesh with mmgrid tags, write an ALARA geometry file
    
    Parameters
    ----------
    filename : string
        Path/filename of mesh file to write ALARA geometry to
    mesh : ScdMesh object or iMesh.Mesh object
        Mesh object containing materials tags
    namedict : dictionary (optional)
        Dictionary of names for material compositions
    """
    mixtures, mat_tags = create_mixture_definitions(mesh)

    with open(filename,'w') as output_file:
        write_zones(mesh, output_file)
        write_mixtures(mixtures, mat_tags, namedict, output_file)
        write_mat_loading(mesh, mat_tags, mixtures, output_file)


def main():

    # TODO: How to handle non-structured meshes from the command line...
    mesh = ScdMesh.fromFile(sys.argv[1])
    write_alara_geom("alara_geom", mesh)


if __name__ == '__main__':
    main()
