#! /usr/bin/env python

import sys
import ConfigParser
import os.path

from r2s.io import read_alara_phtn, write_gammas
from r2s import mcnp_n2p
from r2s.scdmesh import ScdMesh, ScdMeshError
from itaps import iMesh, iMeshExtensions
from r2s_setup import get_input_file, FileMissingError


cfgfile = 'r2s.cfg'
if len(sys.argv) > 1:
    cfgfile = sys.argv[1]

config = ConfigParser.SafeConfigParser()
config.read(cfgfile)


###########################
# Read in config file information

# Required input files
if config.has_option('r2s-files', 'step2_datafile'):
    datafile = get_input_file(config, 'step2_datafile')
else:
    datafile = get_input_file(config, 'step1_datafile')

phtn_src = get_input_file(config, 'alara_phtn_src')


# Filenames
mcnp_p_problem = None
if config.has_option('r2s-files','photon_mcnp_input'):
    mcnp_n_problem = config.get('r2s-files','neutron_mcnp_input')
    mcnp_p_problem = config.get('r2s-files','photon_mcnp_input')
    

# Read other parameters from r2s.cfg

# This list stores (1) parameter names as listed in r2s.cfg; (2) their defaults;
#  (3) which 'get' function to use for the parameter
param_guide = [ #parameter  #default #get function
        [ 'photon_isotope', "TOTAL", config.get],
        [ 'photon_cooling', 0,       config.get],
        [ 'sampling'      , 'v',     config.get],
        [ 'custom_ergbins', False,   config.getboolean],
        [ 'photon_bias'   , False,   config.getboolean],
        [ 'cumulative'    , False,   config.getboolean],
        [ 'add_fmesh_card', True,    config.getboolean]
        ] 

param_list = list()

for param in param_guide:
    try:
        # Try to read from r2s.cfg
        # Note that param[2] is a function
        param_list.append( param[2]('r2s-params', param[0]) )
    except ConfigParser.NoOptionError:
        # Use default
        param_list.append( param[1])

(opt_isotope, opt_cooling, opt_sampling, opt_ergs, opt_bias, opt_cumulative, opt_phtnfmesh) = param_list


###########################
# Do step 2

print "Loading step one data file '{0}'".format(datafile)
smesh = ScdMesh.fromFile(datafile)

# Tagging mesh
print "Reading ALARA photon source '{0}'".format(phtn_src)
read_alara_phtn.read_to_h5m(phtn_src, smesh, isotope=opt_isotope, \
        coolingstep=opt_cooling, retag=True, totals=True)

print "Saving photon source information to '{0}'".format(datafile)
smesh.imesh.save(datafile)

fr = open(phtn_src, 'r')
coolingstepstring = read_alara_phtn.get_cooling_step_name(opt_cooling, fr)[0]
fr.close()

print "Writing gammas file"
write_gammas.gen_gammas_file_from_h5m(smesh, sampling=opt_sampling, \
        do_bias=opt_bias, cumulative=opt_cumulative, cust_ergbins=opt_ergs, \
        coolingstep=coolingstepstring, isotope=opt_isotope)

# Create photon MCNP input file from neutron input if it doesn't exist already
if mcnp_p_problem:

    if os.path.exists(mcnp_p_problem):
        print "MCNP photon transport input file '{0}' already exists and will" \
                " not be recreated.".format(mcnp_p_problem)

    else:
        print "Modifying MCNP input file '{0}'".format(mcnp_n_problem)

        mod = mcnp_n2p.ModMCNPforPhotons(mcnp_n_problem)
        mod.read()
        mod.convert()

        # If phtnfmesh is True, we generate an fmesh card with same 
        #  layout as found on the scdmesh.
        if opt_phtnfmesh:
            mod.add_fmesh_from_scdmesh(smesh)

        mod.write_deck(mcnp_p_problem)

print "" # Empty line to separate output from multiple runs of this script
