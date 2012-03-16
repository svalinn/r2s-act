from nose import with_setup
import PhtnSrcToH5M
import os

#
# The methods in PhtnSrcToH5M.py are written to return 1 or 0.
#  0 corresponds with errors, and 1 is returned otherwise...
# We use 'assert method()' to do the testing.
#

# These directories are relative to scripts directory.
inputfile = "../testcases/simplebox-3/phtn_src"
meshfile_orig  = "../testcases/simplebox-3/matFracs.h5m"
meshfile  = "../testcases/simplebox-3/matFracs3.h5m"

def setup_h5m():
    os.system("rm " + meshfile)
    os.system("cp " + meshfile_orig + " " + meshfile)

@with_setup(setup_h5m)
def test_simple_pass():
    assert PhtnSrcToH5M.read_to_h5m(inputfile, meshfile) == 1

def test_simple_retag_fail():
    """We try again to tag the same mesh. An error should be returned"""
    assert PhtnSrcToH5M.read_to_h5m(inputfile, meshfile) == 0

def test_simple_retag_pass():
    """We try again to tag the same mesh, but with the retag parameter = True
    Should succeed fine."""
    assert PhtnSrcToH5M.read_to_h5m(inputfile, meshfile, retag=True) == 1

@with_setup(setup_h5m)
def test_unobtanium():
    """Supplied isotope doesn't exist in file."""
    assert PhtnSrcToH5M.read_to_h5m(inputfile, meshfile, "unobtanium") == 0

@with_setup(setup_h5m)
def test_cooling_num_pass():
    """We send a numeric value for the cooling step. Should return 1"""
    assert PhtnSrcToH5M.read_to_h5m(inputfile, meshfile, coolingstep=3) == 1

@with_setup(setup_h5m)
def test_cooling_num_fail1():
    """We send an invalid numeric value for the cooling step. Should return 0"""
    assert PhtnSrcToH5M.read_to_h5m(inputfile, meshfile, coolingstep=53) == 0

@with_setup(setup_h5m)
def test_cooling_num_fail2():
    """We send an invalid numeric value for the cooling step. Should return 0"""
    assert PhtnSrcToH5M.read_to_h5m(inputfile, meshfile, coolingstep=-3) == 0

@with_setup(setup_h5m)
def test_cooling_string_pass():
    """We send a valid string value for the cooling step. Should return 1"""
    assert PhtnSrcToH5M.read_to_h5m(inputfile, meshfile, coolingstep="1 s") == 1

@with_setup(setup_h5m)
def test_cooling_string_fail():
    """We send an invalid string value for the cooling step.  String is not in 
    file and should return 0"""
    assert PhtnSrcToH5M.read_to_h5m(inputfile, meshfile, coolingstep="never") == 0


os.system("rm " + meshfile)

