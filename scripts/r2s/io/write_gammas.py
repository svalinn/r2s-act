#!/usr/bin/env python 

######################################################################
# write_gammas.py
######################################################################
# This python script reads the photon source strength tags from a
#  structured MOAB mesh, normalizes these values, and the creates the
#  'gammas' file to be used with a custom source.F90 routine in MCNP.
#
#
#
######################################################################

import os.path
from datetime import datetime
from optparse import OptionParser
from itaps import iBase,iMesh,iMeshExtensions

from r2s.scdmesh import ScdMesh, ScdMeshError


def gen_gammas_file_from_h5m(sm, outfile="gammas", sampling='v', \
        do_bias=False, cumulative=False, cust_ergbins=False, **kwargs):
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
    Optional: An output file name for the 'gammas' file; do_bias=True will add
    any values found on the PHTN_BIAS tag to the gammas file.
    """

    try:
        grouptag = sm.imesh.getTagHandle("phtn_src_group_001")
    except iBase.TagNotFoundError:
        print "ERROR: The structured mesh does not contain tags of the " \
                "form 'phtn_src_group_#.'"
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
    numactivatedcells = 0 # number of voxels that have nonzero source strength
    sumvoxelstrengths = 0 # total photon source strength in entire model
    sourcevolumetotal = 0 # total activated volume in model
    for cnt, meshstr in enumerate(meshstrengths):
        if meshstr > 0:
            numactivatedcells += 1
            sumvoxelstrengths += vols[cnt] * meshstr
            sourcevolumetotal += vols[cnt]

    _tag_sumvoxelstrengths(sm, sumvoxelstrengths)

    print "The number of activated voxels and total number of voxels is " \
            "{0}/{1}".format(numactivatedcells, len(meshstrengths))
    print "The total photon source strength of the model is {0:03e} photons/s. " \
            "This is stored in the PHTN_SRC_TOTAL tag".format(sumvoxelstrengths)

    # This is command line call is useful for tracking sumvoxelstrengths
    os.system("echo {0:03e} >> phtn_src_totals".format(sumvoxelstrengths))
    
    # norm is the average volumetric source strength (phtns/s/cm3)
    try:
        norm = sumvoxelstrengths / sourcevolumetotal
    except ZeroDivisionError:
        print "ERROR: Zero photon source strength was found on the mesh."
        return 0

    if cust_ergbins:
        # We now look for the tag with the energy bin boundary values
        try:
            phtn_ergs = sm.imesh.getTagHandle("PHTN_ERGS")
            myergbins = phtn_ergs[sm.scdset] 
            print "Found a custom set of {0} energy bins in the PHTN_ERGS " \
                    "tag.".format(len(myergbins)-1)

        # if there is no PHTN_ERGS tag, then send an empty string in myergbins
        except iBase.TagNotFoundError: 
            print "Could not find PHTN_ERGS tag with custom energy bins."
            myergbins = "" # _gen_gammas_header will skip the energies line
    else: myergbins = ""

    # If the user has enabled adding bias information to the gammas file,
    #  check to see if there are corresponding tags on the mesh.
    if do_bias:
        # We look for the tag handle for voxel biasing information
        try:
            bias_tag = sm.imesh.getTagHandle("PHTN_BIAS")
            have_bias_info = True
            print "Found tags for biasing photon production based on source " \
                    "voxel."

        except iBase.TagNotFoundError:
            print "The option for biasing photon production was chosen, "\
                    "but corresponding tags were not found on the mesh."
            have_bias_info = False

    else:
        have_bias_info = False

    # The header of the gammas file is created in outfile, and the file writing
    #  stream is returned to fw
    fw = _gen_gammas_header(sm, outfile, sampling, myergbins, have_bias_info, \
            cumulative, **kwargs)

    for cnt, voxel in enumerate(voxels):
        sourcetotal = 0
        ergproblist = list()
        # We go through each energy group for the voxel and:
        # -make list of energy bin source strengths & group #s (ergproblist)
        # -sum up the total source strength (sourcetotal)
        #
        # Note an important distinction depending on sampling approach:
        # -We account for voxel volume in voxel sampling
        # -We do not do this for uniform sampling, because it is already
        #   accounted for - more particles start in a voxel if it is larger
        # How to think of this difference: for correct 'normalization' in the 
        #  sampling process, we want photons/s/voxel for voxel sampling, and 
        #  photons/s/volume for uniform sampling.
        for i in xrange(1, numergbins + 1):
            if sampling == 'v':
                ergproblist.append(float(vols[cnt] * sm.imesh.getTagHandle( \
                        "phtn_src_group_{0:03d}".format(i))[voxel]) / norm)
            elif sampling == 'u':
                ergproblist.append(float(sm.imesh.getTagHandle( \
                        "phtn_src_group_{0:03d}".format(i))[voxel]) / norm)

            sourcetotal += ergproblist[i-1]
            if cumulative: ergproblist[i-1] = sourcetotal

        if have_bias_info:
            bias = str(bias_tag[voxel]) + " "
        else: bias = ""

        # Special case if there is no source strength: write line full of 0's
        if sourcetotal == 0:
            fw.write(" ".join( \
                    ["0"]*(numergbins + int(bool(have_bias_info))) ) \
                    + "\n")
                    # int(bool()) ensures either 1 or 0 is added
            continue

        if have_bias_info:
            bias = " " + str(bias_tag[voxel])
        else: bias = ""

        # Regular case:
        # We write the list of properly normalized probabilities for the voxel
        #  to a line.
        fw.write(" ".join(["{0:<12.5E}".format(x) for x in ergproblist]) + \
                bias + "\n")

    fw.close()

    print "The file '{0}' was created successfully".format(outfile)

    return 1


def _gen_gammas_header(sm, outfile, sampling, ergbins, biasing, cumulative, \
        **kwargs):
    """Open a stream to write the header information for a gammas file
    
    ACTION: Method writes the header lines for gammas file, and method
    is used by gen_gammas_file_from_h5m().
    Receives
    ---------
    sm : scdmesh.ScdMesh object
        MOAB mesh file
    outfile : string
        File name for the 'gammas' file. (Usually just 'gammas')
    sampling : char
        Character/flag corresponding with sampling type to be used. Options are:
        'v' for voxel sampling; 'u' for uniform sampling;
    ergbins : 
        is either a null string or a list of energies. 
    biasing : boolean
        Flag for biasing is added if true.
    cumulative : boolean
        Flag for listing cumulative erg probabilities is added if true.

    Returns
    ---------
    fw : stream
        A file writing object
    """
    
    fw = open(outfile, 'w')

    # write metadata/comment line
    fw.write("# File created: {0};".format(datetime.now().strftime("%D %H:%M")))
    if 'title' in kwargs:
        fw.write("Problem name: {0};".format(kwargs['title']))
    if 'coolingstep' in kwargs:
        fw.write(" Cooling time: {0};".format(kwargs['coolingstep']))
    if 'isotope' in kwargs:
        fw.write(" Source isotope: {0};".format(kwargs['isotope']))
    fw.write("\n")
    
    # write number of intervals for x, y, z dimensions (1st line)
    extents = [sm.dims[3], sm.dims[4], sm.dims[5]]
    fw.write(" ".join([str(x) for x in extents]) + "\n")
    
    # create and write x mesh edges line (2nd line)
    fw.write(" ".join([str(x) for x in sm.getDivisions('x')]) + "\n")
    # create and write y mesh edges line (3rd line)
    fw.write(" ".join([str(y) for y in sm.getDivisions('y')]) + "\n")
    # create and write z mesh edges line (4th line)
    fw.write(" ".join([str(z) for z in sm.getDivisions('z')]) + "\n")

    # create and write 5th line (placeholder list of activated materials)
    fw.write(" ".join([str(x) for x in xrange(1,101)]) + "\n")

    # create 6th line - parameters
    paramline = "p " + sampling + " "
    if biasing: paramline = paramline + "b "
    if ergbins != "": paramline = paramline + "e "
    #paramline = paramline + "d " # enable source debug
    #paramline = paramline + "m "
    if cumulative: paramline = paramline + "c "
    fw.write(paramline + "\n")

    # If storing the energy bins information, write line 6
    # Line starts with 'e', then the number of energy GROUPS, then
    #  lists all group boundaries
    if ergbins != "":
        fw.write("e " + str(len(ergbins)-1) + " " + \
                " ".join([str(x) for x in ergbins]) + "\n")

    return fw


def calc_volumes_list(sm):
    """Create list of voxel volumes for a cartesian mesh
    
    ACTION: Method creates a 1D list of voxel volumes
    RECEIVES: sm, a scdmesh.ScdMesh object.
    RETURNS: vols, a 1D list of voxel volumes in order 'xyz'

    NOTE: Voxel ordering follows meshtal file convention which is
     -for x for y iterate z
     -for x iterate y
     -iterate x
    """
    
    meshplanes = [ sm.getDivisions('x'),
                   sm.getDivisions('y'),
                   sm.getDivisions('z') ]

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


def _tag_sumvoxelstrengths(sm, val):
    # Get the Tag object called PHTN_BIAS
    try:
        tag = sm.imesh.createTag("PHTN_SRC_TOTAL",1,"d")
    except iBase.TagAlreadyExistsError:
        tag = sm.imesh.getTagHandle("PHTN_SRC_TOTAL")

    tag[sm.imesh.rootSet] = val

    return 1


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
    #
   
    (options, args) = parser.parse_args()

    # Create ScdMesh object, which also loads 'meshfile' into mesh.
    sm = ScdMesh.fromFile(args[0])

    gen_gammas_file_from_h5m(sm, options.output)

    return 1


# Handles module being called as a script.
if __name__=='__main__':
    main()

