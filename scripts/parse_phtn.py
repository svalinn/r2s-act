#!/usr/bin/env python

# This is an example script that reads in a phtn_src file to the object variable
#  'thing', and then calls several methods, culminating in a file named "phtn_sdef"
#  being produced.

################
# INSTRUCTIONS:
# -Generate your phtn_src file, and point to it when creating the object 'thing'
# -If interested in a specific isotope, change thing.get_isotope()'s argument
# -Define the meshing limits and number of coarse meshes for x, y, z in the line
#  'thing.gen_sdef_probabilities....'
################

# General summary of steps file takes:
# -create object
# -call object's read method
# -call get_isotope method to get the total entries for the 7th mesh cell
# -look at a list of unformatted cooling times.
# -call isotope_source_strengths method which generates a list of total source
#   strengths for each mesh cell
# -call gen_sdef_probabilities which generates an sdef carde with required SI,
#   SP, DS and TR cards

import obj_phtn_src as psr

thing = psr.PhtnSrcReader("../testcases/simplebox-3/phtn_src")

thing.read()

# Optional 1st parameter is isotope identifier, and defaults to "TOTAL"
thing.get_isotope()
# Alternate example, getting source strengths for na-25 instead of totals.
#thing.get_isotope("na-25") 

print "Cooling steps are:\n", thing.coolingSteps, "\n"

thing.isotope_source_strengths(0) #parameter is cooling step

# Method's argument is a 3x3 list for x y z, with each sub list of form
#  [min, max, mesh intervals]. Unused second parameter is output file name.
# Produces file 'phtn_sdef' which can be copied into an MCNP deck by hand.
thing.gen_sdef_probabilities([[0,10,3],[0,10,3],[0,10,3]])


#print len(thing.meshstrengths)
#print thing.meshstrengths
