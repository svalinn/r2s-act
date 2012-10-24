#! /usr/bin/env python

#

import sys
import os
import re
import ConfigParser
from time import gmtime, strftime
from shutil import copy
from r2s_setup import get_input_file
cfgfile = 'r2s.cfg'
if len(sys.argv) > 1:
    cfgfile = sys.argv[1]

config = ConfigParser.SafeConfigParser()
config.read(cfgfile)

# Get isotopes and cooling times

# Filenames
mcnp_p_problem = None
if config.has_option('r2s-files','photon_mcnp_input'):
    #mcnp_n_problem = get_input_file(config,'neutron_mcnp_input')
    mcnp_n_problem = config.get('r2s-files','neutron_mcnp_input')
    mcnp_p_problem = config.get('r2s-files','photon_mcnp_input')

datafile = config.get('r2s-files','step1_datafile')
phtn_src = get_input_file(config, 'alara_phtn_src')

#defaults
iso_list = ['TOTAL']
cool_list = ['shutdown', '1 d']
path_list = list()

if config.has_section('r2s-params'):
    opt_isotope = config.get('r2s-params','photon_isotope')
    opt_cooling = config.get('r2s-params','photon_cooling')
else:
    sys.exit("ERROR: r2s-params section required in your config file " \
            "({0})".format(cfgfile))

thisdir = os.curdir


# Parse isotopes
iso_list = [x.strip() for x in opt_isotope.split(',')]
print "Isotopes found:", iso_list
# Parse cooling times
cool_list = [x.strip() for x in opt_cooling.split(',')]
print "Cooling times found:", cool_list

list_cool_needed = list()
for i, time in enumerate(cool_list):
    try:
        list_cool_needed.append(int(time))
    except ValueError:
        break # We assume all entries are not plain integers

# If given list of integers, get the cooling steps from phtn_src file
if len(list_cool_needed) > 0:
    list_cool_needed.sort()
    with open(phtn_src, 'r') as fr:
        cnt = -1
        for i, t in enumerate(list_cool_needed):
            while cnt < t:
                line = fr.readline()
                cnt += 1
            # replace integers in cool_list with cooling step names
            cool_list[i] = (line.split("\t")[1]).strip()


# Create directories for each case with proposed naming isotope_cooling_time, 
#  e.g. mn-56_1_d or TOTAL_5_h
for iso in iso_list:
    for time in cool_list:
        thispath = "{0}_{1}".format(iso, time.replace(' ', '_'))
        path_list.append([os.path.join(thisdir, thispath), iso, time])
        try:
            os.mkdir(os.path.join(thisdir, thispath))
        except OSError:
            print "Folder {0} already exists.".format(os.path.join(thisdir, thispath))

# Modify/copy files for each directory
for folder, iso, time in path_list:
    print folder, iso, time

    # Copy .h5m datafile
    copy(os.path.join(thisdir, datafile), folder)

    oldfile = os.path.join(thisdir, cfgfile)
    newfile = os.path.join(folder, cfgfile )

    # open r2s.cfg and copy contents with replacements to the new r2s.cfg
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
                    data)

            changed = re.sub('neutron_mcnp_input =.*?\n',
                    'neutron_mcnp_input = ../{0}\n'.format(mcnp_n_problem),
                    data)
            changed = re.sub('alara_phtn_src =.*?\n',
                    'alara_phtn_src = ../{0}\n'.format(phtn_src),
                    data)

            target.write("### Modified file generated for isotope {0} and " \
                    "cooling step {1} at {2}\n".format(iso,time, \
                            strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()) ))
            target.write(changed)    


    # Copy mcnp photon transport input to each directory
    # (Modify title card?)
    oldfile = os.path.join(thisdir, mcnp_p_problem)
    newfile = os.path.join(folder, mcnp_p_problem)
    try:
        with open(oldfile, 'r') as source:
            with open(newfile, 'w') as target:
                # Write the title card
                target.write(source.readline())
                # Add note after title card with timestamp
                target.write("c $ Input generated for isotope {0} and " \
                        "cooling step {1} at {2}\n".format(iso,time, \
                            strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()) ))

                #Alternately, append above note after any comment lines that 
                # follow the title card
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
        print " WARNING, {0} doesn't exist. MCNP photon input was not copied." \
                "".format(oldfile)


# Create shell script in parent directory to run all r2s_step2.py cases.

