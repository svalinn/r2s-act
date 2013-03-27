#!/usr/bin/env python

"""Module contains the read_and_tag_phtn_ergs() and destroy_erg_bins_tag() 
methods.  These are used for adding the photon energy group boundaries to a
mesh; The functions are typically used when the user does not want to use the
default 42 group structure for photons.
"""

from optparse import OptionParser
from itaps import iBase,iMesh,iMeshExtensions

from r2s.scdmesh import ScdMesh


def read_and_tag_phtn_ergs(fr, sm):
    """ Method reads a file with a list of energies and tags them to the root
    set.

    Method replaces the 'PHTN_ERGS' tag if it already exists.

    Parameters
    ----------
    fr : readable file stream
        a file stream listing one energy per line. It should have
        n+1 entries where n is the number of energy groups. Low energy first!
    sm : scdmesh.ScdMesh object
        Structured mesh object to tag energies to.

    Notes
    -----
    Reads a single energy from each line of 'fr', creating a list
    of these values. These values are tagged to the scdset of 'sm'
    with the tag handle 'PHTN_ERGS'. 
    """

    ergs = list()

    for line in fr:
        # We float() the values to get rid of whitespace
        try:
            ergs.append(float(line))
        except ValueError:
            print "A non-numeric value was found in the list of energies."
            return 0
        
        if len(ergs) > 1 and ergs[-1] <= ergs[-2]:
            print "Energy values are not in order. Must start with lowest."
            return 0

    try:
        phtn_ergs_tag = sm.imesh.createTag("PHTN_ERGS", len(ergs), float)

    except iBase.TagAlreadyExistsError:
        # We completely rewrite the tag if it already existed
        sm.imesh.destroyTag(sm.imesh.getTagHandle("PHTN_ERGS"), force=True)
        phtn_ergs_tag = sm.imesh.createTag("PHTN_ERGS", len(ergs), float)

    # Give the values to the mesh tag on the scdset
    phtn_ergs_tag[sm.scdset] = ergs
    print "{0} energies have been added to the mesh on the PHTN_SRC tag of " \
            "the scdset.".format(len(ergs))

    return 1


def destroy_erg_bins_tag(sm):
    """Method removes the 'PHTN_ERGS' tag from a MOAB mesh
    
    Parameters
    ----------
    sm : scdmesh.ScdMesh object
        Structured mesh object with tags to be removed

    Returns
    -------
    return code
        1 if successful; 0 if failed.
    """

    try:
        sm.imesh.destroyTag(sm.imesh.getTagHandle("PHTN_ERGS"), force=True)
    except:
        print "Failed to delete 'PHTN_ERGS' tag from the MOAB mesh."
        return 0

    return 1


def main():
    """ACTION: Method defines an option parser and handles command-line
    usage of this module.
    REQUIRES: command line arguments to be passed - otherwise prints help
    information.
    """

    usage = "usage: %prog ENERGY_FILE MESH_FILE [options] \n\n" \
            "ENERGY_FILE is a list of the energy bins for each photon energy " \
            "group, with a single energy per line. MESH_FILE is the MOAB " \
            "mesh that will store the contents of ENERGY_FILE in the tag " \
            "'PHTN_ERGS'."
    parser = OptionParser(usage)

    (options, args) = parser.parse_args()

    fr = open(args[0])
    sm = ScdMesh.fromFile(args[1])

    # Call the method to read fr and tag mesh
    read_and_tag_phtn_ergs(fr, sm)

    sm.scdset.save(args[1])
    fr.close()

    return 1


# Handles module being called as a script.
if __name__ == '__main__':
    main()
