import unittest
import os.path
import itertools
from itaps import iMesh

from r2s import mcnp_n2p
import scdmesh


# These directories are relative to scripts directory.
thisdir = os.path.dirname(__file__)
testfile = os.path.join(thisdir, "files_test_mcnp_n2p/inp_n2p")
testfile_out = os.path.join(thisdir, "files_test_mcnp_n2p/inp_n2p_p")
testfile_compare = os.path.join(thisdir, "files_test_mcnp_n2p/inp_n2p_converted")
testfile_compare_ergs = os.path.join(thisdir, "files_test_mcnp_n2p/inp_n2p_converted_ergs")
meshfile = os.path.join(thisdir, "files_test_mcnp_n2p/n2p_grid543.h5m")


class TestRegularMCNP(unittest.TestCase):

    def setUp(self):
        self.obj = mcnp_n2p.ModMCNPforPhotons(testfile, dagmc=False)
        self.obj.read()
        #self.obj.change_block_1()
        #self.obj.change_block_2()
        #self.obj.change_block_3()
        self.obj.convert()

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


dag_testfile = os.path.join(thisdir, "files_test_mcnp_n2p/inp_dag_n2p")
dag_testfile_out = os.path.join(thisdir, "files_test_mcnp_n2p/inp_dag_n2p_p")
dag_testfile_compare = os.path.join(thisdir, "files_test_mcnp_n2p/inp_dag_n2p_converted")
dag_testfile_compare_ergs = os.path.join(thisdir, "files_test_mcnp_n2p/inp_dag_n2p_converted_ergs")
meshfile = os.path.join(thisdir, "files_test_mcnp_n2p/n2p_grid543.h5m")

class TestDAGMCNP(unittest.TestCase):

    def setUp(self):
        self.obj = mcnp_n2p.ModMCNPforPhotons(dag_testfile, dagmc=True)
        self.obj.read()
        # change only block 3
        self.obj.convert()

    def tearDown(self):
        os.system("rm " + dag_testfile_out)

    def test_run(self):
        """Tests successful run-through using return value
        """
        
        self.assertEqual(self.obj.write_deck(dag_testfile_out), 1)

    def test_consistent(self):
        """Tests that resulting file is identical to expected resulting file.
        """

        self.obj.write_deck(dag_testfile_out)
        fw1 = open(dag_testfile_out, 'r')
        fw2 = open(dag_testfile_compare, 'r')
   
        for line1, line2 in itertools.izip_longest(fw1, fw2):
            self.assertEqual(line1, line2)

        fw1.close()
        fw2.close()
 
    def test_consistent_with_ergs(self):
        """Tests that resulting file has expected fmesh card added
        """

        smesh = scdmesh.ScdMesh.fromFile(meshfile)
        self.obj.add_fmesh_from_scdmesh(smesh)

        self.obj.write_deck(dag_testfile_out)
        fw1 = open(dag_testfile_out, 'r')
        fw2 = open(dag_testfile_compare_ergs, 'r')
   
        for line1, line2 in itertools.izip_longest(fw1, fw2):
            self.assertEqual(line1, line2)

        fw1.close()
        fw2.close()


auto_testfile_out = os.path.join(thisdir, "files_test_mcnp_n2p/inp_auto_dag_n2p_p")

class TestAutoDetermineInputType(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        if os.path.isfile(auto_testfile_out):
            os.system("rm " + auto_testfile_out)

    def test_mcnp_input_run(self):
        self.obj = mcnp_n2p.ModMCNPforPhotons(testfile)
        self.obj.read()
        self.obj.convert()

    def test_dag_input_run(self):
        self.obj = mcnp_n2p.ModMCNPforPhotons(dag_testfile)
        self.obj.read()
        self.obj.convert()

    def test_mcnp_consistent(self):
        """Tests that resulting file is identical to expected resulting file.
        """

        self.obj = mcnp_n2p.ModMCNPforPhotons(testfile)
        self.obj.read()
        self.obj.convert()
        self.obj.write_deck(auto_testfile_out)
        fw1 = open(auto_testfile_out, 'r')
        fw2 = open(testfile_compare, 'r')
   
        for line1, line2 in itertools.izip_longest(fw1, fw2):
            self.assertEqual(line1, line2)

        fw1.close()
        fw2.close()


    def test_dag_consistent(self):
        """Tests that resulting file is identical to expected resulting file.
        """

        self.obj = mcnp_n2p.ModMCNPforPhotons(dag_testfile)
        self.obj.read()
        self.obj.convert()
        self.obj.write_deck(auto_testfile_out)
        fw1 = open(auto_testfile_out, 'r')
        fw2 = open(dag_testfile_compare, 'r')
   
        for line1, line2 in itertools.izip_longest(fw1, fw2):
            self.assertEqual(line1, line2)

        fw1.close()
        fw2.close()
 
