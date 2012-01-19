#!/usr/bin/env python


from optparse import OptionParser
from itaps import iBase,iMesh


def read_to_h5m(inputfile, meshfile, isotope="TOTAL", coolingstep=0, retag=False):
    """ACTION: Method reads in a phtn_src file line by line, looking for
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

        i = 0
        while i <= coolingstep:
            line = fr.readline()
            i += 1
            if line == '':
                raise Exception("Problem reading file contents.")

        lineparts = line.split('\t')
        coolingstep = lineparts[1].strip(' ')
        print "The cooling step being read is '{0}'".format(coolingstep)

    except ValueError:
        # the specified cooling step is a string...
        pass
    
    except Exception as e:
        # File reading problem?
        print e

    # pyTaps stuff starts here
    mesh = iMesh.Mesh()
    mesh.load(meshfile)

    num_erg_groups = 42 # must be an integer

    # We grab the list of mesh entity objects
    voxels = mesh.getEntities(iBase.Type.region)

    # We create a list of tag objects to use while parsing phtn_src
    tagList = []
    for grp in range(len(lineparts) - 2 ):
        try:
            # If tags are new to file...
            tagList.append(mesh.createTag("phtn_src_group_"+str(grp+1), 1, float))
        except:
            # Else if the tags already exist
            if retag:
                # Overwrite them if they already exist
                tagList.append(mesh.getTagHandle("phtn_src_group_"+str(grp+1)))
            else:
                # Or print error if retagging was not specified.
                print "ERROR: The tag phtn_src_group_" + str(grp+1), "already exists " \
                        "in the file", inputfile, "\nNow exiting this method."
                return 0

    voxelcnt = 0

    while line != '':
        lineparts = line.split('\t')

        if lineparts[0].strip(' ') == isotope and \
                lineparts[1].strip(' ') == coolingstep:
                    for grp, val, in enumerate(lineparts[2:]):
                         (tagList[grp])[voxels[voxelcnt]] = float(val)
       

        line = fr.readline()

    fr.close()

    # We get rid of tags corresponding with higher energy groups
    if retag:
        grp = len(lineparts) - 2
        while grp:
            try:
                tag = mesh.getTagHandle("phtn_src_group_"+str(grp+1))
                mesh.destroyTag(tag,force=True)
                grp += 1
            except:
                # this should be when mesh.getTagHandle fails
                grp = 0

    mesh.save(meshfile)




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
            "Default: %default")
    parser.add_option("-r","--retag",action="store_true",dest="retag", \
            default=False,help="Option enables retagging of .h5m meshes, e.g. " \
            "with the -H option. Default: %default")

    (options, args) = parser.parse_args()

    read_to_h5m( \
                options.phtnsrcfile, options.meshfile, options.isotope, \
                options.coolingstep, options.retag)

    return 


# Handles module being called as a script.
if __name__=='__main__':
    main()

