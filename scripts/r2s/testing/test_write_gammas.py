import unittest
import os.path
import itertools

from r2s.io import read_alara_phtn
from r2s.io import write_gammas
from r2s.scdmesh import ScdMesh, ScdMeshError
from itaps import iMesh, iBase


thisdir = os.path.dirname(__file__)
inputfile = os.path.join(thisdir, "sb3_phtn_src")
meshfile_orig = os.path.join(thisdir, "h5m_files/matFracsSCD3x3x3.h5m")
meshfile = os.path.join(thisdir, "h5m_files/matFracsSCD3x3x3_tagged.h5m")
outfile = os.path.join(thisdir, "gammas_test")

# .h5m files for generating different gammas files
meshfile_g = os.path.join(thisdir, "files_test_write_gammas/example_with_bias.h5m")
# gammas files for comparing test result with expected result
gammas1 = os.path.join(thisdir, "files_test_write_gammas/gammas_uni_seq")
gammas2 = os.path.join(thisdir, "files_test_write_gammas/gammas_uni_seq_bias")
gammas3 = os.path.join(thisdir, "files_test_write_gammas/gammas_uni_cum")
gammas4 = os.path.join(thisdir, "files_test_write_gammas/gammas_uni_cum_bias")
gammas5 = os.path.join(thisdir, "files_test_write_gammas/gammas_voxel_seq")
gammas6 = os.path.join(thisdir, "files_test_write_gammas/gammas_voxel_seq_bias")
gammas7 = os.path.join(thisdir, "files_test_write_gammas/gammas_voxel_cum")
gammas8 = os.path.join(thisdir, "files_test_write_gammas/gammas_voxel_cum_bias")

totalsfile = os.path.join(os.getcwd(), "phtn_src_totals")


class TestCalcVolumes(unittest.TestCase):

    def setUp(self):
        filename = os.path.join(thisdir, 'h5m_files/grid543.h5m')
        self.sm = ScdMesh.fromFile(filename)

    def test_calc_volumes_list_1(self):
        """Checks that calc_volumes_list works for 3x3x3 mesh with equal voxel sizing.
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
        os.system("rm " + totalsfile)
    
    def test_gen_gammas(self):
        """Tests a run-through with defaults; direct discrete."""
        self.assertEqual(write_gammas.gen_gammas_file_from_h5m( \
                self.sm, outfile), 1)

    def test_direct_alias_erg_bins(self):
        """Tests a run-through with: direct discrete + erg alias bins."""
        self.assertEqual(write_gammas.gen_gammas_file_from_h5m( \
                self.sm, outfile), 1)

    def test_direct_with_bias(self):
        """Tests a run-through with: direct discrete + bias
        Note: biasing is not enabled with direct discrete, so code defaults
        to regular direct discrete behavior.
        """
        self.assertEqual(write_gammas.gen_gammas_file_from_h5m( \
                self.sm, outfile, do_bias=True), 1)

    def test_voxel_alias(self):
        """Tests a run-through with: voxel sampling specified.
        Note: do_alias must be True for voxel sampling gammas to be made, so
        code defaults to regular direct discrete behavior"""
        self.assertEqual(write_gammas.gen_gammas_file_from_h5m( \
                self.sm, outfile), 1)

    def test_voxel_alias_with_bias_and_erg_alias_bins(self):
        """Tests a run-through with: voxel sampling with biasing."""
        self.assertEqual(write_gammas.gen_gammas_file_from_h5m( \
            self.sm, outfile, do_bias=True), 1)


class TestWriteGammas_Correct(unittest.TestCase):
    # Tests in this class are done with 1x3x1 geometry. Resulting gammas files
    #  are compared for discrepancies.  These tests are focused on getting the
    #  non-header contents correct.  (e.g. we do not test all of the individual
    #  parameters)

    def setUp(self):
        pass

    def tearDown(self):
        os.system("rm " + outfile)
        os.system("rm " + totalsfile)

    def compare_gammas(self, myoutfile, mygammas):
        """Method does comparisons of two 'gammas' files.
        """
        fw1 = open(myoutfile, 'r')
        fw2 = open(mygammas, 'r')
   
        # skip single metadata header line
        line1 = fw1.readline()
        line2 = fw2.readline()
        # compare rest of file
        for line1, line2 in itertools.izip_longest(fw1, fw2):
            self.assertEqual(line1, line2)

        fw1.close()
        fw2.close()

    def test_uni_seq(self):
        """Verify gammas file for uniform sampling with sequential bins"""
        self.meshfile = meshfile_g
        self.sm = ScdMesh.fromFile(self.meshfile)
        write_gammas.gen_gammas_file_from_h5m(self.sm, outfile, sampling='u')
        self.compare_gammas(outfile, gammas1)
    
    def test_uni_seq_bias(self):
        """Verify gammas file for uniform sampling with sequential bins and biasing"""
        self.meshfile = meshfile_g
        self.sm = ScdMesh.fromFile(self.meshfile)
        write_gammas.gen_gammas_file_from_h5m(self.sm, outfile, sampling='u', do_bias=True)
        self.compare_gammas(outfile, gammas2)

    def test_uni_cum(self):
        """Verify gammas file for uniform sampling with cumulative bins"""
        self.meshfile = meshfile_g
        self.sm = ScdMesh.fromFile(self.meshfile)
        write_gammas.gen_gammas_file_from_h5m(self.sm, outfile, sampling='u', cumulative=True)
        self.compare_gammas(outfile, gammas3)
    
    def test_uni_cum_bias(self):
        """Verify gammas file for uniform sampling with cumulative bins and biasing"""
        self.meshfile = meshfile_g
        self.sm = ScdMesh.fromFile(self.meshfile)
        write_gammas.gen_gammas_file_from_h5m(self.sm, outfile, sampling='u', do_bias=True, cumulative=True)
        self.compare_gammas(outfile, gammas4)
  
    def test_vox_seq(self):
        """Verify gammas file for voxel sampling with sequential bins"""
        self.meshfile = meshfile_g
        self.sm = ScdMesh.fromFile(self.meshfile)
        write_gammas.gen_gammas_file_from_h5m(self.sm, outfile)
        self.compare_gammas(outfile, gammas5)
    
    def test_vox_seq_bias(self):
        """Verify gammas file for voxel sampling with sequential bins and biasing"""
        self.meshfile = meshfile_g
        self.sm = ScdMesh.fromFile(self.meshfile)
        write_gammas.gen_gammas_file_from_h5m(self.sm, outfile, do_bias=True)
        self.compare_gammas(outfile, gammas6)

    def test_vox_cum(self):
        """Verify gammas file for voxel sampling with cumulative bins"""
        self.meshfile = meshfile_g
        self.sm = ScdMesh.fromFile(self.meshfile)
        write_gammas.gen_gammas_file_from_h5m(self.sm, outfile, cumulative=True)
        self.compare_gammas(outfile, gammas7)
    
    def test_vox_cum_bias(self):
        """Verify gammas file for voxel sampling with cumulative bins and biasing"""
        self.meshfile = meshfile_g
        self.sm = ScdMesh.fromFile(self.meshfile)
        write_gammas.gen_gammas_file_from_h5m(self.sm, outfile, do_bias=True, cumulative=True)
        self.compare_gammas(outfile, gammas8)
    
