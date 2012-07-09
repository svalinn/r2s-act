#!/usr/bin/env python
import linecache
from optparse import OptionParser
import sys
from itaps import iMesh, iBase
from scdmesh import ScdMesh

def find_num_e_groups(sm):
    
    num_e_groups=0
    for e_group in range(1,1000): #search for up to 1000 e_groups
        
        #Look for tags in the form n_group_'e_group'
        try:
            tag=sm.imesh.getTagHandle('n_group_{0:03d}'.format(e_group))
            num_e_groups = num_e_groups + 1 #increment if tag is found

       # Stop iterating once a tag is not found
        except iBase.TagNotFoundError:
            break
    

    if num_e_groups != 0 :
        print 'Energy groups found: {0}'.format(num_e_groups)

    #Exit if no tags of the form n_group_XXX are found
    else:
        print >>sys.stderr, 'No tags of the form n_group_XXX found'
        sys.exit(1)
  
    return num_e_groups

def print_fluxes(sm, num_e_groups, backward_bool, fluxin_name):

    output=file(fluxin_name, 'w')
    voxels=sm.iterateHex('xyz')

    #Print fluxes for each voxel in xyz order (z changing fastest)
    for voxel in voxels:
        
        #Establish for loop bounds based on if forward or backward printing
        #is requested
        if backward_bool == False :
            min = 1
            max= num_e_groups + 1
            direction = 1
        else:
            min=num_e_groups
            max=0
            direction=-1
        
        #Print flux data to file
        count=0
        for e_group in range(min,max,direction):
            output.write(str(sm.imesh.getTagHandle('n_group_{0:03d}'.format(e_group))[voxel])+' ')
            
            #flux.in formatting: create a new line after every 8th entry
            count += 1   
            if count%8 == 0:
                output.write('\n')
        output.write('\n\n')
   
    print 'flux.in file {0} sucessfully created'.format(fluxin_name)


def write_alara_fluxin( filename, sm, backwards=False ):

    #Find number of energy groups
    num_e_groups=find_num_e_groups(sm)

    #Print flux.in file
    print_fluxes(sm, num_e_groups, backwards, filename)

def main( arguments = None ):

    #Instatiate options parser
    parser = OptionParser\
             (usage='%prog <structured mesh> [options]')

    parser.add_option('-b', action='store_true', dest='backward_bool',\
        default=False, \
        help='Print to ALARA fluxin in fluxes in  decreasing energy')

    parser.add_option('-o', dest='fluxin_name', default='ALARAflux.in',\
        help='Name of ALARA fluxin output file, default=%default')

    (opts, args) = parser.parse_args( arguments )

    if len(args) != 2 :
        parser.error\
        ( '\nNeed exactly 1 argument: structured mesh file' )

    #Load Structured mesh from file
    sm=ScdMesh.fromFile(args[1])

    write_alara_fluxin( opts.fluxin_name, sm, opts.backward_bool )


if __name__ == '__main__':
    main(sys.argv)
