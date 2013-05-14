#!/usr/bin/env python

from itaps import iBase, iMesh, iMeshExtensions

from numpy import cross, dot, sqrt
from numpy.linalg import det


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


def calc_volume(mesh, voxel):
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


