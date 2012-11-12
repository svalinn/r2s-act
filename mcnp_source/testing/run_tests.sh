# Modify and copy source.F90 file
python hide_source.py ../source_gamma_refactor.F90

# Generate the .o files..
gfortran -c mcnp_placeholder.F90 -g
gfortran -c source.F90 -g

# compile!
gfortran test_source.F90 -o test_source   mcnp_placeholder.o source.o -g

# run test
./test_source

# cleanup
rm *.o
rm *.mod
rm test_source
