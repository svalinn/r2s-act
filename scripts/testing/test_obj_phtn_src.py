#import imp
import magic_import as mi

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

