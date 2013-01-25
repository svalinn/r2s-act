#! /usr/bin/env python

#

import sys
import os
import re
import ConfigParser
from time import gmtime, strftime
from shutil import copy
from r2s_setup import get_input_file


class R2S_CFG_Error(Exception):
    pass

def load_configs(cfgfile):
    """Read needed information from .cfg file.

    Parameters
    ----------
    cfgfile - string
        File path to an r2s.cfg file

    Returns
    -------
    A list of the following values taken from the .cfg file:
    mcnp_n_problem, mcnp_p_problem, datafile, phtn_src, opt_isotope, opt_cooling
    """
    config = ConfigParser.SafeConfigParser()
    config.read(cfgfile)

    # Get isotopes and cooling times

    # Filenames
    if config.has_section('r2s-files'):
        mcnp_n_problem = config.get('r2s-files','neutron_mcnp_input')
        mcnp_p_problem = config.get('r2s-files','photon_mcnp_input')
        datafile = config.get('r2s-files','step1_datafile')
        phtn_src = config.get('r2s-files', 'alara_phtn_src')
    else:
        raise R2S_CFG_Error("'r2s-files' section required in your config file.")

    if config.has_section('r2s-params'):
        opt_isotope = config.get('r2s-params','photon_isotope')
        opt_cooling = config.get('r2s-params','photon_cooling')
    else:
        raise R2S_CFG_Error("'r2s-params' section required in your config file.")

    return (mcnp_n_problem, mcnp_p_problem, datafile, phtn_src, opt_isotope, \
            opt_cooling)


def gen_iso_cool_lists(opt_isotope, opt_cooling, phtn_src):
    """Create list of isotope and cooling step combinations and foldernames.

    Parameters
    ----------
    opt_isotope : string
        The isotope identifier as listed in phtn_src file
    opt_cooling : int or string
        The cooling step, either as a numeric index (from 0) or a string
        identifier as listed in phtn_src file

    Returns
    -------
    iso_list : list of strings
        List of the isotope strings
    cool_list : list of strings
        List of the cooling step strings

    Notes
    -----
    Checks phtn_src file if numeric cooling step values are given and grabs the
    corresponding string values.
    """
    #defaults
    iso_list = ['TOTAL']
    cool_list = ['shutdown']

    # Parse isotopes
    iso_list = [x.strip() for x in opt_isotope.split(',')]
    print "Isotopes given:", iso_list
    # Parse cooling times
    cool_list = [x.strip() for x in opt_cooling.split(',')]
    print "Cooling times given:", cool_list

    # If given list of integers, get the cooling steps from phtn_src file
    try:
        list_cool_needed = [int(time) for time in cool_list]
        list_cool_needed.sort()
        with open(phtn_src, 'r') as fr:
            linecnt = -1
            isotope = ""
            firstisotope = ""
            for list_idx, time_idx in enumerate(list_cool_needed):
                while linecnt < time_idx:
                    line = fr.readline()
                    if linecnt == -1:
                        firstisotope = line.split("\t")[0].strip()
                    isotope = line.split("\t")[0].strip()
                    if isotope != firstisotope:
                        raise R2S_CFG_Error("Fewer than {0} cooling steps are in " \
                                "{1}".format(time_idx, phtn_src))
                    linecnt += 1
                # replace integers in cool_list with cooling step names
                cool_list[list_idx] = (line.split("\t")[1]).strip()
    except ValueError:
        if isinstance(cool_list[0], basestring):
            # Get all cooling steps in phtn_src
            with open(phtn_src, 'r') as fr:
                lineparts = fr.readline().split("\t")
                all_cool_list = list()
                isotope = lineparts[0]
                while isotope == lineparts[0]:
                    all_cool_list.append(lineparts[1].strip())
                    lineparts = fr.readline().split("\t")
                
            # If opt_cooling starts off with 'all'
            if cool_list[0].lower() == 'all':
                cool_list = all_cool_list
                print "In {0}, 'all' cooling times corresponds with: ".format( \
                        phtn_src) + ", ".join(cool_list)
            else:  # Else check that all supplied cooling times are valid
                for cooling_time in cool_list:
                    if cooling_time not in all_cool_list:
                        raise R2S_CFG_Error("Cooling time {0} is not found in {1}" \
                                "".format(cooling_time, phtn_src))
        else:
            raise R2S_CFG_Error("'photon_cooling' in r2s.cfg file appears to " \
                    "have a mix of strings and integer values.")

    return iso_list, cool_list


def make_folders(iso_list, cool_list):
    """Create directories for each case with naming isotope_cooling_time 
    
    Example naming: mn-56_1_d or TOTAL_5_h

    Parameters
    ----------
    iso_list : list of strings
        List of the isotope strings
    cool_list : list of strings
        List of the cooling step strings

    Returns
    -------
    path_list : list of strings
        List of the file paths of the created folders.
    """
    path_list = list()
    thisdir = os.curdir
    for iso in iso_list:
        for time in cool_list:
            thispath = "{0}_{1}".format(iso, time.replace(' ', '_'))
            path_list.append([os.path.join(thisdir, thispath), iso, time])
            try:
                os.mkdir(os.path.join(thisdir, thispath))
            except OSError:
                print "Folder {0} already exists.".format( \
                        os.path.join(thisdir, thispath))

    return path_list


def create_new_files(path_list, datafile, cfgfile, mcnp_n_problem, mcnp_p_problem, phtn_src):
    """Creates files for step 2 calculation for each combination of cooling time
    and isotope.

    Parameters
    ----------
    path_list : List of lists of strings
        Each sub list is: [filepath string, isotope string, cooling time string]
    datafile : string
        Path to .h5m structured mesh file
    cfgfile : string
        Path to r2s.cfg config file
    mcnp_n_problem : string
        Path to MCNP input for neutron transport
    mcnp_p_problem : string
        Path to MCNP input for photon transport
    phtn_src : string
        Path to phtn_src file
    """
    thisdir = os.curdir

    # Modify/copy files for each directory
    for folder, iso, time in path_list:
        print folder, iso, time

        # Copy .h5m datafile
        copy(os.path.join(thisdir, datafile), folder)

        oldfile = os.path.join(thisdir, cfgfile)
        newfile = os.path.join(thisdir, folder, os.path.basename(cfgfile))

        _copy_and_mod_r2scfg(oldfile, newfile, iso, time, mcnp_n_problem, phtn_src)

        oldfile = os.path.join(thisdir, os.path.basename(mcnp_p_problem))
        newfile = os.path.join(thisdir, folder, os.path.basename(mcnp_p_problem))
        _copy_and_mod_mcnpinp(oldfile, newfile, iso, time)


def _copy_and_mod_r2scfg(oldfile, newfile, iso, time, mcnp_n_problem, phtn_src):
    """Open r2s.cfg and copy contents with replacements to the new r2s.cfg
 
    Parameters
    ----------
    oldfile : string
        Path to existing r2s.cfg file
    newfile : string
        Path to new copy of r2s.cfg file
    iso : string
        Isotope name
    time : string
        Cooling time string
    mcnp_n_problem : string
        Path to existing MCNP input for neutron transport
    phtn_src : string
        Path to phtn_src file output by ALARA
    """
    with open(oldfile, 'r') as source:
        with open(newfile, 'w') as target:
            data = source.read()

            # Copy r2s.cfg to each new directory, and modify each to point to
            #  files (e.g. phtn_src, .h5m files) to parent directory, as well
            #  as set correct isotope/cooling time
            changed = re.sub('photon_isotope =.*?\n',
                    'photon_isotope = {0}\n'.format(iso),
                    data)
            changed = re.sub('photon_cooling =.*?\n',
                    'photon_cooling = {0}\n'.format(time),
                    changed)

            changed = re.sub('neutron_mcnp_input =.*?\n',
                    'neutron_mcnp_input = ../{0}\n'.format(mcnp_n_problem),
                    changed)
            changed = re.sub('alara_phtn_src =.*?\n',
                    'alara_phtn_src = ../{0}\n'.format(phtn_src),
                    changed)

            target.write("### Modified file generated for isotope {0} and " \
                    "cooling step {1} at {2}\n".format(iso, time, \
                            strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()) ))
            target.write(changed)    


def _copy_and_mod_mcnpinp(oldfile, newfile, iso, time):
    """Copy mcnp photon transport input to each directory

    TBD: Modify title card?

    Parameters
    ----------
    oldfile : string
        Path to MCNP input for photon transport
    newfile : string
        Path to new copy of MCNP input for photon transport
    iso : string
        Isotope name
    time : string
        Cooling time string
    """
    try:
        with open(oldfile, 'r') as source:
            with open(newfile, 'w') as target:
                # Write the title card
                target.write(source.readline())
                # Add note after title card with timestamp
                target.write("c $ Input generated for isotope {0} and " \
                        "cooling step {1} at {2}\n".format(iso, time, \
                            strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()) ))

                #Alternately, append above note after any comment lines that # follow the title card
                #  line = source.readline()
                #  # write any comment lines
                #  while line.split()[0] in 'cC':
                #      target.write(line)
                #  # insert 
                #  target.write("Input created for isotope {0} and cooling " \
                #          "step {1}\n".format(iso,time))
                #  target.write(line)
                
                # write the rest of the MCNP input file.
                target.write(source.read())

    except IOError:
        print " WARNING: {0} doesn't exist. MCNP photon input was not copied." \
                "".format(oldfile)


def gen_run_script(path_list):
    """Create shell script in parent directory to run all r2s_step2 cases
    
    Parameters
    ----------
    path_list : list of strings
        List of the file paths of the created folders.
    """
    
    thisdir = os.curdir
    scriptdir = os.path.dirname(os.path.abspath(__file__))
    scriptpath = os.path.join(scriptdir, "r2s_step2.py")
    with open(os.path.join(thisdir, "r2s_run_all_step2.sh"), 'w') as fw:
        #fw.write("#! /usr/env/bin python\n\n")
        fw.write("rm phtn_src_totals\n")
        for path in path_list:
            fw.write("cd {0}\n".format(path))
            fw.write("rm phtn_src_total\n")
            fw.write(scriptpath + '\n')
            fw.write("cat phtn_src_total >> ../phtn_src_totals\n")
            fw.write("cd ..\n")
        
        fw.write("echo Total photon strength in problem [phtn/s]:\n")
        fw.write("echo Note: these numbers are also in file 'phtn_src_totals'\n")
        fw.write("cat phtn_src_totals\n")

    os.system("chmod +x {0}".format( \
            os.path.join(thisdir, "r2s_run_all_step2.sh")))


if __name__ == "__main__":
    
    cfgfile = 'r2s.cfg'
    if len(sys.argv) > 1:
        cfgfile = sys.argv[1]

    try:
        (mcnp_n_problem, mcnp_p_problem, datafile, phtn_src, opt_isotope, \
                opt_cooling) = load_configs(cfgfile)
        iso_list, cool_list = gen_iso_cool_lists(opt_isotope, opt_cooling, \
                phtn_src)
        path_list = make_folders(iso_list, cool_list)
        create_new_files(path_list, datafile, cfgfile, mcnp_n_problem, \
                mcnp_p_problem, phtn_src)
        gen_run_script([x[0] for x in path_list])

    except Exception as e:
        print "ERROR: {0}\n(in r2s.cfg file {1})".format( e, \
                os.path.abspath(cfgfile) )
