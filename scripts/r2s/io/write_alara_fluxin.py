#!/usr/bin/env python

from optparse import OptionParser
import sys
from itaps import iMesh, iBase
from r2s.scdmesh import ScdMesh


def find_num_e_groups(sm):
    """ """    
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
    fluxin_name : string
        Filename for output ALARA fluxin file
    fluxtaghandles : list of iMesh.Tag objects
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


def write_alara_fluxin( filename, sm, backwards=False ):
    """ """    
    #Find number of energy groups
    num_e_groups = find_num_e_groups(sm)

    #Print flux.in file
    print_fluxes(sm, num_e_groups, backwards, filename)


def main( arguments=None ):
    """ """    
    #Instatiate options parser
    parser = OptionParser\
             (usage='%prog <structured mesh> [options]')

    parser.add_option('-b', action='store_true', dest='backward_bool',\
        default=False, \
        help='Print to ALARA fluxin in fluxes in  decreasing energy. ' \
        'Default=%default')

    parser.add_option('-o', dest='fluxin_name', default='ALARAflux.in',\
        help='Name of ALARA fluxin output file, default=%default')

    (opts, args) = parser.parse_args( arguments )

    if len(args) != 2:
        parser.error\
        ( '\nNeed exactly 1 argument: structured mesh file' )

    #Load Structured mesh from file
    sm = ScdMesh.fromFile(args[1])

    write_alara_fluxin( opts.fluxin_name, sm, opts.backward_bool )


if __name__ == '__main__':
    main(sys.argv)
