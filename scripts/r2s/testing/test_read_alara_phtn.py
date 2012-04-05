from r2s.io import read_alara_phtn
import os
import unittest

#
# The methods in PhtnSrcToH5M.py are written to return 1 or 0.
#  0 corresponds with errors, and 1 is returned otherwise...
# We use 'self.assertEquals(method(), 1 or 0)' to do the testing.
#

# These directories are relative to scripts directory.
inputfile = "../testcases/simplebox-3/phtn_src"
meshfile_orig  = "../testcases/simplebox-3/matFracs.h5m"
meshfile  = "../testcases/simplebox-3/matFracs3.h5m"


class TestPhtn(unittest.TestCase):

    def setUp(self):
        os.system("cp " + meshfile_orig + " " + meshfile)

    def tearDown(self):
        pass
        os.system("rm " + meshfile)

    def test_simple(self):
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, meshfile), 1)

    def test_simple_with_totals(self):
        """Tag a mesh; tagging again should fail; then tagging again should
        succeed when we add the retag=True option"""
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, meshfile, totals=True), 1)

    def test_unobtanium(self):
        """Supplied isotope doesn't exist in file."""
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, meshfile, "unobtanium"), 0)

    def test_cooling_num_pass(self):
        """We send a numeric value for the cooling step. Should return 1"""
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, meshfile, coolingstep=3) , 1)

    def test_cooling_num_fail1(self):
        """We send an invalid numeric value for the cooling step. Should return 0"""
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, meshfile, coolingstep=53), 0)
    
    def test_cooling_num_fail2(self):
        """We send an invalid numeric value for the cooling step. Should return 0"""
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, meshfile, coolingstep=-3), 0)
    
    def test_cooling_string_pass(self):
        """We send a valid string value for the cooling step. Should return 1"""
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, meshfile, coolingstep="1 s"), 1)
    
    def test_cooling_string_fail(self):
        """We send an invalid string value for the cooling step.  String is not in 
        file and should return 0"""
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, meshfile, coolingstep="never"), 0)


class TestPhtnRetagging(unittest.TestCase):
    """Test methods in this class test what happens when phtn_src tags already
    exist. Retagging is enabled with the 'retag' option.  This also applies to
    the phtn_src_total tag via the 'totals' option.
    """

    def setUp(self):
        os.system("cp " + meshfile_orig + " " + meshfile)
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, meshfile), 1)

    def tearDown(self):
        os.system("rm " + meshfile)

    def test_retag_fail(self):
        """We try again to tag the same mesh. An error should be returned"""
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, meshfile), 0)

    def test_retag_totals_fail(self):
        """We try again to tag the same mesh. An error should be returned.
        This test should be redundant as totals should not be reached before 
        the method fails."""
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, meshfile, totals=True), 0)

    def test_retag_ok(self):
        """We try to tag the same mesh, but with the retag 
        parameter = True
        Should succeed fine."""
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, meshfile, retag=True), 1)

    def test_retag_totals_fail(self):
        """We try to tag the same mesh, and also include totals; 
        Should have no problems. should not be reached before """
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, meshfile, retag=True, totals=True), 1)


class TestPhtnTotalsRetagging(unittest.TestCase):
    """We tag a tagless mesh, including totals. Then check retagging behavior.
    """

    def setUp(self):
        os.system("cp " + meshfile_orig + " " + meshfile)
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, meshfile, totals=True), 1)

    def tearDown(self):
        os.system("rm " + meshfile)

    def test_retag_and_totals_ok(self):
        """We enable retagging and also make sure that the totals get retagged.
        """
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, meshfile, retag=True, totals=True), 1)



if __name__ == "__main__":
    unittest.main()
