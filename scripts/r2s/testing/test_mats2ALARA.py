from mats2ALARA import mats_to_alara
from nose.tools import assert_equal
import os

output = 'alara_matlib.txt'

if output in os.listdir('.'):
    os.remove(output)

mats_to_alara(input, output)

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
' water 1.00215818409 2\n'
'     h 1.1190E-01 1\n'
'     o 8.8810E-01 8\n')

assert_equal(written, expected)
os.remove(output)

# Run as script
#
if __name__ == "__main__":
    nose.main()
