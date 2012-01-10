# export SCRIPT_DIR=/filespace/people/r/relson/r2s-act-work/r2s-act/scripts/
export SCRIPT_DIR=../../scripts/
# export TEST_DIR=/filespace/people/r/relson/r2s-act-work/r2s-act/testcases/simplebox-3/
export TEST_DIR=../../testcases/simplebox-3/

cd $TEST_DIR
rm test_gammas1 test_gammas2 test_sdef1 test_sdef2 -f


echo ------------------------------------
echo Now TESTING creation of the simplest sdef file.
echo A warning is expected regarding \# mesh cells != mesh intervals\' product.
echo - - - - - - - - - - - - - - - - - -
# Note: not using default output - avoids accidental overwrite of phtn_sdef
$SCRIPT_DIR/obj_phtn_src.py -i phtn_src -s -o test_sdef1

echo
echo ------------------------------------
echo Now TESTING creation of the simplest gammas file.
echo A warning is expected regarding \# mesh cells != mesh intervals\' product.
echo - - - - - - - - - - - - - - - - - -
# Note: not using default output - avoids accidental overwrite of gammas
$SCRIPT_DIR/obj_phtn_src.py -i phtn_src -s -o test_gammas1

echo
echo ------------------------------------
echo Now TESTING creation of a more advanced sdef file.
echo  No warnings or errors should be given.
echo - - - - - - - - - - - - - - - - - -
$SCRIPT_DIR/obj_phtn_src.py -i phtn_src -s -m 0,10,3,0,10,3,0,10,3 -o test_sdef2

echo
echo --------------------------------------
echo Now TESTING creation of a more advanced gammas file.
echo  No warnings or errors should be given.
echo - - - - - - - - - - - - - - - - - -
$SCRIPT_DIR/obj_phtn_src.py -i phtn_src -g -m 0,10,3,0,10,3,0,10,3 -o test_gammas2

# Cleanup
rm test_gammas1 test_gammas2 test_sdef1 test_sdef2 -f

