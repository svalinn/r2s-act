from r2s.data_transfer import read_alara_phtn
from r2s.scdmesh import ScdMesh, ScdMeshError
import os
import os.path
import unittest
from itaps import iMesh,iBase,iMeshExtensions


#
# The methods in read_alara_phtn.py are written to return 1 or 0.
#  0 corresponds with errors, and 1 is returned otherwise...
# We use 'self.assertEquals(method(), 1 or 0)' to do the testing.
#

# These directories are relative to scripts directory.
thisdir = os.path.dirname(__file__)
inputfile = os.path.join(thisdir, "sb3_phtn_src")
meshfile_orig  = os.path.join(thisdir, "h5m_files/sb3_matFracs.h5m")
meshfile  = os.path.join(thisdir, "h5m_files/sb3_matFracs3.h5m")


class TestPhtn(unittest.TestCase):

    def setUp(self):
        os.system("cp " + meshfile_orig + " " + meshfile)
        self.sm = ScdMesh.fromFile(meshfile)

    def tearDown(self):
        os.system("rm " + meshfile)

    def test_simple(self):
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, self.sm), 1)

    def test_simple_with_totals(self):
        """Tag a mesh; tagging again should fail; then tagging again should
        succeed when we add the retag=True option"""
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, self.sm, totals=True), 1)

    def test_unobtanium(self):
        """Supplied isotope doesn't exist in file."""
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, self.sm, "unobtanium"), 0)

    def test_cooling_num_pass(self):
        """We send a numeric value for the cooling step. Should return 1"""
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, self.sm, coolingstep=3) , 1)

    def test_cooling_num_fail1(self):
        """We send an invalid numeric value for the cooling step. Should return 0"""
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, self.sm, coolingstep=53), 0)
    
    def test_cooling_num_fail2(self):
        """We send an invalid numeric value for the cooling step. Should return 0"""
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, self.sm, coolingstep=-3), 0)
    
    def test_cooling_string_pass(self):
        """We send a valid string value for the cooling step. Should return 1"""
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, self.sm, coolingstep="1 s"), 1)
    
    def test_cooling_string_fail(self):
        """We send an invalid string value for the cooling step.  String is not in 
        file and should return 0"""
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, self.sm, coolingstep="never"), 0)


class TestPhtnRetagging(unittest.TestCase):
    """Test methods in this class test what happens when phtn_src tags already
    exist. Retagging is enabled with the 'retag' option.  This also applies to
    the phtn_src_total tag via the 'totals' option.
    """

    def setUp(self):
        os.system("cp " + meshfile_orig + " " + meshfile)
        self.sm = ScdMesh.fromFile(meshfile)
        read_alara_phtn.read_to_h5m(inputfile, self.sm)

    def tearDown(self):
        os.system("rm " + meshfile)

    def test_retag_fail(self):
        """We try again to tag the same mesh. An error should be returned"""
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, self.sm), 0)

    def test_retag_totals_fail(self):
        """We try again to tag the same mesh. An error should be returned.
        This test should be redundant as totals should not be reached before 
        the method fails."""
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, self.sm, totals=True), 0)

    def test_retag_ok(self):
        """We try to tag the same mesh, but with the retag 
        parameter = True
        Should succeed fine."""
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, self.sm, retag=True), 1)

    def test_retag_totals_fail(self):
        """We try to tag the same mesh, and also include totals; 
        Should have no problems. should not be reached before """
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, self.sm, retag=True, totals=True), 1)


class TestPhtnTotalsRetagging(unittest.TestCase):
    """We tag a tagless mesh, including totals. Then check retagging behavior.
    """

    def setUp(self):
        os.system("cp " + meshfile_orig + " " + meshfile)
        self.sm = ScdMesh.fromFile(meshfile)
        read_alara_phtn.read_to_h5m(inputfile, self.sm, totals=True)

    def tearDown(self):
        os.system("rm " + meshfile)

    def test_retag_and_totals_ok(self):
        """We enable retagging and also make sure that the totals get retagged.
        """
        self.assertEqual(read_alara_phtn.read_to_h5m(inputfile, self.sm, retag=True, totals=True), 1)


class TestGetCoolingStepName(unittest.TestCase):
    """We test the get_cooling_step_name() method with direct calls
    """

    def setUp(self):
        # Create the file reader to pass to methond being tested
        self.fr = open(inputfile, 'r')
        
    def tearDown(self):
        self.fr.close()
        
    def test_get_cooling_step_name1(self):
        """Verify passing 0 as cooling step
        """
        (coolingstep, numergbins) = read_alara_phtn.get_cooling_step_name( \
                0, self.fr)
        self.assertEqual(coolingstep, 'shutdown')
        self.assertEqual(numergbins, 42)

    def test_get_cooling_step_name2(self):
        """Verify passing a string (regardless if it exists) as cooling step
        """
        self.assertRaises(ValueError, read_alara_phtn.get_cooling_step_name, \
                'never', self.fr)

    def test_get_cooling_step_name3(self):
        """Verify passing non-zero cooling step
        """
        (coolingstep, numergbins) = read_alara_phtn.get_cooling_step_name( \
                5, self.fr)
        self.assertEqual(coolingstep, '1 y')
        self.assertEqual(numergbins, 42)

    def test_get_cooling_step_name4(self):
        """Verify passing a cooling step value > # of cooling steps in phtn_src
        """
        self.assertRaises(Exception, read_alara_phtn.get_cooling_step_name, \
                15, self.fr)

    def test_get_cooling_step_name5(self):
        """Verify passing a negative cooling step value
        """
        self.assertRaises(Exception, read_alara_phtn.get_cooling_step_name, \
                -1, self.fr)


if __name__ == "__main__":
    unittest.main()
