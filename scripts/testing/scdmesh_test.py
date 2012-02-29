from itaps import iBase, iMesh, iMeshExtensions
import numpy
import unittest
import os.path
import itertools
from operator import itemgetter

from scdmesh import ScdMesh, ScdMeshError


class ScdMeshTest(unittest.TestCase):

    def setUp(self):
        self.mesh = iMesh.Mesh()

    def test_create(self):
        sm = ScdMesh( self.mesh, range(1,5), range(1,4), range(1,3) )
        self.assertEqual( sm.dims, (0,0,0,4,3,2) )

    def test_create_by_set(self):
        a =  self.mesh.createStructuredMesh( [0,0,0,1,1,1], 
                                             i=[1,2], j=[1,2], k=[1,2], 
                                             create_set=True )
        sm = ScdMesh.fromEntSet( self.mesh, a )
        self.assertEqual( sm.dims, (0,0,0,1,1,1) )

    def test_create_by_file(self):
        filename = os.path.join(os.path.dirname(__file__), 'grid543.h5m')
        sm = ScdMesh.fromFile(self.mesh, filename)
        self.assertEqual( sm.dims, (1, 11, -5, 5, 14, -3) )

    def test_get_hex(self):
        # mesh with valid i values 0-4, j values 0-3, k values 0-2
        sm = ScdMesh( self.mesh, range(11,15), range(21,24), range(31,33) )
        def check( e ):
            self.assertTrue( isinstance(e, iBase.Entity) )
        check(sm.getHex(0, 0, 0))
        check(sm.getHex(1, 1, 1))
        check(sm.getHex(3, 0, 0))
        check(sm.getHex(3, 2, 1))

        self.assertRaises(ScdMeshError, sm.getHex, -1,-1,-1)
        self.assertRaises(ScdMeshError, sm.getHex, 4, 0, 0)
        self.assertRaises(ScdMeshError, sm.getHex, 0, 3, 0)
        self.assertRaises(ScdMeshError, sm.getHex, 0, 0, 2)

    def test_get_vtx(self):
        # mesh with valid i values 0-4, j values 0-3, k values 0-2
        x_range = numpy.array(range(10,15),dtype=numpy.float64)
        y_range = numpy.array(range(21,24),dtype=numpy.float64)
        z_range = numpy.array(range(31,33),dtype=numpy.float64)

        sm = ScdMesh( self.mesh, x_range, y_range, z_range ) 

        for i,x in enumerate(x_range):
            for j,y in enumerate(y_range):
                for k,z in enumerate(z_range):
                    vtx = sm.getVtx(i,j,k)
                    vcoord = self.mesh.getVtxCoords( vtx )
                    self.assertTrue( all( vcoord == [x,y,z]) )


class ScdMeshIterateTest(unittest.TestCase):

    def setUp(self):
        self.mesh = iMesh.Mesh()
        self.sm = ScdMesh( self.mesh, range(10,14), # i = 0,1,2,3
                                      range(21,24), # j = 0,1,2
                                      range(31,33)) # k = 0,1

        self.I = range(0,4)
        self.J = range(0,3)
        self.K = range(0,2)

    def test_bad_iterates(self):

        self.assertRaises( ScdMeshError,  self.sm.iterateHex, 'abc' )
        self.assertRaises( TypeError,  self.sm.iterateHex, 12 )
        self.assertRaises( ScdMeshError,  self.sm.iterateHex, 'xxyz' )
        self.assertRaises( ScdMeshError,  self.sm.iterateHex, 'yyx' )
        self.assertRaises( ScdMeshError,  self.sm.iterateHex, 'xyz',z=[0,1,2] )

    def test_iterate_3d(self):
        
        # use izip_longest in the lockstep iterations below; this will catch any
        # situations where one iterator turns out to be longer than expected.
        izip = itertools.izip_longest

        it = self.sm.scdset.iterate( iBase.Type.region, 
                                     iMesh.Topology.hexahedron )

        print "testing zyx"

        # Test the zyx order, which is default; it should be equivalent
        # to the standard imesh iterator
        for it_x, sm_x in izip( it, self.sm.iterateHex() ):
            self.assertEqual( it_x, sm_x )

        print "testing xyz"

        all_indices_zyx = itertools.product( self.I, self.J, self.K )
        # Test the xyz order, the default from original mmGridGen
        for ijk_index, sm_x in izip( all_indices_zyx, 
                                     self.sm.iterateHex('xyz') ):
            self.assertEqual( self.sm.getHex(*ijk_index), sm_x )

        def tuple_sort( collection, indices ):
            # sorting function for order test
            def t( tup ):
                # sort this 3-tuple according to the order of x, y, and z in indices
                return ( tup['xyz'.find(indices[0])]*100 +
                         tup['xyz'.find(indices[1])]*10 +
                         tup['xyz'.find(indices[2])] )
            return sorted( collection, key = t )

        def test_order( order, *args,  **kw ):
            print 'testing',order
            all_indices = itertools.product(*args)
            for ijk_index, sm_x in izip( tuple_sort(all_indices, order),
                                         self.sm.iterateHex(order,**kw) ):
                self.assertEqual(self.sm.getHex(*ijk_index), sm_x)

        test_order( 'yxz', self.I, self.J, self.K )
        test_order( 'yzx', self.I, self.J, self.K )
        test_order( 'xzy', self.I, self.J, self.K )
        test_order( 'zxy', self.I, self.J, self.K )

        # Specify z=[1] to iterator
        test_order( 'xyz', self.I, self.J, [1], z=[1] )
        # Specify y=2 to iterator
        test_order( 'zyx', self.I, [2], self.K, y=2 )
        # specify x and y both to iterator
        test_order( 'yzx', [1,2,3],self.J[:-1], self.K, y=self.J[:-1], x=[1,2,3] )

    def test_iterate_2d(self):
        def test_order( iter1, iter2 ):
            for i1, i2 in itertools.izip_longest( iter1, iter2 ):
                self.assertEqual( i1, i2 )

        test_order( self.sm.iterateHex('yx'), self.sm.iterateHex('zyx', z=[0] ) )
        test_order( self.sm.iterateHex('yx',z=1), self.sm.iterateHex('zyx',z=[1]) )
        test_order( self.sm.iterateHex('yx',z=1), self.sm.iterateHex('yzx',z=[1]) )
        test_order( self.sm.iterateHex('zy',x=[3]), self.sm.iterateHex('zxy',x=3) )

        # Cannot iterate over multiple z's without specifing z order
        self.assertRaises( ScdMeshError, self.sm.iterateHex, 'yx', z=[0,1] )

    def test_iterate_1d(self):
        
        def test_equal( ijk_list, miter ):
            for ijk, i in itertools.izip_longest( ijk_list, miter ):
                self.assertEqual( self.sm.getHex(*ijk), i )

        test_equal( [[0,0,0],[0,0,1]], 
                    self.sm.iterateHex('z') )

        test_equal( [[0,1,1],[0,2,1]],
                    self.sm.iterateHex('y', y=[1,2], z=1) )

        test_equal( [[2,0,0],[2,1,0],[2,2,0]],
                    self.sm.iterateHex('y', x=2) ) 
        test_equal( [[0,0,0],[1,0,0],[2,0,0]], 
            self.sm.iterateHex('x', x=[0,1,2]) )

    def test_large_iterator(self):
        return 
        print "building large mesh"
        big = ScdMesh(iMesh.Mesh(), range(1,100), range(101,200), range(201,300))
        print "iterating (1)"
        for i in big.iterateHex():
            pass
        print "iterating (2)"
        for i in big.iterateHex( 'yzx' ):
            pass
