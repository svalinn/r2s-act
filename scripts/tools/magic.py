#!/usr/bin/env python
import linecache
from optparse import OptionParser
import sys
from itaps import iMesh, iBase
from r2s.scdmesh import ScdMesh

def find_num_e_groups(sm, particle):
    
    num_e_groups=0
    for e_group in range(1,1000): #search for up to 1000 e_groups
        
        #Look for tags in the form n_group_'e_group'
        try:
            tag=sm.imesh.getTagHandle('{0}_group_{1:03d}'.format(particle, e_group))
            num_e_groups = num_e_groups + 1 #increment if tag is found

       # Stop iterating once a tag is not found
        except iBase.TagNotFoundError:
            break    

    if num_e_groups != 0 :
        print 'Energy groups found: {0}'.format(num_e_groups)

    #Exit if no tags of the form n_group_XXX are found
    else:
        print >>sys.stderr, 'No tags of the form n/p_group_XXX found'
        sys.exit(1)
  
    return num_e_groups


def find_max_fluxes(flux_mesh, particle, e_groups, total_bool):
        
    flux_voxels = flux_mesh.iterateHex('xyz')

    for flux_voxel in flux_voxels:
        max_fluxes = [0]*len(e_groups)
        for i, e_group in enumerate(e_groups):
            flux = flux_mesh.imesh.getTagHandle('{0}_group_{1}'.format(particle, e_group))[flux_voxel]
            if flux > max_fluxes[i]:
                max_fluxes[i] = flux

    return max_fluxes


def magic_wwinp(flux_mesh, ww_mesh='None', total_bool=False, null_value=1):
    """This function reads in a flux mesh and a ww mesh as well as relevant paramters
       then the magic method is applied and a newly tagged flux is returned.
    """

    # find meshtal type
    try:
       tag=flux_mesh.imesh.getTagHandle('n_group_001')
       particle = 'n'
    except:
        particle = 'p'

    # find number of e_groups
    num_e_groups = find_num_e_groups(flux_mesh, particle)

    if total_bool == False:
        e_groups = ['{0:03d}'.format(x) for x in range(1, num_e_groups + 1)]
    else:
        e_groups = ['Total']

    # find the max flux value for each e_group, store in vector
    max_fluxes = find_max_fluxes(flux_mesh, particle, e_groups, total_bool)

    if ww_mesh == 'None':
        ww_bool = False # mesh file NOT preexisting
        # create a mesh with the same dimensions as flux_mesh
        ww_mesh = ScdMesh(flux_mesh.getDivisions('x'),\
                          flux_mesh.getDivisions('y'),\
                          flux_mesh.getDivisions('z'))

    else:
        ww_bool = True # mesh file preexisting
        # make sure the supplied meshes have the same dimenstions
        try:
            for i in ('x', 'y', 'z'):
                flux_mesh.getDivisions(i) == ww_mesh.getDivisions('x')
        except:
            print >>sys.stderr, 'Mismatched dimensions on WWINP and flux meshes'
            sys.exit(1)

    # iterate through all voxels          
    flux_voxels = flux_mesh.iterateHex('xyz')
    ww_voxels = ww_mesh.iterateHex('xyz')

    ww_mesh.imesh.getTagHandle('e_group_001')[ww_voxels] = flux_mesh.imesh.getTagHandle('n_group_001')[flux_voxels]

    return ww_mesh

'''
    for (flux_voxel, ww_voxel) in zip(flux_voxels, ww_voxels):
        for i, e_group in enumerate(e_groups):
            flux = flux_mesh.imesh.getTagHandle(\
                '{0}_group_{1}'.format(particle, e_group))[flux_voxel]
            error = flux_mesh.imesh.getTagHandle(\
                 '{0}_group_{1}_error'.format(particle, e_group))[flux_voxel]
            if ww_bool == False or 0 < error < 0.1:
                ww_mesh.imesh.getTagHandle(\
                    'e_group_{0}'.format(e_group))[ww_voxel]\
                     = flux/(2*max_fluxes[i]) # apply magic method
            elif ww_mesh.imesh.getTagHandle(\
                'e_group_{1}_error'.format(e_group))[ww_voxel] == 0:
                ww_mesh.imesh.getTagHandle(\
                 'e_group_{1}_error'.format(e_group))[ww_voxel]\
                  == null_value
'''



def print_ww_mesh(ww_mesh, output):
    pass



def main( arguments = None ):

    #Instatiate options parser
    parser = OptionParser\
             (usage='%prog <flux mesh> <ww mesh> [options]')

    parser.add_option('-w', dest='ww_mesh', default='None',\
        help='Preexisting WW mesh to apply magic to., default=%default')

    parser.add_option('-o', dest='output_name', default='wwinp.out',\
        help='Name of WWINP output file, default=%default')

    parser.add_option('-t', action='store_true', dest='total_bool',\
        default=False, \
        help='If multiple energy groups exist, only use TOTAL' \
        'Default=%default')

    parser.add_option('-n', dest='null_value', default='1',\
        help='WW value for voxels with error > 10%, default=%default')

    (opts, args) = parser.parse_args( arguments )

    if len(args) != 1:
        parser.error\
        ( '\nNeed exactly 1 argument: flux mesh' )

    #Load Structured mesh from file
    flux_mesh = ScdMesh.fromFile(args[0])

    ww_mesh = magic_wwinp(flux_mesh, opts.ww_mesh, opts.total_bool, opts.null_value)

    ww.scdset.save(test.vtk)

    #print_ww_mesh(ww_mesh, opts.output)



if __name__ == '__main__':
    # No arguments case -> print help output
    if len(sys.argv) == 1:
        sys.arv.append('-h')

    main()
