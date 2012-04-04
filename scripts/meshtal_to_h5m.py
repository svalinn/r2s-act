#!/usr/bin/env python
###############################################################################
# meshtal_to_h5m.py
# Action: This script parses a  neutron or photon meshtal file, multiples the 
#         fluxes by a normalization factor (in particles/s), then either    
#         creates and tags a structred mesh with the fluxes, or tags a user 
#         supplied structured mesh with the fluxes.
# Inputs: Meshtal file, normalization factor, and optional structured mesh
#         (specified by the -m flag)
# Output: Structured mesh file in .h5m format. Mesh output name can be change
#         with the -o flag.
###############################################################################

from itaps import iMesh
import scdmesh
from optparse import OptionParser
import linecache
import sys
from scdmesh import ScdMesh

###############################################################################
#Searchs the meshtal header to determine if it is a neutron or photon meshtal

def find_meshtal_type(meshtal) :

    neutron_index=-1
    photon_index =-1
    count=1
    meshtal_type=''

    while neutron_index == -1 and photon_index == -1 :
        line=linecache.getline(meshtal, count)
        neutron_index=line.find('neutron')
        photon_index=line.find('photon')
        count=count+1
        if count > 100 :
            print >>sys.stderr, 'Meshtal type not detected in first 100 lines;\
                                 check to make sure this is a meshtal file'
            sys.exit(1)

    if neutron_index != -1 :
        print 'Parsing neutron meshtal file.'
        meshtal_type = 'n'

    if photon_index != -1 :
        print 'Parsing photon meshtal file.'
        meshtal_type = 'p'

    return meshtal_type


###############################################################################
#Searchs for the "Energy X Y Z" line, to determine the first line of data

def find_first_line(meshtal) :

    heading=['Energy', 'X','Y', 'Z', 'Result', 'Rel', 'Error']
    m=1
    line_array=[]
    while line_array != heading :
        line=linecache.getline(meshtal,m)
        line_array=line.split()
        m += 1
    return m #first line of data




###############################################################################
#Parse the header of the meshtal to get the X, Y, Z, and energy boundaries
def find_mesh_bounds(meshtal) :

    line=''
    count=0
    while line.find('X direction:') == -1 :
        count += 1
        line=linecache.getline(meshtal, count)
   
    divs=[]
    for x in (0,1,2) :
      divs.append(linecache.getline(meshtal, count + x).split()[2:])
    divs.append(linecache.getline(meshtal, count+3).split()[3:])

    print 'Meshtal dimensions: ({0},{1},{2} with {3} energy bins + Total bin)'.format\
           (len(divs[0])-1,len(divs[1])-1, len(divs[2])-1, len(divs[3])-2)

    return (divs[0],divs[1],divs[2],divs[3])
   

###############################################################################

def tag_fluxes(meshtal, meshtal_type, m, spacial_points, \
               e_bins, sm, mesh, norm, mesh_output) :
    print spacial_points
    voxels=list(sm.iterateHex('xyz'))
    print e_bins
    for e_group in range(1, e_bins +1) : #create a new tag for each E bin
        if e_group != e_bins:
            tag_flux=sm.mesh.createTag\
                    ('{0}_group_{1:03d}'.format(meshtal_type, e_group),1,float)
            tag_error=sm.mesh.createTag\
                    ('{0}_group_{1:03d}_error'.format(meshtal_type, e_group),1,float)
        else :
            tag_flux=sm.mesh.createTag(meshtal_type+'_group_total',1,float)
            tag_error=sm.mesh.createTag(meshtal_type+'_group_total_error',1,float)

        flux_data=[]
        error_data=[]
        for point in range(0, spacial_points) :
           # print float(linecache.getline( meshtal,m+point+(e_group-1)*spacial_points ).split()[4])
            flux_data.append( float(linecache.getline( meshtal,m+point+(e_group-1)*spacial_points ).split()[4])*norm)
            error_data.append(float(linecache.getline( meshtal,m+point+(e_group-1)*spacial_points ).split()[5]))
        print '\n\n\n\n'
        tag_flux[voxels]=flux_data
        tag_error[voxels]=error_data
        #print e_group
    sm.scdset.save(mesh_output)
    print 'Structed mesh creation complete'

###############################################################################

def main( arguments = None ) :

   #Instantiate option parser
    parser = OptionParser\
             (usage='%prog <meshtal_file> <normalization_factor> [options]')

    parser.add_option('-o', dest='mesh_output', default='flux_mesh.h5m',\
                      help = 'Name of mesh output file, default=%default')

    parser.add_option('-m',  dest='mesh_input', default= 'False',\
                      help = 'Tags fluxes onto a pre-existing structred mesh,\
                              supply the path to the file')

    (opts, args) = parser.parse_args( arguments )
    
    if len(args) != 2 :
        parser.error( 'Need exactly 2 arguments: \
                       meshtal file and normalization factor' )


    #Calling functions to run file
    meshtal_type=find_meshtal_type(args[0])
    m=find_first_line(args[0])
    x_bounds, y_bounds, z_bounds, e_bounds = find_mesh_bounds(args[0])
 
    spacial_points=(len(x_bounds)-1)*(len(y_bounds)-1)*(len(z_bounds)-1)
    e_bins=len(e_bounds) #dont substract 1; cancels with totals bin
    print e_bins

    #total_points=int(spacial_points*e_bins) 

    mesh=iMesh.Mesh()
    if opts.mesh_input == 'False' :        
        sm=scdmesh.ScdMesh(mesh, x_bounds, y_bounds, z_bounds)
    else:
        sm = ScdMesh.fromFile(iMesh.Mesh(), opts.mesh_input)
    norm=float(args[1])
    tag_fluxes(args[0], meshtal_type, m, spacial_points, \
               e_bins, sm, mesh, norm, opts.mesh_output)



###############################################################################
if __name__ == '__main__':
    main()
