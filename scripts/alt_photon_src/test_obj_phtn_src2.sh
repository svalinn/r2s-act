#
# The shell script tests the command line options for calling methods in
# obj_phtn_src.py, as well as running MCNP after carrying out a test evaluation.# 
#

# e.g. export SCRIPT_DIR=/filespace/people/r/relson/r2s-act-work/r2s-act/scripts/
export SCRIPT_DIR=../../scripts/
# e.g. export TEST_DIR=/filespace/people/r/relson/r2s-act-work/r2s-act/testcases/simplebox-3/
export TEST_DIR=../../testcases/hemispheres/

export MCNP5_PATH=/filespace/people/r/relson/DAG-MCNP/5.1.51/trunk/Source/src/mcnp5

let CNT=0

cd $TEST_DIR
rm test_gammas1 test_gammas2 test_gammas3 test_gammas4 test_sdef1 test_sdef2 matFracsTest.h5m test_mcnp.* -f

let CNT=CNT+1
echo $CNT------------------------------------
echo Now TESTING creation of the simplest SDEF file.
echo A warning is expected regarding \# mesh cells != mesh intervals\' product.
echo - - - - - - - - - - - - - - - - - -
# Note: not using default output - avoids accidental overwrite of phtn_sdef
/usr/bin/time -f "Time used: %E" $SCRIPT_DIR/obj_phtn_src.py -i phtn_src -s -o test_sdef1

echo
let CNT=CNT+1
echo $CNT------------------------------------
echo Now TESTING creation of the simplest 'gammas' file.
echo A warning is expected regarding \# mesh cells != mesh intervals\' product.
echo - - - - - - - - - - - - - - - - - -
# Note: not using default output - avoids accidental overwrite of gammas
/usr/bin/time -f "Time used: %E" $SCRIPT_DIR/obj_phtn_src.py -i phtn_src -s -o test_gammas1

echo
let CNT=CNT+1
echo $CNT------------------------------------
echo Now TESTING creation of a more advanced SDEF file.
echo  No warnings or errors should be given.
echo - - - - - - - - - - - - - - - - - -
/usr/bin/time -f "Time used: %E" $SCRIPT_DIR/obj_phtn_src.py -i phtn_src -s -m -5,5,8,-5,5,8,-5,5,8 -o test_sdef2

echo
let CNT=CNT+1
echo $CNT------------------------------------
echo Now TESTING creation of a more advanced 'gammas' file.
echo  No warnings or errors should be given.
echo - - - - - - - - - - - - - - - - - -
/usr/bin/time -f "Time used: %E" $SCRIPT_DIR/obj_phtn_src.py -i phtn_src -g -m -5,5,8,-5,5,8,-5,5,8 -o test_gammas2

echo
read -p "Press [Enter] key to run next set of tests..." 
echo
let CNT=CNT+1
echo $CNT------------------------------------
echo Now TESTING addition of photon source information tags to an h5m mesh.
echo  No warnings or errors should be given.
echo - - - - - - - - - - - - - - - - - -

cp matFracs.h5m matFracsTest.h5m
/usr/bin/time -f "Time used: %E" $SCRIPT_DIR/obj_phtn_src.py -i phtn_src -H matFracsTest.h5m

echo
let CNT=CNT+1
echo $CNT------------------------------------
echo Now trying to add the information to the same mesh again.
echo  This should fail when trying to create new tags.
echo - - - - - - - - - - - - - - - - - -
/usr/bin/time -f "Time used: %E" $SCRIPT_DIR/obj_phtn_src.py -i phtn_src -H matFracsTest.h5m

echo
let CNT=CNT+1
echo $CNT------------------------------------
echo Now trying to add the information to the same mesh again, but with retagging enabled.
echo  No warnings or errors should be given.
echo - - - - - - - - - - - - - - - - - -
/usr/bin/time -f "Time used: %E" $SCRIPT_DIR/obj_phtn_src.py -i phtn_src -H matFracsTest.h5m -r

echo
let CNT=CNT+1
echo $CNT------------------------------------
echo Now trying to read the photon source information back from a mesh missing this information.
echo  This should fail, with an error noting the missing information.
echo - - - - - - - - - - - - - - - - - -
/usr/bin/time -f "Time used: %E" $SCRIPT_DIR/obj_phtn_src.py -i phtn_src -p matFracs.h5m -o test_gammas3 -m -5,5,8,-5,5,8,-5,5,8 

echo
let CNT=CNT+1
echo $CNT------------------------------------
echo Now trying to read the photon source information back from a mesh containing this information.
echo  This should successfully create a gammas file.
echo - - - - - - - - - - - - - - - - - -
$/usr/bin/time -f "Time used: %E" SCRIPT_DIR/obj_phtn_src.py -p matFracsTest.h5m -o test_gammas4 -m -5,5,8,-5,5,8,-5,5,8

echo
read -p "Press [Enter] key to run next set of tests..." 
echo
let CNT=CNT+1
echo $CNT------------------------------------
echo "MCNP5 will now be run to test the phtn_src->h5m->gammas->source.f90 workflow for the 3x3x3 case."
echo  This should succeed and look like a normal MCNP5 run - but with a the comment "Reading gammas file completed!"
echo NOTE: MCNP5 must be compiled with the file r2s-act/mcnp_source/source_gamma_meshtal2.F90
echo - - - - - - - - - - - - - - - - - -
echo
read -p "Press [Enter] key to run MCNP5."
echo

cp test_gammas4 gammas

$MCNP5_PATH i=hemispheres_mcnp_phtn.inp n=test_mcnp.

# Cleanup
echo
echo All tests are done. Now removing created files.
rm test_gammas1 test_gammas2 test_gammas3 test_gammas4 test_sdef1 test_sdef2 xmatFracsTest.h5m test_mcnp.* -f

