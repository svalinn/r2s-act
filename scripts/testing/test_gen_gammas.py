import unittest
import gen_gammas
from scdmesh import ScdMesh, ScdMeshError
from itaps import iMesh, iBase
import os.path


class TestGenGammas(unittest.TestCase):

    def setUp(self):
        self.mesh = iMesh.Mesh()
        filename = os.path.join(os.path.dirname(__file__), 'grid543.h5m')
        self.myScd = ScdMesh.fromFile(self.mesh, filename)
        #self.mesh.open

    #@with_setup(test_phtnsrc_read)
    def test_calc_volumes_list_1(self):
        """
        Checks that calc_volumes_list works for 3x3x3 mesh with equal voxel sizing.
        """
        print self.myScd.getDivisions('x')
        gen_gammas.calc_volumes_list(self.myScd)
        self.assertEqual(gen_gammas.calc_volumes_list(self.myScd), [1] * 3*3*3)
    
#    #@with_setup(test_phtnsrc_read)
#    def test_calc_volumes_list_2():
#        """
#        Checks that calc_volumes_list works for 3x3x3 mesh with equal voxel sizing.
#        Also includes some negative mesh intervals, with mixed integers/floats.
#        """
#        gen_gammas.calc_volumes_list([[-2,-1.0,0,1.0],[-2,-1,0,1],[0.0,1.0,2.0,3.0]])
#        assert my_obj.vol == [1] * (3*3*3)
    
    
