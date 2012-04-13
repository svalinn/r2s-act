#!/usr/bin/env python

import re
import string
from optparse import OptionParser
import textwrap as tw

from itaps import iMesh
import scdmesh


class ModMCNPforPhotons(object):
    """Class is used to convert a neutron problem in MCNP to a photon problem

    An MCNP input file is read in, and stored in 4 parts: title card, block 1,
     block 2, and block 3.
    """

    def __init__(self, myInputFileName, dagmc=True):
        """Init function for class ModMCNPforPhotons. Receives an MCNP input file.
        """
        super(ModMCNPforPhotons, self).__init__()

        self.inputFileName = myInputFileName
        self.dagmc = dagmc


    def read(self):
        """Read an MCNP input file and store its parts in the object.

        We clean the input file of a bunch of useless blank lines
        and lines filled with asterisks...
        Saved lines are written to file tempFileName
        Blocks 1 and 2 are used to create a surface parser object
        """

        self.block1Lines = []
        self.block2Lines = []
        self.block3Lines = []
        
        self.block1Comments = []
        self.block2Comments = []
        self.block3Comments = []

        self.extraLines = []
        
        # File reading object for MCNP input file
        fr = open(self.inputFileName, 'r')
        
        # Save the first line as the title card for the MCNP input
        self.title = fr.readline()

        # The mcnp input file is read into it's three blocks
        # comment lines (beginning with 'c' are not included)
        if not self.dagmc:
            self.mcnp_block_parser(fr, self.block1Lines, self.block1Comments)
            self.mcnp_block_parser(fr, self.block2Lines, self.block2Comments)
        self.mcnp_block_parser(fr, self.block3Lines, self.block3Comments)

        # We store anything following the data block in another list
        myLine = fr.readline()
        while myLine != "": # EoF
            self.extraLines.append(myLine)
            myLine = fr.readline()
        
        fr.close()

        print "'{0}' has been read.\n".format(self.inputFileName)

        return 1


    def mcnp_block_parser(self, fr, blockLines, commentLines):
        """Read lines from input file until an entire block has been read.
        
        Method receives a file reader ('fr'), and reads lines
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
                myLine = '' # This escapes the while loop condition
            else:
                # We split once at $, so that comments are unchanged
                mySplit = string.split(myLine, sep='$', maxsplit=1)
                blockLines.append(mySplit[0].replace('\n',''))

                # We do a few list checks to avoid errors
                if len(mySplit) > 1 and len(mySplit[1]) > 0:
                    commentLines.append('$' + mySplit[1])
                else: commentLines.append("\n")
                myLine = fr.readline()

        return 1


    def change_block_1(self):
        """Modify contents of self.block1Lines for a photon problem.
        
        ACTION: Method changes the importance cards to affect protons
        RETURNS: '1' when run successfully
        """

        cntimp = 0
        
        for cnt, line in enumerate(self.block1Lines):
            lineLower = line.lower()

            # ignore comment lines
            if lineLower.split()[0] == 'c':
                continue

            # check for the case where only imp:n is being used
            if "imp:p" not in lineLower and "imp:n" in lineLower:
                line = lineLower.replace("imp:n", "imp:p")
                cntimp += 1

            self.block1Lines[cnt] = line

        print "Block 1 has been updated:\n" \
                "-{0} imp:n were changed to imp:p\n" \
                "".format(cntimp)

        return 1


    def change_block_2(self):
        """Modify contents of self.block2Lines for a photon problem (N/A).
        
        Block 2 of MCNP input doesn't depend on particle type
        Thus nothing is done.
        """

        # print "Block 2 has been updated:\n"

        pass

    
    def change_block_3(self):
        """Modify contents of self.block3Lines for a photon problem.
        
        ACTION: Method 
        -changes the mode card from 'mode n' to 'mode p'
        -remove phys:n
        -change inp:n to inp:p
        -comments out any source-definition cards.  These cards are:
         sdef, si, sp, sb, sc, ds, kcode, ksrc
        """
        
        cntsrc = 0
        notemode = ""
        noteimp = ""
        notephys = ""

        commentout = False # We toggle this to determine whether or not to
                            # comment out continued lines

        sourcecards = ["sdef","si","sp","sb","sc","ds","kcode","ksrc"]

        for cnt, line in enumerate(self.block3Lines):
            
            # ignore comment lines
            if line.split()[0] == 'c' or line.split()[0] == 'C':
                continue

            # If line is indented 5+ spaces and the previous non-indented 
            #  line was commented out, comment out out this line too.
            if line[:5] == '     ' and commentout:
                self.block3Lines[cnt] = "c" + line
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

            elif "phys:n" == linesplit[0]:
                line = "c " + line
                notephys = "-phys:n was commented out \n"

            elif "mode" == linesplit[0]:
                line = "mode p"
                notemode = "-mode card replaced with 'mode p' \n"

            # keep same cell importances, but set them for photons
            elif "imp:n" == linesplit[0]:
                line = "imp:p " + ' '.join(linesplit_orig[1:]) + ''
                noteimp = "-imp:n card converted to imp:p with same values\n"
            
            else: # no changes to the line
                continue

            commentout = True
            self.block3Lines[cnt] = line

        print "Block 3 has been updated: \n" \
                "-{0} source cards commented out\n" \
                "{1}{2}{3}\n" \
                "Note that tallies were not modified. Remember that neutron" \
                " tallies\nshould probably be changed." \
                "\n".format(cntsrc, notemode, notephys, noteimp)

        return 1


    def add_fmesh_from_scdmesh(self, sm):
        """Geometry information is read to create a photon fmesh card.
        
        ACTION: Lines are appended to self.block3lines.
        RECEIVES: A structured mesh object (scdmesh.py)
        REQUIRES: Block 3 has been read into self.block3lines; photon energies
         have been tagged to 'sm.mesh.rootSet'.
        RETURNS: 1 if successful, 0 if an error occurs.
        """
        
        # We get the coarse intervals and the number of steps in each interval
        (xCoarse, xSteps) = _get_coarse_and_intervals(sm.getDivisions("x"))
        (yCoarse, ySteps) = _get_coarse_and_intervals(sm.getDivisions("y"))
        (zCoarse, zSteps) = _get_coarse_and_intervals(sm.getDivisions("z"))

        # We look for the tag with the energy bin boundary values
        try:
            phtn_ergs = sm.mesh.getTagHandle("PHTN_ERGS")
            myergbins = phtn_ergs[sm.mesh.rootSet] 

        # if there is no PHTN_ERGS tag, then we send an empty string in myergbins
        except iBase.TagNotFoundError: 
            print "ERROR: Tag for photon energy group boundaries was not found."
            return 0

        mcnpWrap = tw.TextWrapper()
        mcnpWrap.initial_indent = 0*' '
        mcnpWrap.subsequent_indent = 6*' '
        mcnpWrap.wdith = 80
        mcnpWrap.break_on_hyphens = False

        self.block3lines.append("fmesh444:p\n")
        self.block3lines.append("      geom=xyz  origin={0} {1} {2}" \
                "\n".format(xCoarse[0], yCoarse[0], zCoarse[0]))

        self.block3lines.append( \
                mcnpWrap.wrap("imesh="+" ".join(xCoarse[1:]))+"\n")
        self.block3lines.append( \
                mcnpWrap.wrap("iints="+" ".join(xSteps))+"\n")
        self.block3lines.append( \
                mcnpWrap.wrap("jmesh="+" ".join(yCoarse[1:]))+"\n")
        self.block3lines.append( \
                mcnpWrap.wrap("jints="+" ".join(ySteps))+"\n")
        self.block3lines.append( \
                mcnpWrap.wrap("kmesh="+" ".join(zCoarse[1:]))+"\n")
        self.block3lines.append( \
                mcnpWrap.wrap("kints="+" ".join(zSteps))+"\n")
        
        self.block3lines.append( \
                mcnpWrap.wrap("emesh="+" ".join(phtn_ergs))+"\n")

        return 1


    def write_deck(self, outputFileName=""):
        """Create a new MCNP input file from the object's contents.
        
        ACTION: Method writes the contents of self.block#Lines to a new file.
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
        if not self.dagmc:
            for cnt, line in enumerate(self.block1Lines):
                fw.write(line + self.block1Comments[cnt]) #block 1
            
            fw.write('\n') #blank line dividing blocks 1 and 2

            for cnt, line in enumerate(self.block2Lines):
                fw.write(line + self.block2Comments[cnt]) #block 2
            
            fw.write('\n') #blank line dividing blocks 2 and 3

        for cnt, line in enumerate(self.block3Lines):
            fw.write(line + self.block3Comments[cnt]) #block 3

        if len(self.extraLines) > 0:
            fw.write('\n') #blank line dividing block 3 and extra file contents

        for line in self.extraLines:
            fw.write(line) # extra file contents

        fw.close()

        print "Modified input deck has been written to '{0}'".format(outputFileName)

        return 1


def _get_coarse_and_intervals(xdiv):
    """From list of mesh intervals get xmesh and xints for fmesh card
    """
    xCoarse = [xdiv[0]]
    xSteps = list()
            
    dx = xdiv[1]-xdiv[0]
    oldx = xdiv[1]
    cnt = 1
    for x in xdiv[2:]:
        if round(dx,5) != round(x-oldx,5):
            xCoarse.append(oldx)
            xSteps.append(cnt)
            cnt = 1
            dx = x-oldx
        else:
            cnt += 1
        oldx = x
    xCoarse.append(oldx)
    xSteps.append(cnt)

    return (xCoarse, xSteps)


def main():
    """ACTION: Method defines an option parser and handles command-line
    usage of this module.
    REQUIRES: command line arguments to be passed - otherwise prints help
    information.
    RECEIVES: N/A
    """

    usage = "Usage: %prog INPUTFILE [options]\n\n" \
            "INPUTFILE is the MCNP or DAG-MCNP input deck that is to be " \
            "modified. \nUse the -d option for DAG-MCNP files."
    parser = OptionParser(usage)
    
    # Output file name, and toggle for DAG-MCNP problems
    parser.add_option("-o","--output",action="store",dest="outputfile", \
            default="", help="Filename to write modified MCNP input to." \
            " Default is to append input filename with '_p'.")
    parser.add_option("-d","--dagmc",action="store_true",dest="dagmc", \
            default=False, help="Add flag to parse file like a DAG-MCNP file " \
            "(which has only title card and block 3 cards). Default: %default")

    (options, args) = parser.parse_args()
    
    if len(args):
        x = ModMCNPforPhotons(args[0], options.dagmc)

        x.read()
        if not x.dagmc:
            x.change_block_1()
            x.change_block_2()
        x.change_block_3()
        x.write_deck(options.outputfile)
    
    else:
        print "An input file must be specified as the first argument to use " \
                "this script.\nSee the -h option for more information."

    return 1


# Handles module being called as a script.
if __name__=='__main__':
    main()

