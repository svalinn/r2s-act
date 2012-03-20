from nose import with_setup
import PhtnSrcToH5M
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

class TestPhtnTagging(unittest.TestCase):

    def setUp(self):
        os.system("rm " + meshfile)
        os.system("cp " + meshfile_orig + " " + meshfile)

    def test_tagging(self):
        """Tag a mesh; tagging again should fail; then tagging again should succeed
        when we add the retag=True option"""
    #def test_simple_pass(self):
        self.assertEqual(PhtnSrcToH5M.read_to_h5m(inputfile, meshfile), 1)

    #def test_simple_retag_fail(self):
        """We try again to tag the same mesh. An error should be returned"""
        self.assertEqual(PhtnSrcToH5M.read_to_h5m(inputfile, meshfile), 0)

    #def test_simple_retag_pass():
        """We try again to tag the same mesh, but with the retag parameter = True
        Should succeed fine."""
        self.assertEqual(PhtnSrcToH5M.read_to_h5m(inputfile, meshfile, retag=True), 1)


class TestPhtn(unittest.TestCase):

    def setUp(self):
        os.system("rm " + meshfile)
        os.system("cp " + meshfile_orig + " " + meshfile)

    def test_unobtanium(self):
        """Supplied isotope doesn't exist in file."""
        self.assertEqual(PhtnSrcToH5M.read_to_h5m(inputfile, meshfile, "unobtanium"), 0)

    def test_cooling_num_pass(self):
        """We send a numeric value for the cooling step. Should return 1"""
        self.assertEqual(PhtnSrcToH5M.read_to_h5m(inputfile, meshfile, coolingstep=3) , 1)

    def test_cooling_num_fail1(self):
        """We send an invalid numeric value for the cooling step. Should return 0"""
        self.assertEqual(PhtnSrcToH5M.read_to_h5m(inputfile, meshfile, coolingstep=53), 0)
    
    def test_cooling_num_fail2(self):
        """We send an invalid numeric value for the cooling step. Should return 0"""
        self.assertEqual(PhtnSrcToH5M.read_to_h5m(inputfile, meshfile, coolingstep=-3), 0)
    
    def test_cooling_string_pass(self):
        """We send a valid string value for the cooling step. Should return 1"""
        self.assertEqual(PhtnSrcToH5M.read_to_h5m(inputfile, meshfile, coolingstep="1 s"), 1)
    
    def test_cooling_string_fail(self):
        """We send an invalid string value for the cooling step.  String is not in 
        file and should return 0"""
        self.assertEqual(PhtnSrcToH5M.read_to_h5m(inputfile, meshfile, coolingstep="never"), 0)


os.system("rm " + meshfile)


if __name__ == "__main__":
    unittest.main()
