#
gfortran example.F90 -o testout -fcray-pointer -I/filespace/groups/cnerg/opt/MOAB/opt-cubit-c12/include -lstdc++ -liMesh -L/filespace/groups/cnerg/opt/MOAB/opt-nocgm/lib -lMOAB -lhdf5 -lnetcdf
