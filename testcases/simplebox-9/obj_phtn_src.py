#!/usr/bin/env python 

######################################################################
#obj_phtn_src.py
######################################################################
#This python script defines an object that parses the photon source strength
# output from ALARA.
#
#
#
# Created by Eric Relson, relson@wisc.edu, working under Professor 
# Paul Wilson, University of Wisconsin, Madison
######################################################################

import textwrap as tw

class PhtnSrcReader(object):
    """A new object of class PhtnSrcReader must be supplied the path of the file
     of interest.
    """
    
    def __init__(self, myInputFileName):
        super(PhtnSrcReader, self).__init__()

        self.inputFileName = myInputFileName

        # stores a list of notes
        #self.notes = ['Notes for: ' + self.inputFileName]
        
    
    def read(self):
        """ Method opens and reads in lines and stores them in blocks on a 
        per-heading basis, e.g. headings are isotope identifiers or "TOTAL"
        """

        fr = open(self.inputFileName, 'r')
        
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
            
            #
            if lineParts[1] == "shutdown":
                self.coolingStepsList.append([lineParts[1]])
                self.probList.append(lineParts[2:])
            else:
                self.coolingStepsList.append(lineParts[1:3])
                self.probList.append(lineParts[3:])
                
            line = fr.readline()
        
        # return #what to return?
   

    # DEPRECATED
    def read_pre_alara_2_9(self):
        """ reads in lines and stores them in blocks on a per-heading basis
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
        
        # return #what to return?
        

    def get_isotope(self, isotope="TOTAL"):
        """ Method searches headingList to find which entry in probList is the
        the desired TOTAL, and returns the corresponding TOTAL block, which can 
        include multiple cooling steps.
        To get a specific cooling step's total, call isotope_source_strength
        Method expects that read() has been successfully called.
        """
        
        meshcnt = -1

        # If the lists with headings and probabilities have contents...
        if len(self.headingList) and len(self.probList):
            self.totalHeadingList = list()
            self.totalProbList = list()
            self.totalCoolingStepsList = list()
            
            # Go through all entries in headingList
            for cnt, set in enumerate(self.headingList):
                
                # and save those that match the specified isotope.
                if set == isotope:
                    
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
            print "{0} was not found in photon source." \
            "file.".format(isotope)
            
        else:
            return self.totalHeadingList
                
            
    def format_isotope_mcnp(self, coolingstep=0):
        """Method returns a formatted list of strings that is the block under
        heading TOTAL for some cooling step
        Method expects that get_isotope() has been successfully called.
        If self.totalsList does not exist (e.g. get_total has not been called),
        the method quits.
        If 'coolingstep' is specified, returns the block under TOTAL
        corresponding with the cooling step.
        """
        
        # if not len(self.totalsList):
            # print "object's variable 'totalsList' has not been set." \
            # " format_total_mcnp will now return ['0']"
            # return ['0']

        # try:
            # self.totalsList[coolingstep]
        # except:
            # print 'Cooling step', coolingstep, 'not found. Using last cooling step instead.'
            # coolingstep = len(self.totalsList) - 1

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


    def isotope_source_strengths(self, coolingstep=0):
        """Method parses all contents of self.totalProbList and creates and returns a list of
        the sum of source strengths.  This list can be used to determine the
        mesh cell strength.
        Method expects that get_isotope() has been called already.
        NOTE that volume normalization of resulting list may
        be needed, depending on the mesh.
        If 'coolingstep' is specified, returns the block under TOTAL
        corresponding with the cooling step.
        """
        
        # Not elegant... gen_sdef_probabilities needs to use the same coolingstep value.
        self.coolingstep = coolingstep
        
        self.meshstrengths = list() # of floats

        # For each of these, sum the entries in the corresponding source
        # strengths block, and make a list of these sums (self.meshstrengths)
        if len(self.totalHeadingList) and len(self.totalProbList):

            for set in self.totalProbList:
                #print set[coolingstep]
                #thistotal = [item for sublist in set[coolingstep] for item in sublist]
                
                self.meshstrengths.append(sum(map(float,set[coolingstep])))
                    
        else:
            print "headingList or probList was empty. read() was probably not called"

        return self.meshstrengths


    def gen_sdef_probabilities(self, meshform, outfile="phtn_sdef"):
        """Method assumes that read() and isotope_source_strengths() have been
        called already.
        Method creates a sequentially numbered listed of si and sp cards for
        MCNP input, using the energy structure specified (todo) and the photon
        source strength listed for each mesh cell.
        Method receives a 3D list, meshform, of the form {{zmin,zmax,zintervals},{y...},{x...}}
        """

        try:
            nmesh = len(self.meshstrengths) + 1
        except:
            print "ERROR: total_source_strengths needs to be called before" \
                    "gen_sdef_probabilties"
            return [0]

        if nmesh > 994:
            print "ERROR: Too many mesh cells to create an SDEF card."
            return [0]
        
        # Shoddy placeholder for energy bins
        # Note that we replace the {0} with the .format method for each mesh cell.
        ergbins = "si{0} A  1e-2  2e-2" \
          " 3e-2  4.5e-2  6e-2  7e-2  7.5e-2  1e-1  1.5e-1  2e-1  3e-1" \
          " 4e-1  4.5e-1  5.1e-1  5.12e-1  6e-1  7e-1  8e-1  1e0  1.33e0" \
          " 1.34e0  1.5e0  1.66e0  2e0  2.5e0  3e0  3.5e0" \
          " 4e0  4.5e0  5e0  5.5e0  6e0  6.5e0  7e0  7.5e0  8e0" \
          " 1e1  1.2e1  1.4e1  2e1  3e1  5e1"
        
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
        card.extend(map(str, range(1,nmesh)))
        card = " ".join(card)
        cards.extend(mcnpWrap.wrap(card))

        summeshstrengths = sum(self.meshstrengths)
        strnormmeshstrengths = \
                map(str, map(lambda x: x/summeshstrengths, self.meshstrengths))
        
        # SP card
        card = ["sp995 D"] # D for discrete cummulative probabilities
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
        cards.append("sp996 D 0 1") # D for discrete cummulative probabilities
        
        # create distribution for Y sampling
        # SI card
        cards.extend(["c si997 - y sampling"])
        card = ["si997 H"] # H for bin boundaries.
        card.extend([str(-1*yval),str(yval)])
        card = " ".join(card)
        cards.extend(mcnpWrap.wrap(card))
        # SP card
        cards.append("sp997 D 0 1") # D for discrete cummulative probabilities
        
        # create distribution for Z sampling
        # SI card
        cards.extend(["c si998 - z sampling"])
        card = ["si998 H"] # H for bin boundaries.
        card.extend([str(-1*zval),str(zval)])
        card = " ".join(card)
        cards.extend(mcnpWrap.wrap(card))
        # SP card
        cards.append("sp998 D 0 1") # D for discrete cummulative probabilities

        # create dependent distribution for energy sampling
        cards.extend(["c ds999 - These are the sp/si numbers"])
        card = ["ds999 S"]
        card.extend(map(str, range(1,nmesh)))
        card = " ".join(card)
        cards.extend(mcnpWrap.wrap(card))

        # iterate through each mesh cell, outputting the erg distributions
        for fakecnt, meshcells in enumerate(self.totalProbList):
            cnt = fakecnt + 1
            # sum up source strengths in mesh cell
            meshcell = map(float, meshcells[self.coolingstep])
            summeshstrengths = sum(meshcell)
            
            # then normalize the source strengths in the mesh cell to total 1 (unnecessary...)
            normmeshcell = map(str, map(lambda x: x/summeshstrengths, meshcell))
            
            # create the SI card
            card = ergbins.format(cnt)
            cards.extend(mcnpWrap.wrap(card))
            
            # create the SP card
            card = ["sp{0}".format(cnt)]
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
                            ["tr"+str(cnt), str(xval+2*x*xval), \
                            str(yval+2*y*yval), str(zval+2*z*zval)]\
                            ))
        
        # write all cards to the outfile specified when function was called.
        fw = open(outfile, 'w')
        fw.writelines("\n".join(cards))
        fw.close()
        print "SDEF card has been generated in file '{0}'".format(outfile)
        
        return

