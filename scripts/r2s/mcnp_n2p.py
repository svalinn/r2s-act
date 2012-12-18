#!/usr/bin/env python

import re
import string
from optparse import OptionParser
import textwrap as tw

from itaps import iMesh, iBase, iMeshExtensions
from r2s.scdmesh import ScdMesh, ScdMeshError


class ModMCNPforPhotons(object):
    """Class is used to convert a neutron problem in MCNP to a photon problem

    An MCNP input file is read in, and stored in 4 parts: title card, block 1,
     block 2, and block 3.
    """

    def __init__(self, myInputFileName, dagmc=None):
        """Init function for class ModMCNPforPhotons. Receives an MCNP input 
        file.
        """
        super(ModMCNPforPhotons, self).__init__()

        self.inputFileName = myInputFileName

        self.dagmc = dagmc
        if self.dagmc is None:
            self.dagmc = _is_dagmc(self.inputFileName)


    def read(self):
        """Read an MCNP input file and store its parts in the object.

        We clean the input file of a bunch of useless blank lines
        and lines filled with asterisks...
        Saved lines are written to file tempFileName
        Blocks 1 and 2 are used to create a surface parser object
        """

        # empty initializations
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


    def convert(self):
        """

        """

        if not self.dagmc:
            self.change_block_1()
            self.change_block_2()
        self.change_block_3()

        return


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
        notefmesh = ""

        commentout = False # We toggle this to determine whether or not to
                            # comment out continued lines

        com = "c $ " # using $ avoids issue with long lines.

        sourcecards = ["sdef","si","sp","sb","sc","ds","kcode","ksrc"]

        for cnt, line in enumerate(self.block3Lines):
            
            # ignore existing comment lines
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
                line = com + line
                cntsrc += 1

            elif "phys:n" == linesplit[0]:
                line = com + line
                notephys = "-phys:n was commented out \n"

            elif "mode" == linesplit[0]:
                line = "mode p"
                notemode = "-mode card replaced with 'mode p' \n"

            # keep same cell importances, but set them for photons
            elif "imp:n" == linesplit[0]:
                line = "imp:p " + ' '.join(linesplit_orig[1:]) + ''
                noteimp = "-imp:n card converted to imp:p with same values\n"
            
            # comment out fmesh card
            elif "fmesh" == linesplit[0][:5]:
                line = com + line
                notefmesh = "-fmesh card(s) commented out."

            else: # no changes to the line
                continue

            commentout = True
            self.block3Lines[cnt] = line

        print "Block 3 has been updated: \n" \
                "-{0} source cards commented out\n" \
                "{1}{2}{3}{4}\n" \
                "Note that tallies were not modified. Remember that neutron" \
                " tallies\nshould probably be changed." \
                "\n".format(cntsrc, notemode, notephys, noteimp, notefmesh)

        return 1


    def add_fmesh_from_scdmesh(self, sm):
        """Geometry information is read to create a photon fmesh card.
        
        ACTION: Lines are appended to self.block3Lines.
        RECEIVES: A structured mesh object (scdmesh.py)
        REQUIRES: Block 3 has been read into self.block3Lines; photon energies
         have been tagged to 'sm.imesh.rootSet'.
        RETURNS: 1 if successful, 0 if an error occurs.
        """
        
        # We get the coarse intervals and the number of steps in each interval
        (xCoarse, xSteps) = _get_coarse_and_intervals(sm.getDivisions("x"))
        (yCoarse, ySteps) = _get_coarse_and_intervals(sm.getDivisions("y"))
        (zCoarse, zSteps) = _get_coarse_and_intervals(sm.getDivisions("z"))
        
        # We then convert them from floats to strings
        xCoarse = [str(x) for x in xCoarse]
        xSteps = [str(x) for x in xSteps]
        yCoarse = [str(y) for y in yCoarse]
        ySteps = [str(y) for y in ySteps]
        zCoarse = [str(z) for z in zCoarse]
        zSteps = [str(z) for z in zSteps]

        # String com allows us to comment out the fmesh card if desired
        com = ""

        # We look for the tag with the energy bin boundary values
        try:
            phtn_ergs = sm.imesh.getTagHandle("PHTN_ERGS")
            myergbins = [str(x) for x in phtn_ergs[sm.imesh.rootSet]]

        # if there is no PHTN_ERGS tag then we send an empty string in myergbins
        except iBase.TagNotFoundError: 
            print "WARNING: Tag for photon energy group boundaries was not " \
                    "found.\n\tThe default fmesh card will be commented out."
            myergbins = ""
            com = "c "

        # We set up a TextWrapper for the keywords, indenting lines 6 spaces
        mcnpWrap = tw.TextWrapper()
        mcnpWrap.initial_indent = 6*' '
        mcnpWrap.subsequent_indent = (6+6)*' '
        mcnpWrap.wdith = 80 - len(com) # avoid commented lines being too long
        mcnpWrap.break_on_hyphens = False
        mcnpWrap.drop_whitespace = False

        self.block3Lines.append(com + "fmesh444:p\n")
        self.block3Lines.append(com + "      geom=xyz origin={0} {1} {2}" \
                "\n".format(xCoarse[0], yCoarse[0], zCoarse[0]))
        
        for line in mcnpWrap.wrap("imesh="+" ".join(xCoarse[1:])):
            self.block3Lines.append(com+line+"\n")
        for line in mcnpWrap.wrap("iints="+" ".join(xSteps)):
            self.block3Lines.append(com+line+"\n")
        for line in mcnpWrap.wrap("jmesh="+" ".join(yCoarse[1:])):
            self.block3Lines.append(com+line+"\n")
        for line in mcnpWrap.wrap("jints="+" ".join(ySteps)):
            self.block3Lines.append(com+line+"\n")
        for line in mcnpWrap.wrap("kmesh="+" ".join(zCoarse[1:])):
            self.block3Lines.append(com+line+"\n")
        for line in mcnpWrap.wrap("kints="+" ".join(zSteps)):
            self.block3Lines.append(com+line+"\n")

        for line in mcnpWrap.wrap("emesh="+" ".join(myergbins)):
            self.block3Lines.append(com+line+"\n")

        print "A default photon fmesh card has been added to the input, " \
                "and matches the mesh structure found in the MOAB mesh.\n"

        # We look for the PHTN_SRC_TOTAL tag on the mesh and add it to a
        #  commented out tally multiplier card for the meshtally.
        try:
            sumvoxelstrengths = sm.imesh.getTagHandle( \
                    "PHTN_SRC_TOTAL")[sm.imesh.rootSet]
            self.block3Lines.append("c This multiplier will convert tallies " \
                    "from tallies per source particle\n" \
                    "c  to tallies per second.\n")
            self.block3Lines.append( \
                    "c fm444 {0:e}\n".format(sumvoxelstrengths))
            print "A tally multiplier card (fm444) has been added for " \
                    "normalizing to the total photon source strength in the " \
                    "problem."
        except iBase.TagNotFoundError:
            pass

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
            try:
                fw.write(line + self.block3Comments[cnt]) #block 3
            except IndexError:
                fw.write(line)

        if len(self.extraLines) > 0:
            fw.write('\n') #blank line dividing block 3 and extra file contents

        for line in self.extraLines:
            fw.write(line) # extra file contents

        fw.close()

        print "Modified input deck has been written to '{0}'".format(outputFileName)

        return 1


def _is_dagmc(filename):
    """Use first non-title, non-comment line to determin if input is for DAGMCNP

    The test to determine this has two cases:
    - First character of line is a number -> regular MCNP input
    - Otherwise, first character corresponds
       with some data card... -> DAG MCNP input
    """

    fr = open(filename, 'r')

    line = fr.readline()
    line = fr.readline()

    while line[:2] == 'c ' or line == 'c':
        line = fr.readline().strip().lower()

    try:
        int(line[0])
        # number -> regular MCNP input
        return False
    except ValueError:
        # non-number -> DAG MCNP input
        return True


def _get_coarse_and_intervals(xdiv):
    """From list of mesh intervals get xmesh and xints for fmesh card

    RETURNS: xCoarse and xSteps, which are lists of loats
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
    parser.add_option("-m","--mesh",action="store",dest="fmesh", \
            default=None, help="Add meshtally (fmesh card), with mesh taken " \
            "from a .h5m or .vtk file that is supplied with this option.")

    (options, args) = parser.parse_args()
    
    if len(args):
        x = ModMCNPforPhotons(args[0], options.dagmc)

        x.read()
        x.convert()
        if options.fmesh != None:
            smesh = ScdMesh.fromFile(options.fmesh)
            x.add_fmesh_from_scdmesh(smesh)
        x.write_deck(options.outputfile)
    
    else:
        print "An input file must be specified as the first argument to use " \
                "this script.\nSee the -h option for more information."

    return 1


# Handles module being called as a script.
if __name__=='__main__':
    main()

