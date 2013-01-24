#! /usr/bin/env python

import sys
import ConfigParser
import os.path

from r2s.io import read_alara_phtn, write_gammas
from r2s import mcnp_n2p
from r2s.scdmesh import ScdMesh, ScdMeshError
from itaps import iMesh, iMeshExtensions
from r2s_setup import get_input_file, FileMissingError


##################
# Read config file
def load_config_files(config):
    """Read in config file information for files

    Parameters
    ----------
    config : ConfigParser.ConfigParser object

    Returns
    -------
    A list of the following values taken from the .cfg file:
    datafile, phtn_src, mcnp_n_problem, mcnp_p_problem
    """

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
        
    return (datafile, phtn_src, mcnp_n_problem, mcnp_p_problem)

def load_config_params(config):
    """Read in config file information for parameters

    Parameters
    ----------
    config : ConfigParser.ConfigParser object

    Returns
    -------
    A list of the following values taken from the .cfg file:
    opt_isotope, opt_cooling, opt_sampling, opt_ergs, opt_bias, 
    opt_cumulative, opt_phtnfmesh, resampling, uni_resamp_all
    """

    # This list stores (1) parameter names as listed in r2s.cfg; 
    # (2) their defaults; (3) which 'get' function to use for the parameter
    param_guide = [ #parameter  #default #get function
            [ 'photon_isotope', "TOTAL", config.get],
            [ 'photon_cooling', 0,       config.get],
            [ 'sampling'      , 'v',     config.get],
            [ 'custom_ergbins', False,   config.getboolean],
            [ 'photon_bias'   , False,   config.getboolean],
            [ 'cumulative'    , False,   config.getboolean],
            [ 'add_fmesh_card', True,    config.getboolean],
            [ 'resampling'    , False,   config.getboolean],
            [ 'uni_resamp_all', False,   config.getboolean]
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

    (opt_isotope, opt_cooling, opt_sampling, opt_ergs, opt_bias, \
            opt_cumulative, opt_phtnfmesh, resampling, uni_resamp_all \
            ) = param_list

    # Check for multiple comma delimited values; raise error if this is found
    if len(opt_isotope.split(",")) != 1:
        raise Exception ("r2s.cfg entry 'photon_isotope' contains " \
                "multiple values. r2s_step2.py only uses a single value.")

    if len(opt_cooling.split(",")) != 1:
        raise Exception ("r2s.cfg entry 'photon_cooling' contains " \
                "multiple values. r2s_step2.py only uses a single value.")

    return (opt_isotope, opt_cooling, opt_sampling, opt_ergs, opt_bias, opt_cumulative, opt_phtnfmesh, resampling, uni_resamp_all)


###########################
# Do step 2
def handle_phtn_data(datafile, phtn_src, opt_isotope, opt_cooling,  \
        opt_sampling, opt_bias, opt_cumulative, cust_ergbins, 
        resample, uni_resamp_all, gammas="gammas"):
    """Loads phtn_src data, tags this to mesh, and generates 'gammas' file.

    Parameters
    ----------
    datafile : string
        Path to structured mesh file (e.g. .h5m file)
    phtn_src : string
        Path to phtn_src file
    opt_isotope : string
        The isotope identifier as listed in phtn_src file
    opt_cooling : int or string
        The cooling step, either as a numeric index (from 0) or a string
        identifier as listed in phtn_src file
    opt_sampling : ['v', 'u']
        Type of sampling to generate the 'gammas' file for; v=voxel; u=uniform
    opt_bias : boolean
        If true, look for bias values on the mesh and include them in 'gammas'
    opt_cumulative : boolean
        If true, write energy bins' relative probabilities cumulatively
    cust_ergbins : boolean
        If true, look for custom energy bins on the mesh and include them in
        'gammas'
    resample : boolean
        If true, 'r' flag is added to gammas, and resampling of particles 
        starting in void regions of voxels is enabled.
    uni_resamp_all : boolean
        If true, 'a' flag is added to gammas, and particles starting in void
        regions of voxels, during uniform sampling, are resampled over the
        entire problem, rather than resampling just the voxel.  This has the
        potential to result in an unfair game.
    gammas : string (optional)
        File name for 'gammas' file. Defaults to 'gammas'.

    Returns
    -------
    smesh : ScdMesh object
        Structured mesh object
    """
    print "Loading step one data file '{0}'".format(datafile)
    smesh = ScdMesh.fromFile(datafile)

    # Tagging mesh
    print "Reading ALARA photon source '{0}'".format(phtn_src)
    read_alara_phtn.read_to_h5m(phtn_src, smesh, isotope=opt_isotope, \
            coolingstep=opt_cooling, retag=True, totals=True)

    print "Saving photon source information to '{0}'".format(datafile)
    smesh.imesh.save(datafile)

    with open(phtn_src, 'r') as fr:
        try:
            coolingstepstring = read_alara_phtn.get_cooling_step_name( \
                opt_cooling, fr)[0]
        except ValueError:
            coolingstepstring = opt_cooling

    print "Writing gammas file"
    write_gammas.gen_gammas_file_from_h5m(smesh, outfile=gammas, \
            sampling=opt_sampling, do_bias=opt_bias, \
            cumulative=opt_cumulative, cust_ergbins=cust_ergbins, \
            coolingstep=coolingstepstring, isotope=opt_isotope, \
            resample=resample, uni_resamp_all=uni_resamp_all)

    return smesh


def gen_mcnp_p(smesh, mcnp_p_problem, mcnp_n_problem, opt_phtnfmesh):
    """Create photon MCNP input file from neutron input if it doesn't exist
    already

    Parameters
    ----------
    smesh : ScdMesh object
        Structured mesh object
    mcnp_p_problem : string
        Path to MCNP input for photon transport
    mcnp_n_problem : string
        Path to MCNP input for neutron transport
    opt_phtnfmesh : boolean
        If true, append an FMESH card for photons that matches the mesh layout
        of the structured mesh object being used
    """
    if mcnp_p_problem:

        if os.path.exists(mcnp_p_problem):
            print "MCNP photon transport input file '{0}' already exists " \
                    "and will not be recreated.".format(mcnp_p_problem)

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

    return


if __name__ == "__main__":

    cfgfile = 'r2s.cfg'
    if len(sys.argv) > 1:
        cfgfile = sys.argv[1]

    config = ConfigParser.SafeConfigParser()
    config.read(cfgfile)

    try:
        (datafile, phtn_src, mcnp_n_problem, mcnp_p_problem) = load_config_files(config)

        (opt_isotope, opt_cooling, opt_sampling, opt_ergs, opt_bias, opt_cumulative, opt_phtnfmesh, resampling, uni_resamp_all) = load_config_params(config)

        smesh = handle_phtn_data(datafile, phtn_src, opt_isotope, opt_cooling, \
                opt_sampling, opt_bias, opt_cumulative, opt_ergs, resampling, \
                uni_resamp_all)

        gen_mcnp_p(smesh, mcnp_p_problem, mcnp_n_problem, opt_phtnfmesh)

    except Exception as e:
        print "ERROR: {0}\n(in r2s.cfg file {1})".format( e, \
                os.path.abspath(cfgfile) )

    print "" # Empty line to separate output from multiple runs of this script
