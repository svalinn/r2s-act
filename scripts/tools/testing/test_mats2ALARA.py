from tools import mats2ALARA
from nose.tools import assert_equal
import os

def test_mats2ALARA():
    inp = 'mats2ALARA_test_inp.txt'
    output = 'alara_matlib.txt'
    
    if output in os.listdir('.'):
        os.remove(output)
    
    mats2ALARA.mats_to_alara(inp, output)
    
    with open(output) as f:
        written = f.read()

    expected =(
    '# mat number: 1\n'
    '# source:  Some http//URL.com\n'
    '# comments:  first line of comments second comments third line of comments fort\n'
    '# h line of comments\n'
    ' leu 19.1 2\n'
    '     u:235 4.0000E-02 92\n'
    '     u:238 9.6000E-01 92\n'
    '# mat number: 2\n'
    '# source:  internet\n'
    '# comments:  Here are comments the comments continue here are more even more\n'
    ' water 0.9 2\n'
    '     h 1.1190E-01 1\n'
    '     o 8.8810E-01 8\n'
    '# mat number: 2\n'
    '# source:  internet\n'
    '# comments:  Here are comments the comments continue here are more even more\n'
    ' water 1.00215363272 2\n'
    '     h 1.1190E-01 1\n'
    '     o 8.8810E-01 8\n'
    'pseudo_void 0 1\n'
    'he 1 2'
    )

    assert_equal(written, expected)
    os.remove(output)

# Run as script
#
if __name__ == "__main__":
    test_mats2ALARA()
