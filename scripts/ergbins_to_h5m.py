#!/usr/bin/env python

# Module contains the read_and_tag_phtn_ergs() and destroy_erg_bins_tag() 
#  methods.  These are used for adding the photon energy group boundaries to a
#  mesh; typically when the user does not want to use the default 42 groups.

from optparse import OptionParser
from itaps import iBase,iMesh,iMeshExtensions

def read_and_tag_phtn_ergs(inputfile, mesh):
    """ Method reads a list of energies and tags them to the root set.

    ACTION: Reads a single energy from each line of 'inputfile', creating a list
    of these values. These values are tagged to the rootSet of the 'mesh'
    mesh under the tag 'PHTN_ERGS'. Method destroys the 'PHTN_ERGS' tag if it
    already exists.
    RECEIVES: 
    -inputfile is a plain text file listing one energy per line. It should have
     n+1 entries where n is the number of energy groups. Low energy first!
    -mesh is a MOAB mesh object (itaps.iMesh.Mesh)
    """

    fr = open(inputfile, 'r')
    ergs = list()

    line = fr.readline()
    while line != '': # EoF
        # We float() the values to get rid of whitespace
        try:
            ergs.append(float(line))
        except ValueError:
            print "A non-numeric value was found in '{0}'".format(inputfile)
            return 0
        line = fr.readline()
        
    fr.close()

    try:
        mesh.createTag("PHTN_ERGS", len(ergs), float)

    except iBase.TagAlreadyExistsError:
        mesh.destroyTag(mesh.getTagHandle("PHTN_ERGS"), force=True)
        phtn_ergs = mesh.createTag("PHTN_ERGS", len(ergs), float)

    # Give the values to the mesh tag on the rootSet
    phtn_ergs[mesh.rootSet] = ergs
    print "{0} energies have been added to the mesh on the PHTN_SRC tag of " \
            "the rootSet.".format(len(ergs))

    return 1


def destroy_erg_bins_tag(mesh):
    """Method removes the 'PHTN_ERGS' tag from a MOAB mesh"""

    try:
        mesh.destroyTag(mesh.getTagHandle("PHTN_ERGS"), force=True)
    except:
        print "Failed to delete 'PHTN_ERGS' tag from the MOAB mesh."
        return 0

    return 1


def main():
    """ACTION: Method defines an option parser and handles command-line
    usage of this module.
    REQUIRES: command line arguments to be passed - otherwise prints help
    information.
    RECEIVES: N/A
    """

    usage = "usage: %prog ENERGY_FILE MESH_FILE [options] \n\n" \
            "ENERGY_FILE is a list of the energy bins for each photon energy " \
            "group, with a single energy per line. MESH_FILE is the MOAB " \
            "mesh that will store the contents of ENERGY_FILE in the tag " \
            "'PHTN_ERGS'."
    parser = OptionParser(usage)

    (options, args) = parser.parse_args()

    mesh = iMesh.Mesh()
    mesh.load(args[1])

    # Call the method to read inputfile and tag mesh
    read_and_tag_phtn_ergs( args[0], mesh)

    mesh.save(args[1])

    return 1


# Handles module being called as a script.
if __name__=='__main__':
    main()
