from tools import magic
from nose.tools import assert_equal
import os

def test_block_1_2():
    flux_h5m = 'files_test_magic/block_1_2_test.h5m'
    expected_file = 'files_test_magic/block_1_2_test_expected_wwinp'
    output = 'block_1_2_wwinp'
    
    if output in os.listdir('.'):
        os.remove(output)
    
    magic.magic(flux_h5m, 'None', False, 0, output, 'None', 0.1)

    f=open(output)
    written = f.readlines()
    f.close

    g = open(expected_file)
    expected = g.readlines()
    g.close

    # exclude first line, it contain a date
    # everything else on the first line is the same for all wwinp files and is
    # therefore not particularly import to test.
    assert_equal(written[1:], expected[1:])
    os.remove(output)


def test_block_3():
    flux_h5m = 'files_test_magic/iteration_0.h5m'
    expected_file = 'files_test_magic/iteration_0.wwinp'
    output = 'iteration_0_wwinp'
    
    if output in os.listdir('.'):
        os.remove(output)
    
    magic.magic(flux_h5m, 'None', False, 0, output, 'None', 0.1)

    f=open(output)
    written = f.readlines()
    f.close

    g = open(expected_file)
    expected = g.readlines()
    g.close

    assert_equal(written[1:], expected[1:])
    os.remove(output)



def test_overwrite():
    flux_h5m = 'files_test_magic/iteration_1.h5m'
    ww_mesh = 'files_test_magic/iteration_0.wwmesh'
    expected_file = 'files_test_magic/iteration_1.wwinp'
    output = 'iteration_1_wwinp'
    
    if output in os.listdir('.'):
        os.remove(output)
    
    magic.magic(flux_h5m, ww_mesh, False, 0, output, 'None', 0.1)

    f=open(output)
    written = f.readlines()
    f.close

    g = open(expected_file)
    expected = g.readlines()
    g.close

    assert_equal(written[1:], expected[1:])
    os.remove(output)


def test_null():
    flux_h5m = 'files_test_magic/null_test.h5m'
    expected_file = 'files_test_magic/null_test.wwinp'
    output = 'null_wwinp'
    
    if output in os.listdir('.'):
        os.remove(output)
    
    magic.magic(flux_h5m, 'None', False, 33333, output, 'None', 0.1)

    f=open(output)
    written = f.readlines()
    f.close

    g = open(expected_file)
    expected = g.readlines()
    g.close

    assert_equal(written[1:], expected[1:])
    os.remove(output)

def single_group_test1():
    flux_h5m = 'files_test_magic/single_group_test1.h5m'
    expected_file = 'files_test_magic/single_group_test1.wwinp'
    output = 'single_group_test1'
    
    if output in os.listdir('.'):
        os.remove(output)
    
    magic.magic(flux_h5m, 'None', False, 0, output, 'None', 0.1)

    f=open(output)
    written = f.readlines()
    f.close

    g = open(expected_file)
    expected = g.readlines()
    g.close

    assert_equal(written[1:], expected[1:])
    os.remove(output)

def test_single_group_test2():
    flux_h5m = 'files_test_magic/single_group_test2.h5m'
    ww_mesh = 'files_test_magic/single_group_test1.wwmesh'
    expected_file = 'files_test_magic/single_group_test2.wwinp'
    output = 'single_group_test2'
    
    if output in os.listdir('.'):
        os.remove(output)
    
    magic.magic(flux_h5m, ww_mesh, False, 0, output, 'None', 0.1)

    f=open(output)
    written = f.readlines()
    f.close

    g = open(expected_file)
    expected = g.readlines()
    g.close

    assert_equal(written[1:], expected[1:])
    os.remove(output)


def test_block_3():
    flux_h5m = 'files_test_magic/iteration_0.h5m'
    expected_file = 'files_test_magic/totals_test.wwinp'
    output = 'totals_wwinp'
    
    if output in os.listdir('.'):
        os.remove(output)
    
    magic.magic(flux_h5m, 'None', True, 0, output, 'None', 0.1)

    f=open(output)
    written = f.readlines()
    f.close

    g = open(expected_file)
    expected = g.readlines()
    g.close

    assert_equal(written[1:], expected[1:])
    os.remove(output)

###############################################################
def test_tolerance():
    flux_h5m = 'files_test_magic/iteration_1.h5m'
    ww_mesh = 'files_test_magic/iteration_0.wwmesh'
    expected_file = 'files_test_magic/tolerance_test.wwinp'
    output = 'tolerance_test'
    
    if output in os.listdir('.'):
        os.remove(output)
    
    magic.magic(flux_h5m, ww_mesh, False, 0, output, 'None', 0.7)

    f=open(output)
    written = f.readlines()
    f.close

    g = open(expected_file)
    expected = g.readlines()
    g.close

    assert_equal(written[1:], expected[1:])
    #os.remove(output)


# Run as script
#
if __name__ == "__main__":
    test_block_1_2()
    test_block_3()
    test_overwrite()
