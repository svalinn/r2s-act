from tools import magic
from nose.tools import assert_equal
import os
from itaps import iMesh, iBase
from r2s.scdmesh import ScdMesh

def test_magic_2_group():
    thisdir = os.path.dirname(__file__)
    flux_sm_filename = os.path.join(thisdir, 'files_test_magic/iteration_0_flux_2_group.h5m')
    flux_sm = ScdMesh.fromFile(flux_sm_filename)
    expected_sm_filename = os.path.join(thisdir, 'files_test_magic/iteration_0_magic_2_group.h5m')   
    expected_sm = ScdMesh.fromFile(expected_sm_filename)    

    totals_bool = False
    null_value = 1E-3
    tolerance = 0.2

    written_sm = magic.magic(flux_sm, totals_bool, null_value, tolerance)
    
    #verify weight window lower bounds are the same
    for x in range(0,3):
        for y in range(0,3):
            for z in range(0,3):
                for e_group in range(1, 3):
                    expected_voxel = expected_sm.getHex(x,y,z)
                    expected = expected_sm.imesh.getTagHandle('ww_n_group_00{0}'.format(e_group))[expected_voxel]
                    written_voxel = written_sm.getHex(x,y,z)
                    written = written_sm.imesh.getTagHandle('ww_n_group_00{0}'.format(e_group))[written_voxel]
                    assert_equal(written, expected)

def test_magic_total_group():
    thisdir = os.path.dirname(__file__)
    flux_sm_filename = os.path.join(thisdir, 'files_test_magic/iteration_0_flux_2_group.h5m')
    flux_sm = ScdMesh.fromFile(flux_sm_filename)
    expected_sm_filename = os.path.join(thisdir, 'files_test_magic/iteration_0_magic_total_group.h5m')   
    expected_sm = ScdMesh.fromFile(expected_sm_filename)    

    totals_bool = True
    null_value = 1E-3
    tolerance = 0.2

    written_sm = magic.magic(flux_sm, totals_bool, null_value, tolerance)
    
    #verify weight window lower bounds are the same
    for x in range(0,3):
        for y in range(0,3):
            for z in range(0,3):
                expected_voxel = expected_sm.getHex(x,y,z)
                expected = expected_sm.imesh.getTagHandle('ww_n_group_total')[expected_voxel]
                written_voxel = written_sm.getHex(x,y,z)
                written = written_sm.imesh.getTagHandle('ww_n_group_total')[written_voxel]
                assert_equal(written, expected)


def test_magic_1_group():
    thisdir = os.path.dirname(__file__)
    flux_sm_filename = os.path.join(thisdir, 'files_test_magic/iteration_0_flux_1_group.h5m')
    flux_sm = ScdMesh.fromFile(flux_sm_filename)
    expected_sm_filename = os.path.join(thisdir, 'files_test_magic/iteration_0_magic_1_group.h5m')   
    expected_sm = ScdMesh.fromFile(expected_sm_filename)    

    totals_bool = False
    null_value = 1E-3
    tolerance = 0.2

    written_sm = magic.magic(flux_sm, totals_bool, null_value, tolerance)
    
    #verify weight window lower bounds are the same
    for x in range(0,3):
        for y in range(0,3):
            for z in range(0,3):
                expected_voxel = expected_sm.getHex(x,y,z)
                expected = expected_sm.imesh.getTagHandle('ww_n_group_001')[expected_voxel]
                written_voxel = written_sm.getHex(x,y,z)
                written = written_sm.imesh.getTagHandle('ww_n_group_001')[written_voxel]
                assert_equal(written, expected)

# Run as script
#
if __name__ == "__main__":
    test_magic_2_group()
    test_magic_total_group()
    test_magic_1_group()
