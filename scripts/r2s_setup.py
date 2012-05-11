#! /usr/bin/env python

import sys
import os.path
import optparse
import ConfigParser

class FileMissingError(Exception):
    pass

def get_input_file(config, key):
    filename = config.get('r2s-files',key)
    if not os.path.exists(filename):
        raise FileMissingError(key +' file is missing: '+filename)
    return filename


def main():
    op = optparse.OptionParser('Setup script for R2S workflow')
    opts, args = op.parse_args(sys.argv)

    cfgfile = 'r2s.cfg'
    if len(args) > 1:
        cfgfile = args[1]

    if os.path.exists(cfgfile):
        print 'Config file already exists:', cfgfile
        print 'Will not overwrite.'
    else:
        with file(cfgfile,'w') as f:
            f.write(default_config)
            print 'Wrote default config file:', cfgfile

    
    # If the config file was written or already exists, write snippet if the
    # specified snippet does not already exist
    # Do nothing if config file exists but isn't the expected format.

    config = ConfigParser.SafeConfigParser()
    config.read(cfgfile)
    snippet = config.get('r2s-files','alara_snippet')

    if os.path.exists(snippet):
        print 'Snippet file already exists:', snippet
        print 'Will not overwrite.'
    else:
        with file(snippet,'w') as f:
            f.write(default_snippet)
            print 'Wrote ALARA snippet file:', snippet


default_config = """
## Robust 2-step activation workflow
## Setup file
## This file has python ConfigParser/.ini syntax,
## and should be hand-edited to match your problem definition.

[r2s-files]

# MCNP neutron mesh tally from first step of workflow.
neutron_meshtal = meshtal

# MCNP input file from first first step of workflow.
neutron_mcnp_input = mcnp_n.inp

# DagMC CAD geometry corresponding to MCNP input file.
# If this file does not exist, we will attempt to create it
# using mcnp2cad.
mcnp_geom = geom.sat

# Intermediate mesh file containing data from step 1.
# Must be a format that supports global tags, such at .h5m
step1_datafile = n_fluxes_and_materials.h5m

# ALARA fluxin file
alara_fluxin = alara_fluxin

# ALARA geometry file
alara_geom = alara_geom

# ALARA snippet file
# This file will be appended to the alara_geom during step 1
alara_snippet = alara_problem

# To produce a visualizable file at the end of step 1,
# comment out the following:
# step1_visfile = n_fluxes_and_materials.vtk

# ALARA photon source file.
alara_phtn_src = phtn_src

# MCNP photon problem input file for last step of workflow
photon_mcnp_input = mcnp_p.inp

[r2s-params]
# Non-filename parameters for r2s workflow

# The number of rays per mesh row to fire
# during Monte Carlo generation of the macromaterial grid.
# Raising this number will reduce material errors, but 
# also increase the runtime of r2s_step1.
mmgrid_rays = 10

[r2s-material]
# This section may be used to map material idenfitiers to material names.
# The mapping is used when writing out mixtures to ALARA's format,
# as well as for material tagging.
#
# Example:
# mat1_rho-1.0 = water
"""

default_snippet = """
material_lib    matlib
element_lib     elelib
data_library alaralib FENDL2

cooling
    1   s
    1   m
    1   h
    1   d
    1   y
end

dump_file   dump.file

output zone
       units Ci cm3
#   constituent
       specific_activity
       photon_source  FENDL2  phtn_src 42  1e4  2e4
          3e4  4.5e4  6e4  7e4  7.5e4  1e5  1.5e5  2e5  3e5
          4e5  4.5e5  5.1e5  5.12e5  6e5  7e5  8e5  1e6  1.33e6
          1.34e6  1.5e6  1.66e6  2e6  2.5e6  3e6  3.5e6
          4e6  4.5e6  5e6  5.5e6  6e6  6.5e6  7e6  7.5e6  8e6
          1e7  1.2e7  1.4e7  2e7  3e7  5e7
end

flux flux_1 fluxin 1.0 0 default

schedule    total
    .85 y   flux_1  3.9FPYpulsed    0  s
end

pulsehistory    3.9FPYpulsed
    5   .15 y
end

truncation  1e-7
impurity    5e-6    1e-3
"""

if __name__ == '__main__':
    main()
