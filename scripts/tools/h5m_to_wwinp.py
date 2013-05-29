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


def write_wwinp(ww_mesh, totals_bool, output):
    """This funtion reads a WW mesh file and prints out a corresponding WWIMP
       with the name <output>.

    Parameters
    ----------
    ww_mesh : ScdMesh
        A mesh tagged with weight window lower bounds, with tag names in the 
        form "ww_X_group_YYY" where X is the particle type (n or p) and YYY is 
        the energy group. Tags for "particle" (1 for neutron, 2 for photon) and
        "E_upper_bounds" (a vector of floats for the upper energy bounds) must 
        also exist. This mesh is ostensibly created by magic.py or 
        wwinp_to_h5m.py.
    totals_bool : True or False
        Determines if the function should look for tags in the form 
        "ww_X_group_YYY" (totals_bool = False) or "ww_X_group_total" 
        (totals_bool = True).
    output : The name of the wwinp output file
    """

    # find wwinp type
    particle_int = ww_mesh.imesh.getTagHandle('particle')[ww_mesh.imesh.rootSet]

    # create block 1 string
    block1 = '         1         1         '

    # add particle specifier
    if particle_int == 1:
        block1 += '1'
        particle = 'n' # needed for writting output
    else:
        block1 += '2'
        particle = 'p' # needed for writting output

    # find number of energy groups

    if totals_bool == False:
        e_upper_bounds = ww_mesh.imesh.getTagHandle("E_upper_bounds")[ww_mesh.imesh.rootSet]

    elif totals_bool == True:
        e_upper_bounds = [100]
    #in the single energy group case, the "E_upper_bounds" tag returns a non-iterable float,
    # if this is the case, put this float into an array so that it can be iterated over
    if isinstance(e_upper_bounds, float):
        e_upper_bounds = [e_upper_bounds]

    # add 10 to specify cartesian geometry
    block1 += '        10                     '
    # add date and time
    now = datetime.datetime.now()
    block1 += '{0:02d}/{1}/{2} {3}:{4}:{5}\n'\
        .format(now.month, now.day, str(now.year)[2:], now.hour, now.minute, \
        now.second)
    # if it is a photon mesh, append the number of neutron energy groups, zero.
    if particle_int == 2:
        block1 += '         0'

    # append number of energy groups
    block1 += '         {0}\n'.format(len(e_upper_bounds))

    # find mesh spacial bounds
    x, y, z = [ww_mesh.getDivisions('x'), ww_mesh.getDivisions('y'),\
        ww_mesh.getDivisions('z')]

    # find fine/coarse mesh points
    coarse_points = [[],[],[]]
    nfm = [[],[],[]]
    for i, points in enumerate([x, y, z]):
        coarse_points[i].append(points[0])
        j = 1
        while j < len(points)-1:
            fine_count = 1
             #floating point comparison: need to be careful because this characterizes
             #coarse vs. fine. That is why 1.01E-2 is used.
            while abs((points[j] - points[j-1]) - (points[j+1] - points[j])) <= 1.01E-2: 
               fine_count += 1
               j += 1
               if j == len(points) - 1:
                   break


            nfm[i].append(fine_count)
            coarse_points[i].append(points[j])
            j += 1

        # if j is on the second to last value, then you can't restart the loop 
        # but the last value has not been accounted for. This occures when the 
        # last two mesh points are both coarse (with one fine mesh in between)
        # this last case handles this final special case
        if j == len(points)-1:
            nfm[i].append(1)
            coarse_points[i].append(points[j])

    # append the rest of block 1
    block1 += " {0: 1.5E} {1: 1.5E} {2: 1.5E}"\
        .format(sum(nfm[0]), sum(nfm[1]), sum(nfm[2]))

    block1 += " {0: 1.5E} {1: 1.5E} {2: 1.5E}\n"\
        .format(coarse_points[0][0], coarse_points[1][0], coarse_points[2][0])

    # when printing number of coarse mesh points, must subtract 1. This code
    # (h5m_to_wwinp.py) is considering the origin a coarse mesh point whereas MCNP
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
    line_count = 0

    for e_upper_bound in e_upper_bounds:
        block3 += "  {0:1.5E}".format(e_upper_bound)
        line_count += 1
        if line_count == 6:
           block3 += '\n'

    if line_count != 0:
        block3 += '\n'

    # get ww_data
    count = 0
    for e_group in range(1, len(e_upper_bounds) + 1):
        voxels = ww_mesh.iterateHex('zyx')
        ww_data = []
        count += 1
        for voxel in voxels:
            if totals_bool == False:
                ww_data.append(ww_mesh.imesh.getTagHandle('ww_{0}_group_{1:03d}'.format(particle, e_group))[voxel])

            elif totals_bool == True:
                ww_data.append(ww_mesh.imesh.getTagHandle('ww_{0}_group_total'.format(particle))[voxel])
          
        # append ww_data to block3 string
        line_count = 0
        for ww in ww_data:
                
            block3 += " {0: 1.5E}".format(ww)
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




def main( arguments = None ):

    #Instatiate options parser
    parser = OptionParser\
             (usage='%prog <ww mesh> [options]')

    parser.add_option('-o', dest='output_name', default='wwinp.out',\
        help='Name of WWINP output file, default=%default')

    parser.add_option('-t', action='store_true', dest='totals_bool',\
        default=False, \
        help='If multiple energy groups exist, only use Total \
         default=%default')

    (opts, args) = parser.parse_args( arguments )

    if len(args) != 1:
        parser.error\
        ( '\nNeed exactly 1 argument: <ww mesh>' )

    # load mesh
    ww_mesh = ScdMesh.fromFile(args[0])


    write_wwinp(ww_mesh, opts.totals_bool, opts.output_name)

    print "\tWrote WWINP file '{0}'".format(opts.output_name)

    print "Complete"


if __name__ == '__main__':
    # No arguments case -> print help output
    if len(sys.argv) == 1:
        sys.argv.append('-h')

    main()
