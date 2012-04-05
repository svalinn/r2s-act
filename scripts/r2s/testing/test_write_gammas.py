import unittest
from r2s.io import read_alara_phtn
from r2s.io import write_gammas
from scdmesh import ScdMesh, ScdMeshError
from itaps import iMesh, iBase
import os.path

# These directories are relative to scripts directory.
inputfile = "../testcases/simplebox-3/phtn_src" #revision controlled
meshfile_orig = "r2s/testing/matFracsSCD3x3x3.h5m"
meshfile = "matFracsSCD3x3x3_tagged.h5m"
outfile = "gammas_test"


class TestCalcVolumes(unittest.TestCase):

    def setUp(self):
        self.mesh = iMesh.Mesh()
        filename = os.path.join(os.path.dirname(__file__), '../../testing/grid543.h5m')
        self.myScd = ScdMesh.fromFile(self.mesh, filename)

    def test_calc_volumes_list_1(self):
        """
        Checks that calc_volumes_list works for 3x3x3 mesh with equal voxel sizing.
        """
        volumes = [48,40, 60,50, 60,50, \
                48,40, 60,50, 60,50, \
                48,40, 60,50, 60,50, \
                48,40, 60,50, 60,50]
        self.assertEqual(write_gammas.calc_volumes_list(self.myScd), volumes)
    
class TestGenGammasFile(unittest.TestCase):

    def setUp(self):
        os.system("cp " + meshfile_orig + " " + meshfile)
        read_alara_phtn.read_to_h5m(inputfile, meshfile)

    def tearDown(self):
        os.system("rm " + meshfile)
        os.system("rm " + outfile)
    
    def test_gen_gammas(self):
        """Tests a run-through of the method with 3x3x3 non-void geometry."""
        self.assertEqual(write_gammas.gen_gammas_file_from_h5m( \
                meshfile, outfile), 1)

