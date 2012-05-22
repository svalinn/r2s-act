import unittest
import os.path
import itertools

from r2s.io import read_alara_phtn
from r2s.io import write_gammas
from scdmesh import ScdMesh, ScdMeshError
from itaps import iMesh, iBase

thisdir = os.path.dirname(__file__)
inputfile = os.path.join(thisdir,"sb3_phtn_src")
meshfile_orig = os.path.join(thisdir,"matFracsSCD3x3x3.h5m")
meshfile = "matFracsSCD3x3x3_tagged.h5m"
outfile = "gammas_test"

meshfile1 = os.path.join(thisdir,"files_test_write_gammas/uniform_ergdirect.h5m")
meshfile2 = os.path.join(thisdir,"files_test_write_gammas/uniform_ergalias.h5m")
meshfile3 = os.path.join(thisdir,"files_test_write_gammas/voxel_nobias.h5m")
meshfile4 = os.path.join(thisdir,"files_test_write_gammas/voxel_bias.h5m")

gammas1 = os.path.join(thisdir,"files_test_write_gammas/gammas_uniform_ergdirect")
gammas2 = os.path.join(thisdir,"files_test_write_gammas/gammas_uniform_ergalias")
gammas3 = os.path.join(thisdir,"files_test_write_gammas/gammas_voxel_nobias")
gammas4 = os.path.join(thisdir,"files_test_write_gammas/gammas_voxel_bias")


class TestCalcVolumes(unittest.TestCase):

    def setUp(self):
        filename = os.path.join(thisdir, 'grid543.h5m')
        self.sm = ScdMesh.fromFile(filename)

    def test_calc_volumes_list_1(self):
        """
        Checks that calc_volumes_list works for 3x3x3 mesh with equal voxel sizing.
        """
        volumes = [48,40, 60,50, 60,50, \
                48,40, 60,50, 60,50, \
                48,40, 60,50, 60,50, \
                48,40, 60,50, 60,50]
        self.assertEqual(write_gammas.calc_volumes_list(self.sm), volumes)
    
class TestWriteGammas_Runs(unittest.TestCase):
    # Tests in this class are done witha  3x3x3 non-void geometry

    def setUp(self):
        os.system("cp " + meshfile_orig + " " + meshfile)
        self.sm = ScdMesh.fromFile(meshfile)
        read_alara_phtn.read_to_h5m(inputfile, self.sm)

    def tearDown(self):
        os.system("rm " + meshfile)
        os.system("rm " + outfile)
    
    def test_gen_gammas(self):
        """Tests a run-through with defaults; direct discrete."""
        self.assertEqual(write_gammas.gen_gammas_file_from_h5m( \
                self.sm, outfile), 1)

    def test_direct_alias_erg_bins(self):
        """Tests a run-through with: direct discrete + erg alias bins."""
        self.assertEqual(write_gammas.gen_gammas_file_from_h5m( \
                self.sm, outfile, do_alias=True), 1)

    def test_direct_with_bias(self):
        """Tests a run-through with: direct discrete + bias
        Note: biasing is not enabled with direct discrete, so code defaults
        to regular direct discrete behavior.
        """
        self.assertEqual(write_gammas.gen_gammas_file_from_h5m( \
                self.sm, outfile, do_bias=True), 1)

    def test_voxel_alias(self):
        """Tests a run-through of the method with 3x3x3 non-void geometry."""
        self.assertEqual(write_gammas.gen_gammas_file_from_h5m( \
                self.sm, outfile, by_voxel=True), 1)

    def test_voxel_alias_with_bias_and_erg_alias_bins(self):
        """Tests a run-through of the method with 3x3x3 non-void geometry."""
        self.assertEqual(write_gammas.gen_gammas_file_from_h5m( \
            self.sm, outfile, do_alias=True, by_voxel=True, do_bias=True), 1)

class TestWriteGammas_Correct(unittest.TestCase):
    # Tests in this class are done with 1x3x1 geometry. Resulting gammas files
    #  are compared for discrepancies.

    def tearDown(self):
        #os.system("rm " + self.meshfile)
        os.system("rm " + outfile)

    def compare_gammas(self, myoutfile, mygammas):
        # Method does comparisons of two files.
        fw1 = open(myoutfile, 'r')
        fw2 = open(mygammas, 'r')
   
        for line1, line2 in itertools.izip_longest(fw1, fw2):
            self.assertEqual(line1, line2)

        fw1.close()
        fw2.close()

    def test_uniform_ergdirect(self):
        """ """
        self.meshfile = meshfile1
        self.sm = ScdMesh.fromFile(self.meshfile)
        write_gammas.gen_gammas_file_from_h5m(self.sm, outfile)
        self.compare_gammas(outfile, gammas1)
    
    def test_uniform_ergalias(self):
        """ """
        self.meshfile = meshfile2
        self.sm = ScdMesh.fromFile(self.meshfile)
        write_gammas.gen_gammas_file_from_h5m(self.sm, outfile, \
                do_alias=True)
        self.compare_gammas(outfile, gammas2)

    def test_voxel_nobias(self):
        """ """
        self.meshfile = meshfile3
        self.sm = ScdMesh.fromFile(self.meshfile)
        write_gammas.gen_gammas_file_from_h5m(self.sm, outfile, \
                do_alias=True, by_voxel=True)
        self.compare_gammas(outfile, gammas3)

    def test_voxel_bias(self):
        """ """
        self.meshfile = meshfile4
        self.sm = ScdMesh.fromFile(self.meshfile)
        write_gammas.gen_gammas_file_from_h5m(self.sm, outfile, \
                do_alias=True, by_voxel=True, do_bias=True)
        self.compare_gammas(outfile, gammas4)


