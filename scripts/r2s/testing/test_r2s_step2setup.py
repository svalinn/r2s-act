import unittest
import sys
import os
import os.path
from tempfile import NamedTemporaryFile as NTF
from tempfile import mkdtemp
from shutil import rmtree
import contextlib

import r2s_step2setup as s2s
from r2s_step2setup import R2S_CFG_Error


class TestLoadConfigs(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_load_configs(self):
        """Simulate a .cfg file and check that everything is read correctly.
        """
        with NTF() as myNTF:
            # Create placeholder for r2s.cfg file
            myNTF.write("[r2s-files]\n" \
                    "neutron_mcnp_input = mcnp_n\n" \
                    "photon_mcnp_input = mcnp_p\n" \
                    "step1_datafile = mesh.h5m\n" \
                    "alara_phtn_src = phtn_src\n" \
                    "[r2s-params]\n" \
                    "photon_isotope = u235\n" \
                    "photon_cooling = shutdown\n" \
                    )
            myNTF.seek(0) # Goes to beginning

            mcnp_n, mcnp_p, datafile, phtn_src, iso, cool = \
                    s2s.load_configs(myNTF.name)

            # Check for correctness
            self.assertEqual(mcnp_n, 'mcnp_n')
            self.assertEqual(mcnp_p, 'mcnp_p')
            self.assertEqual(datafile, 'mesh.h5m')
            self.assertEqual(phtn_src, 'phtn_src')
            self.assertEqual(iso, 'u235')
            self.assertEqual(cool, 'shutdown')


class TestGenIsoCoolLists(unittest.TestCase):

    def setUp(self):
        self.NTFcontents = ("a\tshutdown\n" \
                    "a\t1_d\n" \
                    "a\t2 w\n" \
                    "a\t99 y\n" \
                    "a\twhoops\n" \
                    "a\ttoo far\n" \
                    "b\t1_d\n"
                    )
    
    def tearDown(self):
        pass

    def test_gen_iso_cool_lists1(self):
        """Test parsing of non-numeric entries in isotopes and cooling input.
        Varied spacing is intentional.
        """
        isolistraw = "a, b, c,d"
        coollistraw = "1,2,   3, 4"#"x, y,z,1 z"
        
        # Create placeholder for phtn_src file
        with NTF() as myNTF: 
            myNTF.write(self.NTFcontents)
            myNTF.seek(0) # Goes to beginning
            isolist, coollist = s2s.gen_iso_cool_lists(isolistraw, \
                coollistraw, myNTF.name)

        self.assertEqual(isolist, ["a", "b", "c", "d"])
        self.assertEqual(coollist, ["1_d", "2 w", "99 y", "whoops"])

    def test_gen_iso_cool_lists2(self):
        """Test that string cooling steps are correctly accepted
        """
        isolistraw = "a, b, c,d"
        coollistraw = "1_d, 99 y"
        
        # Create placeholder for phtn_src file
        with NTF() as myNTF: 
            myNTF.write(self.NTFcontents)
            myNTF.seek(0) # Goes to beginning
            isolist, coollist = s2s.gen_iso_cool_lists(isolistraw, \
                coollistraw, myNTF.name)

        self.assertEqual(isolist, ["a", "b", "c", "d"])
        self.assertEqual(coollist, ["1_d", "99 y"])

    def test_gen_iso_cool_lists3(self):
        """Test getting string cooling times from phtn_src file.
        """
        isolistraw = "a, b, c, d"
        coollistraw = "0, 1, 2, 3"

        # Create placeholder for phtn_src file
        with NTF() as myNTF: 
            myNTF.write(self.NTFcontents)
            myNTF.seek(0) # Goes to beginning
            isolist, coollist = s2s.gen_iso_cool_lists(isolistraw, \
                coollistraw, myNTF.name)

        self.assertEqual(isolist, ["a", "b", "c", "d"])
        self.assertEqual(coollist, ["shutdown", "1_d", "2 w", "99 y"])

    def test_gen_iso_cool_lists4(self):
        """Test getting string cooling times from phtn_src file w/out of order cooling numbers.
        """
        isolistraw = "a, b, c, d"
        coollistraw = "3, 1, 0, 2"

        # Create placeholder for phtn_src file
        with NTF() as myNTF:
            myNTF.write(self.NTFcontents)
            myNTF.seek(0) # Goes to beginning
            isolist, coollist = s2s.gen_iso_cool_lists(isolistraw, \
                coollistraw, myNTF.name)

        self.assertEqual(isolist, ["a", "b", "c", "d"])
        self.assertEqual(coollist, ["shutdown", "1_d", "2 w", "99 y"])

    def test_gen_iso_cool_lists5(self):
        """Tests that exception is raised when cooling indices go too high.
        """
        isolistraw = "a, b, c,d"
        coollistraw = "1, 2, 3, 14"
        
        # Create placeholder for phtn_src file
        with NTF() as myNTF: 
            myNTF.write(self.NTFcontents)
            myNTF.seek(0) # Goes to beginning
            self.assertRaises(R2S_CFG_Error, s2s.gen_iso_cool_lists, \
                    isolistraw, coollistraw, myNTF.name)

    def test_gen_iso_cool_lists6(self):
        """Test that exception is raised if cooling steps not found in phnt_src
        """
        isolistraw = "a, b, c,d"
        coollistraw = "1_d, 99_y, never"
        
        # Create placeholder for phtn_src file
        with NTF() as myNTF: 
            myNTF.write(self.NTFcontents)
            myNTF.seek(0) # Goes to beginning
            self.assertRaises(R2S_CFG_Error, s2s.gen_iso_cool_lists, \
                    isolistraw, coollistraw, myNTF.name)

    def test_gen_iso_cool_lists7(self):
        """Test that 'all' results in all cooling steps being grabbed.
        """
        isolistraw = "a, b, c, d"
        coollistraw = "all"

        # Create placeholder for phtn_src file
        with NTF() as myNTF: 
            myNTF.write(self.NTFcontents)
            myNTF.seek(0) # Goes to beginning
            isolist, coollist = s2s.gen_iso_cool_lists(isolistraw, \
                coollistraw, myNTF.name)

        self.assertEqual(isolist, ["a", "b", "c", "d"])
        self.assertEqual(coollist, ["shutdown", "1_d", "2 w", "99 y", \
                "whoops", "too far"])


class TestMakeFolders(unittest.TestCase):

    def setUp(self):
        self.isolist = ["a", "b"]
        self.coollist = ["1 d", "2 w", "shutdown"]
        # Redirect os.curdir to a temp folder
        self.curdir = os.curdir
        self.tempdir = mkdtemp()
        os.curdir = self.tempdir
    
    def tearDown(self):
        # Reset os.curdir, and remove temp folder and its contents
        os.curdir = self.curdir
        rmtree(self.tempdir)

    def test_make_folders_exist(self):
        """Verify existence of expected folders
        """
        thisdir = os.curdir
        #s2s.make_folders(self.isolist, self.coollist)
        expected = [os.path.join(thisdir, "a_1_d"),
                os.path.join(thisdir, "a_2_w"),
                os.path.join(thisdir, "a_shutdown"),
                os.path.join(thisdir, "b_1_d"),
                os.path.join(thisdir, "b_2_w"),
                os.path.join(thisdir, "b_shutdown")]
        s2s.make_folders(self.isolist, self.coollist)
        for path in expected:
            self.assertTrue(os.path.isdir(path))
        pass

    def test_make_folders_return(self):
        """Verify list of folders to be generated
        """
        thisdir = os.curdir
        expected = [ [os.path.join(thisdir, "a_1_d"), "a", "1 d"],
                [os.path.join(thisdir, "a_2_w"), "a", "2 w"],
                [os.path.join(thisdir, "a_shutdown"), "a", "shutdown"],
                [os.path.join(thisdir, "b_1_d"), "b", "1 d"],
                [os.path.join(thisdir, "b_2_w"), "b", "2 w"],
                [os.path.join(thisdir, "b_shutdown"), "b", "shutdown"] ]
        result = s2s.make_folders(self.isolist, self.coollist)
        expected.sort()
        result.sort()
        self.assertEqual(expected, result)

    def test_make_folders_already_exist(self):
        """Run make_folders() twice to make sure existing folders do not cause a problem
        """
        s2s.make_folders(self.isolist, self.coollist)
        s2s.make_folders(self.isolist, self.coollist)

class TestCreateNewFiles(unittest.TestCase):
    
    def setUp(self):
        # Redirect os.curdir to a temp folder
        self.curdir = os.curdir
        self.tempdir = mkdtemp()
        os.curdir = self.tempdir
        
        # Make the directories for the various cases
        self.isolist = ["a", "b"]
        self.coollist = ["1 d", "2 w", "shutdown"]
        self.path_list = s2s.make_folders(self.isolist, self.coollist)
        #print >>sys.stderr, [x[0] for x in self.path_list]
    
    def tearDown(self):
        # Reset os.curdir, and remove temp folder and its contents
        os.curdir = self.curdir
        rmtree(self.tempdir)

    def test_create_new_files(self):
        """
        """
        # Create placeholder for phtn_src file
        with contextlib.nested(
                NTF(prefix='data_',dir=os.curdir),
                NTF(prefix='cfg_', dir=os.curdir),
                NTF(prefix='inpp_', dir=os.curdir)) as \
                (dataNTF, cfgNTF, inppNTF):

            cfgNTF.write("photon_isotope = @rb!+r@Ry\t\n" \
                    "photon_cooling =  @rb!+r@Ry\t\n" \
                    "neutron_mcnp_input = @rb!+r@Ry\t\n" \
                    "alara_phtn_src = @rb!+r@Ry\t\n" \
                    "photon_mcnp_input = @rb!+r@Ry\t\n"
                    )
            cfgNTF.seek(0)

            inppNTF.write("Fake title card line\nAnother line.\n")
            inppNTF.seek(0) # Goes to beginning
        
            s2s.create_new_files(self.path_list, dataNTF.name, cfgNTF.name, "mcnp_n.inp", inppNTF.name, "phtn_src")

            # Check that files were copied
            for folder in os.listdir(os.curdir):
                if os.path.isdir(os.path.join(os.curdir,folder)):
                    self.assertTrue(os.path.exists( \
                            os.path.join(os.curdir, folder, dataNTF.name)))
                    self.assertTrue(os.path.exists( \
                            os.path.join(os.curdir, folder, inppNTF.name)))
                    self.assertTrue(os.path.exists( \
                            os.path.join(os.curdir, folder, cfgNTF.name)))

            # # Useful for debug
            # print >>sys.stderr, os.curdir
            # print >>sys.stderr, os.listdir(os.curdir)
            # for folder in os.listdir(os.curdir):
            #     if os.path.isdir(os.path.join(os.curdir,folder)):
            #         print >>sys.stderr, os.path.join(os.curdir,folder)
            #         print >>sys.stderr, os.listdir(os.path.join(os.curdir,folder))
            
            # Check contents of each .cfg file...


