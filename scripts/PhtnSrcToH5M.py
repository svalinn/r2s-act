#!/usr/bin/env python

from optparse import OptionParser
from itaps import iBase,iMesh


def read_to_h5m(inputfile, meshfile, isotope="TOTAL", coolingstep=0, retag=False):
    """Read in a phtn_src file and tag the contents to a moab mesh.
    
    ACTION: Method reads in a phtn_src file line by line, looking for
    a specific isotope at a specific cooling step
    RECEIVES: input file (ALARA phtn_src style), mesh file to write to,
    isotope identifier, cooling step number (0'th is 'shutdown')
    OR cooling step name, whether to retag existing tags in mesh
    """
    
    fr = open(inputfile, 'r')
    line = ' '

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
            #   first voxel)
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

    # pyTaps stuff starts here
    mesh = iMesh.Mesh()
    mesh.load(meshfile)

    # We grab the list of mesh entity objects
    voxels = mesh.getEntities(iBase.Type.region)

    # We create a list of tag objects to use while parsing phtn_src
    tagList = []
    for grp in xrange(len(lineparts) - 2 ): # group tags = parts in the line - 2
        try:
            # If tags are new to file... create tag
            tagList.append(mesh.createTag( \
                    "phtn_src_group_{0:03d}".format(grp+1), 1, float))
        except iBase.TagAlreadyExistsError:
            # Else if the tags already exist...
            if retag:
                # Get existing tag
                # We will overwrite tag values that already exist
                tagList.append(mesh.getTagHandle( \
                        "phtn_src_group_{0:03d}".format(grp+1)))
            else:
                # Or print error if retagging was not specified.
                print "ERROR: The tag phtn_src_group_{0:03d} already exists " \
                        "in the file {1}\nUse -r option to overwrite tags." \
                        "".format(grp+1, inputfile)
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
                tag = mesh.getTagHandle( \
                        "phtn_src_group_"+"{0:03d}".format(grp+1))
                # Normally an exception is thrown by above line
                mesh.destroyTag(tag,force=True)
                grp += 1
            except iBase.TagNotFoundError:
                grp = 0 # breaks the while loop

    mesh.save(meshfile)

    print "The MOAB file '{0}' is now tagged with the photon source strengths" \
            " for isotope '{1}' at cooling step '{2}'".format(meshfile, \
            isotope, coolingstep)

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
            default="TOTAL", help="The isotope string identifier or TOTAL. "\
            "Default: %default")
    parser.add_option("-c","--coolingstep",action="store",dest="coolingstep", \
            default=0, help="The cooling step number or string identifier. " \
            "(0 is first cooling step)  Default: %default")
    parser.add_option("-r","--retag",action="store_true",dest="retag", \
            default=False,help="Option enables retagging of .h5m meshes, e.g. " \
            "with the -H option. Default: %default")

    (options, args) = parser.parse_args()

    read_to_h5m( \
                options.phtnsrcfile, options.meshfile, options.isotope, \
                options.coolingstep, options.retag)

    return 1


# Handles module being called as a script.
if __name__=='__main__':
    main()

