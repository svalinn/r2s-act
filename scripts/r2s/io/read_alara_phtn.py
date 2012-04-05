#!/usr/bin/env python

from optparse import OptionParser
from itaps import iBase,iMesh
from scdmesh import ScdMesh, ScdMeshError


def read_to_h5m(inputfile, sm, isotope="TOTAL", coolingstep=0, \
        retag=False, totals=False):
    """Read in a phtn_src file and tag the contents to a structured mesh.
    
    ACTION: Method reads in a phtn_src file line by line, looking for
     a specific isotope at a specific cooling step.
    Method tags the structured mesh ('sm') with the photon source information,
     and then saves the mesh.
    RECEIVES: input file (ALARA phtn_src style), structured mesh object to tag,
     isotope identifier, cooling step number (0'th is 'shutdown')
     OR cooling step name, whether to retag existing tags in mesh, whether to
     tag the total photon source strength for each voxel
    """
    
    fr = open(inputfile, 'r')

    # First, we determine the coolingstep string to look for
    # ... if given a number, we take the nth line
    try:
        coolingstep = int(coolingstep)

        if coolingstep < 0: 
            raise Exception("ERROR: A negative integer was given for the " \
                    "cooling step")

        # With a numerical value for coolingstep, we read the first few
        #  lines in from the phtn_src file to get the cooling step string.
        i = 0
        while i <= coolingstep:
            line = fr.readline()
            
            # Record first isotope to avoid counting through multiple isotopes
            if i == 0: firstisotope = line.split('\t')[0]
            
            if line == '':
                raise Exception("Problem reading file contents.")

            # If coolingstep is a larger number than the number of cooling steps
            #  (assessed by counting coolingsteps for first isotope in 
            #   first voxel, AKA whether isotope name has changed)
            if firstisotope != line.split('\t')[0]:
                raise Exception("ERROR: File '{0}' does not contain {1} " \
                        "coolingsteps.".format(inputfile, coolingstep) )
                return 0
            
            i += 1

        # The phtn_src file is formated with columns separated by tabs
        #  and some extraneous spaces adjacent to the tabs.  We split lines
        #  by the tabs, and remove these extraneous spaces.
        lineparts = line.split('\t')

        coolingstep = lineparts[1].strip(' ')
        
        print "The cooling step being read is '{0}'".format(coolingstep)
    
    except ValueError:
        # The specified cooling step is a string...
        # should catch this exception, and continue on - coolingstep is
        # presumed to be a valid string
        line = fr.readline()
        lineparts=line.split('\t')
    
    except Exception as e:
        # File reading problem, e.g. malformed phtn_src file
        # We lack an actual example of this happening...
        print e
        return 0

    # structured mesh stuff starts here

    # We grab the list of structured mesh entity objects
    voxels = list(sm.iterateHex('xyz'))

    # We create a list of tag objects ('tagList') to use while parsing phtn_src
    tagList = []
    numergbins = len(lineparts) - 2
    for grp in xrange(numergbins): # group tags = parts in the line - 2
        try:
            # If tags are new to file... create tag
            tagList.append(sm.mesh.createTag( \
                    "phtn_src_group_{0:03d}".format(grp+1), 1, float))
        except iBase.TagAlreadyExistsError:
            # Else if the tags already exist...
            if retag:
                # Get existing tag
                # We will overwrite tag values that already exist
                tagList.append(sm.mesh.getTagHandle( \
                        "phtn_src_group_{0:03d}".format(grp+1)))
            else:
                # Or print error if retagging was not specified.
                print "ERROR: The tag phtn_src_group_{0:03d} already exists " \
                        "in the structured mesh." \
                        "\nUse -r option to overwrite tags." \
                        "".format(grp+1)
                return 0

    voxelcnt = 0

    # Now go through rest of file, tagging mesh with info from lines
    #  that match the isotope and coolingstep specified.
    while line != '':
        lineparts = line.split('\t')

        if lineparts[0].strip(' ') == isotope and \
                lineparts[1].strip(' ') == coolingstep:
                    for grp, val, in enumerate(lineparts[2:]):
                         (tagList[grp])[voxels[voxelcnt]] = float(val)
                    voxelcnt += 1

        line = fr.readline()

    fr.close()
    
    if voxelcnt == 0:
        print "ERROR: Tagging mesh cells failed.\n\t'{0}' was probably " \
                "not found in {1}.".format(isotope, inputfile)
        return 0

    # We get rid of tags corresponding with higher energy groups
    if retag:
        grp = len(lineparts) - 2
        while grp:
            try:
                tag = sm.mesh.getTagHandle( \
                        "phtn_src_group_"+"{0:03d}".format(grp+1))
                # Normally an exception is thrown by above line
                sm.mesh.destroyTag(tag,force=True)
                grp += 1
            except iBase.TagNotFoundError:
                grp = 0 # breaks the while loop

    if totals:
        if not tag_phtn_src_totals(sm, numergbins, retag):
            print "ERROR: failed to tagged the total photon source strengths."
            return 0

    print "The structured mesh is now tagged with the photon source strengths" \
            " for isotope '{0}' at cooling step '{1}'" \
            "".format(isotope, coolingstep)

    return 1


def tag_phtn_src_totals(sm, numergbins=-1, retag=False):
    """Method tags the total photon source strength for each voxel.

    ACTION: Method calculate the total photon source strength, and 
    if retagging is enabled or the tag does not exist, tags the structured mesh.
    RECEIVES: sm, a iMesh.Mesh structured mesh object
    OPTIONAL: numergbins, number of energy group tags to read; retag,
    whether to overwrite an existing 'phtn_src_total' tag.
    """

    voxels = list(sm.iterateHex('xyz'))

    # Check if 'phtn_src_total' tag already exists
    try:
        # If tags are new to file... create tag
        totalPhtnSrcTag = sm.mesh.createTag( \
                "phtn_src_total", 1, float)
    except iBase.TagAlreadyExistsError:
        if not retag:
            print "ERROR: phtn_src_total tag already exists. Use the -r "\
                    "option to enable retagging."
            return 0

        else:
            totalPhtnSrcTag = sm.mesh.getTagHandle("phtn_src_total")
 
    # If not supplied, se try/except to find number of energy bins
    if not numergbins:
        for i in xrange(1,1000): #~ Arbitrary: we look for up to 1000 groups
            try:
                sm.mesh.getTagHandle("phtn_src_group_{0:03d}".format(i))
            except iBase.TagNotFoundError: 
                numergbins = i - 1
                break

    # We go voxel by voxel, calculating total photon source, and then adding
    #  these tags.
    for vox in voxels:
        totstrength = 0.0

        #get total for the voxel
        for i in xrange(1,numergbins + 1):
            grouptag = sm.mesh.getTagHandle("phtn_src_group_{0:03d}".format(i))
            totstrength += float(grouptag[vox])

        # Add the total as a tag
        totalPhtnSrcTag[vox] = float(totstrength)

    return 1


def main():
    """ACTION: Method defines an option parser and handles command-line
    usage of this module.
    REQUIRES: command line arguments to be passed - otherwise prints help
    information.
    RECEIVES: N/A
    """

    usage = "usage: %prog [options] arg"
    parser = OptionParser(usage)
    
    # Input and mesh file names
    parser.add_option("-p","--phtn",action="store",dest="phtnsrcfile", \
            default=False, help="The photon source strengths are read from" \
            "FILENAME.")
    parser.add_option("-m","--mesh",action="store",dest="meshfile", \
            default="", help="file to write source information to, or" \
            " file name for saving a modified mesh.")
    # Other options
    parser.add_option("-i","--isotope",action="store",dest="isotope", \
            default="TOTAL", help="The isotope string identifier or 'TOTAL'. "\
            "Default: %default")
    parser.add_option("-c","--coolingstep",action="store",dest="coolingstep", \
            default=0, help="The cooling step number or string identifier. " \
            "(0 is first cooling step)  Default: %default")
    parser.add_option("-r","--retag",action="store_true",dest="retag", \
            default=False,help="Option enables retagging of .h5m meshes. " \
            "Default: %default")
    parser.add_option("-t","--totals",action="store_true",dest="totals", \
            default=False,help="Option enables adding the total photon " \
            "source strength for all energy groups as a tag for each voxel. " \
            "Default: %default")

    (options, args) = parser.parse_args()

    # Open an ScdMesh and then call read_to_h5m
    sm = ScdMesh.fromFile(iMesh.Mesh(), options.meshfile)

    read_to_h5m( \
                options.phtnsrcfile, sm, options.isotope, \
                options.coolingstep, options.retag, options.totals)

    sm.mesh.save(options.meshfile)

    return 1


# Handles module being called as a script.
if __name__=='__main__':
    main()

