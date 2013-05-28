#!/usr/bin/env python

"""
`write_alara_fluxin.py` is used to create a fluxin file for ALARA. Fluxes are
taken from a MOAB mesh, with tag names of the form 'n_group_###' where ### is
a 3 digit number with leading zeros as needed (e.g. 001).
"""

from optparse import OptionParser
import sys
from itaps import iMesh, iBase
from r2s.scdmesh import ScdMesh


def get_flux_tag_handles(mesh):
    """Method identifies all tags containing flux information from a meshtally

    Parameters
    ----------
    mesh : iMesh.Mesh object
        MOAB mesh file object containing tags of the form TALLY_TAG_lowE-highE

    Returns
    -------
    fluxtaghandles : list of iMesh.Tag objects
        List of tag handles, sorted by tag name, from lowest energy to high
    """

    # Grab first voxel entity on mesh, from which we get voxel-level tag handles
    for x in mesh.iterate(iBase.Type.region, iMesh.Topology.all):
        break
    handles = mesh.getAllTags(x)

    datatags = list()

    for handle in handles:
        tagname = handle.name.lower().split("_")
        if tagname[0:2] == ['tally', 'tag'] and len(tagname) > 2:
            erg = tagname[2].replace("e-","ee").split("-")[0]
            erg = float(erg.replace("ee","e-"))
            datatags.append([erg, handle])

    if not len(datatags):
        return None

    datatags.sort()

    fluxtaghandles = [x[1] for x in datatags]
    
    return fluxtaghandles


def find_num_e_groups(sm):
    """Return the number of energy groups used for neutron flux tags on a mesh

    Parameters
    ----------
    sm - Scdmesh.scmesh object
        Structured mesh object containing tags of the form 'n_group_###'.

    Returns
    -------
    num_e_groups - int
        Number of energy groups
    """    
    num_e_groups = 0
    for e_group in range(1,1000): #search for up to 1000 e_groups
        
        #Look for tags in the form n_group_'e_group'
        try:
            sm.imesh.getTagHandle('n_group_{0:03d}'.format(e_group))
            num_e_groups += 1 #increment if tag is found

       # Stop iterating once a tag is not found
        except iBase.TagNotFoundError:
            break

    if num_e_groups != 0:
        print 'Energy groups found: {0}'.format(num_e_groups)

    #Exit if no tags of the form n_group_XXX are found
    else:
        print >>sys.stderr, 'No tags of the form n_group_XXX found'
        sys.exit(1)
  
    return num_e_groups


def print_fluxes(mesh, num_e_groups, backward_bool, fluxin_name, tags=None):
    """Method writes tag values to ALARA fluxin format for the flux at each
    energy for each voxel

    Parameters
    ----------
    mesh : iMesh.Mesh object
        MOAB mesh file object containing tags of the form TALLY_TAG_lowE-highE
    num_e_groups : integer
        Number of energy groups in tally
    backward_bool : boolean
        If true, output data is in order from high energy to low energy.
        Note that this should be true when working with the FENDL libraries.
    fluxin_name : string
        Filename for output ALARA fluxin file
    tags : list of iMesh.Tag objects
        List of tag handles, sorted by tag name, from lowest energy to high
    """

    output = open(fluxin_name, 'w')

    # Get list of voxels, and set meshtype
    if isinstance(mesh, ScdMesh):
        voxels = mesh.iterateHex('xyz')
        meshtype = 'scd'
    else:
        voxels = list(mesh.iterate(iBase.Type.region, iMesh.Topology.all))
        meshtype = 'gen'
        print "Got {0} voxels from mesh.".format(len(voxels))

    try:
        #Print fluxes for each voxel in xyz order (z changing fastest)
        for voxel in voxels:
            
            #Establish for loop bounds based on if forward or backward printing
            #is requested
            if backward_bool == False:
                min = 0
                max = num_e_groups
                direction = 1
            else:
                min = num_e_groups -1
                max = -1
                direction = -1
            
            #Print flux data to file
            count=0
            for e_group in range(min,max,direction):
                #TODO: use try/except for catching missing tags
                if tags and meshtype == 'gen': # general mesh with given tags
                    output.write(str((tags[e_group])[voxel]) + " ")
                elif meshtype == 'gen': # general mesh with assumed tags
                    output.write(str(mesh.getTagHandle( \
                            'n_group_{0:03d}'.format(e_group+1))[voxel]) + " ")
                else: # structured mesh with assumed tags
                    output.write(str(mesh.imesh.getTagHandle( \
                            'n_group_{0:03d}'.format(e_group+1))[voxel]) + " ")
                
                #flux.in formatting: create a new line after every 8th entry
                count += 1
                if count % 8 == 0:
                    output.write('\n')
            output.write('\n\n')
       
        print "flux.in file {0} sucessfully created".format(fluxin_name)

    except iBase.TagNotFoundError:
        if tags:
            print "Missing tag on mesh: {0}".format(tags[e_group].name)
        else:
            print "Missing tag on mesh: n_group_{0:03d}".format(e_group+1)

    output.close()


def write_alara_fluxin(filename, mesh, backwards=False):
    """Load a MOAB mesh and create an alara_fluxin file from tags
    
    Parameters
    ----------
    filename - string
        Output filename for the fluxin file.
    mesh - ScdMesh or iMesh.Mesh object
        MOAB mesh with tags to create fluxin file from.
    backwards - boolean
        If true, prints fluxes from high energy to low energy. 
        Note that this should be true when working with the FENDL libraries.
    """
    if isinstance(mesh, ScdMesh):
        # Find number of energy groups
        num_e_groups = find_num_e_groups(mesh)
        fluxtaghandles = None
    else:
        # Get list of tag handles, sorted by tag name (lowest energy to high)
        fluxtaghandles = get_flux_tag_handles(mesh)
        num_e_groups = len(fluxtaghandles)

    # Print flux.in file
    print_fluxes(mesh, num_e_groups, backwards, filename, tags=fluxtaghandles)


def main():
    """ """    
    # Instatiate options parser
    parser = OptionParser\
             (usage='%prog <structured mesh> [options]')

    parser.add_option('-b', action='store_true', dest='backward_bool',\
        default=False, \
        help='Print to ALARA fluxin in fluxes in  decreasing energy. ' \
        'Default=%default')

    parser.add_option('-o', dest='fluxin_name', default='ALARAflux.in',\
        help='Name of ALARA fluxin output file, default=%default')

    (opts, args) = parser.parse_args()

    if len(args) != 2:
        parser.error\
        ( '\nNeed exactly 1 argument: structured mesh file' )

    # Load Structured mesh from file
    sm = ScdMesh.fromFile(args[1])

    write_alara_fluxin( opts.fluxin_name, sm, opts.backward_bool )


if __name__ == '__main__':
    main(sys.argv)
