#!/usr/bin/env python

import re

class ModMCNPforPhotons(object):
    """
    """

    def __init__(self, myInputFileName):
        """Init function for class ModMCNPforPhotons. Receives an MCNP input file.
        """
        super(ModMCNPforPhotons, self).__init__()

        self.inputFileName = myInputFileName


    def read(self):
        """ We clean the input file of a bunch of useless blank lines
        and lines filled with asterisks...
        Saved lines are written to file tempFileName
        Blocks 1 and 2 are used to create a surface parser object
        """

        self.block1Lines = []
        self.block2Lines = []
        self.block3Lines = []

        # File reading object for MCNP input file
        fr = open(self.inputFileName, 'r')
        
        # Save the first line as the title card for the MCNP input
        self.title = fr.readline()

        # The mcnp input file is read into it's three blocks
        # comment lines (beginning with 'c' are not included)
        self.mcnp_block_parser(fr, self.block1Lines)
        self.mcnp_block_parser(fr, self.block2Lines)
        self.mcnp_block_parser(fr, self.block3Lines)
        
        fr.close

        print self.inputFileName, 'has been read. use get()', \
                'to access list of sections.'

        return 1


    def mcnp_block_parser(self, fr, blockLines):
        """Method receives a file reader ('fr'), and reads lines
         until a blank line is encountered (or end of file)
        Blank lines are tossed, and any comment lines beginning
         with c are tossed
        Saved lines are added to a list and method returns this list.
        """

        myLine = fr.readline()

        while myLine != '':
            #~ get rid of carriage returns in all lines.
            myLine = myLine.replace('\r','')

            if myLine.replace(" ","") == '\n': # If blank line, goto next section
                myLine = '' # This is the while loop condition
            else:
                blockLines.append(myLine)
                myLine = fr.readline()

        return 1


    def change_block_1(self):
        """ACTION: Method changes the importance cards to affect protons
        """
        
        for line in self.block1:
            # check for the case where both imp:n and imp:p are being used
            if "imp:p" not in line:
                line = line.replace("imp:n", "imp:p")

        return 1


    def change_block_2(self):
        """Block 2 of MCNP input doesn't depend on particle type
        Thus nothing is done.
        """

        pass

    
    def change_block_3(self):
        """ACTION: Method 
        -changes the mode card from 'mode n' to 'mode p'
        -comments out any source-definition cards
        """
        
        commentout = False # We toggle this to determine whether or not to
                            # comment out continued lines

        sourcecards = ["sdef","si","sp","sb","sc","ds,","tr","kcode","ksrc"]

        for line in self.block3:

            # If line is indented 5+ spaces and the previous non-indented 
            #  line was commented out, comment out out this line too.
            if line[:5] == '     ' and commentout:
                line = "c" + line
                continue
            else:
                commentout = False

            linesplit_orig = line.split()
            linesplit = line.lower().split()

            if re.sub("\d+","",linesplit[0]) in sourcecards:
                line = "c " + line
                commentout = True

            elif "mode" == linesplit[0]:
                line = "mode p\n"
            elif "imp:n" == linesplit[0]:
                line = "imp:p " + ' '.join(linesplit_orig[1:]) + '\n'

        return 1


    def write_deck(self, outputFileName=""):
        """
        """

        if outputFileName == "":
            inputFileNameParts = self.inputFileName.split(".")
            x = len(inputFileNameParts) - 1
            if x == 0: x = 1
            outputFileName = ".".join(self.inputFileNameParts[:x]) + "_p" + \
                    ("." + "".join(self.inputFileNameParts[x:])).rstrip(".")

        fw = open(outputFileName, "w")

        # Start writing to file - title card first
        fw.write(self.title)
        for line in self.block1Lines: fw.write(line) #block 1
        fw.write('\n') #blank line dividing blocks 1 and 2
        for line in self.block2Lines: fw.write(line) #block 2
        fw.write('\n') #blank line dividing blocks 2 and 3
        for line in self.block3Lines: fw.write(line) #block 3

        fw.close()

        return 1


