#!/usr/bin/env python

"""Module includes methods which find the lines in a 'phtn_src' file from ALARA
that match a specified isotope and cooling time, and tags the photon source
information to a structured mesh.
"""

from optparse import OptionParser
from itaps import iBase,iMesh
from r2s.scdmesh import ScdMesh, ScdMeshError


def read_to_h5m(inputfile, sm, isotope="TOTAL", coolingstep=0, \
        retag=False, totals=False):
    """Read in a phtn_src file and tag the contents to a structured mesh.
    
    Method reads in a phtn_src file line by line, looking for
    a specific isotope at a specific cooling step, and repeats for each voxel.
    Method tags the structured mesh with the photon source information,
    and then saves the mesh.

    Parameters
    ----------
    inputfile : string
        Path to an ALARA-style 'phtn_src' file
    sm : scdmesh.ScdMesh
        Structured mesh object to tag,
    isotope : string
        Isotope to read data for from 'phtn_src' file 
    coolingstep : int or string
        String cooling step name, or number for index (0'th is 'shutdown')
    retag : boolean
        Whether to retag existing tags in mesh
    totals : boolean
        Whether to tag the total photon source strength for each voxel
    """
    
    fr = open(inputfile, 'r')

    # First, we determine the coolingstep string to look for
    try: # get_cooling_step_name() can throw a few exceptions
        (coolingstep, numergbins) = get_cooling_step_name(coolingstep, fr)

    except ValueError:
        # The specified cooling step is a string...
        # should catch this exception, and continue on - coolingstep is
        # presumed to be a valid string
        lineparts = fr.readline().split('\t')
        numergbins = len(lineparts) - 2
    
    except Exception as e:
        # File reading problem, e.g. malformed phtn_src file
        # We lack an actual example of this happening...
        print e
        return 0

    print "The cooling step being read is '{0}'".format(coolingstep)

    # structured mesh stuff starts here

    # We grab the list of structured mesh entity objects
    voxels = list(sm.iterateHex('xyz'))

    # We create a list of tag objects ('tagList') to use while parsing phtn_src
    tagList = []
    for grp in xrange(numergbins): # group tags = parts in the line - 2
        try:
            # If tags are new to file... create tag
            tagList.append(sm.imesh.createTag( \
                    "phtn_src_group_{0:03d}".format(grp+1), 1, float))
        except iBase.TagAlreadyExistsError:
            # Else if the tags already exist...
            if retag:
                # Get existing tag
                # We will overwrite tag values that already exist
                tagList.append(sm.imesh.getTagHandle( \
                        "phtn_src_group_{0:03d}".format(grp+1)))
            else:
                # Or print error if retagging was not specified.
                print "ERROR: The tag phtn_src_group_{0:03d} already exists " \
                        "in the structured mesh." \
                        "\nUse -r option to overwrite tags." \
                        "".format(grp+1)
                return 0

    voxelcnt = 0

    # We close and reopen the input file to read from beginning again
    fr.close()
    fr = open(inputfile, 'r')

    # Initial settings for variables that enable correct parsing when interested
    #  in specific isotopes.
    if isotope.strip() != 'TOTAL': specialIsotope = True
    else: specialIsotope = False
    writeZeros = True
    foundIsoCool = False

    # Now go through entire file, tagging mesh with info from lines
    #  that match both the isotope and coolingstep specified.
    # Because phtn_src may not include a given isotope in all voxels' entries,
    #  we do some trickery. We use TOTAL lines to keep track of voxels, and if a
    #  voxel didn't contain the isotope of interest, we tag 0's for that voxel.
    for line in fr:
        lineparts = line.split('\t')

        if lineparts[0].strip(' ') == isotope and \
                lineparts[1].strip(' ') == coolingstep:
            for grp, val, in enumerate(lineparts[2:]):
                 (tagList[grp])[voxels[voxelcnt]] = float(val)
            foundIsoCool = True
            if specialIsotope: 
                writeZeros = False # Ignores TOTAL line in this voxel
            else: voxelcnt += 1

        # Note voxels that do not have the isotope of interest, and tag
        #  them as 0.0 source strength.
        elif lineparts[0] == 'TOTAL' and \
                lineparts[1].strip(' ') == coolingstep:
            if writeZeros:
                for grp, val, in enumerate(lineparts[2:]):
                     (tagList[grp])[voxels[voxelcnt]] = 0.0
            voxelcnt += 1
            writeZeros = True # Reset to true at end of voxel's entry

    fr.close()
    
    if not foundIsoCool:
        print "ERROR: No voxels were tagged.\n\tEither cooling step '{0}' or " \
                "isotope '{1}' was probably not found in " \
                "{2}.".format(coolingstep, isotope, inputfile)
        return 0

    # We get rid of tags corresponding with higher energy groups
    if retag:
        grp = len(lineparts) - 2
        while grp:
            try:
                tag = sm.imesh.getTagHandle( \
                        "phtn_src_group_"+"{0:03d}".format(grp+1))
                # Normally an exception is thrown by above line
                sm.imesh.destroyTag(tag,force=True)
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


def get_cooling_step_name(coolingstep, fr):
    """Method determines the user-specified cooling step name in a phtn_src file

    If coolingstep is a number, we search for the corresponding line in
    the file stream 'fr', and determine the corresponding cooling step string.

    Parameters
    ----------
    coolingstep : int or string
        number for cooling step index or string for cooling step name
    fr : readable file stream

    Returns
    -------
    A 2 value tuple: (the cooling step string name, the number of
    photon energy bins used in the phtn_src file)

    Notes
    -----
    If `coolingstep` is not an integer, the calling function must catch a
    ValueError.
    """
    
    # ... if given a number, we take the nth line. Otherwise expect a ValueError
    coolingstep = int(coolingstep)

    if coolingstep < 0: 
        raise Exception("ERROR: A negative integer was given for the " \
                "cooling step")

    # With a numerical value for coolingstep, we read the first few
    #  lines in from the phtn_src file to get the cooling step string.
    # Note: coolingstep+1 makes sure we read correct number of lines
    for i in xrange(coolingstep+1):
        line = fr.readline()
        
        # Record first isotope to avoid counting through multiple isotopes
        if i == 0: firstisotope = line.split('\t')[0]
        
        if line == '':
            raise Exception("Problem reading file contents.")

        # If coolingstep is a larger number than the number of cooling steps
        #  (assessed by counting cooling steps for first isotope in 
        #   first voxel, AKA whether isotope name has changed)
        if firstisotope != line.split('\t')[0]:
            raise Exception("ERROR: Filestream does not contain {0} " \
                    "coolingsteps.".format(coolingstep) )
            return 0

    # The phtn_src file is formated with columns separated by tabs
    #  and some extraneous spaces adjacent to the tabs.  We split lines
    #  by the tabs, and remove these extraneous spaces.
    lineparts = line.split('\t')

    coolingstep = lineparts[1].strip(' ')
    numergbins = len(lineparts) - 2

    return (coolingstep, numergbins)


def tag_phtn_src_totals(sm, numergbins=-1, retag=False):
    """Method tags the total photon source strength for each voxel.

    ACTION: Method calculate the total photon source strength, and 
    if retagging is enabled or the tag does not exist, tags the structured mesh.
    RECEIVES: sm, scdmesh.ScdMesh object
    OPTIONAL: numergbins, number of energy group tags to read; retag,
    whether to overwrite an existing 'phtn_src_total' tag.
    """

    voxels = list(sm.iterateHex('xyz'))

    # Check if 'phtn_src_total' tag already exists
    try:
        # If tags are new to file... create tag
        totalPhtnSrcTag = sm.imesh.createTag( \
                "phtn_src_total", 1, float)
    except iBase.TagAlreadyExistsError:
        if not retag:
            print "ERROR: phtn_src_total tag already exists. Use the -r "\
                    "option to enable retagging."
            return 0

        else:
            totalPhtnSrcTag = sm.imesh.getTagHandle("phtn_src_total")
 
    # If not supplied, se try/except to find number of energy bins
    if not numergbins:
        for i in xrange(1,1000): #~ Arbitrary: we look for up to 1000 groups
            try:
                sm.imesh.getTagHandle("phtn_src_group_{0:03d}".format(i))
            except iBase.TagNotFoundError: 
                numergbins = i - 1
                break

    # We go voxel by voxel, calculating total photon source, and then adding
    #  these tags.
    for cnt, vox in enumerate(voxels):
        totstrength = 0.0

        #get total for the voxel
        for i in xrange(1,numergbins + 1):
            grouptag = sm.imesh.getTagHandle("phtn_src_group_{0:03d}".format(i))
            try:
                totstrength += float(grouptag[vox])
            except iBase.TagNotFoundError:
                if cnt == 0:
                    print "ERROR: phtn_src_group_# tags not found on first " \
                            "voxel. Tags are probably missing."
                else:
                    print "ERROR: phtn_src_group_# tags not found on a non-" \
                            "first voxel. phtn_src file used to create tags " \
                            "probably did not include enough voxels. This is " \
                            "a problem with ALARA and voids. Replace void " \
                            "with any zero density material to fix this."
                return 0

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
    sm = ScdMesh.fromFile(options.meshfile)

    read_to_h5m( \
                options.phtnsrcfile, sm, options.isotope, \
                options.coolingstep, options.retag, options.totals)

    sm.imesh.save(options.meshfile)

    return 1


# Handles module being called as a script.
if __name__=='__main__':
    main()

