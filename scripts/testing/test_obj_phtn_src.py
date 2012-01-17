#import imp
from nose import with_setup
import magic_import as mi

#
# The method sin obj_phtn_src.py are written to return 1 or 0.
#  0 corresponds with errors, and 1 is returned otherwise...
# We use assert method() to do the testing.
#

# trickery for importing module from parent folder
obj_phtn_src = mi.__import__("obj_phtn_src", ["../"])

idea = 1 # placeholder that becomes a PhtnSrcReader object.

def test_phtnsrc_read(myfile="../../testcases/simplebox-3/phtn_src"):
    """ """
    global idea # .. so that next line creates a global object.
    idea = obj_phtn_src.PhtnSrcReader(myfile)
    assert idea.read_file()

@with_setup(test_phtnsrc_read)
def test_get_isotope():
    """ """
    assert idea.get_isotope()

def test_isotope_source_strengths():
    """ """
    assert idea.isotope_source_strengths()

@with_setup(test_phtnsrc_read)
def test_get_isotope_unobtanium():
    """test_get_isotope_unobtanium 
    Checks that non-extant isotopes cause method to fail gracefully.
    """
    assert not idea.get_isotope("unobtanium")

def test_phtn_src_read_nonextant_file(myfile="fake.file"):
    """test_phtn_src_read_nonextant_file
    Check that read_file() fails if object's input file doesn't exist.
    """
    idea = obj_phtn_src.PhtnSrcReader(myfile)
    assert not idea.read_file()

