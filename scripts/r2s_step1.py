#! /usr/bin/env python

import sys
import os.path
import ConfigParser

from r2s.io.read_meshtal import read_meshtal, find_tallies
from r2s.io.write_alara_fluxin import write_alara_fluxin
from r2s.io.write_alara_geom import write_alara_geom
from r2s import mmgrid
from r2s_setup import get_input_file as r2s_input_file
from r2s_setup import FileMissingError
from r2s.scdmesh import ScdMesh, ScdMeshError

cfgfile = 'r2s.cfg'
if len(sys.argv) > 1:
    cfgfile = sys.argv[1]

config = ConfigParser.SafeConfigParser()
config.read(cfgfile)

def get_input_file(name):
    return r2s_input_file(config,name)

def get_material_dict():
    d = {}
    if config.has_section('r2s-material'):
        keys = config.options('r2s-material')
        for key in keys:
            d[key] = config.get('r2s-material',key)
    return d

###########################
# Read in config file information

# Get the input files for this step: the meshtal and the mcnp geometry

meshtal_file = get_input_file('neutron_meshtal')

try:
    mcnp_geom = get_input_file('mcnp_geom')
except FileMissingError:
    filename = config.get('r2s-files','mcnp_geom')
    print 'The DagMC geometry file',filename,'is missing.'
    print 'Will try to create it using mcnp2cad...'
    mcnp_file = get_input_file('neutron_mcnp_input')
    os.system('mcnp2cad -o {0} {1}'.format(filename,mcnp_file))
    mcnp_geom = get_input_file('mcnp_geom')

try:
    alara_snippet = get_input_file('alara_snippet')
except FileMissingError:
    print 'Warning: the alara snippet file is missing.'
    print '         The alara problem file produced will not be complete.'
    alara_snippet = None

visfile = None
if config.has_option('r2s-files','step1_visfile'):
    visfile = config.get('r2s-files','step1_visfile')

# Output filenames

datafile = config.get('r2s-files','step1_datafile')
fluxin = config.get('r2s-files','alara_fluxin')
alara_geom = config.get('r2s-files','alara_geom')
alara_matdict = get_material_dict()

# Read parameters

# This list stores (1) parameter names as listed in r2s.cfg; 
# (2) their defaults; (3) which 'get' function to use for the parameter
param_guide = [ #parameter  #default #get function
        [ 'gen_mmgrid', True, config.getboolean],
        [ 'mmgrid_rays', 10, config.getint],
        [ 'step2setup', False, config.getboolean]
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

(gen_mmgrid, mmgrid_rays, opt_step2setup) = param_list



###########################
# Do step 1

print "Loading mesh tally file `{0}'".format(meshtal_file)
tally_numbers, tally_lines = find_tallies(meshtal_file)
# If not regenerating the mmGrid info, attempt to load existing datafile
if gen_mmgrid == False:
    print "Attempting to re-use existing ScdMesh file '{0}'".format(datafile)
    alt_sm = ScdMesh.fromFile(datafile)
    try:
        smesh = read_meshtal(meshtal_file, tally_lines[0], smesh=alt_sm)
    except ScdMeshError:
        print "ERROR:"
        print "Existing mesh in '{0}' does not match mesh in '{1}'. Set the " \
                "'gen_mmgrid' option to True in your 'r2s.cfg' file.".format( \
                datafile, meshtal_file)
        sys.exit()
else:
    smesh = read_meshtal(meshtal_file, tally_lines[0])

print "Loading geometry file `{0}'".format(mcnp_geom)
mmgrid.load_geom(mcnp_geom)

# Do ray tracing to create macromaterials, if enabled.
if gen_mmgrid:
    print "Will use {0} rays per mesh row".format(mmgrid_rays)

    grid = mmgrid.mmGrid( smesh )
    grid.generate( mmgrid_rays, False )
    grid.createTags()


print "Saving fluxes and materials to `{0}'".format(datafile)
smesh.imesh.save(datafile)

if visfile != None:
    print "Producing visualization file `{0}' with mbconvert".format(visfile)
    os.system('mbconvert {0} {1}'.format(datafile,visfile))

print "Writing alara problem file `{0}'".format(alara_geom)
mdict = get_material_dict()
write_alara_geom( alara_geom, smesh, mdict )

if alara_snippet:
    print "Appending alara snippet file `{0}' to problem file".format(alara_snippet)
    with open(alara_geom,'a') as f:
        with open(alara_snippet,'r') as snip:
            f.write(snip.read())

print "Writing alara fluxin file `{0}'".format(fluxin)
write_alara_fluxin( fluxin, smesh, backwards=True )


print "It should now be possible to run `alara {0}'".format(alara_geom)
print "and proceed to step 2 of the workflow."
