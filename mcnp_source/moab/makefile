#include /path/to/iMesh/iMesh-Defs.inc
include /filespace/groups/cnerg/opt/MOAB/bld/opt-cubit-c12/itaps/imesh/iMesh-Defs.inc

FC = gfortran -fcray-pointer -m32 -I/filespace/groups/cnerg/opt/MOAB/opt-cubit-c12/include -lstdc++ -liMesh -L/filespace/groups/cnerg/opt/MOAB/opt-nocgm/lib -lMOAB -lhdf5 -lnetcdf -o testout
CXX = g++
CC = gcc


Fortran:
	${FC} -c ${FFLAGS} ${IMESH_INCLUDES} $< example.F90

#.F.o:
#	${FC} -c ${FFLAGS} ${IMESH_INCLUDES} $<

##FindConnectF: FindConnectF.o
#FindConnectF:
#	$(CXX) -m32 -lgfortran -lgfortranbegin -o $@ FindConnectF.o ${IMESH_LIBS}
#
##FindConnectC: FindConnectC.o
#FindConnectC:
#	$(CXX) $(CXXFLAGS) -o $@ FindConnectC.o ${IMESH_LIBS}
#
#.c.o:
#	$(CC) -c $(CFLAGS) $(IMESH_INCLUDES) $<
#
