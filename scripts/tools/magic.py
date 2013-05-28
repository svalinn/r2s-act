#!/usr/bin/env python
#python imports
import linecache
from optparse import OptionParser
import sys
import datetime
# itaps imports
from itaps import iMesh
from itaps import iBase
# r2s imports
from r2s.scdmesh import ScdMesh



def find_max_fluxes(flux_mesh, particle, e_groups, total_bool):
        
    max_fluxes = [0]*len(e_groups)
    for i, e_group in enumerate(e_groups):
        for flux_voxel in flux_mesh.iterateHex('xyz'):
            flux = flux_mesh.imesh.getTagHandle('{0}_group_{1}'.format(particle, e_group))[flux_voxel]
            if flux > max_fluxes[i]:
                max_fluxes[i] = flux

    #print "\tMaximum flux(es) found to be {0}".format(max_fluxes)
    return max_fluxes

def magic_wwinp(flux_mesh, ww_mesh='None', total_bool=False, null_value=0, tolerance=0.1):
    """This function reads in a flux mesh and a ww mesh as well as relevant paramters
       then the magic method is applied and a newly tagged flux is returned.
    """

    # find meshtal type

    tag_names = []
    for tag in flux_mesh.imesh.getAllTags(flux_mesh.getHex(0,0,0)):
        tag_names.append(tag.name)

    if 'n_group_001' in tag_names or 'n_group_total' in tag_names:
       particle = 'n'
    elif 'p_group_001' in tag_names or 'p_group_total' in tag_names:
        particle = 'p'
    else:
        print >>sys.stderr, 'Tag X_group_YYY or X_group_total not found'
        sys.exit(1)

    # find number of e_groups
    num_e_groups  = len(flux_mesh.imesh.getTagHandle("E_upper_bounds")[ww_mesh.imesh.rootSet])

    if total_bool == False:
        e_groups = ['{0:03d}'.format(x) for x in range(1, num_e_groups + 1)]
        print "\tGenerating WW for {0} energy groups".format(num_e_groups)
    else:
        e_groups = ['total']
        print "\tGenerating WW for Total energy group"

    # find the max flux value for each e_group, store in vector
    max_fluxes = find_max_fluxes(flux_mesh, particle, e_groups, total_bool)

    if ww_mesh == 'None':
        print "\tNo WW mesh file supplied; generating one based on meshtal"
        ww_bool = False # mesh file NOT preexisting
        # create a mesh with the same dimensions as flux_mesh
        ww_mesh = ScdMesh(flux_mesh.getDivisions('x'),\
                          flux_mesh.getDivisions('y'),\
                          flux_mesh.getDivisions('z'))
        # create a tag for each energy group
        for e_group in e_groups:
            group_name = "ww_{0}_group_{1}".format(particle, e_group)
            ww_mesh.imesh.createTag(group_name, 1, float)   

        # create energy bounds
        tag_e_groups = ww_mesh.imesh.createTag("e_groups", len(e_groups), float)

        if e_groups != ['total']:
            tag_e_groups[ww_mesh.imesh.rootSet] = \
                flux_mesh.imesh.getTagHandle("e_groups")[flux_mesh.imesh.rootSet]
        else:
            tag_e_groups[ww_mesh.imesh.rootSet] = 1E36 # usual MCNP value           


    else:
        ww_bool = True # mesh file preexisting
        # make sure the supplied meshes have the same dimenstions
        ww_mesh = ScdMesh.fromFile(ww_mesh)
        try:
            for i in ('x', 'y', 'z'):
                flux_mesh.getDivisions(i) == ww_mesh.getDivisions(i)

        except:
            print >>sys.stderr, 'Mismatched dimensions on WWINP and flux meshes'
            sys.exit(1)

    print "\tSupplied meshes confirmed to have same dimensions"
    
    # iterate through all voxels          
    flux_voxels = flux_mesh.iterateHex('xyz')
    ww_voxels = ww_mesh.iterateHex('xyz')

    for (flux_voxel, ww_voxel) in zip(flux_voxels, ww_voxels):
        for i, e_group in enumerate(e_groups):
            flux = flux_mesh.imesh.getTagHandle(\
                '{0}_group_{1}'.format(particle, e_group))[flux_voxel]
            error = flux_mesh.imesh.getTagHandle(\
                 '{0}_group_{1}_error'.format(particle, e_group))[flux_voxel]
            if ((ww_bool == False and error != 0.0) \
            or (0.0 < error and error < tolerance)):
                if ww_bool == True:
                    if ww_mesh.imesh.getTagHandle('ww_{0}_group_{1}'\
                    .format(particle, e_group))[ww_voxel] != -1:       
                        ww_mesh.imesh.getTagHandle('ww_{0}_group_{1}'\
                        .format(particle, e_group))[ww_voxel]\
                        = flux/(2*max_fluxes[i]) # apply magic method

                else:
                    ww_mesh.imesh.getTagHandle(\
                        'ww_{0}_group_{1}'.format(particle, e_group))[ww_voxel]\
                         = flux/(2*max_fluxes[i]) # apply magic method

            elif ww_bool == False and error == 0.0 :
                ww_mesh.imesh.getTagHandle(\
                    'ww_{0}_group_{1}'.format(particle, e_group))[ww_voxel]\
                     = null_value

    return ww_mesh, e_groups







def magic(flux_h5m, ww_mesh, total_bool, null_value, output, output_mesh, tolerance):
    """Runs magic.py from as a module
    """
    flux_mesh = ScdMesh.fromFile(flux_h5m)

    ww_mesh, e_groups = magic_wwinp(flux_mesh, ww_mesh, total_bool, null_value, tolerance)

    if output_mesh != 'None':
        ww_mesh.scdset.save(output_mesh)

    write_wwinp(ww_mesh, e_groups, output)



def main( arguments = None ):

    #Instatiate options parser
    parser = OptionParser\
             (usage='%prog <flux mesh> <ww mesh> [options]')

    parser.add_option('-w', dest='ww_mesh', default='None',\
        help='Preexisting WW mesh to apply magic to, default=%default')

    parser.add_option('-o', dest='output_name', default='wwinp.out',\
        help='Name of WWINP output file, default=%default')

    parser.add_option('-m', dest='output_mesh', default='None',\
        help='Name of WWINP output file, default=%default')

    parser.add_option('-t', action='store_true', dest='total_bool',\
        default=False, \
        help='If multiple energy groups exist, only use Total \
         default=%default')

    parser.add_option('-n', dest='null_value', default='0',\
        help='WW value for voxels with error > 10%, default=%default')

    parser.add_option('-e', dest='tolerance', default='0.1',\
        help='Specify the maximum allowable error for overwriting  values, default=%default')

    (opts, args) = parser.parse_args( arguments )

    if len(args) != 1:
        parser.error\
        ( '\nNeed exactly 1 argument: flux mesh' )


    magic(args[0], opts.ww_mesh, opts.total_bool, opts.null_value, opts.output_name, opts.output_mesh, opts.tolerance)

    print "\tWrote WWINP file '{0}'".format(opts.output_name)

    if opts.output_mesh != 'None':
        print "\tWrote WW mesh file '{0}'".format(opts.output_mesh)

    print "Complete"


if __name__ == '__main__':
    # No arguments case -> print help output
    if len(sys.argv) == 1:
        sys.argv.append('-h')

    main()
