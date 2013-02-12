#include /path/to/iMesh/iMesh-Defs.inc
include /filespace/groups/cnerg/opt/MOAB/bld/opt-cubit-c12/itaps/imesh/iMesh-Defs.inc

FC = gfortran -fcray-pointer -m32
CXX = g++
CC = gcc

FindConnectC: FindConnectC.o
	$(CXX) $(CXXFLAGS) -o $@ FindConnectC.o ${IMESH_LIBS}

FindConnectF: FindConnectF.o
	$(CXX) -m32 -lgfortran -lgfortranbegin -o $@ FindConnectF.o ${IMESH_LIBS}

.c.o:
	$(CC) -c $(CFLAGS) $(IMESH_INCLUDES) $<

.F.o:
	${FC} -c ${FFLAGS} ${IMESH_INCLUDES} $<
