#! /usr/bin/env python

import sys
import os.path
import ConfigParser

from itaps import iMesh

from r2s.data_transfer.read_meshtal import read_meshtal, find_tallies
from r2s.data_transfer.write_alara_fluxin import write_alara_fluxin
from r2s.data_transfer.write_alara_geom import write_alara_geom
from r2s import mmgrid
from r2s_setup import get_input_file as r2s_input_file
from r2s_setup import FileMissingError, R2S_CFG_Error
from r2s.scdmesh import ScdMesh, ScdMeshError

#cfgfile = 'r2s.cfg'
#if len(sys.argv) > 1:
#    cfgfile = sys.argv[1]
#
#config = ConfigParser.SafeConfigParser()
#config.read(cfgfile)

def get_input_file(name):
    return r2s_input_file(config,name)

def get_material_dict(config):
    d = {}
    if config.has_section('r2s-material'):
        keys = config.options('r2s-material')
        for key in keys:
            d[key] = config.get('r2s-material',key)
    return d

###########################
# Read in config file information

# Get the input files for this step: the meshtal and the mcnp geometry

def load_config_files(config):
    """Read in config file information for files

    Parameters
    ----------
    config : ConfigParser.ConfigParser object

    Returns
    -------
    A tuple of the following values taken from the .cfg file:
    meshtal_file, mcnp_geom, alara_snippet, visfile, datafile,
    fluxin, alara_geom, alara_matdict
    """


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
        print 'WARNING: the alara snippet file is missing.'
        print '         The alara problem file produced will not be complete.'
        alara_snippet = None

    visfile = None
    if config.has_option('r2s-files','step1_visfile'):
        visfile = config.get('r2s-files','step1_visfile')

    # Output filenames

    datafile = config.get('r2s-files','step1_datafile')
    fluxin = config.get('r2s-files','alara_fluxin')
    alara_geom = config.get('r2s-files','alara_geom')
    alara_matdict = get_material_dict(config)

    return (meshtal_file, mcnp_geom, alara_snippet, visfile, datafile, \
            fluxin, alara_geom, alara_matdict)


# Read parameters
def load_config_params(config):
    """Read in config file information for parameters

    Parameters
    ----------
    config : ConfigParser.ConfigParser object

    Returns
    -------
    A list of the following values taken from the .cfg file:
    gen_mmgrid, mmgrid_rays, opt_step2setup, isscd
    """
    # This list stores (1) parameter names as listed in r2s.cfg; 
    # (2) their defaults; (3) which 'get' function to use for the parameter
    param_guide = [ #parameter  #default #get function
            [ 'gen_mmgrid',     True,  config.getboolean],
            [ 'mmgrid_rays',    10,    config.getint],
            [ 'step2setup',     False, config.getboolean],
            [ 'structuredmesh', True,  config.getboolean]
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

    (gen_mmgrid, mmgrid_rays, opt_step2setup, isscd) = param_list

    return (gen_mmgrid, mmgrid_rays, opt_step2setup, isscd)


###########################
# Do step 1

def handle_meshtal(meshtal_file, gen_mmgrid, datafile, isscd=True):
    """Read MCNP meshtal file and tag mesh

    Parameters
    ----------
    mesh : ScdMesh or iMesh.Mesh()
        Mesh object to be tagged.
    gen_mmgrid : boolean
        Whether to generate a new macromaterials grid
    datafile : string
        File/path to mesh file to be created/loaded/tagged.
    isscd : boolean
        If True, handle geometry as a structured mesh. Otherwise mesh is
        assumed to be unstructured and unstructured mesh tally results are
        assumed to exist on the mesh (Error raised if tag TALLY_TAG is missing).
    """
    if not isscd: # is unstructured
        mesh = iMesh.Mesh()
        mesh.load(datafile)
        try:
            mesh.getTagHandle("TALLY_TAG")
        except iBase.TagNotFoundError as e:
            print "Missing tag 'TALLY_TAG' suggests that '{0}' is missing " \
                    "unstructured mesh tally information.".format(datafile)
            raise e
            
        return mesh

    print "Loading mesh tally file `{0}'".format(meshtal_file)
    tally_numbers, tally_lines = find_tallies(meshtal_file)
    # If not regenerating the mmGrid info, attempt to load existing datafile
    if gen_mmgrid == False:
        print "Attempting to re-use existing ScdMesh file '{0}'".format(datafile)
        alt_sm = ScdMesh.fromFile(datafile)  # Note: ray tracing is done later
        try:
            mesh = read_meshtal(meshtal_file, tally_lines[0], mesh=alt_sm)
        except ScdMeshError:
            print "ERROR:"
            print "Existing mesh in '{0}' does not match mesh in '{1}'. " \
                    "Set the 'gen_mmgrid' option to True in your 'r2s.cfg' " \
                    "file.".format(datafile, meshtal_file)

    else:
        print "Creating ScdMesh file '{0}' from scratch.".format(datafile)
        mesh = read_meshtal(meshtal_file, tally_lines[0])

    return mesh


def handle_mesh_materials(mesh, mcnp_geom, gen_mmgrid=False, mmgrid_rays=10, 
                          isscd=True):
    """Tag the mesh with materials

    Parameters
    ----------
    mesh : ScdMesh or iMesh.Mesh()
        Mesh object to be tagged.
    mcnp_geom : string
        Filename/path for CAD geometry to be loaded into DAGMC from.
    gen_mmgrid : boolean
        Whether to generate a new macromaterials grid
    mmgrid_rays : integer
        Number of rays in each dimension to run mmgrid with
    isscd : boolean
        If True, handle geometry as a structured mesh. Otherwise mesh is
        assumed to be unstructured and materials are based on voxel centers.
    """

    print "Loading geometry file `{0}'".format(mcnp_geom)
    mmgrid.load_geom(mcnp_geom)

    if not isscd: # is unstructured
        # Use non-structured mesh approach: tag material of voxel center points
        grid = mmgrid.SingleMatGrid(mesh)
        grid.generate()
        grid.create_tags()

    elif gen_mmgrid:
        # Do ray tracing to create macromaterials, if enabled.
        print "Will use {0} rays per mesh row".format(mmgrid_rays)

        grid = mmgrid.mmGrid( mesh )
        grid.generate( mmgrid_rays, False )
        grid.create_tags()

    else:
        # Materials should already exist, e.g. via mmgrid
        return


def save_mesh(mesh, datafile, visfile=None):
    """Save changes made to the mesh object. Optionally creates .vtk file.
    
    Parameters
    ----------
    mesh : ScdMesh or iMesh.Mesh()
        Mesh object to be saved.
    datafile : string
        Filename/path for mesh file to be saved to.
    visfile : string
        Filename/path for .vtk file to be created. File is not created if
        visfile=None.
    
    """
    if isinstance(mesh, ScdMesh):
        print "Saving fluxes and materials to `{0}'".format(datafile)
        mesh.imesh.save(datafile)
    else:
        mesh.save(datafile)

    if visfile != None:
        print "Producing visualization file `{0}' with mbconvert".format(
                visfile)
        os.system('mbconvert {0} {1}'.format(datafile, visfile))


def gen_alara_main_input(mesh, alara_geom, config, alara_snippet=None):
    """Create ALARA input file

    Parameters
    ----------
    mesh : ScdMesh or iMesh.Mesh()
        Mesh object tagged with material/volume information to be written.
    alara_geom : string
        Filename/path for ALARA input file.
    config : ConfigParser.ConfigParser object
        Config parser to find optional material dict in.
    alara_snippet : string
        Filename/path for snippet file containing non-geom/material input.
    """
    print "Writing alara problem file `{0}'".format(alara_geom)
    mdict = get_material_dict(config)
    write_alara_geom(alara_geom, mesh, mdict)

    if alara_snippet:
        print "Appending alara snippet file `{0}' to problem file".format( \
                alara_snippet)
        with open(alara_geom,'a') as f:
            with open(alara_snippet,'r') as snip:
                f.write(snip.read())


def gen_alara_fluxin(mesh, fluxin):
    """Create the ALARA fluxin file
    
    Parameters
    ----------
    mesh : ScdMesh or iMesh.Mesh()
        Mesh object tagged with flux information to be written.
    fluxin : string
        Filename/path for ALARA fluxin file.
    """
    print "Writing alara fluxin file `{0}'".format(fluxin)
    write_alara_fluxin(fluxin, mesh, backwards=True)


if __name__ == "__main__":

    cfgfile = 'r2s.cfg'
    if len(sys.argv) > 1:
        cfgfile = sys.argv[1]

    config = ConfigParser.SafeConfigParser()
    config.read(cfgfile)

    try:
        # Read config file
        (meshtal_file, mcnp_geom, alara_snippet, visfile, datafile, \
            fluxin, alara_geom, alara_matdict) = load_config_files(config)

        (gen_mmgrid, mmgrid_rays, opt_step2setup, isscd) = \
                load_config_params(config)

        # Do step 1
        mesh = handle_meshtal(meshtal_file, gen_mmgrid, datafile, isscd)

        handle_mesh_materials( \
                mesh, mcnp_geom, gen_mmgrid, mmgrid_rays, isscd)

        save_mesh(mesh, datafile, visfile)

        gen_alara_main_input(mesh, alara_geom, config, alara_snippet)

        gen_alara_fluxin(mesh, fluxin)

    except R2S_CFG_Error as e:
        print "ERROR: {0}\n(in r2s.cfg file {1})".format( e, \
                os.path.abspath(cfgfile) )

    print "It should now be possible to run `alara {0}'".format(alara_geom)
    print "and proceed to step 2 of the workflow."
