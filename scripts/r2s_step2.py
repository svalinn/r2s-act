#! /usr/bin/env python
import sys
import ConfigParser
import os.path

from r2s.io import read_alara_phtn, write_gammas
from r2s import mcnp_n2p
from scdmesh import ScdMesh, ScdMeshError
from itaps import iMesh, iMeshExtensions
from r2s_setup import get_input_file, FileMissingError

cfgfile = 'r2s.cfg'
if len(sys.argv) > 1:
    cfgfile = sys.argv[1]

config = ConfigParser.SafeConfigParser()
config.read(cfgfile)

# Required input files
if config.has_option('r2s-files', 'step2_datafile'):
    datafile = get_input_file(config, 'step2_datafile')
else:
    datafile = get_input_file(config, 'step1_datafile')

phtn_src = get_input_file(config, 'alara_phtn_src')


# Filenames
mcnp_p_problem = None
if config.has_option('r2s-files','photon_mcnp_input'):
    mcnp_n_problem = get_input_file(config,'neutron_mcnp_input')
    mcnp_p_problem = config.get('r2s-files','photon_mcnp_input')
    
# Optional values from r2s-params section.
if config.has_section('r2s-params'):
    opt_isotope = config.get('r2s-params','photon_isotope')
    opt_cooling = config.get('r2s-params','photon_cooling')
    opt_sampling = config.get('r2s-params','sampling')
    opt_ergs = bool(int(config.get('r2s-params','custom_ergbins')))
    opt_bias = bool(int(config.get('r2s-params','photon_bias')))
    opt_cumulative = bool(int(config.get('r2s-params','cumulative')))
else:
    opt_isotope = "TOTAL"
    opt_cooling = 0
    opt_sampling = 'v'
    opt_ergs = False
    opt_bias = False
    opt_cumulative = False
    
# Do processing

print "Loading step one data file `{0}'".format(datafile)
smesh = ScdMesh.fromFile(datafile)

# Tagging mesh
print "Reading ALARA photon source `{0}'".format(phtn_src)
read_alara_phtn.read_to_h5m(phtn_src, smesh, isotope=opt_isotope, \
        coolingstep=opt_cooling, retag=True, totals=True)

print "Saving photon source information to '{0}'".format(datafile)
smesh.imesh.save(datafile)

print "Writing gammas file"
write_gammas.gen_gammas_file_from_h5m(smesh, sampling=opt_sampling, \
        do_bias=opt_bias, cumulative=opt_cumulative, cust_ergbins=opt_ergs)

if mcnp_p_problem:

    if os.path.exists(mcnp_p_problem):
        print "MCNP photon transport input file '{0}' already exists and will" \
                " not be recreated.".format(mcnp_p_problem)

    else:

        print "Modifying MCNP input file `{0}'".format(mcnp_n_problem)

        # Set dagmc to True if input only contains the title card and data block
        dagmc = False
        mod = mcnp_n2p.ModMCNPforPhotons(mcnp_n_problem, dagmc)
        mod.read()

        if not dagmc:
            mod.change_block_1()
            mod.change_block_2()
        mod.change_block_3()

        # If phtnfmesh is True, we generate an fmesh card with same 
        #  layout as found on the scdmesh.
        phtnfmesh = True
        if phtnfmesh:
            mod.add_fmesh_from_scdmesh(smesh)

        mod.write_deck(mcnp_p_problem)

print "" # Empty line to separate output from multiple runs of this script
