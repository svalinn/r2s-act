import unittest
from r2s import mcnp_n2p
import os.path
import itertools

# These directories are relative to scripts directory.
testfile = "testing/inp_ModMCNPforPhotons"
testfile_out = "testing/inp_ModMCNPforPhotons_p"
testfile_compare = "testing/inp_ModMCNPforPhotons_converted"


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
        """

        self.obj.write_deck(testfile_out)
        fw1 = open(testfile_out, 'r')
        fw2 = open(testfile_compare, 'r')
   
        for line1, line2 in itertools.izip_longest(fw1, fw2):
            self.assertEqual(line1, line2)

        fw1.close()
        fw2.close()

