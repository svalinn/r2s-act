#!/usr/bin/env python

from optparse import OptionParser
from itaps import iBase,iMesh,iMeshExtensions

def read_and_tag_phtn_ergs(inputfile, meshfile):
    """ Method reads a list of energies and tags them to the root set.

    ACTION: Reads a single energy from each line of 'inputfile', creating a list
    of these values. These values are tagged to the rootSet of the 'meshfile'
    mesh under the tag 'PHTN_ERGS'. Method destroys the 'PHTN_ERGS' tag if it
    already exists.
    RECEIVES: 
    -inputfile is a plain text file listing one energy per line. It should have
     n+1 entries where n is the number of energy groups. Low energy first!
    -meshfile is a MOAB mesh
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

    mesh = iMesh.Mesh()
    mesh.load(meshfile)

    try:
        mesh.createTag("PHTN_ERGS", len(ergs), float)

    except iBase.TagAlreadyExistsError:
        mesh.destroyTag(mesh.getTagHandle("PHTN_ERGS"), force=True)
        phtn_ergs = mesh.createTag("PHTN_ERGS", len(ergs), float)

    # Give the values to the mesh tag on the rootSet
    phtn_ergs[mesh.rootSet] = ergs
    print "{0} energies have been added to '{1}' on the PHTN_SRC tag of the " \
            "rootSet.".format(len(ergs), meshfile)

    mesh.save(meshfile)

    return 1


def destroy_erg_bins_tag(meshfile):
    """Method removes the 'PHTN_ERGS' tag from a MOAB mesh"""
    mesh = iMesh.Mesh()
    mesh.load(meshfile)
    try:
        mesh.destroyTag(mesh.getTagHandle("PHTN_ERGS"), force=True)
    except:
        print "Failed to delete 'PHTN_ERGS' tag from '{0}'".format(meshfile)
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

    # Call the method to read inputfile and tag meshfile
    read_and_tag_phtn_ergs( args[0], args[1])

    return 1


# Handles module being called as a script.
if __name__=='__main__':
    main()
