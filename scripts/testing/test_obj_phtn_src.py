#import imp
import magic_import as mi

# The method sin obj_phtn_src.py are written to return 1 or 0.
#  0 corresponds with errors, and 1 is returned otherwise...
# We use assert method() to do the testing.

obj_phtn_src = mi.__import__("obj_phtn_src", ["../"])

idea = 1

def test_phtnsrc_to_sdef():
    global idea
    idea = obj_phtn_src.PhtnSrcReader("../../testcases/simplebox-3/phtn_src")
    assert idea.read()

def test_get_isotope():
    assert idea.get_isotope()

def test_isotope_source_strengths():
    assert idea.isotope_source_strengths()

