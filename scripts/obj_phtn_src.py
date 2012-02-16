#!/usr/bin/env python 

######################################################################
#obj_phtn_src.py
######################################################################
# This python script defines an object that parses the photon source strength
#  output from ALARA.  
# The script supports command line calls, but is intended to be
#  used modularly by other scripts.
#
#
#
######################################################################

import textwrap as tw
import os
from optparse import OptionParser
from itaps import iBase,iMesh
import alias


class PhtnSrcReader(object):
    """USE: Object of class stores photon source strength information that is
    read in from the phtn_src file from ALARA.  Class methods can:
        read in phtn_src, tag h5m mesh with this data, create SDEF cards from
        this data, create gammas file from this data or from h5m tags ...
    REQUIRES: A new object of class PhtnSrcReader must be supplied the path of 
    the file of interest.
    """
    
    def __init__(self, myInputFileName):
        """Init function for class PhtnSrcReader. Receives a phtn_src file.
        """
        super(PhtnSrcReader, self).__init__()

        self.inputFileName = myInputFileName

        # stores a list of notes
        #self.notes = ['Notes for: ' + self.inputFileName]
        

    def read_file(self):
        """Method opens self.inputFileName and passes this object to self.read()"""
        if os.path.isfile(self.inputFileName):
            fr = open(self.inputFileName, 'r')
            read_ok = self.read(fr) # stores the 1 or 0 returned from read()
            fr.close()
        else:
            print "The file '{0}' could not be found.".format(self.inputFileName)
            return 0
        return read_ok # return 1


    def read(self, fr=''):
        """ Method reads in lines from an IO stream, and stores them in blocks on a 
        per-heading basis, e.g. headings are isotope identifiers or "TOTAL"
        RECEIVES: fr, an IO stream, e.g. from open('file', 'r'), fr is NOT a filename
        """

        if fr == '': #default to the file at self.inputFileName
            return self.read_file()

        self.headingList = list() # contains every line's list of isotope IDs
        self.coolingStepsList = list() # contains every line's list of cooling steps   
        self.probList = list() # contains every line's list of probabilities
        
        self.coolingSteps = list() # list of just the different cooling steps
        self.phtnList = list() # contains every line in string.split() form
        
        needCoolStepCnt = True

        # Read through the file...
        
        line = fr.readline()
        
        while(line != ''): # != EOF
            lineParts = line.split()
            
            self.phtnList.append(lineParts)
            
            # if list of the cooling steps in file is not complete yet...
            if needCoolStepCnt:
            # then we add next cooling step name
                # if we already started a list of cooling steps and shutdown
                if len(self.coolingSteps) and lineParts[1] == "shutdown": 
                        #alternately: == self.coolingSteps[0]:
                    needCoolStepCnt = False
                else:
                    if lineParts[1] != "shutdown":
                        # pull the next two pieces to make the cooling step identifier...
                        self.coolingSteps.append(lineParts[1:3])
                    else:
                        # pull the next piece which should be "shutdown"
                        self.coolingSteps.append(lineParts[1])
                
            self.headingList.append(lineParts[0])
            
            # handling the single string cooling step "shutdown"
            if lineParts[1] == "shutdown":
                self.coolingStepsList.append([lineParts[1]])
                self.probList.append(lineParts[2:])
            # or the two string cooling steps, e.g. "1 d"
            else:
                self.coolingStepsList.append(lineParts[1:3])
                self.probList.append(lineParts[3:])
                
            line = fr.readline() # read next line
        
        print "The file '{0}' has been read successfully.".format(self.inputFileName)
        return 1


    def get_isotope(self, isotope="TOTAL"):
        """ACTION: Method searches headingList to find which entry in probList is
        the desired TOTAL or isotope, and returns the corresponding TOTAL block,
        which can include multiple cooling steps.
        To get a specific cooling step's total, call isotope_source_strengths
        REQUIRES: Method expects that read() has been successfully called.
        RETURNS: If the isotope is sucessfully found, returns self.totalHeadingList
        """
        
        meshcnt = -1 # gets incremented immediately to our starting value of 0

        # If the lists with headings and probabilities have contents...
        if len(self.headingList) and len(self.probList):
            self.totalHeadingList = list() #
            self.totalProbList = list()
            self.totalCoolingStepsList = list()
            
            # Go through all entries in headingList
            for cnt, set in enumerate(self.headingList):
                
                # and save those that match the specified isotope.
                if set == isotope:
                   
                    # Look for entries with "shutdown" as cooling step. This
                    #  indicates the beginning of the entries for another mesh
                    #  cell.  When found, append empty list and increment
                    #  meshcnt.
                    if self.coolingStepsList[cnt] == ["shutdown"]:
                        self.totalHeadingList.append([])
                        self.totalProbList.append([])
                        self.totalCoolingStepsList.append([])
                        meshcnt += 1
                        
                    self.totalHeadingList[meshcnt].append(self.headingList[cnt])
                    self.totalProbList[meshcnt].append(self.probList[cnt])
                    self.totalCoolingStepsList[meshcnt].append(self.coolingStepsList[cnt])
                        
        else:
            print "totalsList or probList was empty. read() was probably not called"
        
        if len(self.totalHeadingList) == 0:
            print "{0} was not found in photon source " \
            "file.".format(isotope)
            return 0
            
        else:
            return self.totalHeadingList

        return 1
                

    def isotope_source_strengths(self, coolingstep=0):
        """ACTION: Method parses all contents of self.totalProbList and creates a list of
        the sum of source strengths in each mesh cell, and a list of each mesh
        cell's list of source strengths at each energy.
        REQUIRES: Method expects that get_isotope() has been called already.
        NOTE that volume normalization of resulting list may
        be needed, depending on the mesh.
        RECEIVES: If 'coolingstep' is specified, returns the block under TOTAL
        corresponding with the cooling step.
        """
        
        self.meshprobs = list() # of lists of strings; each string is a source strength
        self.meshstrengths = list() # of floats; each float is the total source
                                    #  strength of a voxel at the chosen cooling step

        # For each of these, sum the entries in the corresponding source
        # strengths block, and make a list of these sums (self.meshstrengths)
        if len(self.totalHeadingList) and len(self.totalProbList):
            
            for probset in self.totalProbList:
                #print set[coolingstep]
                #thistotal = [item for sublist in set[coolingstep] for item in sublist]
                
                self.meshprobs.append(probset[coolingstep])
                self.meshstrengths.append(sum([float(prob) for prob in probset[coolingstep]]))
                    
        else:
            print "headingList or probList was empty. read() was probably not called"
            return 0
        
        return self.meshstrengths


    def gen_sdef_probabilities(self, meshform, outfile="phtn_sdef", ergbins=""):
        """REQUIRES: Method assumes that read() and isotope_source_strengths() have been
        called already.
        ACTION: Method creates a sequentially numbered listed of si and sp cards for
        MCNP input, using the energy structure specified (todo) and the photon
        source strength listed for each mesh cell.
        RECEIVES: Method receives a 3D list, meshform, of the form 
        {{xmin,xmax,xintervals},{y...},{z...}}
        """

        try:
            nmesh = len(self.meshstrengths)
        except:
            print "ERROR: isotope_source_strengths needs to be called before " \
                    "gen_sdef_probabilties"
            return 0

        if nmesh != meshform[0][2]*meshform[1][2]*meshform[2][2]:
            print "WARNING: Number of mesh cells in phtn_src file does not " \
                    "match the product of the mesh intervals given:"
            print "     ", nmesh, "!=", \
                    meshform[0][2],"*",meshform[1][2],"*",meshform[2][2]

        if nmesh > 994:
            print "ERROR: Too many mesh cells to create an SDEF card."
            return 0
        
        # ~Shoddy placeholder for energy bins
        # Note that we replace the {0} with the .format method for each mesh cell.a
        if ergbins == "":
            # we set a default 42 groups
            print "The energy bins were not specified. A default 42 group set" \
                    " of bins is being used instead."
            self.ergbins = "si{0} 0  1e-2  2e-2" \
              " 3e-2  4.5e-2  6e-2  7e-2  7.5e-2  1e-1  1.5e-1  2e-1  3e-1" \
              " 4e-1  4.5e-1  5.1e-1  5.12e-1  6e-1  7e-1  8e-1  1e0  1.33e0" \
              " 1.34e0  1.5e0  1.66e0  2e0  2.5e0  3e0  3.5e0" \
              " 4e0  4.5e0  5e0  5.5e0  6e0  6.5e0  7e0  7.5e0  8e0" \
              " 1e1  1.2e1  1.4e1  2e1  3e1  5e1"
        else:
            # Not currently implemented
            self.ergbins = ergbins
            print "ERROR: ergbins."
            return 0
        
        # calculate the mesh spacing in each direction
        xval = (meshform[0][1]-meshform[0][0])/float(meshform[0][2])/2
        yval = (meshform[1][1]-meshform[1][0])/float(meshform[1][2])/2
        zval = (meshform[2][1]-meshform[2][0])/float(meshform[2][2])/2
        
        cards=["sdef par=2 x=d996 y=d997 z=d998  erg ftr d999 tr=d995"]
        
        mcnpWrap = tw.TextWrapper()
        mcnpWrap.initial_indent = 0*' '
        mcnpWrap.subsequent_indent = 5*' '
        mcnpWrap.wdith = 80
        mcnpWrap.break_on_hyphens = False
        
        # create distribution for tr entries (point to transform cards)
        # SI card
        cards.extend(["c si995 - These are the mesh center coords"])
        card = ["si995 L"] # 
        card.extend([str(x) for x in range(1,nmesh+1)])
        card = " ".join(card)
        cards.extend(mcnpWrap.wrap(card))

        summeshstrengths = sum(self.meshstrengths)
        strnormmeshstrengths = \
                [str(x/summeshstrengths) for x in self.meshstrengths]
        
        # SP card
        card = ["sp995 D"] # D for discrete cumulative probabilities
        card.extend(strnormmeshstrengths)
        card = " ".join(card)
        cards.extend(mcnpWrap.wrap(card))
        
        # create distribution for X sampling
        # SI card
        cards.extend(["c si996 - x sampling"])
        card = ["si996 H"] # H for bin boundaries with continuous bin sampling.
        card.extend([str(-1*xval),str(xval)])
        card = " ".join(card)
        cards.extend(mcnpWrap.wrap(card))
        # SP card
        cards.append("sp996 D 0 1") # D for discrete cumulative probabilities
        
        # create distribution for Y sampling
        # SI card
        cards.extend(["c si997 - y sampling"])
        card = ["si997 H"] # H for bin boundaries.
        card.extend([str(-1*yval),str(yval)])
        card = " ".join(card)
        cards.extend(mcnpWrap.wrap(card))
        # SP card
        cards.append("sp997 D 0 1") # D for discrete cumulative probabilities
        
        # create distribution for Z sampling
        # SI card
        cards.extend(["c si998 - z sampling"])
        card = ["si998 H"] # H for bin boundaries.
        card.extend([str(-1*zval),str(zval)])
        card = " ".join(card)
        cards.extend(mcnpWrap.wrap(card))
        # SP card
        cards.append("sp998 D 0 1") # D for discrete cumulative probabilities

        # create dependent distribution for energy sampling
        cards.extend(["c ds999 - These are the sp/si numbers"])
        card = ["ds999 S"]
        card.extend([str(i) for i in range(1,nmesh+1)])
        card = " ".join(card)
        cards.extend(mcnpWrap.wrap(card))

        # iterate through each mesh cell, outputting the erg distributions
        for fakecnt, meshcellstring in enumerate(self.meshprobs): #self.totalProbList):
            cnt = fakecnt + 1
            # sum up source strengths in mesh cell
            meshcell = [float(item) for item in meshcellstring]
            summeshstrengths = sum(meshcell)
           
            # We write fake probabilities if the mesh cell has no photon source
            #  strength.  This keeps MCNP from objecting.
            # Otherwiese we normalize and stringify the probability values.
            #~ Coding to exclude these cards would make this code more convoluted
            if summeshstrengths == 0:
                normmeshcell = [str(item + 1) for item in meshcell]
                cards.append("c  following distribution has zero photon source probability" \
                        + "\nc  however, non-zero bin probabilities keep MCNP happy.")
            else:
                # then normalize the source strengths in the mesh cell to total 1 (unnecessary...)
                normmeshcell = [str(x/summeshstrengths) for x in meshcell]
            
            # create the SI card
            card = self.ergbins.format(cnt)
            cards.extend(mcnpWrap.wrap(card))
            
            # create the SP card
            card = ["sp{0} 0".format(cnt)]
            card.extend(normmeshcell)
            card = " ".join(card)
            cards.extend(mcnpWrap.wrap(card))
            
        # create transform (TR) cards, 1 for each mesh cell.
        cnt = 0
        for x in range(meshform[0][2]):
            for y in range(meshform[1][2]):
                for z in range(meshform[2][2]):
                    cnt += 1
                    cards.append(" ".join( \
                            ["tr"+str(cnt), \
                            str(meshform[0][0]+xval+2*x*xval), \
                            str(meshform[1][0]+yval+2*y*yval), \
                            str(meshform[2][0]+zval+2*z*zval)]\
                            ))
        
        # write all cards to the outfile specified when function was called.
        fw = open(outfile, 'w')
        fw.writelines("\n".join(cards))
        fw.close()
        print "SDEF card has been generated in file '{0}'".format(outfile)
        print "Remember to update the imp:n to imp:p, as well as updating the " \
                "mode card."
        
        return 1


    def gen_gammas_file(self, meshform, outfile="gammas", ergbins=""):
        """ACTION: Method generates a file called 'gammas' to be used with a 
        modified version of MCNP5.
        REQUIRES: Method assumes that read() and isotope_source_strengths() 
        have been called already, OR that self.meshstrengths and self.meshprobs
        have been otherwise created properly.
        RECEIVES:
        3D list, meshform, of the form {{xmin,xmax,xintervals},{y...},{z...}}
        Optional: 'outfile' allows for an alternate file name instead of gammas
        Optional: 'ergbins' can specify different energy bins, rather than a
           default set of 42 bins. (This adds an additional line in gammas
           and requires a different source.F90.)
        RETURNS: 1 if successful, 0 if an error occurred.
        """

        try:
            nmesh = len(self.meshstrengths) # We use this to check for a warning
                            # and to make sure a required method has been called
        except:
            print "ERROR: isotope_source_strengths needs to be called before " \
                    "gen_sdef_probabilties"
            return 0

        if nmesh != meshform[0][2]*meshform[1][2]*meshform[2][2]:
            print "WARNING: Number of mesh cells in phtn_src file does not " \
                    "match the product of the mesh intervals given:"
            print "     ", nmesh, "!=", \
                    meshform[0][2],"*",meshform[1][2],"*",meshform[2][2]

        # We call the function that opens our gammas file and writes the header
        fw = self._gen_gammas_header(meshform, outfile, ergbins)

        # We calcualte the normalization factor as the average total source
        #  strength in each mesh cell divided by the number of mesh cells
        #  with non-zero source strength.
        # This applies ONLY for uniform voxel size meshing.
        numactivatedcells = 0
        for val in self.meshstrengths:
            if val > 0:
                numactivatedcells += 1 
                # volsourcetot += volcell
        print "The number of activated voxels and total number of voxels is " \
                "{0}/{1}".format(numactivatedcells, nmesh)
        norm = sum(self.meshstrengths) / numactivatedcells

        #~ Future normalizations:
        # With just void fractions included, so void rejection is doable:
        # norm = sum(self.meshstrengths) / sum([1-x for x in self.voidfracs])

        # With varying voxel size, but no void fraction info
        # norm = sum(self.meshstrengths_vol_weighted

        # With both varying voxel size and void fraction info
        # norm = sum(self.meshstrengths_vol_weighted

        # Create and write lines for each mesh cell's gamma source strength,
        #  but first we must create a cumulative list of normalized probabilities.
        for binset in self.meshprobs:
            binset_f = [float(prob) for prob in binset]
            cumulative_binset = list() # of floats
            prevbin = 0.0
            for bin in binset_f:
                # Normalize value of current bin, and add it to previous bin,
                #  since the previous bin is now the sum of all previous bins.
                binsum = bin/norm + prevbin
                cumulative_binset.append(binsum)
                prevbin = binsum

            # The following list comprehension uses a format specifying output
            #  of 12 characters, with 5 values
            #  after the decimal point, using scientific notation.
            cumulative_binset2 = ["{0:<12.5E}".format(x) for x in cumulative_binset]
            fw.write("".join(cumulative_binset2) + "\n")

        # all lines written, close file.
        fw.close()
        
        print "The file '{0}' was created successfully".format(outfile)

        return 1


    def gen_gammas_file_aliasing(self, meshform, outfile="gammas", ergbins=""):
        """ACTION: Method creates the file gammas with the photon energy bins
        for each voxel stored as alias tables.
        Header information is the same as that in gen_gammas_file().

        Each voxel's line corresponds with an alias table of the form:
        [total source strength, p1, g1a, g1b, p2, g2a, g2b ... pN, gNa, gNb]
        Where each p#, g#a, g#b are the info for one bin in the alias table.

        REQUIRES: Method assumes that read() and isotope_source_strengths() 
        have been called already, OR that self.meshstrengths and self.meshprobs
        have been otherwise created properly.
        RECEIVES:
        3D list, meshform, of the form {{xmin,xmax,xintervals},{y...},{z...}}
        Optional: 'outfile' allows for an alternate file name instead of gammas
        Optional: 'ergbins' can specify different energy bins, rather than a
           default set of 42 bins. (This adds an additional line in gammas
           and requires a different source.F90.)
        RETURNS: 1 if successful, 0 if an error occurred.
        """

        try:
            nmesh = len(self.meshstrengths) # We use this to check for a warning
                            # and to make sure a required method has been called
        except:
            print "ERROR: isotope_source_strengths needs to be called before " \
                    "gen_sdef_probabilties"
            return 0

        if nmesh != meshform[0][2]*meshform[1][2]*meshform[2][2]:
            print "WARNING: Number of mesh cells in phtn_src file does not " \
                    "match the product of the mesh intervals given:"
            print "     ", nmesh, "!=", \
                    meshform[0][2],"*",meshform[1][2],"*",meshform[2][2]

        fw = self._gen_gammas_header(meshform, outfile, ergbins)

        # We call the function that opens our gammas file and writes the header
        fw = self._gen_gammas_header(meshform, outfile, ergbins)

        # We calcualte the normalization factor as the average total source
        #  strength in each mesh cell divided by the number of mesh cells
        #  with non-zero source strength.
        # This applies ONLY for uniform voxel size meshing.
        numactivatedcells = 0
        for val in self.meshstrengths:
            if val > 0:
                numactivatedcells += 1 
                # volsourcetot += volcell
        print "The number of activated voxels and total number of voxels is " \
                "{0}/{1}".format(numactivatedcells, nmesh)
        norm = sum(self.meshstrengths) / numactivatedcells

        for binset in self.meshprobs:

            # We create the list to send to alias.gen_alias_table()
            ergproblist = list()
            sourcetotal = sum([float(prob) for prob in binset]) # binset)

            # Special case of a zero source strength voxel...
            # In this case, we write the correct number of zeros to the gammas
            #  file so that the source.F90 code doesn't run out of values to read
            if sourcetotal == 0:
                fw.write(" ".join([0]*(len(binset)*3+1)) + "\n")
                continue

            for cnt, p in enumerate(binset):
                ergproblist.append([float(p)/sourcetotal, cnt+1])
    
            aliastable = alias.gen_alias_table(ergproblist)

            # We compactly format the alias table as a bunch of strings.
            # The following list comprehension uses a format specifying output
            #  of 12 characters, with 5 values after the decimal point and 
            #  scientific notation for the probability values, and integer 
            #  format for the energy group numbers
            aliasstrings = ["{0:<12.5E} {1} {2}".format(x[0][0],x[0][1],x[1][1]) \
                    for x in aliastable]

            fw.write(str(sourcetotal/norm) + " " + " ".join(aliasstrings) + "\n")

        # all lines written, close file.
        fw.close()
        
        print "The file '{0}' was created successfully".format(outfile)

        return 1


    def _gen_gammas_header(self, meshform, outfile, ergbins):
        """ACTION: Method writes the header lines for gammas file, and method
        is used by both gen_gammas_file() and gen_gammas_file_aliasing().
        RETURNS: A file writing object, fw.
        """
        
        # calculate the mesh spacing in each direction
        xval = (meshform[0][1]-meshform[0][0])/float(meshform[0][2])#/2
        yval = (meshform[1][1]-meshform[1][0])/float(meshform[1][2])#/2
        zval = (meshform[2][1]-meshform[2][0])/float(meshform[2][2])#/2

        fw = open(outfile, 'w')
        
        # write first line (intervals for x, y, z)
        fw.write(" ".join([str(x[2]) for x in meshform]) + "\n")
        
        # create and write x mesh edges line (2nd line)
        coords = [meshform[0][0]]
        for cnt in range(1, meshform[0][2]+1):
            coords.append(meshform[0][0]+cnt*xval)
        fw.write(" ".join([str(x) for x in coords]) + "\n")
        
        # create and write y mesh edges line (3rd line)
        coords = [meshform[1][0]]
        for cnt in range(1, meshform[1][2]+1):
            coords.append(meshform[1][0]+cnt*yval)
        fw.write(" ".join([str(x) for x in coords]) + "\n")
        
        # create and write z mesh edges line (4th line)
        coords = [meshform[2][0]]
        for cnt in range(1, meshform[2][2]+1):
            coords.append(meshform[2][0]+cnt*zval)
        fw.write(" ".join([str(x) for x in coords]) + "\n")

        # create and write 5th line (list of activated materials... ?????)
        fw.write(" ".join([str(x) for x in range(1,101)]) + "\n")

        # If storing the energy bins information, write line 6
        if ergbins != "":
            fw.write(" ".join([str(x) for x in ergbins]) + "\n")

        return fw


    def calc_volumes_list(self, meshplanes):
        """ACTION: Method creates a 1D list of voxel volumes
        RECEIVES: meshplanes: a 2D list of mesh intervals, e.g.
                    [[x0,x1,x2,...],[y0,y1,y2,...],[z0,z1,z2,...]]

        NOTE: Voxel ordering follows meshtal file convention which is
         -for x for y iterate z
         -for x iterate y
         -iterate x
        """
        
        oldz = meshplanes[2][0]
        oldy = meshplanes[1][0]
        oldx = meshplanes[0][0]

        nxdiv = len(meshplanes[0]) - 1
        nydiv = len(meshplanes[1]) - 1
        nzdiv = len(meshplanes[2]) - 1

        # create 1D list
        self.vol = [0] * (nxdiv * nydiv * nzdiv)

        for cntx, x in enumerate(meshplanes[0][1:]):
            oldy = meshplanes[1][0]
            for cnty, y in enumerate(meshplanes[1][1:]):
                oldz = meshplanes[2][0]
                for cntz, z in enumerate(meshplanes[2][1:]):
                    # Calc volume here
                    self.vol[nydiv*nzdiv*cntx + nzdiv*cnty + cntz] = \
                            (x - oldx) * \
                            (y - oldy) * \
                            (z - oldz)
                    oldz = z
                oldy = y
            oldx = x

        return 1


    def weight_mesh_strengths_by_vol(self):
        """
        """

#        self.meshstrengths_vol_weighted[]
        pass

    
    def gen_phtn_src_h5m_tags(self, inputfile, outfile="", retag=False):
        """ACTION: Method adds tag with photon source strengths from ALARA to a
        moab mesh.
        If there are photon energy group tags with numbers higher than those
        added and retagging is enabled, these tags are removed.
        REQUIRES:

        RECEIVES: The file (a .h5m moab file) containing the mesh of interest.
        An output file which is fun
        TODO:
        Check to make sure the correct number of energy groups were added as tags.
        """

        try:
            nmesh = len(self.meshstrengths)
        except:
            print "ERROR: isotope_source_strengths needs to be called before " \
                    "gen_phtn_src_h5m_tags"
            return 0

        if outfile == "": outfile = inputfile

        # pyTaps stuff starts here
        mesh = iMesh.Mesh()
        mesh.load(inputfile)

        num_erg_groups = 42 # must be an integer

        # We grab the list of mesh entity objects
        voxels = mesh.getEntities(iBase.Type.region)

        # We need to create the list of photon probabilities for each mesh cell.
        # Because this list can be quite large, we will do this element-by-element.
        
        # for grp, prob in enumerate(self.meshprobs[0]):
        for grp in range( len(self.meshprobs[0]) ):
            try:
                tag = mesh.createTag( \
                        "phtn_src_group_{0:03d}".format(grp+1), 1, float)
            except:
                if retag:
                    tag = mesh.getTagHandle("phtn_src_group_{0:03d}".format(grp+1))
                else:
                    print "ERROR: The tag phtn_src_group_{0:03d}".format(grp+1), \
                            "already exists in the file", inputfile, \
                            "\nNow exiting this method."
                    return 0

            # we give each voxel to the tag dictionary, and assign the tag the value
            # stored in self.meshprobs 
            for cnt, vox in enumerate(voxels):
                # we create tag, which is a dictionary, and give the dictionary 
                tag[vox] = float(self.meshprobs[cnt][grp])

        #~ some caution needed with making sure 'grp' remains as is at end of
        #~  above for loop
        grp += 1

        # We get of tags corresponding with higher energy groups here.
        if retag:
            while grp:
                try:
                    tag = mesh.getTagHandle("phtn_src_group_{0:03d}".format(grp+1))
                    mesh.destroyTag(tag,force=True)
                    grp += 1
                except:
                    grp = 0


        mesh.save(outfile)

        print "The file '{0}' was created successfully".format(outfile)

        return 1

    
    def gen_gammas_file_from_h5m(self, meshform, inputfile, outfile="gammas"):
        """ACTION: Method reads tags with photon source strengths from an h5m
        file and generates the gammas file for the modified KIT source.f90 routine
        To do this, we generate self.meshprobs and call gen_gammas_file().
        REQUIRES: the .h5m moab mesh must have photon source strength tags of the
        form "phtn_src_group_#"
        Will read photon energy bin boundary values if the root set has the tag 
        PHOT_ERG (a list of floats)

        RECEIVES: The file (a .h5m moab file) containing the mesh of interest.
        An output file name for the 'gammas' file.
        TODO:
        """

        mesh = iMesh.Mesh()
        mesh.load(inputfile)

        try:
            group = mesh.getTagHandle("phtn_src_group_001")
        except:
            print "ERROR: The file", inputfile, "does not contain tags of the " \
                    "form 'phtn_src_group_#'"
            return 0

        voxels = mesh.getEntities(iBase.Type.region)
        numvoxels = len(voxels)

        #Need to create: self.meshstrengths, self.meshprobs
        self.meshprobs = list() # of lists of strings; each string is a source strength
        self.meshstrengths = list() # of floats; each float is the total source
                                    #  strength of a voxel at the chosen cooling step

        # Fun!:
        # We create meshprobs with a list comprehension. Voxels are mesh entity pointers(?)
        # groups is a dictionary, receives the list of pointers, and returns a list of
        # photon source probabilities.  We use a list comprehension to make this a list of
        # lists, and assign this to meshprobs.
        # In the following for loop, each of these lists is appended for each energy group.
        self.meshprobs = [[x] for x in group[voxels]]

        for i in range(2,1000): #~ Arbitrary: we look for up to 1000 groups
            try:
                group = mesh.getTagHandle("phtn_src_group_{0:03d}".format(i))
                for cnt, vox in enumerate(voxels):
                    self.meshprobs[cnt].append(group[vox])
            except iBase.TagNotFoundError: break
        
        # Make list of total photons/cm3/s for each mesh cell
        self.meshstrengths = [sum([float(prob) for prob in x]) for x in self.meshprobs]

        # We now look for the tags with the energy bin boundary values
        try:
            phtn_ergs = mesh.getTagHandle("PHTN_BINS")
            myergbins = phtn_ergs[mesh.rootSet] #UNTESTED... does this need list() around it?
            print "NOTE: photon energy bins were found in the .h5m mesh and added to "\
                    "'{0}'. The modified mcnp5/source.f90 looks for a file caled " \
                    "'gammas_ener'".format(outfile)
        except: # if there is no PHTN_BINS tag, then we send an empty string in its place
            myergbins = ""

        self.gen_gammas_file(meshform, outfile, myergbins)

        return 1

    # Method will probably not be used/developed; volumes will instead be
    #  recalculated rather than read from tags.
    def voxel_volumes_from_h5m(self, inputfile):
        """ACTION: Method reads tags with voxel volumes from an h5m
        file and stores the information in 
        To do this, we generate self.meshprobs and call gen_gammas_file().
        REQUIRES: the .h5m moab mesh must have 

        RECEIVES: The file (a .h5m moab file) containing the mesh of interest.
        TODO:
        """

        #~ NOTE: The below code is a placeholder from 'gen_gammas_from_h5m_file()'

        mesh = iMesh.Mesh()
        mesh.load(inputfile)

        try:
            group = mesh.getTagHandle("VOLUMES")
        except:
            print "ERROR: "
                    
            return 0

        voxels = mesh.getEntities(iBase.Type.region)
        numvoxels = len(voxels)

        return 1


    # DEPRECATED
    def format_isotope_mcnp(self, coolingstep=0):
        """NOTE: Intended for taking phtn_src file for a single mesh (1x1x1) and 
        formatting its contents for use as probabilities in an sdef card.
        RETURNS: Method returns a formatted list of strings that is the block under
        heading TOTAL for some cooling step
        REQUIRES: Method expects that get_isotope() has been successfully called.
        If self.totalsList does not exist (e.g. get_total has not been called),
        the method quits.
        RECEIVES: If 'coolingstep' is specified, returns the block under TOTAL
        corresponding with the cooling step.
        """
        
        grandTotal = [item for sublist in self.totalsList[coolingstep] for
                item in sublist]
        grandTotal = " ".join(grandTotal)

        # wrap is set up so that lines indent 5 spaces and wrap at 80 chars
        #  First line indents extra to make room for SI card.
        #  Resulting 'grandTotal' should copy/paste nicely into MCNP input deck.
        mcnpWrap = tw.TextWrapper()
        mcnpWrap.initial_indent = 7*' '
        mcnpWrap.subsequent_indent = 5*' '
        mcnpWrap.wdith = 80
        mcnpWrap.break_on_hyphens = False

        grandTotal = mcnpWrap.wrap(grandTotal)

        return grandTotal


    def read_pre_alara_2_9(self):
        """ DEPRECATED METHOD - Handles the earlier formatting of phtn_src file
        from ALARA.
        Method reads in lines and stores them in blocks on a per-heading basis
         e.g. headings are isotope identifiers or TOTAL
        This method handles the phtn_src format in ALARA prior to version 2.9
        """

        fr = open(self.inputFileName, 'r')

        line = fr.readline()
        
        hcnt = 0;
        pcnt = 1;
        
        self.headingList = []
        self.probList = []
        
        justReadAHeading = False
        wasBlank = False

        # Read through the file...
        # Events of interest:
        #  Blank lines signify either a new isotope, or a new set of probabilities
        #  Lines specifying isotopes are id'd by alphabetical characters
        #  Lines with photon source strengths are id'd by number
        
        while(line != ''): # != EOF
            lineParts = line.split()

            if len(lineParts) == 0:
                line = fr.readline()
                wasBlank = True
                continue
            
            if justReadAHeading:
                justReadAHeading = False
                
            if wasBlank and lineParts[0][0].isdigit():
                wasBlank = False
                self.probList[hcnt - 1].append([])
                pcnt += 1
                
            if lineParts[0][0].isalpha(): # check if first entry of line
                                            # starts with a letter
                justReadAHeading = True
                hcnt += 1
                pcnt = 1
                self.headingList.append(lineParts[0]) #~ storing a single string
                                                      #~ for consistency, use a list?
                self.probList.append([ [] ]) # empty list to hold lines.
                wasBlank = False
                
            else: # line is a list of numbers...
                
                self.probList[hcnt - 1][pcnt - 1].append(lineParts)
                
            line = fr.readline()
        
        return 1

    #END DEPRECATED
        

def main():
    """ACTION: Method defines an option parser and handles command-line
    usage of this module.
    REQUIRES: command line arguments to be passed - otherwise prints help
    information.
    RECEIVES: N/A
    """
    usage = "usage: %prog [options] arg"
    parser = OptionParser(usage)
    
    # Input and output file names
    parser.add_option("-i","--input",action="store",dest="filename", \
            default=False, help="The photon source strengths are read from" \
            "FILENAME. This option is required to supplement most other " \
            "options.")
    parser.add_option("-o","--output",action="store",dest="outputfile", \
            default="", help="file to write source information to, or" \
            " file name for saving a modified mesh.")

    # Options for type of output
    parser.add_option("-m","--mesh",action="store",dest="meshform", \
            default="0,1,1,0,1,1,0,1,1",help="Meshing information.\n" \
            "Needs a 9-valuelist, meshform, of the form " \
            "-m xmin,xmax,xintervals,y...,z... delimited by commas (no spaces)." \
            "Default: %default")
    parser.add_option("-s","--sdef",action="store_true",dest="sdef", \
            default=False, help="Will generate a file with the SDEF, " \
            "SI, SP, and TR cards for MCNP. Mesh information from the -m " \
            "option is required.")
    parser.add_option("-g","--gammas",action="store_true",dest="gammas", \
            default=False,help="Will generate a 'gammas' file directly " \
            "from a phtn_src file for use by " \
            "modified versions of MCNP. Needs mesh info from -m.")
    parser.add_option("-H","--H5M",action="store",dest="h5m_write_filename", \
            default=False,help="Adds the photon source information to an " \
            "existing .h5m mesh. " \
            "You must specify the file name/location for the .h5m mesh.")
    parser.add_option("-p","--pull",action="store",dest="h5m_read_filename", \
            default=False,help="Reads photon source information from a .h5m mesh " \
            "and generates a corresponding 'gammas' file. You must specify the " \
            ".h5m mesh file's name/location. Mesh information from the -m " \
            "option is required.")

    # Other options
    parser.add_option("-r","--retag",action="store_true",dest="retag", \
            default=False,help="Option enables retagging of .h5m meshes, e.g. " \
            "with the -H option. Default: %default")

    (options, args) = parser.parse_args()

    # create an object and read it in if options specify getting info from phtn_src
    if not options.h5m_read_filename:
        # Print warning and then exit if no file was specified with -i/--input
        if options.filename == False:
            parser.error( "Methods in this module need a file name to begin. " \
                          "Use the -i option." )

        exampleReader = PhtnSrcReader(options.filename)
        exampleReader.read_file()

        exampleReader.get_isotope()
        print "Cooling steps are:\n", exampleReader.coolingSteps, "\n"
    
    else:
        # We need a dummy object in order to call needed methods later.
        exampleReader = PhtnSrcReader('fake.file')

    # Toss error and then exit if too few mesh values given
    if len(options.meshform.split(",")) != 9:
        print "ERROR: The specified mesh parameters, '{0}', should have 9 values." \
                .format(options.meshform)
        return 0

    # Turn meshform list received into the 3D list used by other methods
    # Also avoiding DeprecationWarnings by mixing floats and ints...    
    meshform3D = options.meshform.split(",")
    meshform3D[0:9:3] = [float(x) for x in meshform3D[0:9:3] ]
    meshform3D[1:9:3] = [float(x) for x in meshform3D[1:9:3] ]
    meshform3D[2:9:3] = [int(x) for x in meshform3D[2:9:3] ]
    meshform3D = [ meshform3D[0:3], meshform3D[3:6], meshform3D[6:9] ]

    if options.sdef:
        print "The sdef card will now be generated from a phtn_src file."
        exampleReader.isotope_source_strengths()
        if options.outputfile=="": exampleReader.gen_sdef_probabilities(meshform3D)
        else: exampleReader.gen_sdef_probabilities(meshform3D, options.outputfile)

    elif options.gammas:
        print "A 'gammas' file will now be created from a phtn_src file."
        exampleReader.isotope_source_strengths()
        if options.outputfile=="": exampleReader.gen_gammas_file(meshform3D)
        else: exampleReader.gen_gammas_file(meshform3D, options.outputfile)
    
    elif options.h5m_write_filename:
        print "The specified h5m mesh will now have tags added containing photon" \
                " source information from a phtn_src file."
        exampleReader.isotope_source_strengths()
        if options.outputfile=="": 
            exampleReader.gen_phtn_src_h5m_tags(options.h5m_write_filename, \
                    retag=options.retag)
        else: exampleReader.gen_phtn_src_h5m_tags( \
                options.h5m_write_filename, options.outputfile, retag=options.retag)

    elif options.h5m_read_filename:
        print "The specified h5m mesh will now be checked for tags containing photon" \
                " source information, and a 'gammas' file will be generated."
        if options.outputfile=="": 
            exampleReader.gen_gammas_file_from_h5m( \
                meshform3D, options.h5m_read_filename)
        else: 
            exampleReader.gen_gammas_file_from_h5m( \
                meshform3D, options.h5m_read_filename, options.outputfile)
    
    return 1


# Handles module being called as a script.
if __name__=='__main__':
    main()
