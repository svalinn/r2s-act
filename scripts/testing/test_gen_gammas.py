import unittest
import PhtnSrcToH5M
import gen_gammas
from scdmesh import ScdMesh, ScdMeshError
from itaps import iMesh, iBase
import os.path

# These directories are relative to scripts directory.
inputfile = "../testcases/simplebox-3/phtn_src"
meshfile_orig  = "../testcases/simplebox-3/matFracs.h5m"
meshfile  = "../testcases/simplebox-3/matFracs3.h5m"




class TestCalcVolumes(unittest.TestCase):

    def setUp(self):
        self.mesh = iMesh.Mesh()
        filename = os.path.join(os.path.dirname(__file__), 'grid543.h5m')
        self.myScd = ScdMesh.fromFile(self.mesh, filename)
        #self.mesh.open

    def test_calc_volumes_list_1(self):
        """
        Checks that calc_volumes_list works for 3x3x3 mesh with equal voxel sizing.
        """
        volumes = [48,40, 60,50, 60,50, \
                48,40, 60,50, 60,50, \
                48,40, 60,50, 60,50, \
                48,40, 60,50, 60,50]
        self.assertEqual(gen_gammas.calc_volumes_list(self.myScd), volumes)
    
class TestGenGammasFile(unittest.TestCase):

    def setUp(self):

#    #@with_setup(test_phtnsrc_read)
#    def test_calc_volumes_list_2():
#        """
#        Checks that calc_volumes_list works for 3x3x3 mesh with equal voxel sizing.
#        Also includes some negative mesh intervals, with mixed integers/floats.
#        """
#        gen_gammas.calc_volumes_list([[-2,-1.0,0,1.0],[-2,-1,0,1],[0.0,1.0,2.0,3.0]])
#        assert my_obj.vol == [1] * (3*3*3)
    
    
