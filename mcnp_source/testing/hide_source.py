#! /usr/bin/env python

#This script is passed a path for a source.F90 file (e.g. from the parent
#  directory).  It searches the file for 'subroutine source' at the start of
#  a line, and then comments that line and subsequent lines until a line is
#  found that begins with 'end subroutine source'. This hack is used for crude
#  testing purposes.

import sys
import os

def main():
    if not os.path.isfile(sys.argv[1]):
        print "File", sys.argv[1], "not found."
        sys.exit(1)
    if sys.argv[1] == "source.F90":
        print "File", sys.argv[1], "has same name as script output; " \
                "script will not overwrite the original."

    fr = open(sys.argv[1], 'r')
    fw = open("source.F90", 'w')

    commentout = 0
    for line in fr:
        # Fun fact: range specifications exceeding list sizes are not a problem
        if commentout == 0 and line.split()[0:2] == ["subroutine","source"]:
            commentout = 1
        if commentout == 1:
            fw.write("!" + line)
            if line.split()[0:3] == ["end","subroutine","source"]:
                commentout = 2
        elif commentout < 0:
            fw.write("!" + line)
            if line.split()[-1:] != ["&"]:
                commentout += 3
        elif line.split()[0:1] == ["write(*,*)"]:
            fw.write("!" + line)
            if line.split()[-1:] == ["&"]:
                commentout -= 3
        else:
            fw.write(line)

    fr.close()
    fw.close()
    print "Successful modification for testing made to 'source.F90'\n"

    return


if __name__ == '__main__':
    if len(sys.argv) == 2:
        main()
    else:
        print "Fail.", sys.argv
        sys.exit(1)
