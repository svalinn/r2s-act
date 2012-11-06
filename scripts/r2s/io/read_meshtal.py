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
from itaps import iMesh
from optparse import OptionParser
import linecache
import sys
from scdmesh import ScdMesh, ScdMeshError

################################################################################
#Searches the meshtal file to determine the number of tallies present and

def find_tallies(meshtal) :
    tally_lines=[]
    tally_numbers = []
    count = 1;
    line=linecache.getline(meshtal,count)
    while line != '' :

        if line.split()[0:3] == ['Mesh', 'Tally', 'Number'] :
            tally_numbers.append(line.split()[3])
            tally_lines.append(count)
        count += 1;

        line = linecache.getline(meshtal, count)
    return tally_numbers, tally_lines

################################################################################
#Searchs the meshtal header to determine if it is a neutron or photon meshtal

def find_meshtal_type(meshtal, tally_line) :

    neutron_index= -1
    photon_index = -1

    count= tally_line
    meshtal_type=''

    while neutron_index == -1 and photon_index == -1 :
        line=linecache.getline(meshtal, count)
        neutron_index=line.find('neutron')
        photon_index=line.find('photon')
        count=count+1
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
#Searchs for the "Energy X Y Z" line, to determine the first line of data

def find_first_line(meshtal, tally_line) :

    heading=['Result', 'Rel', 'Error']
    m=tally_line
    line_array=[]
    while line_array[4:7] != heading :
        line=linecache.getline(meshtal,m)
        line_array=line.split()
        m += 1
        if (m-tally_line) > 100 :
            print >>sys.stderr,'Table heading not found in first 100 lines\n',\
                                meshtal, ' may not be a meshtal file.'
            sys.exit(1)

    return m #first line of data




###############################################################################
#Parse the header of the meshtal to get the X, Y, Z, and energy boundaries
def find_mesh_bounds(meshtal,tally_line) :

    #Locate line where 'X direction' appears
    line=''
    count=tally_line
    while line.find('direction:') == -1 :
        count += 1
        line=linecache.getline(meshtal, count)

        #Exit loop is spacial information is not found
        if count-tally_line > 100 :
            print >>sys.stderr,\
                 'Spacial bounderies not found in first 100 lines'
            sys.exit(1)
            
    #Create list of all spacial and energy bounderies
    divs=[]
    for x in (0,1,2) :
        divs.append(linecache.getline(meshtal, count + x).split()[2:])
    divs.append(linecache.getline(meshtal, count+3).split()[3:])
    
    print '\tMeshtal has dimensions ({0},{1},{2}) with {3} energy bin(s)'\
           .format(len(divs[0])-1,len(divs[1])-1, len(divs[2])-1, len(divs[3])-1)

    return (divs[0],divs[1],divs[2],divs[3])
   

###############################################################################

def tag_fluxes(meshtal, meshtal_type, m, spacial_points, \
               e_bins, sm,  norm ) :
    
    voxels=list(sm.iterateHex('xyz'))
    
    for e_group in range(1, e_bins +1) : 

        if e_group != e_bins: #create a new tag for each E bin
            tag_flux=sm.imesh.createTag\
                    ('{0}_group_{1:03d}'.format(meshtal_type, e_group),1,float)
            tag_error=sm.imesh.createTag\
                    ('{0}_group_{1:03d}_error'.format(meshtal_type, e_group),1,float)
        elif e_group==e_bins or e_bins == 1: #create a tags for totals group
            tag_flux=sm.imesh.createTag(meshtal_type+'_group_total',1,float)
            tag_error=sm.imesh.createTag(meshtal_type+'_group_total_error',1,float)

        #Create lists of data from meshtal file for energy group 'e_group'
        flux_data=[]
        error_data=[]
        for point in range(0, spacial_points) :
            flux_data.append( float(linecache.getline( meshtal,m+point+\
                               (e_group-1)*spacial_points ).split()[4])*norm)
            error_data.append(float(linecache.getline( meshtal,m+point+\
                               (e_group-1)*spacial_points ).split()[5]))

        #Tag data for energy group 'e_group' onto all voxels
        tag_flux[voxels]=flux_data
        tag_error[voxels]=error_data
    print '\tFluxes multiplied by source normalization of {0}'.format(norm)

def read_meshtal( filename, tally_line, norm,  **kw ):
    """Read an MCNP meshtal file and return a structured mesh for it

    The optional normalization factor will be multipled into each flux value.
    This can be used to rescale a tally if a tally multiplier was not used
    in the original MCNP problem.

    Keyword arguments:
        smesh: An existing scdmesh on which to tag the fluxes.  
               A ScdMeshError is raised if this mesh has incompatible ijk dims
    """
    #Getting relevant information from meshtal header
    meshtal_type=find_meshtal_type( filename, tally_line )
    m=find_first_line( filename, tally_line )
    x_bounds, y_bounds, z_bounds, e_bounds = find_mesh_bounds( filename, tally_line )
 
    #Calculating pertainent information from meshtal header and input
    spacial_points=(len(x_bounds)-1)*(len(y_bounds)-1)*(len(z_bounds)-1)
    if len(e_bounds) > 2 :
        e_bins=len(e_bounds) #dont substract 1; cancels with totals bin
    elif len(e_bounds) == 2 : #for 1 energy bin, meshtal doesn't have TOTALS group
        e_bins=1 
    sm = ScdMesh(x_bounds, y_bounds, z_bounds)

    if 'smesh' in kw:
        dims = kw['smesh'].dims
        if dims != sm.dims:
            raise ScdMeshError('Incorrect dimension in preexisting structured mesh')
        sm = kw['smesh']

    #Tagging structured mesh
    tag_fluxes(filename, meshtal_type, m, spacial_points,
               e_bins, sm, norm)

    return sm

###############################################################################

def main( arguments = None ) :

   #Instantiate option parser
    parser = OptionParser\
             (usage='%prog <meshtal_file> <normalization_factor> [options]')

    parser.add_option('-o', dest='mesh_output', default=None,\
                      help = 'Name of mesh output file, default=%default')
    parser.add_option('-n', dest='norm', default=None,
                      help = 'Normalization factor, default=%default')
    parser.add_option('-m', dest='smesh_filename', default=None,
                      help='Preexisting mesh on which to tag fluxes')
                         

    (opts, args) = parser.parse_args(arguments)
    
    #if len(args) != 2 :
     #   parser.error('\nNeed 1 argument: meshtal file')
    print "\n\nRunning read_meshtal.py"
    tally_numbers, tally_lines =find_tallies(args[1])
    print 'Number of tallies found: {0}\nTally number(s): {1}'\
                                     .format(len(tally_numbers), tally_numbers)

    # Parse input from options parser, generate default values
    if opts.norm :
        norm = opts.norm.split(',')
    else :
        norm=[1]*len(tally_numbers)

    if opts.mesh_output :
        mesh_output = opts.mesh_output.split(',')
    else:
        mesh_output=[]
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
    print '\nStructured mesh tagging complete\n\n'



###############################################################################
if __name__ == '__main__':
    main( sys.argv )
