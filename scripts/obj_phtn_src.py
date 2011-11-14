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
        ##self.notes = ['Notes for: ' + self.inputFileName]
        
    
    def read(self):
        """ reads in lines and stores them in blocks on a per-heading basis
         e.g. headings are isotope identifiers or TOTAL
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
                wasBlank = True;
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
        

    def get_total(self, meshcellnum=0):
        """ Method searches headingList to find which entry in probList is the
        the desired TOTAL, and returns the corresponding TOTAL block.
        Method expects that read() has been successfully called.
        If meshcellnum has a value, n, the nth (starting from zero) total entry
        is returned. Otherwise it returns the first total entry.
        """
        
        found = False # records whether a total entry was found
        totcnt = 0
        
        if len(self.headingList) and len(self.probList):
            for cnt, set in enumerate(self.headingList):
                if set == "TOTAL":
                    
                    if totcnt == meshcellnum:
                        found = True
                        self.totalsList = self.probList[cnt]
                        break

                    totcnt += 1
                    
        else:
            print "totalsList or probList was empty. read() was probably not called"
        
        if not found:
            print "'TOTAL' entry {0} was not found in photon source
            file.".format(meshcellnum)
            
        else:
            return self.totalsList
                
            
    def format_total_mcnp(self, coolingstep=0):
        """Method returns a formatted list of strings that is the block under
        heading TOTAL for some cooling step
        Method expects that get_total() has been successfully called.
        If self.totalsList does not exist (e.g. get_total has not been called),
        the method quits.
        If 'coolingstep' is specified, returns the block under TOTAL
        corresponding with the cooling step.
        """
        
        if not len(self.totalsList):
            print "object's variable 'totalsList' has not been set.
            format_total_mcnp will now return ['0']"
            return ['0']

        try:
            self.totalsList[coolingstep]
        except:
            print 'Cooling step', coolingstep, 'not found. Using last cooling step instead.'
            coolingstep = len(self.totalsList) - 1

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


    def total_source_strengths(self, coolingstep=0):
        """Method parses all "TOTAL" sections and creates and returns a list of
        the sum of source strengths.  This list can be used to determine the
        mesh cell strength. NOTE that volume normalization of resulting list may
        be needed, depending on the mesh.
        If 'coolingstep' is specified, returns the block under TOTAL
        corresponding with the cooling step.
        """
       
        self.meshstrengths = list()

        # Search through all headings for those called TOTAL.
        # For each of these, sum the entries in the corresponding source
        # strengths block, and make a list of these sums (self.meshstrengths)
        if len(self.headingList) and len(self.probList):
            for cnt, set in enumerate(self.headingList):
                if set == "TOTAL": 
                    
                    thistotal = [item for sublist in self.probList[cnt][coolingstep] for item in sublist]
                    
                    self.meshstrengths.append(sum(map(float,thistotal)))
                    
        else:
            print "totalsList or probList was empty. read() was probably not called"

        return self.meshstrengths

