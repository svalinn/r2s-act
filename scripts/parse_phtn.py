#!/usr/bin/env python

# This is an example script that reads in a phtn_src file to the object variable
# 'thing'.

# Steps:
# -create object
# -call object's read method
# -look at some of the contents of the object's variables
# -call get_total method to get the total entries for the 7th mesh cell
# -call format_total_mcnp method to formate a single total entry for MCNP input
# (e.g. when putting the source strengths into an SI card by hand)
# -call total_source_strengths method which generates a list of total source
# strengths for each mesh cell

import obj_phtn_src as psr

thing = psr.PhtnSrcReader("/filespace/people/r/relson/r2s-act-work/r2s-act/testcases/simplebox-3/phtn_src")

thing.read()

print thing.headingList
print thing.probList[0]
for x in thing.probList[2][0]:
    print x
print 'AND'
for x in thing.probList[2][1]:
    print x

thing.get_total(7)
print '\n'
thing.format_total_mcnp()
print "lahdidahhh"
print thing.total_source_strengths(0)
