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


# Default contents of the r2s.cfg file
default_config = """
## Robust 2-step activation workflow
## Setup file
## This file has python ConfigParser/.ini syntax,
## and should be hand-edited to match your problem definition.

###############################################################################
[r2s-files]
###############################################################################

#-------------------------------------------------------------------------------
# Files needed for Step 1
# These files must exist prior to running r2s_step1.py
#-------------------------------------------------------------------------------

# MCNP neutron mesh tally from first step of workflow.
neutron_meshtal = meshtal

# MCNP input file from first first step of workflow.
neutron_mcnp_input = mcnp_n.inp

# DagMC CAD geometry corresponding to MCNP input file.
# If this file does not exist, we will attempt to create it
# using mcnp2cad.
mcnp_geom = geom.sat

#-------------------------------------------------------------------------------
# Files produced in Step 1
# These files are created by r2s_step1.py. Specify the desired file names.
#-------------------------------------------------------------------------------

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
# uncomment the following:
# step1_visfile = n_fluxes_and_materials.vtk

#-------------------------------------------------------------------------------
# Files needed for Step 2
# These files must exist prior to running r2s_step2.py
#-------------------------------------------------------------------------------

# ALARA photon source file; ALARA generates this file using a filename specified
# in the ALARA input.
alara_phtn_src = phtn_src

#-------------------------------------------------------------------------------
# Files produced in Step 2
# This file are created by r2s_step2.py. Specify the desired file names.
#-------------------------------------------------------------------------------

# MCNP photon problem input file for last step of workflow
photon_mcnp_input = mcnp_p.inp

# The 'gammas' file is created by r2s_step2.py, but alternate names are not
# supported currently.


###############################################################################
[r2s-params]
# Non-filename parameters for r2s workflow
###############################################################################

#-------------------------------------------------------------------------------
# Step 1 Parameters
#-------------------------------------------------------------------------------

# The number of rays per mesh row to fire
# during Monte Carlo generation of the macromaterial grid.
# Raising this number will reduce material errors, but 
# also increase the runtime of r2s_step1.
mmgrid_rays = 10

# If 
# If gen_mmgrid is True, ray tracing is performed to generate the macromaterials
#  grid during r2s_step1.py. If the macromaterial grid already exists, set this
#  parameter to False to avoid re-running the ray tracing.
gen_mmgrid = True

# If step2setup is True, runs the r2s_step2setup.py script at the end of 
#  r2s_step1.py.  r2s_step2setup.py creates folders for all cooling steps
#  and isotopes specified
step2setup = False

#-------------------------------------------------------------------------------
# Step 2 Parameters
#-------------------------------------------------------------------------------

# These parameters are for step 2.
# -photon_isotope default is TOTAL. This is the isotope taken from phtn_src
#  for tagging
# -photon_cooling is the cooling step read from phtn_src. 0 is shutdown,
#  other numbers correspond with cooling times listed in your ALARA input.
# -sampling determines the sampling method used:
#   u for uniform sampling; v for voxel sampling (default)
# -if photon_bias is True, the gammas file will try to include voxel
#  bias values from the mesh (stored as PHTN_BIAS tag). Currently requires
#  photon_by_voxel to be 1.
# -if custom_ergbins is True, custom energy bins will be looked for on
#   the mesh, and included in gammas file if found. 
#   (Default: False; 42 grps used)
# -cumulative determines the format for listing voxels in gammas file.
#   Default is False, which is preferred.
# -add_fmesh_card adds an FMESH tally with mesh information to the MCNP
#   photon input file that is created. Mesh information is taken from 
#   step1_datafile.
# -resample enables resampling within a voxel for both uniform and voxel
#   sampling.
# -uni_resamp_all toggles whether a resampled particle in uniform sampling
#   is resampled over the entire problem, rather than within the selected voxel.
#   This approach will result in an unfair game being played for most problems.
# Note: photon_isotope and photon_cooling can have multiple, comma 
#  delimited entries for use in conjunction with the r2s_step2setup.py script.
photon_isotope = TOTAL
photon_cooling = 0
sampling = v
# Next six boolean values
photon_bias = False
custom_ergbins = False
cumulative = False
add_fmesh_card = True
resample = True
uni_resamp_all = False


###############################################################################
[r2s-material]
# This section may be used to map material idenfitiers to material names.
# The mapping is used when writing out mixtures to ALARA's format,
# as well as for material tagging.
###############################################################################

# Example:
# mat1_rho-1.0 = water
"""


# Default contents of the ALARA input template file
default_snippet = default_snippet = """
# ALARA Snippet file: See ALARA user manual for additional syntax information

# Specify the material, element, and data libraries.
material_lib    matlib
element_lib     isolib
data_library alaralib FENDL2

# Specify the cooling times for which activation results are desired
cooling
    1   s
    1   m
    1   h
    1   d
    1   y
end

# Specify the fluxin file and normalization, if needed 
#    flux name  flux file     norm   shift   unused
flux flux_1     alara_fluxin  1.0    0     default

# Specify the irradiation schedule using "schedule" and "pulsehistory"
# Syntax is found in the ALARA user manual
schedule    total
    .85 y   flux_1  pulse_once    0  s
end

# A pulse history is applied to each flux in the schedule. Pulse syntax is:
#  pulsehistory    pulse_name
#       num_pulses   delay_between_pulses
#  end
pulsehistory    pulse_once
    1   0.0 y
end
pulsehistory    pulse_thrice_wait_some
    3   0.1 y
end

# Specify desired ALARA output (e.g. constituant, specific activity).
# Photon source card must be present to produce the pthn_src file for step2.
output zone
       units Ci cm3
       # constituent
       # specific_activity
       photon_source  FENDL2  phtn_src 42  1e4  2e4
          3e4  4.5e4  6e4  7e4  7.5e4  1e5  1.5e5  2e5  3e5
          4e5  4.5e5  5.1e5  5.12e5  6e5  7e5  8e5  1e6  1.33e6
          1.34e6  1.5e6  1.66e6  2e6  2.5e6  3e6  3.5e6
          4e6  4.5e6  5e6  5.5e6  6e6  6.5e6  7e6  7.5e6  8e6
          1e7  1.2e7  1.4e7  2e7  3e7  5e7
end

#other parameters
truncation  1e-12
impurity    5e-6    1e-3
dump_file   dump.file
"""

if __name__ == '__main__':
    main()
