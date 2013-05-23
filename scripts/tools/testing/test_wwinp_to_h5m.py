from tools import wwinp_to_h5m
from nose.tools import assert_equal
import os
from itaps import iMesh, iBase
from r2s.scdmesh import ScdMesh

def test_wwinp_to_h5m_3D_n():
    thisdir = os.path.dirname(__file__)
    wwinp = os.path.join(thisdir, 'files_test_wwinp_to_h5m/3D_n.e')
    expected_file = os.path.join(thisdir, 'files_test_wwinp_to_h5m/expected_ww_mesh_3D_n.h5m')

    written_sm = wwinp_to_h5m.cartesian(wwinp)
    expected_sm = ScdMesh.fromFile(expected_file)
    
    #verify weight window lower bounds are the same
    for x in range(0,14):
        for y in range(0,8):
            for z in range(0,6):
                for e_group in range(1, 8):
                    expected_voxel = expected_sm.getHex(x,y,z)
                    expected = expected_sm.imesh.getTagHandle('ww_n_group_00{0}'.format(e_group))[expected_voxel]
                    written_voxel = written_sm.getHex(x,y,z)
                    written = written_sm.imesh.getTagHandle('ww_n_group_00{0}'.format(e_group))[written_voxel]
                    assert_equal(written, expected)

    #verify correct particle identifier
    assert_equal(written_sm.imesh.getTagHandle('particle')[written_sm.imesh.rootSet], 1)

    #verify correct energy upper bounds
    expected_E = [1E-9, 1E-8, 1E-7, 1E-6, 1E-5, 1E-4, 1E-3]
    written_E = written_sm.imesh.getTagHandle('E_upper_bounds')[written_sm.imesh.rootSet]
    
    for i in range(0, len(expected_E)):
        assert_equal(written_E[i], expected_E[i])


def test_wwinp_to_h5m_1D_p():
    thisdir = os.path.dirname(__file__)
    wwinp = os.path.join(thisdir, 'files_test_wwinp_to_h5m/1D_p.e')
    expected_file = os.path.join(thisdir, 'files_test_wwinp_to_h5m/expected_ww_mesh_1D_p.h5m')

    written_sm = wwinp_to_h5m.cartesian(wwinp)
    expected_sm = ScdMesh.fromFile(expected_file)
 
    #verify weight window lower bounds are the same
    for x in range(0,1):
        for y in range(0,1):
            for z in range(0,9):
                expected_voxel = expected_sm.getHex(x,y,z)
                expected = expected_sm.imesh.getTagHandle('ww_n_group_001')[expected_voxel]
                written_voxel = written_sm.getHex(x,y,z)
                written = written_sm.imesh.getTagHandle('ww_n_group_001')[written_voxel]
                assert_equal(written, expected)

    #verify correct particle identifier
    assert_equal(written_sm.imesh.getTagHandle('particle')[written_sm.imesh.rootSet], 1)

    #verify correct energy upper bounds
    expected_E = 100
    written_E = written_sm.imesh.getTagHandle('E_upper_bounds')[written_sm.imesh.rootSet]

    assert_equal(written_E, expected_E)


# Run as script
#
if __name__ == "__main__":
    test_wwinp_to_h5m_3D_n()
    test_wwinp_to_h5m_1D_p()
