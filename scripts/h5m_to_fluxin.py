#!/usr/bin/env python
import linecache
from optparse import OptionParser
import sys
from itaps import iMesh, iBase
import scdmesh
from scdmesh import ScdMesh

def find_num_e_groups(sm):
    
    num_e_groups=0
    for e_group in range(1,1000): #search for up to 1000 e_groups

        try:
            tag=sm.mesh.getTagHandle('n_group_{0:03d}'.format(e_group))
            num_e_groups = num_e_groups + 1

        except iBase.TagNotFoundError:
            break
    print 'Energy groups found: {0}'.format(num_e_groups)  
    return num_e_groups

def print_fluxes(sm, num_e_groups, backward_bool, fluxin_name):

    output=file(fluxin_name, 'w')

    voxels=sm.iterateHex('xyz')
    for voxel in voxels:
    
        count=0

        if backward_bool == False :
            min = 1
            max= num_e_groups + 1
            direction = 1
        else:
            min=num_e_groups
            max=0
            direction=-1
        for e_group in range(min,max,direction):
            output.write(str(sm.mesh.getTagHandle('n_group_{0:03d}'.format(e_group))[voxel])+' ')
            
            count += 1   
            if count%8 == 0:
                output.write('\n')
        output.write('\n\n')   
    print 'flux.in file {0} sucessfully created'.format(fluxin_name)


def main( arguments = None ):

    parser = OptionParser\
             (usage='%prog <mesh> [options]')

    parser.add_option('-b', action='store_true', dest='backward_bool',\
        default=False, \
        help='Print to ALARA fluxin in fluxes in  decreasing energy')

    parser.add_option('-o', dest='fluxin_name', default='ALARAflux.in',\
        help='Name of ALARA fluxin output file, default=%default')

    (opts, args) = parser.parse_args( arguments )

    sm=ScdMesh.fromFile(iMesh.Mesh(),args[0])    

    num_e_groups=find_num_e_groups(sm)
    print_fluxes(sm,num_e_groups,opts.backward_bool,opts.fluxin_name)



if __name__ == '__main__':
    main()
