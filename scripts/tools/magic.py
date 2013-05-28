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
from tools import h5m_to_wwinp


################################################################################
def gen_e_group_names(flux_mesh, totals_bool):

    # find meshtal type
    particle_int = flux_mesh.imesh.getTagHandle('particle')[flux_mesh.imesh.rootSet]

    if particle_int == 1:
        particle = 'n' 
    else:
        particle = 'p'

    # find number of energy groups
    if totals_bool == True :
        e_group_names = ['{0}_group_total'.format(particle)]

    elif totals_bool == False:
        e_upper_bounds = flux_mesh.imesh.getTagHandle("E_upper_bounds")[flux_mesh.imesh.rootSet]

        if isinstance(e_upper_bounds, float):
            e_upper_bounds = [e_upper_bounds]

        num_e_groups = len(e_upper_bounds)    
        e_group_names = ['{0}_group_{1:03d}'.format(particle, x) for x in range(1, num_e_groups + 1)]


    return e_group_names

################################################################################
def find_max_fluxes(flux_mesh, e_group_names):

    max_fluxes = [0]*len(e_group_names)
    for i, e_group_name in enumerate(e_group_names):

        for flux_voxel in flux_mesh.iterateHex('xyz'):
            flux = flux_mesh.imesh.getTagHandle(e_group_name)[flux_voxel]

            if flux > max_fluxes[i]:
                max_fluxes[i] = flux

    return max_fluxes

################################################################################
def create_ww_mesh(flux_mesh, e_group_names):

    ww_mesh = ScdMesh(flux_mesh.getDivisions('x'),\
                       flux_mesh.getDivisions('y'),\
                       flux_mesh.getDivisions('z'))

    # create ww tags
    for e_group_name in e_group_names:
            ww_tag = ww_mesh.imesh.createTag('ww_{0}'.format(e_group_name), 1, float)
            for voxel in ww_mesh.iterateHex('xyz'):
                ww_tag[voxel] = 0

    # create e_upper_bound tags
    e_upper_bounds = flux_mesh.imesh.getTagHandle("E_upper_bounds")[flux_mesh.imesh.rootSet]
    if isinstance(e_upper_bounds, float):
        e_upper_bounds = [e_upper_bounds]

    e_tag = ww_mesh.imesh.createTag("E_upper_bounds", len(e_upper_bounds), float)
    e_tag[ww_mesh.imesh.rootSet] = flux_mesh.imesh.getTagHandle("E_upper_bounds")[flux_mesh.imesh.rootSet]

    # create  particle tag
    particle = flux_mesh.imesh.getTagHandle("particle")[flux_mesh.imesh.rootSet]
    particle_tag = ww_mesh.imesh.createTag("particle", 1, int)
    particle_tag[ww_mesh.imesh.rootSet] = particle

    return ww_mesh

################################################################################

def magic(flux_mesh, totals_bool, null_value, tolerance, ww_mesh=None):

    tolerance = float(tolerance)
    null_value = float(null_value)

    e_group_names = gen_e_group_names(flux_mesh, totals_bool)

    max_fluxes = find_max_fluxes(flux_mesh, e_group_names)
    
    if ww_mesh == None:
        print "\tNo WW mesh file supplied; generating one based on meshtal"
        ww_bool = False # mesh file NOT preexisting

        # create a mesh with the same dimensions as flux_mesh
        ww_mesh = create_ww_mesh(flux_mesh, e_group_names)

    else:
        ww_bool = True # mesh file preexisting

        # make sure the supplied meshes have the same dimensions
        try:
            for i in ('x', 'y', 'z'):
                flux_mesh.getDivisions(i) == ww_mesh.getDivisions(i)

        except:
            print >>sys.stderr, 'Mismatched dimensions on WWINP and flux meshes'
            sys.exit(1)

        print "\tSupplied meshes confirmed to have same dimensions"


    # iterate through all voxels and energy groups and apply MAGIC  
    flux_voxels = flux_mesh.iterateHex('xyz')
    ww_voxels = ww_mesh.iterateHex('xyz')

    for (flux_voxel, ww_voxel) in zip(flux_voxels, ww_voxels):

        for i, e_group_name in enumerate(e_group_names):

            flux = flux_mesh.imesh.getTagHandle(e_group_name)[flux_voxel]
            error = flux_mesh.imesh.getTagHandle(e_group_name + '_error')[flux_voxel]
            ww = ww_mesh.imesh.getTagHandle('ww_{0}'.format(e_group_name))[ww_voxel]

            if error < tolerance and error != 0 and ww != -1:
                ww_mesh.imesh.getTagHandle('ww_{0}'.format(e_group_name))[ww_voxel]  = flux/(2*max_fluxes[i]) # apply magic method

            elif ww_bool == False and (error > tolerance or error == 0.0):
                ww_mesh.imesh.getTagHandle('ww_{0}'.format(e_group_name))[ww_voxel] = null_value

    return ww_mesh


################################################################################

def write_magic(flux_mesh_filename, ww_inp_mesh_filename, totals_bool, null_value, output_mesh, tolerance):
    """Opens up h5m files, sends them to the magic function, saves resulting WW
       mesh files and converts to a wwinp
    """

    flux_mesh = ScdMesh.fromFile(flux_mesh_filename)

    if ww_inp_mesh_filename != None:
        ww_inp_mesh = ScdMesh.fromFile(ww_inp_mesh_filename)

    else:
        ww_inp_mesh = None
   

    ww_mesh = magic(flux_mesh, totals_bool, null_value, tolerance, ww_inp_mesh)
    ww_mesh.scdset.save(output_mesh)
    print "\tWrote WW mesh file '{0}'".format(output_mesh)

    #h5m_to_wwinp.write_wwinp(ww_mesh, output)
    #print "\tWrote WWINP file '{0}'".format(output)


################################################################################

def main( arguments = None ):

    #Instatiate options parser
    parser = OptionParser\
             (usage='%prog <flux mesh> <ww mesh> [options]')

    parser.add_option('-w', dest='ww_mesh', default=None,\
        help='Preexisting WW mesh to apply magic to, default=%default')

    parser.add_option('-o', dest='output_mesh', default='magic_ww.h5m',\
        help='Name of WWINP output file, default=%default')

    parser.add_option('-t', action='store_true', dest='totals_bool',\
        default=False, \
        help='If multiple energy groups exist, only use Total \
         default=%default')

    parser.add_option('-n', dest='null_value', default='0',\
        help='WW value for voxels with error > tolerance (on the first iteration only), default=%default')

    parser.add_option('-e', dest='tolerance', default='0.1',\
        help='Specify the maximum allowable relative error for \
              overwriting existing ww values, default=%default')

    (opts, args) = parser.parse_args( arguments )

    if len(args) != 1:
        parser.error\
        ( '\nNeed exactly 1 argument: flux mesh' )


    write_magic(args[0], opts.ww_mesh, opts.totals_bool, opts.null_value, opts.output_mesh, opts.tolerance)



if __name__ == '__main__':
    # No arguments case -> print help output
    if len(sys.argv) == 1:
        sys.argv.append('-h')

    main()
