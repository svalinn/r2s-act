#! /usr/bin/env python
import sys
import ConfigParser

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
datafile = get_input_file(config, 'step1_datafile')
phtn_src = get_input_file(config, 'alara_phtn_src')


# Filenames
mcnp_p_problem = None
if config.has_option('r2s-files','photon_mcnp_input'):
    mcnp_n_problem = get_input_file(config,'neutron_mcnp_input')
    mcnp_p_problem = config.get('r2s-files','photon_mcnp_input')
    

# Do processing

print "Loading step one data file `{0}'".format(datafile)
smesh = ScdMesh.fromFile(datafile)

print "Reading alara photon source `{0}'".format(phtn_src)
read_alara_phtn.read_to_h5m(phtn_src, smesh, isotope="TOTAL", coolingstep=0, \
        retag=True, totals=True)

print "Writing gammas file"
write_gammas.gen_gammas_file_from_h5m(smesh)

if mcnp_p_problem:

    print "Modifying MCNP input file `{0}'".format(mcnp_n_problem)

    # Set dagmc to True if input only contains the title card and data block
    dagmc = False
    mod = mcnp_n2p.ModMCNPforPhotons(mcnp_n_problem, dagmc)
    mod.read()

    if not dagmc:
        mod.change_block_1()
        mod.change_block_2()
    mod.change_block_3()

    # If phtnfmesh is True, we generate an fmesh card with same layout as mesh
    phtnfmesh = True
    if phtnfmesh:
        mod.add_fmesh_from_scdmesh(smesh)

    mod.write_deck(mcnp_p_problem)
