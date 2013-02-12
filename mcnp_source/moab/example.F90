! FindAdjacency: Interacting with iMesh
! 
! This program shows how to get more information about a mesh, by
! getting connectivity two different ways (as connectivity and as
! adjacent 0-dimensional entities).
  
! Usage: FindAdjacency
#define CHECK(a) \
  if (ierr .ne. 0) print *, a

program findadjacency
  implicit none

!#include "iBase_f.h"
#include "iMesh_f.h"

    ! declarations
    integer vert_uses, i
    integer ioffsets

    iMesh_Instance mesh
    IBASE_HANDLE_T rpents, rpverts, rpallverts, ipoffsets
    IBASE_HANDLE_T ents, verts, allverts
    pointer (rpents, ents(0:*))
    pointer (rpverts, verts(0:*))
    pointer (rpallverts, allverts(0:*))
    pointer (ipoffsets, ioffsets(0,*))
    integer ierr, ents_alloc, ents_size
    integer iverts_alloc, iverts_size
    integer allverts_alloc, allverts_size
    integer offsets_alloc, offsets_size
    iBase_EntitySetHandle root_set

    ! create the Mesh instance
    call iMesh_newMesh("", mesh, ierr)
    CHECK("Problems instantiating interface.")

    ! load the mesh
    call iMesh_getRootSet(%VAL(mesh), root_set, ierr)
    CHECK("Problems getting root set")

    call iMesh_load(%VAL(mesh), %VAL(root_set), &
         "bllitenb9culeftTotheat.vtk", "", ierr)
         !"125hex.vtk", "", ierr)
    CHECK("Load failed")

    ! get all 3d elements
    ents_alloc = 0
    call iMesh_getEntities(%VAL(mesh), %VAL(root_set), %VAL(iBase_REGION), &
         %VAL(iMesh_TETRAHEDRON), rpents, ents_alloc, ents_size, &
         ierr)
         !%VAL(iMesh_ALL_TOPOLOGIES), rpents, ents_alloc, ents_size, &
         !ierr)
    CHECK("Couldn't get entities")

    vert_uses = 0

    ! iterate through them; 
    do i = 0, ents_size-1
       ! get connectivity
       iverts_alloc = 0
       call iMesh_getEntAdj(%VAL(mesh), %VAL(ents(i)), &
            %VAL(iBase_VERTEX), &
            rpverts, iverts_alloc, iverts_size, &
            ierr)
       CHECK("Failure in getEntAdj")
       ! sum number of vertex uses

       vert_uses = vert_uses + iverts_size

       if (iverts_size .ne. 0) call free(rpverts)
    end do

    ! now get adjacencies in one big block
    allverts_alloc = 0
    offsets_alloc = 0
    call iMesh_getEntArrAdj(%VAL(mesh), %VAL(rpents), &
         %VAL(ents_size), %VAL(iBase_VERTEX), rpallverts,  &
         allverts_alloc, allverts_size, ipoffsets, offsets_alloc, &
         offsets_size, ierr)
    CHECK("Failure in getEntArrAdj")

    if (allverts_size .ne. 0) call free(rpallverts);
    if (offsets_size .ne. 0) call free(ipoffsets);
    if (ents_size .ne. 0) call free(rpents);

    ! compare results of two calling methods
    if (allverts_size .ne. vert_uses) then
       write(*,'("Sizes didn''t agree!")')
    else 
       write(*,'("Sizes did agree!")')
       write(*,*) allverts_size
    endif

    call iMesh_dtor(%VAL(mesh), ierr)
    CHECK("Failed to destroy interface")

end program findadjacency

