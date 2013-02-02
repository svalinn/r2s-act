gfortran -c ../mcnp_placeholder.F90
gfortran -c ../source_data.F90
gfortran -c tetsample.F90 -g

gfortran ../test_speed.F90 -o test_speed tetsample.o mcnp_placeholder.o -g

rm *.o *.mod

./test_speed
