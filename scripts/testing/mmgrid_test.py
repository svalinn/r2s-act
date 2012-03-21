import unittest
import sys
import os
import itertools
import numpy

try:
    import mmgrid
    import pydagmc
except ImportError as e:
    print >>sys.stderr, "Could not import mmgrid:", e
    print >>sys.stderr, "The mmgrid test cases will be skipped."
    import nose
    raise nose.SkipTest
   
from itaps import iMesh, iMeshExtensions
from scdmesh import ScdMesh

class mmGridHelperTest( unittest.TestCase) :

    def test_linspace_square(self):
        f = mmgrid._linspace_square( 1 )
        gen = f( 0.0, 2.0, 0.0, 2.0 )
        self.assertEqual( gen.next(), (1.0,1.0) )
        self.assertRaises( StopIteration, gen.next )

        f = mmgrid._linspace_square( 2 )
        gen = f( 0, 3, -1, 2 )
        check = itertools.product( (1,2), (0,1) )
        for x,y in itertools.izip_longest( gen, check ):
            self.assertEqual(x, y)

    def test_random_square(self):
        f = mmgrid._random_square( 100 )
        gen = f( 0, 1, 0, 1 )
        for pt in gen:
            self.assertTrue( all(pt[x] > 0 and pt[x] < 1.0 
                                 for x in (0,1)) )


class mmGridTest( unittest.TestCase ):
    
    # must load dagmc geometry only once; use this alphabetically first name to ensure
    # this function runs before other tests
    def test__load(self):
        path = os.path.join( os.path.dirname( __file__ ), 'hemispheres.h5m' )
        pydagmc.dagmc.load( path )

    def test_matset(self):
        """Test the prepare_materials and get_mata_id functions"""
        matdict = mmgrid.prepare_materials()
        self.assertEqual( matdict, 
                         {(0, 0.0): (0, 'matVOID'),
                          (2, -8.0): (1, 'mat2_rho-8.0'),
                          (3, -1.0): (2, 'mat3_rho-1.0')} )

        self.assertEqual( 0, mmgrid.get_mat_id(matdict,1) )
        self.assertEqual( 1, mmgrid.get_mat_id(matdict,2) )
        self.assertEqual( 2, mmgrid.get_mat_id(matdict,4) )

    def test_rayframes(self):

        # a mesh with divisions at -1, 0, and 1 for all three dimensions
        sm = ScdMesh( iMesh.Mesh(), *([(-1, 0, 1)]*3) )
        mg = mmgrid.mmGrid(sm)

        squares = [ (-1,0,-1,0), (-1,0,0,1), (0,1,-1,0), (0,1,0,1) ]

        ijks = [ [0,0,0], [0,0,1], [0,1,0], [0,1,1] ]


        for (ijk,ab), ab_test, ijk_test in itertools.izip_longest( mg._rayframe('x'), squares,ijks):
            self.assertEqual( ab, ab_test )
            self.assertEqual( ijk, ijk_test )

    def test_mmgrid_create(self):
        sm = ScdMesh( iMesh.Mesh(), *([(-1, 0, 1)]*3) )
        grid = mmgrid.mmGrid( sm )
        self.assertEqual( grid.grid.shape, (2,2,2) )
        self.assertEqual( grid.grid[0,0,0]['mats'].shape, (3,) )
        self.assertEqual( grid.grid[0,0,0]['errs'].shape, (3,) )

    def test_create_from_geom(self):
        grid = mmgrid.mmGrid.fromDagGeom(8)
        sm = grid.scdmesh
        self.assertEqual( sm.dims, (0,0,0,7,7,7) )
        extents = (-22.8, 22.8)
        for dim in 'xyz':
            divs = sm.getDivisions('x')
            self.assertAlmostEqual( extents[0], divs[0], 4 )
            self.assertAlmostEqual( extents[1], divs[-1], 4 )


    def test_mmgrid_generate(self):
        grid_side = [-5,-3.75,-2.5,-1.25,0,1.25,2.5,3.75,5]
        sm = ScdMesh( iMesh.Mesh(), *([grid_side]*3) )
        grid = mmgrid.mmGrid( sm )
        grid.generate(2, True)

        for ijk, x in numpy.ndenumerate(grid.grid):
            self.assertAlmostEqual( 
                    sum(x['mats']), 1.0, 
                    msg='Normality at ijk={0}:\n'
                        '    sum({1}) = {2} != 1.0'.format(ijk, x['mats'], sum(x['mats'])))

        grid.createTags()


    def test_unequal_grid_size(self):
        """Test creating an mmgrid on a mesh with uneven grid spacing"""
        grid_side = [-3,0,.1,.2,3]
        sm = ScdMesh( iMesh.Mesh(), *([grid_side]*3) )
        grid = mmgrid.mmGrid( sm )
        grid.generate(5)#, True)

        for ijk, x in numpy.ndenumerate(grid.grid):
            self.assertAlmostEqual( 
                    sum(x['mats']), 1.0, 
                    msg='Normality at ijk={0}:\n'
                        '    sum({1}) = {2} != 1.0'.format(ijk, x['mats'], sum(x['mats'])))

