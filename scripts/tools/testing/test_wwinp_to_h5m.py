from tools import wwinp_to_h5m
from nose.tools import assert_equal
import os
from itaps import iMesh, iBase
from r2s.scdmesh import ScdMesh

def test_wwinp_to_h5m():
    thisdir = os.path.dirname(__file__)
    wwinp = os.path.join(thisdir, 'files_test_wwinp_to_h5m/wwinp_test.e')
    output = os.path.join(os.getcwd(), 'wwinp_mesh.h5m')
    
    if output in os.listdir('.'):
        os.remove(output)
    
    wwinp_to_h5m.cartesian(wwinp, output)
    
    with open(output) as f:
        written = f.read()
    
    expected_sm = ScdMesh.fromFile(os.path.join(thisdir, 'files_test_wwinp_to_h5m/expected_wwinp_mesh.h5m'))
    written_sm = ScdMesh.fromFile(output)
    
    for x in range(0,14):
        for y in range(0,8):
            for z in range(0,6):
                expected_voxel = expected_sm.getHex(x,y,z)
                expected = expected_sm.imesh.getTagHandle('ww_n_group_001')[expected_voxel]
                written_voxel = written_sm.getHex(x,y,z)
                written = written_sm.imesh.getTagHandle('ww_n_group_001')[written_voxel]
                assert_equal(written, expected)
    
    os.remove(output)


# Run as script
#
if __name__ == "__main__":
    test_wwinp_to_h5m()
