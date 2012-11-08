To run tests, run the script ``run_tests.sh``

This script can be modified at the top to change the location of the source file that it is testing.

-----

Actual tests are contained in ```test_source.F90```.

Of note is that ``source.F90`` file being tested is modified before testing. The modifications made are:

- comment out the ``source`` subroutine; avoids needing several mcnp-internal arrays
- comment out ``write(*,*)`` statements so that output from testing is easily observed

If you want ``write(*,*)`` statements to go through, change the capitalization, e.g. ``WRITE(*,*)`` ...
