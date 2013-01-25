#!/usr/bin/env python
# See MCNP5 Appendix J

# python imports
from optparse import OptionParser
import linecache
import sys
# MOAB imports
from itaps import iMesh
from itaps import iBase
# r2s imports
from r2s.scdmesh import ScdMesh, ScdMeshError

def cartesian(wwinp, output):
    """This function reads in a cartesian WWINP file and outputs tagged, 
        structured mesh .h5m file with name "output".
    """

    print "Parsing Cartesian WWINP"

    # collect easy to parse energy group and mesh sized info
    num_e_bins = int(linecache.getline(wwinp, 2).split()[0])
    # total number of fine mesh points
    nfx, nfy, nfz = \
        [int(float(x)) for x in linecache.getline(wwinp, 3).split()[0:3]]
    x0, y0, z0 = [float(x) for x in linecache.getline(wwinp, 3).split()[3:6]]
    # numer of course points
    ncx, ncy, ncz = \
        [int(float(x)) for x in linecache.getline(wwinp, 4).split()[0:3]]

    # get the x, y, and z bounds
    x_bounds, x_last_line = block_2_bounds(wwinp, 5, ncx)
    y_bounds, y_last_line = block_2_bounds(wwinp, x_last_line + 1, ncy)
    z_bounds, z_last_line = block_2_bounds(wwinp, y_last_line + 1, ncz)

    # create structured mesh these bounds
    sm = ScdMesh(x_bounds, y_bounds, z_bounds)
    
    # Find the first line of WW values by counting through the e_bin values
    # until the expected number of e_bins is reached
    e_bins = []
    line_num = z_last_line + 1
    while len(e_bins) < num_e_bins:
        e_bins += \
            [float(x) for x in linecache.getline(wwinp, line_num).split()]
        line_num += 1
    ww_first_line = line_num

    # tag structured mesh with WW values
    tag_mesh(sm, wwinp, ww_first_line, num_e_bins, nfx*nfy*nfz, output)



def block_2_bounds(wwinp, line_num, nc):
    """This function reads wwinp starting at a given line, and returns bounds
       for the spacial varible beginging on that line. First it pulls out
       vectors from Block 2 data (Appendix J) in the form:

       x0 nfmx(1) x(1) ry(1) nfmx(2) x(2) ry(2) ... nfmx(ncx) x(ncx) rx(ncx)
    
       It does this by considering the number of course mesh points, nc. Then
       The mesh bounds for the structured mesh are parsed out and returned as
       a vector.
    """

    # parse raw values from wwinp
    raw = []
    while len(raw) < 3*nc + 1:
        raw += \
            [float(x) for x in linecache.getline(wwinp, line_num).split()]
        line_num += 1

    last_line = line_num - 1 # for loop goes the last line by one

    # remove all the rx(i)/ry(i)/rz(i) values that contaminated the raw list
    removed_values = [raw[0]]
    for i in range(1, len(raw)):
        if i % 3 != 0:
            removed_values.append(raw[i])

    # expaned out nfx/nfy/nfx values to get structured mesh bounds
    bounds = []
    for i in range(0, len(removed_values)):
        if i % 2 == 0:
            bounds.append(removed_values[i])
        else:
            for j in range(1, int(removed_values[i])):
                bounds.append((removed_values[i+1] - removed_values[i-1])*j\
                    /removed_values[i] + removed_values[i-1])

    return bounds, last_line


def tag_mesh(sm, wwinp, ww_first_line, num_e_bins, nf, output):
    """This function reads in a structured and tags it with ww values from 
       wwinp then saves to output.
    """
    # ordered voxels, z changes fastest, then y, then x.
    voxels=list(sm.iterateHex('xyz'))

    # iterate over energy groups
    line_num = ww_first_line
    for i in range(1, num_e_bins +1):
        # Create tags for e_group
        tag_name = 'e_group_{0:03d}'.format(i) # good sorting for up to 999 groups
        tag_ww = sm.imesh.createTag(tag_name, 1, float)
        
        # Get all data for energy group i
        ww_data = []
        while len(ww_data) < nf:
            ww_data += \
                [float(x) for x in linecache.getline(wwinp, line_num).split()]
            line_num += 1

        tag_ww[voxels] = ww_data # tag data to voxels

    sm.scdset.save(output) # save to output

      
          
def cylindrical(wwinp, output):
    """ This function has not been made yet, so right now it just returns an
        error message.
    """
    print "Cylindrical WWINP not currently supported"


def main(arguments=None):
    parser = OptionParser(usage='%prog <wwinp_file> [options]')
    parser.add_option('-o', dest='output', default='wwinp.h5m',\
        help='Name of ALARA matlib output file, default=%default')
    (opts, args) = parser.parse_args(arguments)

    # determine nr from MCNP5 manual Table J.2
    # nr = 10 is Cartesian and nr = 16 is cylindrical
    nr = linecache.getline(args[0],1).split()[3]
    if int(nr) == 10:
        cartesian(args[0], opts.output)
    elif int(nr) == 16:
        cylindrical(args[0], opts.output)        

if __name__ == '__main__':
    # No arguments case -> print help output
    if len(sys.argv) == 1:
        sys.arv.append('-h')

    main()

