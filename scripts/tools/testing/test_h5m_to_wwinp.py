from tools import h5m_to_wwinp
from nose.tools import assert_equal
import os

def test_h5m_to_wwinp_3D_n():
    thisdir = os.path.dirname(__file__)
    input = os.path.join(thisdir, 'files_test_wwinp_to_h5m/expected_ww_mesh_3D_n.h5m')
    output = os.path.join(os.getcwd(), 'test.e')
    expected_output = os.path.join(thisdir, 'files_test_wwinp_to_h5m/3D_n.e')
    
    if output in os.listdir('.'):
        os.remove(output)
    
    h5m_to_wwinp.write_wwinp(input, output)
    
    with open(output) as f:
        written = f.readlines()

    with open(expected_output) as f:
        expected = f.readlines()

    # check to make sure the first line is the same except for the date
    assert_equal(written[0].split()[:-2], expected[0].split()[:-2])

    # check to make sure files are the same length
    assert_equal(len(written), len(expected))

    # check to make sure the rest of the lines have the same values
    # since the number formats are different, float comparisons are used
    for i in range(1, len(expected)):
        for j in range(0, len(expected[i].split())):
            assert_equal(float(written[i].split()[j]), float(expected[i].split()[j]))

    os.remove(output)


def test_h5m_to_wwinp_1D_p():
    thisdir = os.path.dirname(__file__)
    input = os.path.join(thisdir, 'files_test_wwinp_to_h5m/expected_ww_mesh_1D_p.h5m')
    output = os.path.join(os.getcwd(), 'test.e')
    expected_output = os.path.join(thisdir, 'files_test_wwinp_to_h5m/1D_p.e')
    
    if output in os.listdir('.'):
        os.remove(output)
    
    h5m_to_wwinp.write_wwinp(input, output)
    
    with open(output) as f:
        written = f.readlines()

    with open(expected_output) as f:
        expected = f.readlines()

    # check to make sure the first line is the same except for the date
    assert_equal(written[0].split()[:-2], expected[0].split()[:-2])

    # check to make sure files are the same length
    assert_equal(len(written), len(expected))

    # check to make sure the rest of the lines have the same values
    # since the number formats are different, float comparisons are used
    for i in range(1, len(expected)):
        for j in range(0, len(expected[i].split())):
            assert_equal(float(written[i].split()[j]), float(expected[i].split()[j]))

    os.remove(output)


# Run as script
#
if __name__ == "__main__":
    test_h5m_to_wwinp_3D_n()
    test_h5m_to_wwinp_1D_p()
