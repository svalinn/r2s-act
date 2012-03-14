from nose import with_setup
import unittest
import obj_phtn_src

#
# The methods in obj_phtn_src.py are written to return 1 or 0.
#  0 corresponds with errors, and 1 is returned otherwise...
# We use 'assert method()' to do the testing.
#

my_obj = 1 # placeholder that becomes a PhtnSrcReader object.

def test_phtnsrc_read(myfile="../testcases/simplebox-3/phtn_src"):
    """ """
    global my_obj # .. so that next line creates a global object.
    my_obj = obj_phtn_src.PhtnSrcReader(myfile)
    assert my_obj.read_file()

@with_setup(test_phtnsrc_read)
def test_get_isotope():
    """ """
    assert my_obj.get_isotope()

def test_isotope_source_strengths():
    """ """
    assert my_obj.isotope_source_strengths()

@with_setup(test_phtnsrc_read)
def test_get_isotope_unobtanium():
    """test_get_isotope_unobtanium 
    Checks that non-extant isotopes cause method to fail gracefully.
    """
    assert not my_obj.get_isotope("unobtanium")

def test_phtn_src_read_nonextant_file(myfile="fake.file"):
    """test_phtn_src_read_nonextant_file
    Check that read_file() fails if object's input file doesn't exist.
    """
    my_obj = obj_phtn_src.PhtnSrcReader(myfile)
    assert not my_obj.read_file()

@with_setup(test_phtnsrc_read)
def test_calc_volumes_list_1():
    """
    Checks that calc_volumes_list works for 3x3x3 mesh with equal voxel sizing.
    """
    my_obj.calc_volumes_list([[0,1,2,3],[0,1,2,3],[0,1,2,3]])
    assert my_obj.vol == [1] * (3*3*3)

@with_setup(test_phtnsrc_read)
def test_calc_volumes_list_2():
    """
    Checks that calc_volumes_list works for 3x3x3 mesh with equal voxel sizing.
    Also includes some negative mesh intervals, with mixed integers/floats.
    """
    my_obj.calc_volumes_list([[-2,-1.0,0,1.0],[-2,-1,0,1],[0.0,1.0,2.0,3.0]])
    assert my_obj.vol == [1] * (3*3*3)

#class test_obj(unittest.TestCase):
#    def setUp(self)
#        pass
#
#    def test_read_phtn_tag(self):
#        self.assertEqual(1,self.obj.gen_gammas([[],[],[]], "gammastest"))


