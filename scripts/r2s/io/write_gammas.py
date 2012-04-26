#!/usr/bin/env python 

######################################################################
#gen_gammas.py
######################################################################
# This python script reads the photon source strength tags from a
#  structured MOAB mesh, normalizes these values, and the creates the
#  'gammas' file to be used with a custom source.F90 routine in MCNP.
#
#
#
######################################################################

from optparse import OptionParser
from itaps import iBase,iMesh,iMeshExtensions
from r2s import alias
from scdmesh import ScdMesh, ScdMeshError


def gen_gammas_file_from_h5m(sm, outfile="gammas", do_alias=False):
    """Generate gammas file using information from tags on a MOAB mesh.
    
    ACTION: Method reads tags with photon source strengths from an h5m
    file and generates the gammas file for the modified KIT source.f90 routine.
    To do this, we generate 'meshstrengths' for each voxel and write this
    information to the gammas file, along with header information.
    REQUIRES: the .h5m moab mesh must have photon source strength tags of the
    form "phtn_src_group_###"
    Will read photon energy bin boundary values if the root set has the tag 
    PHTN_ERG (a list of floats)

    RECEIVES: The file (a moab mesh file) containing the mesh of interest.
    Optional: An output file name for the 'gammas' file; do_alias=True will
    generate the gammas_alias file with alias tables.
    """

    try:
        grouptag = sm.imesh.getTagHandle("phtn_src_group_001")
    except iBase.TagNotFoundError:
        print "ERROR: The file '{0}' does not contain tags of the " \
                "form 'phtn_src_group_#'".format(meshfile)
        return 0

    voxels = list(sm.iterateHex('xyz'))

    # Initialize list to first erg bin source strength value for each voxel
    meshstrengths = [float(grouptag[x]) for x in voxels]

    numergbins = 0

    # We now go through all photon energy groups and sum the individual bins
    #  to get the total source strength in each voxel
    for i in xrange(2,1000): #~ Arbitrary: we look for up to 1000 groups
        try:
            grouptag = sm.imesh.getTagHandle("phtn_src_group_{0:03d}".format(i))
            for cnt, vox in enumerate(voxels):
                meshstrengths[cnt] += float(grouptag[vox])
        except iBase.TagNotFoundError: 
            numergbins = i - 1
            break
    
    print "Found tags for for {0} photon energy bins.".format(numergbins)

    vols = calc_volumes_list(sm)

    if len(vols) != len(meshstrengths):
        print "ERROR: mismatch in calculated number of volumes ({0}) and " \
                "number of voxel source strengths " \
                "({1}).".format(len(vols), len(meshstrengths))
        return 0

    # We calculate the normalization factor as the sum over all voxels of:
    #  voxel volumetric source strength * voxel volume
    # Divided by the volume of all voxels with non-zero source strength.
    # This applies for variable voxel sizes in a structured mesh.
    numactivatedcells = 0
    sumvoxelstrengths = 0
    sourcevolumetotal = 0
    for cnt, meshstr in enumerate(meshstrengths):
        if meshstr > 0:
            numactivatedcells += 1
            sumvoxelstrengths += vols[cnt] * meshstr
            sourcevolumetotal += vols[cnt]
    print "The number of activated voxels and total number of voxels is " \
            "{0}/{1}".format(numactivatedcells, len(meshstrengths))
    
    # norm is the average volumetric source strength
    norm = sumvoxelstrengths / sourcevolumetotal

    # We now look for the tag with the energy bin boundary values
    try:
        phtn_ergs = sm.imesh.getTagHandle("PHTN_ERGS")
        myergbins = phtn_ergs[sm.imesh.rootSet] 
        print "Found a custom set of {0} energy bins in the PHTN_ERGS " \
                "tag.".format(len(myergbins)-1)

    # if there is no PHTN_ERGS tag, then we send an empty string in myergbins
    except iBase.TagNotFoundError: 
        myergbins = "" # _gen_gammas_header will skip the energies line

    # The header of the gammas file is created in outfile, and the file writing
    #  stream is returned to fw
    fw = _gen_gammas_header(sm, outfile, myergbins)

    if do_alias:
        for cnt, voxel in enumerate(voxels):
            sourcetotal = 0
            ergproblist = list()
            # We go through each energy group for the voxel and:
            # -sum up the total source strength (sourcetotal)
            # -make a list of bin source strengths and group #s (ergproblist)
            for i in xrange(1, numergbins + 1):
                sourcetotal += float(sm.imesh.getTagHandle( \
                        "phtn_src_group_{0:03d}".format(i))[voxel])
                ergproblist.append([float(sm.imesh.getTagHandle( \
                        "phtn_src_group_{0:03d}".format(i))[voxel]), i])

            # Special case if there is no source strength
            if sourcetotal == 0:
                fw.write(" ".join( ["0"]*(numergbins*3+1) ) + "\n")
                continue

            # Reduce the source strengths to fractional probabilities
            ergproblist = [ [x[0]/sourcetotal,x[1]] for x in ergproblist ]

            # And generate the alias table
            aliastable = alias.gen_alias_table(ergproblist)

            # We compactly format the alias table as a bunch of strings.
            # The following list comprehension uses a format specifying output
            #  of 12 characters, with 5 values after the decimal point and 
            #  scientific notation for the probability values, and integer 
            #  format for the energy group numbers
            aliasstrings = [ \
                    "{0:<12.5E} {1} {2}".format(x[0][0],x[0][1],x[1][1]) \
                    for x in aliastable ]

            # We write the alias table to one line, prepended by the source
            #  strength of the voxel divided by the average source strength per
            #  volume
            # sourcetotal*vols[cnt]/norm can be used as the particle's weight
            fw.write(str(sourcetotal*vols[cnt]/norm) + " " + \
                    " ".join(aliasstrings) + "\n")

    # Else, for each voxel, write the cummulative source strength at each energy
    else:
        for voxel in voxels:
            writestring = ""
            binval = 0.0
            for i in xrange(1, numergbins + 1):
                binval += float(sm.imesh.getTagHandle( \
                        "phtn_src_group_{0:03d}".format(i))[voxel])
                writestring += "{0:<12.5E}".format(binval/norm)
            fw.write(writestring + "\n")
    
    fw.close()

    print "The file '{0}' was created successfully".format(outfile)

    return 1


def _gen_gammas_header(scd, outfile, ergbins):
    """Open a stream to write the header information for a gammas file
    
    ACTION: Method writes the header lines for gammas file, and method
    is used by both gen_gammas_file_from_h5m() and gen_gammas_file_aliasing().
    RECEIVES: scd is an scdmesh.ScdMesh object.
    RETURNS: A file writing object, fw.
    """
    
    # calculate the mesh spacing in each direction

    fw = open(outfile, 'w')
    
    # write 1st line (intervals for x, y, z)
    extents = [scd.dims[3], scd.dims[4], scd.dims[5]]
    fw.write(" ".join([str(x) for x in extents]) + "\n")
    
    # create and write x mesh edges line (2nd line)
    fw.write(" ".join([str(x) for x in scd.getDivisions('x')]) + "\n")
    # create and write y mesh edges line (3rd line)
    fw.write(" ".join([str(y) for y in scd.getDivisions('y')]) + "\n")
    # create and write z mesh edges line (4th line)
    fw.write(" ".join([str(z) for z in scd.getDivisions('z')]) + "\n")

    # create and write 5th line (placeholder list of activated materials)
    fw.write(" ".join([str(x) for x in xrange(1,101)]) + "\n")

    # If storing the energy bins information, write line 6
    # Line starts with 'e', then the number of energy GROUPS, then
    #  lists all group boundaries
    if ergbins != "":
        fw.write("e " + str(len(ergbins)-1) + " " + \
                " ".join([str(x) for x in ergbins]) + "\n")

    return fw


def calc_volumes_list(scd):
    """Create list of voxel volumes for a cartesian mesh
    
    ACTION: Method creates a 1D list of voxel volumes
    RECEIVES: scd, a scdmesh.ScdMesh object.
    RETURNS: vols, a 1D list of voxel volumes in order 'xyz'

    NOTE: Voxel ordering follows meshtal file convention which is
     -for x for y iterate z
     -for x iterate y
     -iterate x
    """
    
    meshplanes = [ scd.getDivisions('x'),
                   scd.getDivisions('y'),
                   scd.getDivisions('z') ]

    oldz = meshplanes[2][0]
    oldy = meshplanes[1][0]
    oldx = meshplanes[0][0]

    nxdiv = len(meshplanes[0]) - 1
    nydiv = len(meshplanes[1]) - 1
    nzdiv = len(meshplanes[2]) - 1

    # create 1D list
    vols = [0] * (nxdiv * nydiv * nzdiv)

    for cntx, x in enumerate(meshplanes[0][1:]):
        oldy = meshplanes[1][0]
        for cnty, y in enumerate(meshplanes[1][1:]):
            oldz = meshplanes[2][0]
            for cntz, z in enumerate(meshplanes[2][1:]):
                # Calc volume here
                vols[nydiv*nzdiv*cntx + nzdiv*cnty + cntz] = \
                        (x - oldx) * \
                        (y - oldy) * \
                        (z - oldz)
                oldz = z
            oldy = y
        oldx = x
    
    return vols


def main():
    """ACTION: Method defines an option parser and handles command-line
    usage of this module.
    REQUIRES: command line arguments to be passed - otherwise prints help
    information.
    RECEIVES: N/A
    """

    usage = "usage: %prog input-h5m-file [options] arg"
    parser = OptionParser(usage)
    
    # Input and mesh file names
    parser.add_option("-o","--output",action="store",dest="output", \
            default="gammas",help="Option specifies the name of the 'gammas'" \
            "file. Default: %default")
    # Other options
    parser.add_option("-a","--alias",action="store_true",dest="alias", \
            default=False,help="Generate the gammas file with an alias table " \
            "of energy bins for each voxel. Default: %default \n\r" \
            "Default file name changes to 'gammas_alias' " \
            "\n\n" \
            "Creates the file gammas with the photon energy bins for each \
            voxel stored as alias tables. Reads directly from phtn_src file.\n\n \
            Each voxel's line corresponds with an alias table of the form: \
            [total source strength, p1, g1a, g1b, p2, g2a, g2b ... pN, gNa, gNb] \
            Where each p#, g#a, g#b are the info for one bin in the alias table." 
           )
   
    (options, args) = parser.parse_args()

    # Check for combination of default filename, and alias mode
    if options.alias and options.output == 'gammas':
        # Use a different default file name and print a message about this
        options.output = 'gammas_alias'
        print "NOTE: Generated file will use name 'gammas_alias' instead " \
            "of 'gammas'."

    # Create ScdMesh object, which also loads 'meshfile' into mesh.
    sm = ScdMesh.fromFile(args[0])

    gen_gammas_file_from_h5m(sm, options.output, options.alias)

    return 1


# Handles module being called as a script.
if __name__=='__main__':
    main()

