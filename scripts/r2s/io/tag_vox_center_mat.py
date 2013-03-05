#! /usr/bin/env python

from operator import itemgetter
import itertools
import numpy as np

from pydagmc import dagmc
from pydagmc import util as dagutil

from itaps import iMesh, iBase


def prepare_materials():
    """

    Returns
    -------
    names : ?
        ?
    """
    matset = dagutil.get_material_set(with_rho=True)
    names = {}
    for idx, (mat, rho) in enumerate(sorted(matset, key=itemgetter(0))):
        if mat == 0:
            name = 'matVOID'
        else:
            name = 'mat{0}_rho{1}'.format( mat, rho )
        names[(mat, rho)] = (idx, name)
    return names




def tag_vox_centers(mesh):
    """
    """

    pass

def get_vox_centers(mesh, voxels):
    """
    """
    coords = list()
    for voxel in voxels:
        vtxcoords = mesh.getVtxCoords(mesh.getEntAdj(voxel, iBase.Type.vertex))
        xavg = np.mean([c[0] for c in vtxcoords])
        yavg = np.mean([c[1] for c in vtxcoords])
        zavg = np.mean([c[2] for c in vtxcoords])
        coords.append( [xavg, yavg, zavg] )

    print "Got center coords for {0} voxels.".format(len(voxels))
    return coords

def get_center_materials(materials, coords):
    """
    """
    mats = list()
    for coord in coords:
        vol_id = dagmc.find_volume(coord)
        mats.append(get_mat_id(materials, vol_id))
        
    return mats

def get_mat_id(materials, volume_id):
    """
    """
    mat = dagmc.volume_metadata(volume_id)
    matnum = mat['material']
    matrho = mat['rho']
    if matnum == 0.0:
        matrho = 0.0
    mat_idx = materials[(matnum,matrho)][0]
    return mat_idx


class matGrid:
    """Object representing a single material grid"""

    def __init__( self, mesh ):
        """Create a grid based on a given structured mesh"""
        self.mesh = mesh
        self.materials = prepare_materials()

        self.voxels = list(mesh.iterate(iBase.Type.region, iMesh.Topology.all))


    def create_tags(self):
        """ """
        mesh = self.mesh
        for idx, ((mat, rho), (matnum,matname)) in enumerate(self.materials.iteritems()):
            # Get tag handle
            try: 
                mattag = mesh.createTag( matname, 1, np.float64 )
            except iBase.TagAlreadyExistsError:
                mattag = mesh.getTagHandle( matname )
            try:
                errtag = mesh.createTag( matname+'_err', 1, np.float64 )
            except iBase.TagAlreadyExistsError:
                errtag = mesh.getTagHandle( matname + '_err')

            # Tag each voxel
            for vox, mat in itertools.izip(self.voxels, self.voxmats):
                #offset_ijk = [x+y for x,y in zip(ijk,self.scdmesh.dims[0:3])]
                #hx = self.scdmesh.getHex(*offset_ijk)

                if mat == matnum:
                    # Material matnum is assumed to be 100%  of voxel contents
                    mattag[vox] = 1.0 #mat[matnum]
                else:
                    # matnum is treated as not present in the voxel
                    mattag[vox] = 0.0

                # We don't have errors with this method
                errtag[vox] = 0.0 #err[matnum]


    def gen_vox_mats_list(self):
        """
        """


        self.coords = get_vox_centers(self.mesh, self.voxels)
        self.voxmats = get_center_materials(self.materials, self.coords)



def load_geom(filename):
    """Load geometry from the given file into dagmc

    This is provided as a convenience so client code doesn't need 
    to invoke pydagmc.

    Note that DagMC can only have one set of geometry loaded per program 
    invocation. This means that this function should only be called once, and 
    the resulting geometry will become globally visible to all clients of 
    mmgrid.
    """
    dagmc.load( filename )
