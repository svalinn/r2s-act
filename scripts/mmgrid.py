#!/usr/bin/env python

from operator import itemgetter
import itertools
import numpy as np
import random
import sys
import optparse

from itaps import iMesh
import scdmesh
from pydagmc import dagmc
from pydagmc import util as dagutil


class mmGridError(Exception):
    pass


_quiet = False


def _msg(msg, newline=True):
    if not _quiet:
        sys.stdout.write(msg)
        if newline:
            sys.stdout.write('\n')
        sys.stdout.flush()


def prepare_materials():
    matset = dagutil.get_material_set(with_rho=True)
    names = {}
    for idx, (mat, rho) in enumerate(sorted(matset, key=itemgetter(0))):
        if mat == 0:
            name = 'matVOID'
        else:
            name = 'mat{0}_rho{1}'.format( mat, rho )
        names[(mat, rho)] = (idx, name)
    return names


def get_mat_id(materials, volume_id):

    mat = dagmc.volume_metadata(volume_id)
    matnum = mat['material']
    matrho = mat['rho']
    if matnum == 0.0:
        matrho = 0.0
    mat_idx = materials[(matnum,matrho)][0]
    return mat_idx


def _linspace_square( n ):
    """Return a callable that creates an evenly spaced grid in the given quad"""
    def points_inside(a0, a1, b0, b1):
        # linspace includes the start point, which we do not want
        # so ask for one extra point and drop the zeroth result
        aspace = np.linspace(a0, a1, n+1, endpoint=False)[1:]
        bspace = np.linspace(b0, b1, n+1, endpoint=False)[1:]
        return itertools.product(aspace,bspace)
    return points_inside


def _random_square( n ):
    """Return a callable that creates randomly distributed points in the give quad"""
    def points_inside(a0, a1, b0, b1):
        for _ in xrange(n):
            a = random.uniform(a0,a1)
            b = random.uniform(b0,b1)
            yield a,b
    return points_inside


def pairwise( l ):
    it = iter(l)
    x0 = it.next()
    for x1 in it:
        yield (x0,x1)
        x0 = x1


class mmGrid:

    def __init__( self, scdmesh ):
        self.scdmesh = scdmesh
        self.materials = prepare_materials()

        idim = scdmesh.dims.imax - scdmesh.dims.imin
        jdim = scdmesh.dims.jmax - scdmesh.dims.jmin
        kdim = scdmesh.dims.kmax - scdmesh.dims.kmin
        mat_dim = len( self.materials )

        self.voxel_dt = np.dtype([('mats',np.float64,mat_dim),
                                  ('errs',np.float64,mat_dim)])
        self.grid = np.zeros( (idim, jdim, kdim), dtype=self.voxel_dt )
        self.first_vol = None

    @classmethod
    def from_dag_geom( cls, ndiv=10 ):
        low_corner, high_corner = dagutil.find_graveyard_inner_box()
        divisions = [0]*3
        for i in range(3):
            divisions[i] = np.linspace(low_corner[i],high_corner[i],ndiv,endpoint=True)
        return cls( scdmesh.ScdMesh( iMesh.Mesh(), *divisions) )

    def _rayframe(self, dim):
        sm = self.scdmesh

        plane = 'xyz'.replace(dim,'')

        adivs = sm.getDivisions( plane[0] )
        a_idx = 'xyz'.find(plane[0])

        bdivs = sm.getDivisions( plane[1] )
        b_idx = 'xyz'.find(plane[1])

        ijk = list(sm.dims[0:3])

        for a0, a1 in pairwise( adivs ):
            print b_idx, ijk, sm.dims
            ijk[b_idx] = sm.dims[b_idx]
            for b0, b1 in pairwise( bdivs ):
                yield ijk, (a0, a1, b0, b1)
                ijk[b_idx] += 1
            ijk[a_idx] += 1

    def _grid_fragments(self, divs, div, startloc, length):
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

    def _alloc_one_ray(self, start_ijk, dim, xyz, uvw, divs):
        first_vol = self.first_vol
        if not first_vol or not dagmc.point_in_volume(first_vol,xyz,uvw):
            first_vol = dagmc.find_volume(xyz,uvw)

        vol = first_vol
        loc = divs[0]
        div = 0
        ijk = list(start_ijk)
        samples = np.zeros((len(divs)-1,(len(self.materials))), dtype=np.float64)

        for nxtvol, raydist, _ in dagmc.ray_iterator( vol, xyz, uvw ):
            mat_idx = get_mat_id( self.materials, vol )
            for meshdist, meshrat, newloc in self._grid_fragments( divs, div, loc, raydist ):
                # allocate meshdist to mesh at this location
                # with material for volume 'vol'
                #print ijk, "gets vol", vol, "mat", mat_idx, "length", meshdist, "({0})".format(meshrat), "at", div
                samples[div,mat_idx] += meshrat

                loc += meshdist
                if(newloc):
                    div += 1
                    ijk[dim] = div
            vol = nxtvol

        self.first_vol = first_vol

        # prepare an indexing object for self.grid to access the appropriate mesh row.
        # It is important to use a slice object rather than a general sequence
        # because a general sequence will trigger numpy's advanced iteration,
        # which returns copies of data instead of views.
        idx_ijk = ijk
        idx_ijk[dim] = slice(self.scdmesh.dims[dim], self.scdmesh.dims[dim+3])
        for sample, voxel in itertools.izip_longest( samples, self.grid[idx_ijk]):
            voxel['mats'] += sample
            voxel['errs'] += sample**2

    def generate(self, N):
        count = 1
        rays = _linspace_square(N)

        # iterate over ray-firing directions
        for idx, dim in enumerate('xyz'):
            uvw = np.array([0,0,0],dtype=np.float64)
            uvw[idx] = 1.0
            divs = self.scdmesh.getDivisions(dim)

            def make_xyz(a,b):
                    xyz = [a,b]
                    xyz.insert(idx,divs[0])
                    return xyz

            # iterate over all the scdmesh squares on the plane normal to uvw
            for ijk, square in self._rayframe(dim):
                _msg('\rGenerating: {0}'.format(count), False)
                # For each ray that starts in this square, take a sample
                for xyz in (make_xyz(a,b) for a,b in rays(*square)):
                    self._alloc_one_ray( ijk, idx, xyz, uvw, divs )
                    count += 1

        total_scores = N*N*3
        max_err = 0
        _msg("\nnormalizing...")
        for vox in self.grid.flat:
            # Note: vox['mats'] = ... does not work as expected, but
            #       vox['mats'] /= ... does the right thing.
            # To get the correct assignment behavior, use an extra [:], as below
            vox['mats'] /= total_scores
            errs = vox['errs'] / total_scores
            sigma = np.sqrt( (errs - (vox['mats']**2)) / total_scores )
            vox['errs'][:] = sigma
            max_err = max(max_err, max(vox['errs']))
        _msg("Maximum error: {0}".format(max_err))

    def tag(self):
        mesh = self.scdmesh.mesh
        fractag = mesh.createTag( 'FRACTIONS', len(self.materials), np.float64 )
        errstag = mesh.createTag( 'ERRORS', len(self.materials), np.float64 )
        for ijk,(mat,err) in np.ndenumerate(self.grid):
            # TODO: This incorrectly assumes ijk is zero-based
            hx = self.scdmesh.getHex(*ijk)
            fractag[ hx ] = mat
            errstag[ hx ] = err

    def tag_for_visualization(self):
        mesh = self.scdmesh.mesh
        for idx, ((mat, rho), (matnum,matname)) in enumerate(self.materials.iteritems()):
            mattag = mesh.createTag( matname, 1, np.float64 )
            errtag = mesh.createTag( matname+'_err', 1, np.float64 )
            for ijk, (mat,err) in np.ndenumerate(self.grid):
                # TODO: assumes ijk is zero-based
                hx = self.scdmesh.getHex(*ijk)
                mattag[hx] = mat[matnum]
                errtag[hx] = err[matnum]

    def writeFile(self, filename):
        mesh = self.scdmesh
        mesh.scdset.save(filename)


def main( arguments=None ):
    global _quiet
    op = optparse.OptionParser()
    op.add_option( '-n', '--numrays', help='Number of rays per voxel, default=%default',
                   dest='numrays', default=20, type=int )
    op.add_option( '-o', '--output', help='Output file name, default=%default',
                   dest='output_filename', default='mmgrid_output.h5m' )
    op.add_option( '-q', '--quiet', help='Suppress non-error output from mmgrid',
                   dest='quiet', default=False, action='store_true' )
    op.add_option( '--divs', help='Number of mesh divisions to use when inferring mesh size, default=%default',
                   dest='ndivs', default=10 )
    opts, args = op.parse_args( arguments )
    if len(args) != 1 and len(args) != 2:
        op.error( 'Need one or two arguments' )

    _quiet = opts.quiet

    dagmc.load( args[0] )
    sm = None
    if len(args) == 2:
        sm = scdmesh.ScdMesh.from_file(args[1])
        grid = mmGrid( sm )
    else:
        grid = mmGrid.from_dag_geom(opts.ndivs)

    grid.generate(opts.numrays)
    grid.tag_for_visualization()
    grid.writeFile( opts.output_filename )


if __name__ == '__main__':
    main()
