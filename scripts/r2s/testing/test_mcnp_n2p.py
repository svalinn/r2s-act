import unittest
import os.path
import itertools
from itaps import iMesh

from r2s import mcnp_n2p
import scdmesh


# These directories are relative to scripts directory.
thisdir = os.path.dirname(__file__)
testfile = os.path.join(thisdir,"files_test_mcnp_n2p/inp_n2p")
testfile_out = "files_test_mcnp_n2p/inp_n2p_p"
testfile_compare = os.path.join(thisdir,"files_test_mcnp_n2p/inp_n2p_converted")
testfile_compare_ergs = os.path.join(thisdir,"files_test_mcnp_n2p/inp_n2p_converted_ergs")
meshfile = os.path.join(thisdir,"n2p_grid543.h5m")

dagtestfile = os.path.join(thisdir,"files_test_mcnp_n2p/inp_dag_n2p")
dagtestfile_out = "files_test_mcnp_n2p/inp_dag_n2p_p"
dagtestfile_compare = os.path.join(thisdir,"files_test_mcnp_n2p/inp_dag_n2p_converted")
dagtestfile_compare_ergs = os.path.join(thisdir,"files_test_mcnp_n2p/inp_dag_n2p_converted_ergs")
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
        """Tests successful run-through using return value
        """
        
        self.assertEqual(self.obj.write_deck(testfile_out), 1)

    def test_consistent(self):
        """Tests that resulting file is identical to expected resulting file.
        """

        self.obj.write_deck(testfile_out)
        fw1 = open(testfile_out, 'r')
        fw2 = open(testfile_compare, 'r')
   
        for line1, line2 in itertools.izip_longest(fw1, fw2):
            self.assertEqual(line1, line2)

        fw1.close()
        fw2.close()

    def test_consistent_with_ergs(self):
        """Tests that resulting file has expected fmesh card added
        """

        smesh = scdmesh.ScdMesh.fromFile(meshfile)
        self.obj.add_fmesh_from_scdmesh(smesh)

        self.obj.write_deck(testfile_out)
        fw1 = open(testfile_out, 'r')
        fw2 = open(testfile_compare_ergs, 'r')
   
        for line1, line2 in itertools.izip_longest(fw1, fw2):
            self.assertEqual(line1, line2)

        fw1.close()
        fw2.close()


class TestDAGMCNP(unittest.TestCase):

    def setUp(self):
        self.obj = mcnp_n2p.ModMCNPforPhotons(dagtestfile, dagmc=True)
        self.obj.read()
        # change only block 3
        self.obj.change_block_3()

    def tearDown(self):
        os.system("rm " + dagtestfile_out)

    def test_run(self):
        """Tests successful run-through using return value
        """
        
        self.assertEqual(self.obj.write_deck(dagtestfile_out), 1)

    def test_consistent(self):
        """Tests that resulting file is identical to expected resulting file.
        """

        self.obj.write_deck(dagtestfile_out)
        fw1 = open(dagtestfile_out, 'r')
        fw2 = open(dagtestfile_compare, 'r')
   
        for line1, line2 in itertools.izip_longest(fw1, fw2):
            self.assertEqual(line1, line2)

        fw1.close()
        fw2.close()
 
    def test_consistent_with_ergs(self):
        """Tests that resulting file has expected fmesh card added
        """

        smesh = scdmesh.ScdMesh.fromFile(meshfile)
        self.obj.add_fmesh_from_scdmesh(smesh)

        self.obj.write_deck(dagtestfile_out)
        fw1 = open(dagtestfile_out, 'r')
        fw2 = open(dagtestfile_compare_ergs, 'r')
   
        for line1, line2 in itertools.izip_longest(fw1, fw2):
            self.assertEqual(line1, line2)

        fw1.close()
        fw2.close()

