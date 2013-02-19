# Modify and copy source.F90 file
python hide_source.py ../../source_moab.F90

# Generate the .o files..
gfortran -c mcnp_placeholder.F90 source.F90 tests.F90 \
    -fbounds-check -g -fcray-pointer \
    -I/filespace/groups/cnerg/users/relson/MOAB/opt-cubit-c12/include
    #-I/filespace/groups/cnerg/opt/MOAB/opt-cubit-c12/include


# compile!
gfortran test_source.F90 -o test_source  -fbounds-check -g -fcray-pointer \
    mcnp_placeholder.o source.o tests.o \
    -liMesh -L/filespace/groups/cnerg/opt/MOAB/opt-nocgm/lib \
    -I/filespace/groups/cnerg/users/relson/MOAB/opt-cubit-c12/include \
    -lMOAB -lhdf5 -lnetcdf -lstdc++

    #-I/filespace/groups/cnerg/opt/MOAB/opt-cubit-c12/include \

# run unit tests
./test_source

# cleanup
rm *.o
rm *.mod
rm test_source
rm source.F90
