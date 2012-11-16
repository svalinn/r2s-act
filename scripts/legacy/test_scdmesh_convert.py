from itaps import iBase, iMesh
import unittest
import os.path
import itertools

from scdmesh import ScdMesh, ScdMeshError


import scdmesh_convert as sc_convert


class ScdConvertTest(unittest.TestCase):

    def setUp(self):
        self.mesh = iMesh.Mesh()
        self.mesh.rootSet.load( os.path.join(os.path.dirname(__file__), 'test_matFracs.h5m'))
        # each dimension is equal in this test file and has the following divisions
        self.reference = [-5,-3.75,-2.5,-1.25,0,1.25,2.5,3.75,5]

    def test_extract(self):
        extracted_dims = sc_convert.extract_dimensions( self.mesh, self.mesh.rootSet )
        for dim in extracted_dims:
            self.assertEqual( set(self.reference), dim )

    def test_convert(self):
        m = iMesh.Mesh()
        sm = sc_convert.convert_mesh( self.mesh, self.mesh.rootSet, m )
        self.assertEqual( sm.dims, (0,0,0,8,8,8) )
        for L in 'xyz':
            self.assertEqual( sm.getDivisions(L), self.reference )

        # also test that converting into the same iMesh instance doesn't fault
        sm2 = sc_convert.convert_mesh( self.mesh, self.mesh.rootSet, self.mesh )

    def test_tags(self):
        m = iMesh.Mesh()
        sm = sc_convert.convert_mesh( self.mesh, self.mesh.rootSet, m )
        for tname in ["FRACTIONS","ERRORS"]:
            t1 = self.mesh.getTagHandle(tname)
            t2 = sm.imesh.getTagHandle(tname)
            for (e1,e2) in itertools.izip_longest( 
                               self.mesh.iterate( iBase.Type.region, iMesh.Topology.hexahedron ),
                               sm.iterateHex( 'xyz' )):
                self.assertTrue( all( t1[e1] == t2[e2] ) )
        for tname in ["GRID_DIMS","MATS"]: # tags on root set
            t1 = self.mesh.getTagHandle(tname)
            t2 = sm.imesh.getTagHandle(tname)
            self.assertTrue( all(t1[self.mesh.rootSet] == t2[sm.scdset]) )

    def test_error(self):
        sm = ScdMesh( *([range(5)]*3) )
        self.assertRaises( ScdMeshError, 
                           sc_convert.convert_mesh, sm.imesh, sm.scdset, sm.imesh )
