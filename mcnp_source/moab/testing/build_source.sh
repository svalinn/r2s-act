python hide_source.py ../../source_moab.F90

# Generate the .o files..
#gfortran -c mcnp_placeholder.F90 ../../source_moab.F90 \
gfortran -c mcnp_placeholder.F90 \
    -fbounds-check -g -fcray-pointer \
    -I/filespace/groups/cnerg/opt/MOAB/opt-cubit-c12/include

gfortran source.F90 mcnp_placeholder.o \
    -fbounds-check -g -fcray-pointer \
    -liMesh -L/filespace/groups/cnerg/opt/MOAB/opt-nocgm/lib \
    -I/filespace/groups/cnerg/opt/MOAB/opt-cubit-c12/include \
    -lMOAB -lhdf5 -lnetcdf -lstdc++
