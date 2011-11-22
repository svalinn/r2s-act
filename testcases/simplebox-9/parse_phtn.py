#!/usr/bin/env python

# This is an example script that reads in a phtn_src file to the object variable
#  'thing', and then calls several methods, culminating in a file named "phtn_sdef"
#  being produced.

# Steps:
# -create object
# -call object's read method
# -call get_isotope method to get the total entries for the 7th mesh cell
# -look at a list of unformatted cooling times.
# -call isotope_source_strengths method which generates a list of total source
#   strengths for each mesh cell
# -call gen_sdef_probabilities which generates an sdef carde with required SI,
#   SP, DS and TR cards

import obj_phtn_src as psr

thing = psr.PhtnSrcReader("phtn_src")

thing.read()

# -1 specifies values for all mesh cells; second parameter is isotope identifier,
# and defaults to "TOTAL"
thing.get_isotope()#, "na-25") 

print "Cooling steps are:\n", thing.coolingSteps, "\n"

thing.isotope_source_strengths(0) #parameter is cooling step

# Method's argument is a 3x3 list for x y z, with each sub list of form
#  [min, max, mesh intervals]. Unused second parameter is output file name.
# Produces file 'phtn_sdef' which can be copied into an MCNP deck by hand.
thing.gen_sdef_probabilities([[0,10,9],[0,10,9],[0,10,9]])


#print len(thing.meshstrengths)
#print thing.meshstrengths
