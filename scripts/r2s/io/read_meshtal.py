#!/usr/bin/env python
################################################################################
# meshtal_to_h5m.py
# Action: This script parses a  neutron or photon meshtal file, multiples the 
#         fluxes by a normalization factor (in particles/s), then either    
#         creates and tags a structred mesh with the fluxes, or tags a user 
#         supplied structured mesh with the fluxes.
# Inputs: Meshtal file, normalization factor, and optional structured mesh
#         (specified by the -m flag)
# Output: Structured mesh file in .h5m format. Mesh output name can be change
#         with the -o flag.
################################################################################
# Written by Elliott Biondo, Biondo@wisc.edu
###############################################################################
from itaps import iMesh, iBase
from optparse import OptionParser
import linecache
import sys
from r2s.scdmesh import ScdMesh, ScdMeshError

################################################################################

def find_tallies(meshtal) :
    """Searches the meshtal file to determine the number of tallies present and
    returns the tallies and lines where they are listed.
    
    Parameters
    ----------
    meshtal : string
        File path to meshtal file.

    Returns
    -------
    tally_numbers : list of strings
        List of tally numbers (as strings)
    tally_lines : list of integers
        List of the line numbers where tallies begin
    """
    tally_lines=[]
    tally_numbers = []
    count = 1;
    line = linecache.getline(meshtal, count)
    while line != '' :

        if line.split()[0:3] == ['Mesh', 'Tally', 'Number'] :
            tally_numbers.append(line.split()[3])
            tally_lines.append(count)
        count += 1;

        line = linecache.getline(meshtal, count)
    return tally_numbers, tally_lines

################################################################################

def find_meshtal_type(meshtal, tally_line) :
    """Searchs the meshtal header to determine if it is a neutron or photon 
    meshtally

    Parameters
    ----------
    meshtal : string
        File path to meshtal file.
    tally_line : int
        Line number in file where tally begins

    Returns
    -------
    meshtal_type : {'n', 'p'}
        Tally type; either neutron ('n') or photon ('p) is supported.
    """
    neutron_index = -1
    photon_index = -1

    count = tally_line
    meshtal_type = ''

    while neutron_index == -1 and photon_index == -1 :
        line = linecache.getline(meshtal, count)
        neutron_index = line.find('neutron')
        photon_index = line.find('photon')
        count = count+1
        if (count - tally_line) > 100 :
            print >>sys.stderr, 'Tally type not found in first 100 lines\n',\
                                 meshtal, ' may not be a meshtal file.'
            sys.exit(1)

    if neutron_index != -1 :
        print '\tThis is a neutron tally.'
        meshtal_type = 'n'

    if photon_index != -1 :
        print '\tThis is a photon tally.'
        meshtal_type = 'p'
    return meshtal_type


###############################################################################

def find_first_line(meshtal, tally_line) :
    """Searchs for the "Energy X Y Z" line, to determine the first line of data

    Parameters
    ----------
    meshtal : string
        File path to meshtal file.
    tally_line : int
        Line number in file where tally begins

    Returns
    -------
    m : int
        Line number of first data line for the tally in `meshtal`
    """
    heading = ['Result', 'Rel', 'Error']
    m = tally_line
    line_array = []
    while line_array[-3:] != heading :
        line = linecache.getline(meshtal,m)
        line_array = line.split()
        m += 1
        if (m-tally_line) > 100 :
            print >>sys.stderr,'Table heading not found in first 100 lines\n',\
                                meshtal, ' may not be a meshtal file.'
            sys.exit(1)

    return m #first line of data



###############################################################################

def find_mesh_bounds(meshtal,tally_line) :
    """Parse the header of the meshtal to get the x, y, z, and energy boundaries

    Parameters
    ----------
    meshtal : string
        File path to meshtal file.
    tally_line : int
        Line number in file where tally begins

    Returns
    -------
    ... : tuple of 4 ints 
        Tuple of the divisions in x, y, z and energy
    """
    #Locate line where 'X direction' appears
    line=''
    count=tally_line
    while line.find('direction:') == -1 :
        count += 1
        line=linecache.getline(meshtal, count)

        #Exit loop is spatial information is not found
        if count-tally_line > 100 :
            print >>sys.stderr,\
                 'Spacial bounderies not found in first 100 lines'
            sys.exit(1)
            
    #Create list of all spatial and energy bounderies
    divs=[]
    for x in (0,1,2) :
        divs.append(linecache.getline(meshtal, count + x).split()[2:])

    divs.append(linecache.getline(meshtal, count+3).split()[3:])
    
    print '\tMeshtal has dimensions ({0},{1},{2}) with {3} energy bin(s)'\
           .format(len(divs[0])-1,len(divs[1])-1, len(divs[2])-1, len(divs[3])-1)

    return (divs[0],divs[1],divs[2],divs[3])
   

###############################################################################

def tag_fluxes(meshtal, meshtal_type, m, spatial_points, \
               e_bins, sm, norm) :
    """Tags the fluxes from a meshtally to a structured mesh.

    Parameters
    ----------
    meshtal : string
        File path to meshtal file.
    meshtal_type : {'n', 'p'}
        Tally type; either neutron ('n') or photon ('p) is supported.
    m : int
        Line number of first data line for the tally in `meshtal`
    spatial_points : int
        Number of meshtally points (aka voxels)
    e_bins : int
        Number of energy bins in the meshtally
    sm : scdmesh.ScdMesh
        Structured mesh to tag fluxes to
    norm : float, optional
       Normalization factor to multiply into each flux value. 

    Returns
    -------
    N/A
    """
    
    voxels = list(sm.iterateHex('xyz'))
    
    for e_group in range(1, e_bins +1) : 
        # Create tags if they do not already exist
        if e_group != e_bins or e_bins == 1: # tag name for each E bin
            flux_str = '{0}_group_{1:03d}'.format(meshtal_type, e_group)
            error_str = '{0}_group_{1:03d}_error'.format(meshtal_type, e_group)
        elif e_group == e_bins : # tag name for totals group
            flux_str = meshtal_type + '_group_total'
            error_str = meshtal_type + '_group_total_error'

        try:
            tag_flux = sm.imesh.createTag(flux_str, 1, float)
        except iBase.TagAlreadyExistsError:
            tag_flux = sm.imesh.getTagHandle(flux_str)
        try:
            tag_error = sm.imesh.createTag(error_str ,1, float)
        except iBase.TagAlreadyExistsError:
            tag_error = sm.imesh.getTagHandle(error_str)

        #Create lists of data from meshtal file for energy group 'e_group'
        flux_data = list()
        error_data = list()
        for point in range(0, spatial_points) :
            flux_data.append( float(linecache.getline( meshtal,m+point+\
                               (e_group-1)*spatial_points ).split()[-2])*norm)
            error_data.append(float(linecache.getline( meshtal,m+point+\
                               (e_group-1)*spatial_points ).split()[-1]))

        #Tag data for energy group 'e_group' onto all voxels
        tag_flux[voxels] = flux_data
        tag_error[voxels] = error_data
    print "\tFluxes multiplied by source normalization of {0}".format(norm)


def read_meshtal( filename, tally_line, norm=1.0, **kw ):
    """Read an MCNP meshtal file and return a tagged structured mesh for it

    The optional normalization factor will be multiplied into each flux value.
    This can be used to rescale a tally if a tally multiplier was not used
    in the original MCNP problem.

    Parameters
    ----------
    filename : string
        File path to meshtal file.
    tally_line : int
        Line number in file where tally begins
    norm : float, optional
       Normalization factor to multiply into each flux value. 
    Keyword arguments:
        smesh: An existing scdmesh on which to tag the fluxes.  
               A ScdMeshError is raised if this mesh has incompatible ijk dims

    Returns
    -------
    sm : ScdMesh object
        Opened structured mesh from filename, with meshtally data tagged
    """
    # Getting relevant information from meshtal header
    meshtal_type = find_meshtal_type( filename, tally_line )
    m = find_first_line( filename, tally_line )
    x_bounds, y_bounds, z_bounds, e_groups = \
            find_mesh_bounds( filename, tally_line )
 
    # Calculating pertinent information from meshtal header and input
    spatial_points = (len(x_bounds)-1)*(len(y_bounds)-1)*(len(z_bounds)-1)
    if len(e_groups) > 2 :
        e_bins = len(e_groups) #don't substract 1; cancels with totals bin
    elif len(e_groups) == 2 : #for 1 energy bin, meshtal doesn't have TOTALS group
        e_bins = 1 
    sm = ScdMesh(x_bounds, y_bounds, z_bounds)

    if 'smesh' in kw:
        dims = kw['smesh'].dims
        if dims != sm.dims:
            raise ScdMeshError( \
                    "Incorrect dimension in preexisting structured mesh")
        sm = kw['smesh']

    # Tagging structured mesh with particle type at root level
    tag_particle = sm.imesh.createTag("particle", 1, int)

    if meshtal_type == 'n':
        tag_particle[sm.imesh.rootSet] = 1

    elif meshtal_type == 'p':
        tag_particle[sm.imesh.rootSet] = 2

    # Tagging structured mesh with energy lower bounds (at root level)
    # only the upper bounds are tagged, so the first value in e_groups,
    # which is always 0.000 is ommitted.
    tag_e_bin = sm.imesh.createTag("E_upper_bounds", len(e_groups) - 1, float)
    tag_e_bin[sm.imesh.rootSet] = e_groups[1:]

    # Tagging structured mesh
    tag_fluxes(filename, meshtal_type, m, spatial_points,
               e_bins, sm, norm)

    return sm

###############################################################################

###############################################################################
def main( arguments = None ) :

    # Instantiate option parser
    parser = OptionParser\
             (usage='%prog <meshtal_file> <normalization_factor> [options]')

    parser.add_option('-o', dest='mesh_output', default='flux_mesh.h5m',\
                      help = 'Name of mesh output file, default=%default.\
                             For meshtal files with multiple tallies,\
                             if the -o flag is used all tallies must be named,\
                             with file names seperated by commas and no spaces\
                             (e.g. "tally14.h5m,tally24.h5m,tally34.h5m")')
    parser.add_option('-n', dest='norm', default=None,
                      help='Normalization factor, default=%default,\
                            For meshtal files with multiple tallies, if the -n\
                            flag is used, a normalization factor must be\
                            specified for all tallies, seperated by commas but \
                            not spaces (eg. -n 1.1,2.2,3.3) ')
    parser.add_option('-m', dest='smesh_filename', default=None,
                      help='Preexisting mesh on which to tag fluxes')
                         

    (opts, args) = parser.parse_args(arguments)
    
    #if len(args) != 2 :
     #   parser.error('\nNeed 1 argument: meshtal file')
    print "\n\nRunning read_meshtal.py"
    tally_numbers, tally_lines = find_tallies(args[1])
    print "Number of tallies found: {0}\nTally number(s): {1}" \
                                     .format(len(tally_numbers), tally_numbers)

    # Parse input from options parser, generate default values
    if opts.norm :
        norm = opts.norm.split(',')
    else :
        norm = [1]*len(tally_numbers)

    if opts.mesh_output !='flux_mesh.h5m' :
        mesh_output = opts.mesh_output.split(',')
    else:
        mesh_output = []
        for n in range(0, len(tally_numbers)) :
            if len(tally_numbers) == 1 :
                mesh_output.append('flux_mesh.h5m')
            else :
                mesh_output.append('flux_mesh_tally{0}.h5m'.format(tally_numbers[n]))

    # Convert each tally to h5m and name accordingly
    for n in range(0,len(tally_numbers)) :
        print "\nNow parsing tally number {0}".format(tally_numbers[n])
        if opts.smesh_filename:
            alt_sm = ScdMesh.fromFile(opts.smesh_filename)
            sm = read_meshtal(args[1], tally_lines[n], float(norm[n]), smesh=alt_sm)
        else:
            sm = read_meshtal(args[1], tally_lines[n],float(norm[n]))
        sm.scdset.save(mesh_output[n])

        print "\tSaved tally {0} as {1}".format(tally_numbers[n], mesh_output[n])
    print "\nStructured mesh tagging complete\n\n"



###############################################################################
if __name__ == '__main__':
    # No arguments case -> print help output
    if len(sys.argv) == 1:
        sys.argv.append('-h')
    main( sys.argv )
