To run unit tests, run the script ``run_unit_tests.sh``

This script can be modified at the top to change the location of the source file that it is testing.

These tests are copied from mcnp_source/testing, for use with source_moab.F90.

-----

Actual tests are contained in ``test_source.F90``.

Of note is that ``source.F90`` file being tested is modified before testing. The modifications made are:

- comment out the ``source`` subroutine; avoids needing several mcnp-internal arrays/variables
- comment out ``write(*,*)`` statements so that output from testing is easily observed
- replaces ``expirx`` calls with ``continue``

If you are making your own modifications/testing and want ``write(*,*)`` statements to go through, change the capitalization, e.g. ``WRITE(*,*)`` or ``wRIte(*,*)`` ...


