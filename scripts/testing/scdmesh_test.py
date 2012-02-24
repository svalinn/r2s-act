from itaps import iBase, iMesh, iMeshExtensions
import numpy
import unittest
import os.path

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


