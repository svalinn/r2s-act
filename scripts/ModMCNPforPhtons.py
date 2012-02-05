#!/usr/bin/env python

import re
from optparse import OptionParser


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

        print "'{0}' has been read.\n".format(self.inputFileName)

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
        RETURNS: N/A
        """

        cntimp = 0
        
        for cnt, line in enumerate(self.block1Lines):
            # check for the case where both imp:n and imp:p are being used
            if "imp:p" not in line:
                line = line.replace("imp:n", "imp:p")
                cntimp += 1

            self.block1Lines[cnt] = line

        print "Block 1 has been updated:\n" \
                "-{0} imp:n were changed to imp:p\n" \
                "".format(cntimp)

        return 1


    def change_block_2(self):
        """Block 2 of MCNP input doesn't depend on particle type
        Thus nothing is done.
        """

        # print "Block 2 has been updated:\n"

        pass

    
    def change_block_3(self):
        """ACTION: Method 
        -changes the mode card from 'mode n' to 'mode p'
        -comments out any source-definition cards
        """
        
        cntsrc = 0
        notemode = ""
        noteimp = ""
        notephys = ""

        commentout = False # We toggle this to determine whether or not to
                            # comment out continued lines

        sourcecards = ["sdef","si","sp","sb","sc","ds","tr","kcode","ksrc"]

        for cnt, line in enumerate(self.block3Lines):

            # If line is indented 5+ spaces and the previous non-indented 
            #  line was commented out, comment out out this line too.
            if line[:5] == '     ' and commentout:
                line = "c" + line
                continue
            else:
                commentout = False

            linesplit_orig = line.split()
            linesplit = line.lower().split()

            # remove numbers from first string part, and try to match with
            #  the basic source cards.
            if re.sub("\d+","",linesplit[0]) in sourcecards:
                line = "c " + line
                cntsrc += 1
                commentout = True

            elif "phys:n" == linesplit[0]:
                line = "c " + line
                notephys = "-phys:n was commented out \n"
                commentout = True

            elif "mode" == linesplit[0]:
                line = "mode p\n"
                notemode = "-mode card replaced with 'mode p' \n"

            elif "imp:n" == linesplit[0]:
                line = "imp:p " + ' '.join(linesplit_orig[1:]) + '\n'
                noteimp = "-imp:n card converted to imp:p \n"

            self.block3Lines[cnt] = line

        print "Block 3 has been updated: \n" \
                "-{0} source cards commented out\n" \
                "{1}{2}{3}\n" \
                "Note that tallies were not modified." \
                "\n".format(cntsrc, notemode, notephys, noteimp)
        return 1


    def write_deck(self, outputFileName=""):
        """ACTION: Method writes the contents of self.block#Lines to a new file.
            File name is determined automatically if not supplied.
        REQUIRES: read() has been called for the class object so that blockLines
            and title are not empty.
        RETURNS: N/A
        """

        if outputFileName == "":
            inputFileNameParts = self.inputFileName.split(".")
            x = len(inputFileNameParts) - 1
            if x == 0: x = 1
            outputFileName = ".".join(inputFileNameParts[:x]) + "_p" + \
                    ("." + "".join(inputFileNameParts[x:])).rstrip(".")

        fw = open(outputFileName, "w")

        # Start writing to file - title card first
        fw.write(self.title)
        for line in self.block1Lines: fw.write(line) #block 1
        fw.write('\n') #blank line dividing blocks 1 and 2
        for line in self.block2Lines: fw.write(line) #block 2
        fw.write('\n') #blank line dividing blocks 2 and 3
        for line in self.block3Lines: fw.write(line) #block 3

        fw.close()

        print "Modified input deck has been written to '{0}'".format(outputFileName)

        return 1


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
            default=False, help="The MCNP input file to read from") 
    parser.add_option("-o","--output",action="store",dest="outputfile", \
            default="", help="Filename to write modified MCNP input to." \
            " Default is to append input filename with '_p'.")

    (options, args) = parser.parse_args()

    if options.filename != False:
        x = ModMCNPforPhotons(options.filename)

        x.read()
        x.change_block_1()
        x.change_block_2()
        x.change_block_3()
        x.write_deck(options.outputfile)
    
    else:
        print "An input file must be specified to use this script.\n" \
                "Use the -i option or see the -h option for more information."

    return 1


# Handles module being called as a script.
if __name__=='__main__':
    main()

