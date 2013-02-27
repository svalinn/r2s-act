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

    #Exit if no tags of the form n_group_XXX are found
    else:
        print >>sys.stderr, 'No tags of the form n/p_group_XXX found'
        sys.exit(1)
  
    return num_e_groups


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
    num_e_groups = find_num_e_groups(flux_mesh, particle)

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


def write_wwinp(ww_mesh, e_groups, output):
    """This funtion reads a WW mesh file and prints out a corresponding WWIMP
    """

    # find wwinp type
    tag_names = []
    for tag in ww_mesh.imesh.getAllTags(ww_mesh.getHex(0,0,0)):
        tag_names.append(tag.name)

    if 'ww_n_group_001' in tag_names or 'ww_n_group_total' in tag_names:
       particle = 'n'
    elif 'ww_p_group_001' in tag_names or 'ww_p_group_total' in tag_names:
        particle = 'p'
    else:
        print >>sys.stderr, 'Tag ww_X_group_YYY or ww_X_group_total not found'
        sys.exit(1)

    # create block 1 string
    block1 = '         1         1         '

    # add particle specifier
    if particle == 'n':
        block1 += '1'
    else:
        block1 += '2'

    # add 10 to specify cartesian geometry
    block1 += '        10                     '
    # add date and time
    now = datetime.datetime.now()
    block1 += '{0:02d}/{1}/{2} {3}:{4}:{5}\n'\
        .format(now.month, now.day, str(now.year)[2:], now.hour, now.minute, \
        now.second)
    # append number of e_groups
    block1 += '         {0}\n'.format(len(e_groups))

    # find mesh spacial bounds
    x, y, z = [ww_mesh.getDivisions('x'), ww_mesh.getDivisions('y'),\
        ww_mesh.getDivisions('z')]

    # find fine/coarse mesh points
    coarse_points = [[],[],[]]
    nfm = [[],[],[]]
    for i, points in enumerate([x, y, z]):
        coarse_points[i].append(points[0])
        j = 1
        ###print "\n\n\nfirst coarse point in dim {0} is {1}".format(i, points[0])
        while j < len(points)-1:
            fine_count = 1
             #floating point comparison: need to be careful because this characterizes
             #coarse vs. fine. That is why 1.01E-2 is used.
            while abs((points[j] - points[j-1]) - (points[j+1] - points[j])) <= 1.01E-2: 
               ###print "dim {0} point {1} is a fine point".format(i, points[j])
               fine_count += 1
               ###print "fine count increased to {0}".format(fine_count)
               j += 1
               ###print "next point to be considered is {0}".format(points[j])
               if j == len(points) - 1:
                   ###print "j is now equal to {0}, breaking".format(j)
                   break

            ###print "appending fine count {0}".format(fine_count)
            nfm[i].append(fine_count)
            ###print "{0} is a coarse point".format(points[j])
            coarse_points[i].append(points[j])
            j += 1
            ###if j < len(points):
                ###print "next point to be considered is {0} (bottom)".format(points[j])

        # if j is on the second to last value, then you can't restart the loop 
        # but the last value has not been accounted for. This occures when the 
        # last two mesh points are both coarse (with one fine mesh in between)
        # this last case handles this final special case
        if j == len(points)-1:
            ###print "inside last course point loop"
            nfm[i].append(1)
            coarse_points[i].append(points[j])

    ###print coarse_points
    ###print nfm
    # append the rest of block 1
    block1 += " {0: 1.5E} {1: 1.5E} {2: 1.5E}"\
        .format(sum(nfm[0]), sum(nfm[1]), sum(nfm[2]))

    block1 += " {0: 1.5E} {1: 1.5E} {2: 1.5E}\n"\
        .format(coarse_points[0][0], coarse_points[1][0], coarse_points[2][0])

    # when printing number of coarse mesh points, must subtract 1. This code
    # (magic.py) is considering the origin a coarse mesh point whereas MCNP
    # does not
    block1 += " {0: 1.5E} {1: 1.5E} {2: 1.5E}  1.0000E+00\n"\
        .format(len(coarse_points[0])-1, len(coarse_points[1])-1, len(coarse_points[2])-1)
    # block 1 now complete

    # create vector of block2 values:
    block2_array = [[],[],[]]
    for i in range(0, 3):
        block2_array[i].append(coarse_points[i][0])
        for j in range(0, len(coarse_points[i]) - 1):
           block2_array[i] += [nfm[i][j], coarse_points[i][j+1], 1.0000]

    # translate block2 vector into a string
    block2 = ''
    for i in range(0,3):
        line_count = 0 # number of entries printed to current line, max = 6
        for j in range(0, len(block2_array[i])):
           
            block2 += ' {0: 1.5E}'.format(block2_array[i][j])
            line_count += 1
            if line_count == 6:
                block2 += '\n'
                line_count = 0

        if line_count != 0:
            block2 += '\n'
    # block 2 string now complete

    # create block 3 string
    # first get energy values and added then to the block 3 string
    block3 = ''
    e_bounds = ww_mesh.imesh.getTagHandle("e_groups")[ww_mesh.imesh.rootSet]
    line_count = 0

    #in the single e_group case, the "e_groups" tag returns a non-iterable float,
    # if this is the case, put this float into an array so that it can be iterated over
    if isinstance(e_bounds, float):
        e_bounds = [e_bounds]

    for e_bound in e_bounds:
        block3 += "  {0:1.5E}".format(e_bound)
        line_count += 1
        if line_count == 6:
           block3 += '\n'

    if line_count != 0:
        block3 += '\n'

    # get ww_data
    count = 0
    for e_group in e_groups:
        voxels = ww_mesh.iterateHex('xyz')
        ww_data = []
        count += 1
        for voxel in voxels:
            ww_data.append(ww_mesh.imesh.getTagHandle('ww_{0}_group_{1}'.format(particle, e_group))[voxel])
          
        # append ww_data to block3 string
        line_count = 0
        for ww in ww_data:
            if ww >= 0:
                block3 += ' '
                
            block3 += " {0:1.5E}".format(ww)
            line_count += 1

            if line_count == 6:
                block3 += '\n'
                line_count = 0

        if line_count != 0:
            block3 += '\n'


    out=file(output, 'w')
    out.write(block1)
    out.write(block2)
    out.write(block3)           



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
