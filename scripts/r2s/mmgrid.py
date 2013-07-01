#!/usr/bin/env python

from operator import itemgetter
import itertools
import numpy as np
import random
import sys
import optparse

from itaps import iMesh, iBase
from r2s import scdmesh
from io.write_alara_geom import write_alara_geom
from pydagmc import dagmc
from pydagmc import util as dagutil


class mmGridError(Exception):
    pass


_quiet = False


def _msg(msg, newline=True):
    """Print to stdout if the module's _quiet flag is not set.

    Optionally skip printing a newline, allowing in-place update 
    of a running status line
    """
    if not _quiet:
        sys.stdout.write(msg)
        if newline:
            sys.stdout.write('\n')
        sys.stdout.flush()


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


def prepare_cells():
    """

    Returns
    -------
    cellnames: ?
           
    """
    celllist = dagmc.get_volume_list()
    cellnames = {} 
    for idx in range(len(celllist)):
        name = 'Cell_{0}'.format( celllist[idx] )
        cellId = celllist[idx]
        cellnames[ cellId ] = (idx, name)
    return cellnames


def get_mat_id(materials, volume_id):
    """

    Returns
    -------
    mat_idx : int?
    """
    mat = dagmc.volume_metadata(volume_id)
    matnum = mat['material']
    matrho = mat['rho']
    if matnum == 0.0:
        matrho = 0.0
    mat_idx = materials[(matnum,matrho)][0]
    return mat_idx


def get_vox_centers(mesh, voxels):
    """Calculate the center point of voxels and return a list of (x,y,z) coords

    Parameters
    ----------
    mesh : iMesh.Mesh object
        Mesh on which voxels are stored.
    voxels : list of iBase.EntityHandles
        List of volume entities on mesh to get center points of.

    Returns
    -------
    coords : list of (x, y, z) float triplets
        Coordinates of voxel centers in mesh's canonical voxel order.
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


def get_point_materials(materials, coords):
    """Query DAGMC for materials at a list of points

    Parameters
    ----------
    materials : dictionary
        ...
    coords : list of (x, y, z) float triplets
        Point coordinates; typically for voxel centers.
    
    Returns
    -------
    mats : list of integers
        List of integers corresponding material at each point in coords.

    Notes
    -----
    Requires that DagMC geometry has already been loaded via dagmc.load().
    """
    mats = list()
    for coord in coords:
        vol_id = dagmc.find_volume(coord)
        mats.append(get_mat_id(materials, vol_id))
        
    return mats


def _linspace_square( n ):
    """Return a callable that creates an evenly spaced grid in the given quad
    
    Parameters
    ----------
    n : integer
        Number of rays to fire in each dimension
    
    Returns
    -------
    points_inside : generator
        Generator that provides n 
        uniformly spaced (a,b) points given (a0, a1, b0, b1)
    """
    def points_inside(a0, a1, b0, b1):
        # We want our points to start/end a half-interval from edges, so we do
        #  some math.
        # np.linspace() includes the start and end points.
        a0x = a0 + (a1-a0) / (2.0*n)
        a1x = a1 - (a1-a0) / (2.0*n)
        b0x = b0 + (b1-b0) / (2.0*n)
        b1x = b1 - (b1-b0) / (2.0*n)
        aspace = np.linspace(a0x, a1x, n)
        bspace = np.linspace(b0x, b1x, n)
        return itertools.product(aspace,bspace)
    return points_inside


def _random_square( n ):
    """Return a callable that creates randomly distributed points in the give quad
    
    Parameters
    ----------
    n : integer
        Number of rays to fire
    
    Returns
    -------
    points_inside : generator
        Generator that provides n random (a,b) points given (a0, a1, b0, b1)
    """
    def points_inside(a0, a1, b0, b1):
        for _ in xrange(n):
            a = random.uniform(a0,a1)
            b = random.uniform(b0,b1)
            yield a,b
    return points_inside


def pairwise(l):
    """Generator: given a sequence x, yield (x[0],x[1]), (x[1],x[2]), ..."""
    it = iter(l)
    x0 = it.next()
    for x1 in it:
        yield (x0,x1)
        x0 = x1


class MatGrid:
    """Parent class for mmGrid-likes.
    
    Daughter classes should define
    - create_tags()
    - generate()
    """

    def __init__(self, mesh):
        """ """
        self.materials = prepare_materials()
        self.cells = prepare_cells()

class SingleMatGrid(MatGrid):
    """Object representing a single material grid
    
    Each voxel on the grid contains a single material.
    """

    def __init__( self, mesh ):
        """Create a grid based on a given mesh"""
        MatGrid.__init__(self, mesh)
        self.mesh = mesh

        self.voxels = list(mesh.iterate(iBase.Type.region, iMesh.Topology.all))


    def create_tags(self):
        """Tag voxels with each material
        """
        mesh = self.mesh
        # Iterate through each material in the problem
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

                if mat == matnum:
                    # Material matnum is assumed to be 100%  of voxel contents
                    mattag[vox] = 1.0
                else:
                    # matnum is treated as not present in the voxel
                    mattag[vox] = 0.0

                # We don't have errors with this method
                errtag[vox] = 0.0


    def generate(self):
        """Get voxel materials by getting voxel centers and checking with DagMC
        """
        self.coords = get_vox_centers(self.mesh, self.voxels)
        self.voxmats = get_point_materials(self.materials, self.coords)


class mmGrid(MatGrid):
    """Object representing a macromaterial grid"""

    def __init__( self, scdmesh ):
        """Create a grid based on a given structured mesh"""
        MatGrid.__init__(self, scdmesh.imesh)
        self.scdmesh = scdmesh

        idim = scdmesh.dims.imax - scdmesh.dims.imin
        jdim = scdmesh.dims.jmax - scdmesh.dims.jmin
        kdim = scdmesh.dims.kmax - scdmesh.dims.kmin
        mat_dim = len( self.materials )
        cell_dim = len( self.cells )

        self.voxel_dt = np.dtype([('mats',np.float64,mat_dim),
                                  ('errs',np.float64,mat_dim),
                                  ('cells',np.float64,cell_dim)])
        self.grid = np.zeros( (idim, jdim, kdim), dtype=self.voxel_dt )
        self.first_vol = None

    @classmethod
    def fromDagGeom( cls, ndiv=10 ):
        """Create a grid based on the geometry currently loaded in DagMC

        Creates an equally spaced grid with ndiv divisions per side, set
        within the full DagMC geometry.  This constructor requires that
        DagMC has geometry loaded with a rectangular graveyard volume
        """
        low_corner, high_corner = dagutil.find_graveyard_inner_box()
        divisions = [0]*3
        for i in range(3):
            divisions[i] = np.linspace(low_corner[i],high_corner[i],ndiv,endpoint=True)
        return cls( scdmesh.ScdMesh(*divisions) )

    def _rayframe_count(self, dim):

        sm = self.scdmesh

        plane = 'xyz'.replace(dim,'')
        adivs = sm.getDivisions( plane[0] )
        bdivs = sm.getDivisions( plane[1] )

        return (len(adivs)-1)*(len(bdivs)-1)

    def _rayframe(self, dim):
        """Generator: yield squares on the side of the mesh perpendicular to dim
        
        Returns ijk, the structured mesh coordinate of the hex along which
        the square lies, and (a0,a1,b0,b1), the coordinates of the corners of 
        the squares
        """
        sm = self.scdmesh

        plane = 'xyz'.replace(dim,'')

        adivs = sm.getDivisions( plane[0] )
        a_idx = 'xyz'.find(plane[0])

        bdivs = sm.getDivisions( plane[1] )
        b_idx = 'xyz'.find(plane[1])

        ijk = list(sm.dims[0:3])

        for a0, a1 in pairwise( adivs ):
            ijk[b_idx] = sm.dims[b_idx]
            for b0, b1 in pairwise( bdivs ):
                yield ijk, (a0, a1, b0, b1)
                ijk[b_idx] += 1
            ijk[a_idx] += 1

    def _grid_fragments(self, divs, div, startloc, length):
        """Generator: yield line segments along a ray

        The divs parameter is the divisions of the grid along a ray.  Div is
        the division index after which the ray starts, and startloc is the
        starting position.  Length is the length of the ray from startloc.

        Yields a 3-tuple (L, ratio, keepgoing)
            L: The length of the ray segment in the next grid element
            ratio: the ratio of L to length of the grid element.
            keepgoing: true if unassigned length remains after this iteration.
        """
        L = length
        loc = startloc
        for x0, x1 in pairwise(divs[div:]):
            diff = x1 - loc
            meshdiff = x1 - x0
            if diff < L:
                L -= diff
                loc += diff
                yield (diff,diff/meshdiff,True)
            else:  # diff >= L
                yield (L,L/meshdiff,False)
                loc = L
                break

    def _alloc_one_ray(self, start_ijk, dim, xyz, uvw, divs, samples, cell_samples):
        """Fire a single ray and store the sampled data to the grid
        
        start_ijk: structured mesh coordinates of the hex from which ray begins
        dim: 0, 1, or 2 depending on whether whether ray is x, y, or z-directed.
        xyz: start position of ray
        uvw: direction of ray
        divs: The structured grid divisions along this dimension.
        samples: 2D array of zeros used to store ray info
        """
        first_vol = self.first_vol
        if not first_vol or not dagmc.point_in_volume(first_vol,xyz,uvw):
            first_vol = dagmc.find_volume(xyz,uvw)

        vol = first_vol
        loc = divs[0]
        div = 0
        for nxtvol, raydist, _ in dagmc.ray_iterator( vol, xyz, uvw ):
            mat_idx = get_mat_id( self.materials, vol )
            vol = nxtvol
            vol_idx = self.cells[vol][0]
            for meshdist, meshrat, newloc in self._grid_fragments( divs, div, loc, raydist ):
                # The ray fills this voxel for a normalized distance of
                # meshrat = (meshdist / length_of_voxel)
                samples[div,mat_idx] += meshrat
                cell_samples[div,vol_idx] += meshrat
                loc += meshdist
                if(newloc):
                    div += 1

        # Save the first detected volume to speed future queries
        self.first_vol = first_vol

        # prepare an indexing object for self.grid to access the appropriate mesh row.
        # It is important to use a slice object rather than a general sequence
        # because a general sequence will trigger numpy's advanced iteration,
        # which returns copies of data instead of views.
        idx_ijk = start_ijk
        idx_ijk[dim] = slice(self.scdmesh.dims[dim], self.scdmesh.dims[dim+3])
        for sample, voxel in itertools.izip_longest( samples, self.grid[idx_ijk]):
            voxel['mats'] += sample
            voxel['errs'] += sample**2

        for cell_sample, voxel in itertools.izip_longest( cell_samples, self.grid[idx_ijk]):
            voxel['cells'] += cell_sample

    def generate(self, N, use_grid=False ):
        """Sample the DagMC geometry and store the results on this grid.

        N is the number of samples to take per voxel per dimension
        """
        count = 1
        if use_grid:
            rays = _linspace_square(N)
        else:
            rays = _random_square(N**2)

        total_ray_count = sum([self._rayframe_count(dim) for dim in 'xyz']) * (N**2)

        # iterate over ray-firing directions
        for idx, dim in enumerate('xyz'):
            uvw = np.array([0,0,0],dtype=np.float64)
            uvw[idx] = 1.0
            divs = self.scdmesh.getDivisions(dim)
            samples = np.zeros((len(divs)-1,(len(self.materials))), dtype=np.float64)
            cell_samples = np.zeros((len(divs)-1,(len(self.cells))), dtype=np.float64)             


            def make_xyz(a,b):
                    xyz = [a,b]
                    xyz.insert(idx,divs[0])
                    return xyz

            # iterate over all the scdmesh squares on the plane normal to uvw
            for ijk, square in self._rayframe(dim):
                _msg('\rFiring rays: {0}%'.format((100*count)/total_ray_count), False)
                # For each ray that starts in this square, take a sample
                for xyz in (make_xyz(a,b) for a,b in rays(*square)):
                    self._alloc_one_ray( ijk, idx, xyz, uvw, divs, samples, cell_samples )
                    count += 1
                    samples[:,:] = 0
                    cell_samples[:,:] = 0
        _msg('\rFiring rays: 100%')

        total_scores_per_vox = N*N*3
        max_err = 0
        _msg("Normalizing...")
        for vox in self.grid.flat:
            # Note: vox['mats'] = ... does not work as expected, but
            #       vox['mats'] /= ... does the right thing.
            # To get the correct assignment behavior, use an extra [:], as below
            vox['mats'] /= total_scores_per_vox
            errs = vox['errs'] / total_scores_per_vox
            sigma = np.sqrt( (errs - (vox['mats']**2)) / total_scores_per_vox )
            vox['errs'][:] = sigma
            vox['cells'] /= total_scores_per_vox
            max_err = max(max_err, max(vox['errs']))
        _msg("Maximum error: {0}".format(max_err))


    def create_tags(self):
        """Tags material information to mesh"""
        mesh = self.scdmesh.imesh
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
            try:
                celltag = mesh.createTag( matname+'_cell', 1, np.float64 )
            except iBase.TagAlreadyExistsError:
                celltag = mesh.getTagHandle( matname+'_cell', 1, np.float64 )
            # Tag each hex
            for ijk, (mat,err,cell) in np.ndenumerate(self.grid):
                offset_ijk = [x+y for x,y in zip(ijk,self.scdmesh.dims[0:3])]
                hx = self.scdmesh.getHex(*offset_ijk)
                mattag[hx] = mat[matnum]
                errtag[hx] = err[matnum]


        for idx, (cell, (cellnum,cellname)) in enumerate(self.cells.iteritems()):
            # Get tag handle
            try:
                celltag = mesh.createTag( cellname, 1, np.float64 )
            except iBase.TagAlreadyExistsError:
                celltag = mesh.getTagHandle( cellname, 1, np.float64 )
            # Tag each hex
            for ijk, (mat,err,cell) in np.ndenumerate(self.grid):
                offset_ijk = [x+y for x,y in zip(ijk,self.scdmesh.dims[0:3])]
                hx = self.scdmesh.getHex(*offset_ijk)
                celltag[hx] = cell[cellnum]


    def writeFile(self, filename, alara_geom_file=None ):
        """Save mesh file, and optionally invoke creation of alara_geom file"""
        mesh = self.scdmesh
        mesh.scdset.save(filename)
        if alara_geom_file:
            write_alara_geom(alara_geom_file, mesh)


def load_geom(filename):
    """Load geometry from the given file into dagmc

    This is provided as a convenience so client code doesn't need to invoke 
    pydagmc.  Note that DagMC can only have one set of geometry loaded per 
    program invocation.  This means that this function should only be called 
    once, and the resulting geometry will become globally visible to all 
    clients of mmgrid.

    Parameters
    ----------
    filename : string
        Filename with geometry information. Typically a .sat file.
    """
    dagmc.load( filename )


def main( arguments=None ):
    global _quiet
    op = optparse.OptionParser()
    op.set_usage('%prog [options] geometry_file [structured_mesh_file]')
    op.set_description('Compute a macromaterial grid in the tradition of '
                       'mmGridGen.  The first required argument should be a '
                       'DagMC-loadable geometry.  The optional second argument '
                       'must be a file with a single structured mesh.  In the '
                       'absence of the second argument, mmgrid will attempt to '
                       'infer the shape of the DagMC geometry and create a '
                       'structured grid to match it, with NDVIS divisions '
                       'on each side.')
    op.add_option( '-n',  help='Set N. N^2 rays fired per row.  Default N=%default',
                   dest='numrays', default=20, type=int )
    op.add_option( '-g', '--grid', help='Use grid of rays instead of randomly selected starting points',
                    dest='usegrid', default=False, action='store_true' )
    op.add_option( '-o', '--output', help='Output file name, default=%default',
                   dest='output_filename', default='mmgrid_output.h5m' )
    op.add_option( '-q', '--quiet', help='Suppress non-error output from mmgrid',
                   dest='quiet', default=False, action='store_true' )
    op.add_option( '-d','--divs', help='Number of mesh divisions to use when inferring mesh size, default=%default',
                   dest='ndivs', default=10 )
    op.add_option( '-a', '--alara', help='Write alara geom to specified file name',
                   dest='alara_geom_file', default=None, action='store')
    opts, args = op.parse_args( arguments )
    if len(args) != 1 and len(args) != 2:
        op.error( 'Need one or two arguments' )

    _quiet = opts.quiet

    load_geom( args[0] )
    sm = None
    if len(args) == 2:
        sm = scdmesh.ScdMesh.fromFile(args[1])
        grid = mmGrid( sm )
    else:
        grid = mmGrid.fromDagGeom(opts.ndivs)

    grid.generate(opts.numrays, opts.usegrid)
    grid.createTags()
    grid.writeFile( opts.output_filename, opts.alara_geom_file )


if __name__ == '__main__':
    main()
