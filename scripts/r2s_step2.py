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
    mcnp_n_problem = config.get('r2s-files','neutron_mcnp_input')
    mcnp_p_problem = config.get('r2s-files','photon_mcnp_input')
    

# Read other parameters from r2s.cfg

# This list stores (1) parameter names as listed in r2s.cfg; (2) their defaults;
#  (3) whether these variables need to be converted to a boolean.
param_guide = [ #parameter  #default #boolean?
        [ 'photon_isotope', "TOTAL", False],
        [ 'photon_cooling', 0,       False],
        [ 'sampling'      , 'v',     False],
        [ 'custom_ergbins', False,   True ],
        [ 'photon_bias'   , False,   True ],
        [ 'cumulative'    , False,   True ],
        [ 'add_fmesh_card', True,    True ]
        ] 

param_list = list()

for param in param_guide:
    try:
        # Try to read from r2s.cfg
        param_list.append( config.get('r2s-params', param[0]) )
        if param[2]:
            param_list[-1] = bool(int(param_list[-1]))
    except ConfigParser.NoOptionError:
        # Use default
        param_list.append( param[1])

(opt_isotope, opt_cooling, opt_sampling, opt_ergs, opt_bias, opt_cumulative, opt_phtnfmesh) = param_list


# Do processing

print "Loading step one data file '{0}'".format(datafile)
smesh = ScdMesh.fromFile(datafile)

# Tagging mesh
print "Reading ALARA photon source '{0}'".format(phtn_src)
read_alara_phtn.read_to_h5m(phtn_src, smesh, isotope=opt_isotope, \
        coolingstep=opt_cooling, retag=True, totals=True)

print "Saving photon source information to '{0}'".format(datafile)
smesh.imesh.save(datafile)

print "Writing gammas file"
write_gammas.gen_gammas_file_from_h5m(smesh, sampling=opt_sampling, \
        do_bias=opt_bias, cumulative=opt_cumulative, cust_ergbins=opt_ergs)

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
