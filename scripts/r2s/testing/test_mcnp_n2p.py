import unittest
import os.path
import itertools
from itaps import iMesh

from r2s import mcnp_n2p
import scdmesh


# These directories are relative to scripts directory.
thisdir = os.path.dirname(__file__)
testfile = os.path.join(thisdir,"inp_n2p")
testfile_out = "testing/inp_n2p_p"
testfile_compare = os.path.join(thisdir,"inp_n2p_converted")
testfile_compare_ergs = os.path.join(thisdir,"inp_n2p_converted_ergs")
meshfile = os.path.join(thisdir,"n2p_grid543.h5m")


class TestRegularMCNP(unittest.TestCase):

    def setUp(self):
        self.obj = mcnp_n2p.ModMCNPforPhotons(testfile, dagmc=False)
        self.obj.read()
        self.obj.change_block_1()
        self.obj.change_block_2()
        self.obj.change_block_3()

    def tearDown(self):
        os.system("rm " + testfile_out)

    def test_run(self):
        """
        Tests successful run-through
        """
        
        self.assertEqual(self.obj.write_deck(testfile_out), 1)

    def test_consistent(self):
        """
        Tests that resulting file is identical to expected resulting file.
        """

        self.obj.write_deck(testfile_out)
        fw1 = open(testfile_out, 'r')
        fw2 = open(testfile_compare, 'r')
   
        for line1, line2 in itertools.izip_longest(fw1, fw2):
            self.assertEqual(line1, line2)

        fw1.close()
        fw2.close()

    def test_consistent_with_ergs(self):
        """
        Tests that resulting file is identical to expected resulting file.
        """

        smesh = scdmesh.ScdMesh.fromFile(iMesh.Mesh(), meshfile)
        self.obj.add_fmesh_from_scdmesh(smesh)

        self.obj.write_deck(testfile_out)
        fw1 = open(testfile_out, 'r')
        fw2 = open(testfile_compare_ergs, 'r')
   
        for line1, line2 in itertools.izip_longest(fw1, fw2):
            self.assertEqual(line1, line2)

        fw1.close()
        fw2.close()

