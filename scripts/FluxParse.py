#!/usr/bin/env python
#This is the second version of FluxParse, which uses an array of numbers 
#instead of using a readlines()

import linecache
from optparse import OptionParser
import sys
from itaps import iMesh, iBase

#use for lines in filename
def find_meshtal_type(meshtal):
    neutron_index=-1
    photon_index =-1
    count=0
    meshtal_type=''
    while neutron_index == -1 and photon_index == -1 :
        line=linecache.getline(meshtal, count)
        neutron_index=line.find('neutron')
        photon_index=line.find('photon')
        count=count+1
        if count > 100 :
            print >>sys.stderr, 'Type of meshtal not detected in first 100 lines'
            sys.exit(1)
    if neutron_index != -1 :
        print 'This is a neutron meshtal file.'
        meshtal_type = 'n'
    if photon_index != -1 :
        print 'This is a photon meshtal file.'
        meshtal_type = 'p'
    
    return meshtal_type

def find_first_line(meshtal):
    table_heading ='   Energy         '
    n=1
    line=linecache.getline(meshtal, 1)
    while line[0:18] != table_heading :
        n=n+1
        line=linecache.getline(meshtal, n)
    m=n+1
    print 'Skipping Header:', n, 'lines'  
    return m #first line of data

def meshtal_to_array(meshtal, m):
    n=m
    line=linecache.getline(meshtal, n)
    array = []
    while line[:11] != '   Total   ' :
        column_count=0
        char_count=0
        column_data=[0]*6
        while column_count <= 5:
            if line[char_count] == ' ':
                char_count = char_count +1
            else :
                min_char = char_count
                while line[char_count] != ' ' and char_count<len(line)-1:
                    char_count=char_count +1
                max_char=char_count
                column_data[column_count]=float(line[min_char:max_char])
                column_count = column_count+1
        array.append(column_data)        
        n=n+1
        line=linecache.getline(meshtal, n)
    return array

def count_mesh_points(array) :
    j=1
    while abs(array[j][0]/array[0][0] - 1) < 0.00001 :
        j=j+1
    print 'Mesh points found:', j
    return j

def count_energy_bins(array):
    k=1
    for n in range(0,len(array)-1):
        if abs(array[n][0]/array[n+1][0] -1) > 0.00001 :
            k=k+1
    print 'Energy bins found:', k
    return k

def count_data_points(array):
    l=len(array)
    print 'Total data points found:', l
    return l

def count_delinations(array) :
    #Finding number or Z deliniations
    z=1
    while abs(array[1][3]-array[z+1][3])>0.001:
        z=z+1
        #Finding number of Y delinations
    y=1
    while abs(array[1][2]-array[1+z*y][2])>0.001:
        y=y+1
    #Finding number of X deliniations
    x=1
    while abs(array[1][1]-array[1+z*y*x][1])>0.001:
        x=x+1
    print 'Spacial Deliniations: (',x,',',y,',',z,')'
    return(x, y, z)

def check_meshtal_data(l, j, k, x, y, z) :
    if l != (j*k) :
        print >>sys.stderr, 'Number of data points does not equal meshpoints*energy groups'
        sys.exit(1)
    if x*y*z != j :
        print >>sys.stderr, 'Number of mesh points does not equal x*y*z'
        sys.exit(1)

def print_fluxin(array, j, k, norm, output_file, backwardbool):
    output=file(output_file, 'w')
    for t in range(0, j):
        pointoutput=''
        if backwardbool==False :
            a=0
            b=k
            c=1
        else :
            a=k-1
            b=-1
            c=-1
        for s in range(a, b, c):
           pointoutput+=str((array[s*j + t][4])*norm)+' '
           
           if (s+1)%8 == 0 & s != (k-1):
               pointoutput+='\n'
        output.write(pointoutput + '\n\n')
    print 'ALARA flux input file,', output_file , ', created sucessfully'

def tag_fluxes_preexisting(array, j, k, mestal_type, mesh_input, mesh_output):
    mesh = iMesh.Mesh()
    mesh.load(mesh_input)
    voxels = mesh.getEntities(iBase.Type.region)
    column_flux=[]
    column_error=[]
    count=0    
    for groupID in range(1,k+1): #need to add one for total fluxes
        tag_flux=mesh.createTag(meshtal_type+'_group_'+str(groupID),1,float)
        tag_error=mesh.createTag(meshtal_type+'_group_'+str(groupID)+'_error',1,float)
        for x in range(0,j):
            array_index=x+j*count            
            column_flux.append(array[array_index][4])
            column_error.append(array[array_index][5])
        count=count+1
        tag_flux[voxels]=column_flux
        tag_error[voxels]=column_error
        column_flux=[]
        column_error=[]
        mesh.save(mesh_output)
    if meshtal_type == 'n':
        print 'Tagged user supplied mesh with neutron fluxes'
    if meshtal_type == 'p':
        print 'Tagged user supplied mesh with photon fluxes'
   
if __name__=='__main__':
    print 'Parsing meshtal file'
    parser = OptionParser()
    parser.add_option('-b', action='store_true', dest='backward_bool', default=False, help='Print to ALARA fluxin in fluxes in decreasing energy')
    parser.add_option('-o', dest='fluxin_name', default='ALARAflux.in', help='Name of ALARA fluxin output file')
    parser.add_option('-m',  dest='mesh_input', default= 'none', help = 'Tag meshes onto user preexisting mesh, supply file name')
    parser.add_option('-p', dest='mesh_output', default='mesh.vtk', help = 'Name of mesh output file')
    parser.add_option('-s', action='store_true', dest='supress_mesh', default=False, help='Supress creation of mesh file, only fluxin file is created')
    (opts, args) = parser.parse_args()
    meshtal_type=find_meshtal_type(args[0])
    m=find_first_line(args[0])
    array=meshtal_to_array(args[0],m)
    j=count_mesh_points(array)
    k=count_energy_bins(array)
    l=count_data_points(array)
    x,y,z=count_delinations(array)
    check_meshtal_data(l, j, k, x, y, z)
    norm=float(args[1])
    print_fluxin(array, j, k, norm, opts.fluxin_name, opts.backward_bool)
    #if opts.mesh_input = 'none' and opts.supress_mesh == 'False'
    
    if opts.mesh_input != 'none':
        tag_fluxes_preexisting(array, j, k, meshtal_type, opts.mesh_input, opts.mesh_output)


