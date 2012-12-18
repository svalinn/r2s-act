import unittest
import os.path
import itertools
import StringIO

from r2s import tag_ebins as te
from r2s.scdmesh import ScdMesh, ScdMeshError
from itaps import iMesh, iBase


thisdir = os.path.dirname(__file__)
meshfile = os.path.join(thisdir, "h5m_files/sb3_matFracs.h5m")


class TestEbins(unittest.TestCase):
    """Class methods test read_and_tag_phtn_ergs()"""

    def setUp(self):
        self.sm = ScdMesh.fromFile(meshfile)

    def tearDown(self):
        pass

    def testTagClean(self):
        """Test an acceptable set of energy bin values"""
        ergs = StringIO.StringIO('1\n2\n3\n4')
        self.assertEqual(1,te.read_and_tag_phtn_ergs(ergs, self.sm))

    def testTagAddedAndReadable(self):
        """Test that we can access the tag and read back contents"""
        ergs = StringIO.StringIO('1\n2\n3\n4.1')
        te.read_and_tag_phtn_ergs(ergs, self.sm)
        tag = self.sm.imesh.getTagHandle("PHTN_ERGS")

        for val1, val2 in itertools.izip_longest( \
                [1., 2., 3., 4.1], tag[self.sm.scdset]):
            self.assertEqual(val1, val2)

    def testRepeatedErg(self):
        """Test a set of energy bin values where one bin is repeated"""
        ergs = StringIO.StringIO('1\n1\n3\n4')
        self.assertEqual(0,te.read_and_tag_phtn_ergs(ergs, self.sm))

    def testDecreasingErg(self):
        """Test a set of energy bin values where energies decrease."""
        ergs = StringIO.StringIO('2\n1\n3\n4')
        self.assertEqual(0,te.read_and_tag_phtn_ergs(ergs, self.sm))
