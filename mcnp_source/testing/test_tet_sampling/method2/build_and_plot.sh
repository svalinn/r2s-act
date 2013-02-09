gfortran -c ../mcnp_placeholder.F90
gfortran -c ../source_data.F90
gfortran -c tetsample.F90 -g

gfortran ../test_correct_pos.F90 -o test_correct tetsample.o mcnp_placeholder.o source_data.o -g

rm *.o *.mod

./test_correct

python ../plot_tet_points.py source_points
