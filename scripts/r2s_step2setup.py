#! /usr/bin/env python

import sys
import os
import re
import ConfigParser
#import datetime
from time import gmtime, strftime
from shutil import copy
from r2s_setup import get_input_file #as r2s_input_file from r2s_setup import FileMissingError 
cfgfile = 'r2s.cfg'
if len(sys.argv) > 1:
    cfgfile = sys.argv[1]

config = ConfigParser.SafeConfigParser()
config.read(cfgfile)

# Get isotopes and cooling times

# Filenames
mcnp_p_problem = None
if config.has_option('r2s-files','photon_mcnp_input'):
    mcnp_n_problem = get_input_file(config,'neutron_mcnp_input')
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

if opt_isotope != '':
    iso_list = [x.strip() for x in opt_isotope.split(',')]
    print "Isotopes found:", iso_list
if opt_cooling != '':
    cool_list = [x.strip() for x in opt_cooling.split(',')]
    print "Cooling times found:", cool_list


#thisdir = os.path.realpath(__file__)
thisdir = os.curdir

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

            target.write(changed)    

    oldfile = os.path.join(thisdir, mcnp_n_problem)
    newfile = os.path.join(folder, mcnp_n_problem)

    # Copy mcnp photon transport input to each directory
    # (Modify title card?)
    with open(oldfile, 'r') as source:
        with open(newfile, 'w') as target:
            # Write the title card
            target.write(source.readline())
            # Add note after title card
            target.write("Input created for isotope {0} and cooling step {1}" \
                    " at {2}\n".format(iso,time, \
                        strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime()) ) )
                        #strftime("%Y-%m-%d %H:%M", datetime.datetime.now) ) )
                        #datetime.datetime.now.strftime("%Y-%m-%d %H:%M")))

            #Alternately, append above note after any comment lines that follow
            # the title card
            #  line = source.readline()
            #  # write any comment lines
            #  while line.split()[0] in 'cC':
            #      target.write(line)
            #  # insert 
            #  target.write("Input created for isotope {0} and cooling step {1}" \
            #          "\n".format(iso,time))
            #  target.write(line)
            
            # write the rest of the MCNP input file.

            target.write(source.read())


# Create shell script in parent directory to run all r2s_step2.py cases.

