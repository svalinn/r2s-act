import unittest
import sys
import os
import os.path
from tempfile import NamedTemporaryFile as NTF
from tempfile import mkdtemp
from shutil import copyfile
import ConfigParser
import contextlib

import r2s_step2 as s2


class TestLoadConfigFiles(unittest.TestCase):
    #

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_load_config_files(self):
        """Simulate a .cfg file and check that file names are read correctly.
        """
        with contextlib.nested(
                NTF(prefix='data_',dir=os.curdir),
                NTF(prefix='cfg_', dir=os.curdir),
                NTF(prefix='phtn_', dir=os.curdir)) as \
                (dataNTF, cfgNTF, phtnNTF):
            # Create placeholder for r2s.cfg file
            cfgNTF.write("[r2s-files]\n" \
                    "neutron_mcnp_input = mcnp_n\n" \
                    "photon_mcnp_input = mcnp_p\n" \
                    "step1_datafile = {0}\n" \
                    "alara_phtn_src = {1}\n".format(dataNTF.name, phtnNTF.name)
                    )
            cfgNTF.seek(0) # Goes to beginning

            config = ConfigParser.SafeConfigParser()
            config.read(cfgNTF.name)

            datafile, phtn_src, mcnp_n, mcnp_p = \
                    s2.load_config_files(config)

            # Check for correctness
            self.assertEqual(mcnp_n, 'mcnp_n')
            self.assertEqual(mcnp_p, 'mcnp_p')
            self.assertEqual(datafile, dataNTF.name)
            self.assertEqual(phtn_src, phtnNTF.name)


class TestLoadConfigParams(unittest.TestCase):
    #

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_load_config_params(self):
        """Simulate a .cfg file and check that parameters are read correctly.
        """
        with NTF() as myNTF:
            # Create placeholder for r2s.cfg file
            myNTF.write("[r2s-params]\n" \
                    "photon_isotope = u235\n" \
                    "photon_cooling = shutdown\n" \
                    "sampling = u\n" \
                    "custom_ergbins = True\n" \
                    "photon_bias = True\n" \
                    "cumulative = True\n" \
                    "add_fmesh_card = False\n"
                    )
            myNTF.seek(0) # Goes to beginning

            config = ConfigParser.SafeConfigParser()
            config.read(myNTF.name)

            (opt_isotope, opt_cooling, opt_sampling, opt_ergs, opt_bias, opt_cumulative, opt_phtnfmesh, resample, uni_resamp_all) = \
                    s2.load_config_params(config)
            # Check for correctness
            self.assertEqual(opt_isotope, 'u235')
            self.assertEqual(opt_cooling, 'shutdown')
            self.assertEqual(opt_sampling, 'u')
            self.assertTrue(opt_ergs)
            self.assertTrue(opt_bias)
            self.assertTrue(opt_cumulative)
            self.assertFalse(opt_phtnfmesh)
            self.assertFalse(resample)
            self.assertFalse(uni_resamp_all)

    def test_load_config_params_badisotope(self):
        """Simulate a .cfg file and check that multiple isotopes in r2s.cfg
        raises an error
        """
        with NTF() as myNTF:
            # Create placeholder for r2s.cfg file
            myNTF.write("[r2s-params]\n" \
                    "photon_isotope = u235, u234\n" \
                    "photon_cooling = shutdown\n" \
                    "sampling = u\n" \
                    "custom_ergbins = True\n" \
                    "photon_bias = True\n" \
                    "cumulative = True\n" \
                    "add_fmesh_card = False\n"
                    )
            myNTF.seek(0) # Goes to beginning

            config = ConfigParser.SafeConfigParser()
            config.read(myNTF.name)

            self.assertRaises(Exception, s2.load_config_params, config)
 
    def test_load_config_params_badcooling(self):
        """Simulate a .cfg file and check that multiple cooling steps in r2s.cfg
        raises an error
        """
        with NTF() as myNTF:
            # Create placeholder for r2s.cfg file
            myNTF.write("[r2s-params]\n" \
                    "photon_isotope = u235\n" \
                    "photon_cooling = shutdown, 1 d\n" \
                    "sampling = u\n" \
                    "custom_ergbins = True\n" \
                    "photon_bias = True\n" \
                    "cumulative = True\n" \
                    "add_fmesh_card = False\n"
                    )
            myNTF.seek(0) # Goes to beginning

            config = ConfigParser.SafeConfigParser()
            config.read(myNTF.name)

            self.assertRaises(Exception, s2.load_config_params, config)
 

class TestHandlePhtnData(unittest.TestCase):
    #
    # Note we do not compare the produced 'gammas' file, as that is handled
    # by test_write_gammas.py.

    def setUp(self):
        thisdir = os.path.dirname(__file__)
        # .h5m files for generating different gammas files
        self.meshfile = os.path.join(thisdir, "files_test_r2s_step2/n_fluxes_and_materials.h5m")
        self.meshfile_new = os.path.join(thisdir, "files_test_r2s_step2/copy_n_fluxes_and_materials.h5m")
        # phtn_src files for comparing test result with expected result
        self.phtnfile = os.path.join(thisdir, "files_test_r2s_step2/phtn_src")
        copyfile(self.meshfile, self.meshfile_new)

    def tearDown(self):
        os.remove(self.meshfile_new)

    def test_handle_phtn_data_string_cooling(self):
        """Tests handling of phtn_src file with string cooling step
        """
        with NTF() as gammaNTF:
            s2.handle_phtn_data(self.meshfile_new, self.phtnfile, 'TOTAL', 
                    'shutdown', 'v', False, False, False, False, False,
                    gammas=gammaNTF.name)

    def test_handle_phtn_data_string_cooling2(self):
        """Tests handling of phtn_src file with string cooling step
        """
        with NTF() as gammaNTF:
            s2.handle_phtn_data(self.meshfile_new, self.phtnfile, 'TOTAL', 
                    '1 d', 'v', False, False, False, False, False,
                    gammas=gammaNTF.name)

    def test_handle_phtn_data_integer_cooling(self):
        """Tests handling of phtn_src file with numeric cooling step
        """
        with NTF() as gammaNTF:
            s2.handle_phtn_data(self.meshfile_new, self.phtnfile, 'TOTAL', '1',
                    'v', False, False, False, False, False,
                    gammas=gammaNTF.name)


class TestGenMCNPP(unittest.TestCase):
    #

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_gen_mcnp_p_exists(self):
        """Tests successful run when mcnp photon input exists already.
        """
        with NTF(prefix='mcnpp_',dir=os.curdir) as mcnppNTF:
            s2.gen_mcnp_p(None, mcnppNTF.name, None, False)

