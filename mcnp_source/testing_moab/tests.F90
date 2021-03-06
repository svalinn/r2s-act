! This program runs a set of tests on the individual subroutines for a 
!  mesh-based photon source sampling routine in MCNP.
! In lieu of packaging a unit testing framework, current tests are ad-hoc
!  checks using conditionals.
!

module tests_mod
! Module contains all tests
        use mcnp_global
        !use source_data
implicit none

#include "iMesh_f.h"

#define SET_UP \
  terr = 0
#define ASSERT_TRUE(a) \
  if (.not.a) terr=terr+1
#define ASSERT_EQUAL(a,b) \
  if (a.ne.b) terr=terr+1
#define ASSERT_NOT_EQUAL(a,b) \
  if (a.eq.b) terr=terr+1

        integer :: testunitnum, i, terr

        ! Attempt to get around 'ambiguous reference' errors.
        integer :: iBase_REGION_t, iMesh_TETRAHEDRON_t, iMesh_HEXAHEDRON_t


!contains 
end module tests_mod

! Beginning of test subroutines

! subroutine test_read_custom_ergs
!   use tests_mod
!   use source_data
! ! Reads in values from 'test_ergs_list.txt' and matches them to expected values 
!         integer :: n_grps = 42
!         real(dknd),dimension(1:43) :: test_ener_phot
!         real(dknd) :: a, b
! 
!         testunitnum = getUnit()
!         OPEN(unit=testunitnum, form='formatted', file='test_ergs_list.txt')
!         call read_custom_ergs(testunitnum)
!         CLOSE(testunitnum)
! 
!         test_ener_phot = (/0.0,0.01,0.02,0.03,0.045,0.06,0.07,0.075,0.1,0.15, &
!             0.2,0.3,0.4,0.45,0.51,0.512,0.6,0.7,0.8,1.0,1.33,1.34,1.5, &
!             1.66,2.0,2.5,3.0,3.5,4.0,4.5,5.0,5.5,6.0,6.5,7.0,7.5,8.0, &
!             10.0,12.0,14.0,20.0,30.0,50.0/)
! 
!         do i=1,n_grps+1
!           !assert
!           a = test_ener_phot(i)
!           b = my_ener_phot(i)
!           if (abs(a-b).gt.(1e-4*max(a,b))) then
!             write(*,*) "Mismatch in custom energies!", test_ener_phot(i), &
!                 ' ', my_ener_phot(i)
!             return
!           endif
!         enddo
! 
!         write(*,*) "test_custom_ergs: successfully read bins"
! 
!         deallocate(my_ener_phot)
! 
! end subroutine test_read_custom_ergs


! subroutine test_read_params
! ! Reads in several combinations of parameter specifications from the file
! !  'test_params.txt'.
!   use tests_mod
!   use source_data
!         
!         integer :: cnt = 1
! 
!         testunitnum = getUnit()
!         OPEN(unit=testunitnum, form='formatted', file='test_params.txt')
! 
!         do ! assertions
!           ! Test: 'p u v'
!           call read_params(testunitnum)
!           if (bias.eq.0.and.samp_uni.eq.0.and.samp_vox.eq.1) then
!             cnt = cnt + 1
!           else 
!             exit
!           endif
!           ! Test: 'p'
!           call read_params(testunitnum)
!           if (samp_vox.eq.0.and.mat_rej.eq.0.and.cumulative.eq.0) then
!             cnt = cnt + 1
!           else 
!             exit
!           endif
!           ! Test: 'p v u b'
!           call read_params(testunitnum)
!           if (samp_vox.eq.0.and.samp_uni.eq.1.and.bias.eq.0) then
!             cnt = cnt + 1
!           else 
!             exit
!           endif
!           ! Test: 'p b'
!           call read_params(testunitnum)
!           if (bias.eq.1) then
!             cnt = cnt + 1
!           else 
!             exit
!           endif
!           ! Test: 'p d'
!           call read_params(testunitnum)
!           if (debug.eq.1) then
!             cnt = cnt + 1
!           else 
!             exit
!           endif
!           ! Test: 'p e'
!           call read_params(testunitnum)
!           if (ergs.eq.1) then
!             cnt = cnt + 1
!           else 
!             exit
!           endif
!           ! Test: 'p m'
!           call read_params(testunitnum)
!           if (mat_rej.eq.1) then
!             cnt = cnt + 1
!           else 
!             exit
!           endif
!           ! Test: 'p c'
!           call read_params(testunitnum)
!           if (cumulative.eq.1) then
!             cnt = cnt + 1
!           else 
!             exit
!           endif
!           ! Test: 'p v'
!           call read_params(testunitnum)
!           if (samp_vox.eq.1) then
!             cnt = cnt + 1
!           else 
!             exit
!           endif
!           ! Test: 'p u'
!           call read_params(testunitnum)
!           if (samp_uni.eq.1) then
!             cnt = cnt + 1
!           else 
!             exit
!           endif
!           ! Test: 'p b u'
!           call read_params(testunitnum)
!           if (samp_uni.eq.1.and.bias.eq.0) then
!             cnt = cnt + 1
!           else 
!             exit
!           endif
!           ! Test: 'p u r'
!           call read_params(testunitnum)
!           if (samp_uni.eq.1.and.resample.eq.1) then
!             cnt = cnt + 1
!           else 
!             exit
!           endif
!           exit
! 
!         enddo
! 
!         CLOSE(testunitnum)
! 
!         if (cnt.lt.13) then
!           write(*,*) "ERROR - test_read_params completed tests:", i, "/ 13"
!         else 
!           write(*,*) "test_read_params: successfully tested parameters parsing"
!         endif
! 
! end subroutine test_read_params


subroutine test_gen_erg_alias_table
! Fake (normalized) probabiltiies are supplied to gen_erg_alias_table, and the
!  resulting probList and pairsList are matched to expected result.
  use tests_mod
  use source_data

        real(dknd),dimension(1:10) :: binList
        integer(i4knd),dimension(1:10) :: pairsList, expectedPairsList
        real(dknd),dimension(1:10) :: probList, expectedProbList
        real(dknd) :: a, b

        binList = (/ .01,.04,.05,.07,.09,.1,.13,.2,.22,.09 /)

        expectedPairsList = (/ 8,9,9,9, 9,-1,-1,7,8,9 /)

        expectedProbList = (/ 9.9999997E-002,0.3999999,0.5000000, &
                 0.7000000,0.9000000,1.0000000, &
                 1.0000000,0.7000000,0.6000000, &
                 0.9000000 /)
 
        call gen_erg_alias_table(10, binList, pairsList, probList)

        do i=1,10
          !assert
          a = probList(i)
          b = expectedProbList(i)
          if (abs(a-b).gt.(1e-5*max(a,b))) then
            write(*,*) "ERROR - test_gen_erg_alias_table: " // &
                                "discrepancy in table's probabilities", a, b
            write(*,*) "Full list of expected probabilities:", expectedProbList
            write(*,*) "Full list of actual probabilities:", probList
            return
          endif
          if (pairsList(i).ne.expectedPairsList(i)) then
            write(*,*) "ERROR - test_gen_erg_alias_table: " // &
                                "mismatch in table's bin pairs"
            write(*,*) "Expected:", expectedPairsList
            write(*,*) "Result:", pairsList
            write(*,*) "Full list of expected probabilities:", expectedProbList
            write(*,*) "Full list of actual probabilities:", probList
            return
          endif
        enddo

        write(*,*) "test_gen_erg_alias_table: successfully " // &
                                "created expected alias table"

end subroutine test_gen_erg_alias_table


subroutine test_erg_sampling_distrib
! Subroutine does 'testcnt' energy samplings for ten energy bins, and finds
!  the largest relative error in bin sampling frequency.
  use tests_mod
  use source_data

        real(dknd),dimension(1:10) :: binList
        integer(i4knd),dimension(1:10) :: tallyList
        integer(i4knd),dimension(1:1,1:10,1:2) :: pairsList
        real(dknd),dimension(1:1,1:10) :: probList
        real(dknd) :: a, b, testerg, maxdev, val
        integer(i4knd) :: nbins, cnt, talcnt, testcnt

        nbins = 10
        binList = (/ .01,.04,.05,.07,.09,.1,.13,.2,.22,.09 /)
        tallyList = (/ 0,0,0,0,0,0,0,0,0,0 /)
        
        ! Initialize my_ener_phot array
        ALLOCATE(my_ener_phot(1:nbins+1))
        my_ener_phot = (/0.0,0.01,0.02,0.03,0.045,0.06,0.07,0.075,0.1,0.15,0.2/)

        call gen_erg_alias_table(nbins, binList, pairsList(1,1:10,1:2), &
                                              probList(1,1:10) )

        testcnt = 100000
        do cnt=1,testcnt
          ! Sample an energy, testerg
          call sample_erg (testerg, 1, nbins, 1, probList, pairsList)

          ! Tally the energy bin corresponding with testerg
          do talcnt=1,nbins
            if (testerg.lt.my_ener_phot(talcnt + 1)) then
              tallyList(talcnt) = tallyList(talcnt) + 1
              exit
            endif
          enddo

        enddo
        
        maxdev = 0
        do talcnt=1,nbins
          val = abs(tallyList(talcnt)/binList(talcnt) - testcnt) / testcnt
          if (val.gt.maxdev) then
            maxdev = val
          endif
        enddo

        write(*,'(a,a,es10.3)') " test_erg_sampling_distrib: maximum ", &
                "relative error in bin sampling frequency - ", maxdev
        write(*,*) tallyList

        deallocate(my_ener_phot)

end subroutine test_erg_sampling_distrib


subroutine test_get_tet_vol
! Tests that the volume of the reference tetrahedron in 1tet.vtk is 1/6.
  use tests_mod
  use source_data
  implicit none

        !iBase_EntitySetHandle :: root_set
        integer :: ents_alloc, ents_size, myerr
        iBase_EntityHandle :: t_entity_handles
        iBase_EntityHandle :: t_pointer_entity_handles
        real(dknd) :: volume, a, b

        pointer (t_pointer_entity_handles, t_entity_handles(1:*))

        ! create the Mesh instance
        call iMesh_newMesh("", mesh, ierr)
        ! load the mesh
        call iMesh_getRootSet(%VAL(mesh), root_set, ierr)
        ! Read mesh file
        call iMesh_load(%VAL(mesh), %VAL(root_set), &
             "1tet.vtk", "", ierr)

        ! get single tet element
        ents_alloc = 0
        call iMesh_getEntities(%VAL(mesh), %VAL(root_set), &
             %VAL(iBase_REGION_t), &
             %VAL(iMesh_TETRAHEDRON_t), t_pointer_entity_handles, &
             ents_alloc, ents_size, ierr)

        call get_tet_vol(mesh, t_entity_handles, volume)

        myerr = ierr

        call iMesh_dtor(%VAL(mesh), ierr)

        a = volume
        b = 1._rknd/6
        if (abs(a-b).gt.(1e-4*max(a,b))) then
          write(*,*) "ERROR - test_get_tet_vol; ierr=", myerr
          write(*,*) "expected:", b, "calculated:", a
          return
        endif

        write(*,*) "test_get_tet_vol: got correct volume for reference tet"

end subroutine test_get_tet_vol


subroutine test_get_hex_vol1
! Tests that the volume of the reference hexahedron in 1hex.vtk is 1.00.
  use tests_mod
  use source_data
  implicit none

        !iBase_EntitySetHandle :: root_set
        integer :: ents_alloc, ents_size, myerr
        iBase_EntityHandle :: t_entity_handles
        iBase_EntityHandle :: t_pointer_entity_handles
        real(dknd) :: volume, a, b

        pointer (t_pointer_entity_handles, t_entity_handles(1:*))

        ! create the Mesh instance
        call iMesh_newMesh("", mesh, ierr)
        ! load the mesh
        call iMesh_getRootSet(%VAL(mesh), root_set, ierr)
        ! Read mesh file
        call iMesh_load(%VAL(mesh), %VAL(root_set), &
             "1hex.vtk", "", ierr)

        ! get single hex element
        ents_alloc = 0
        call iMesh_getEntities(%VAL(mesh), %VAL(root_set), &
             %VAL(iBase_REGION_t), &
             %VAL(iMesh_HEXAHEDRON_t), t_pointer_entity_handles, &
             ents_alloc, ents_size, ierr)

        call get_hex_vol(mesh, t_entity_handles, volume)

        myerr = ierr

        call iMesh_dtor(%VAL(mesh), ierr)

        a = volume
        b = 1._rknd
        if (abs(a-b).gt.(1e-4*max(a,b))) then
          write(*,*) "ERROR - test_get_hex_vol1; ierr=", myerr
          write(*,*) "expected:", b, "calculated:", a
          return
        endif

        write(*,*) "test_get_hex_vol1: got correct volume for reference hex"

end subroutine test_get_hex_vol1


subroutine test_get_hex_vol2
! Tests that the volume of the reference hexahedron in 1hex.vtk is 1.00.
  use tests_mod
  use source_data
  implicit none

        !iBase_EntitySetHandle :: root_set
        integer :: ents_alloc, ents_size, myerr
        iBase_EntityHandle :: t_entity_handles
        iBase_EntityHandle :: t_pointer_entity_handles
        real(dknd) :: volume, a, b

        pointer (t_pointer_entity_handles, t_entity_handles(1:*))

        ! create the Mesh instance
        call iMesh_newMesh("", mesh, ierr)
        ! load the mesh
        call iMesh_getRootSet(%VAL(mesh), root_set, ierr)
        ! Read mesh file
        call iMesh_load(%VAL(mesh), %VAL(root_set), &
             "1hexRotated.vtk", "", ierr)

        ! get single hex element
        ents_alloc = 0
        call iMesh_getEntities(%VAL(mesh), %VAL(root_set), &
             %VAL(iBase_REGION_t), &
             %VAL(iMesh_HEXAHEDRON_t), t_pointer_entity_handles, &
             ents_alloc, ents_size, ierr)

        call get_hex_vol(mesh, t_entity_handles, volume)

        myerr = ierr

        call iMesh_dtor(%VAL(mesh), ierr)

        a = volume
        b = 1._rknd
        if (abs(a-b).gt.(1e-4*max(a,b))) then
          write(*,*) "ERROR - test_get_hex_vol2; ierr=", myerr
          write(*,*) "expected:", b, "calculated:", a
          return
        endif

        write(*,*) "test_get_hex_vol2: got correct volume for rotated " &
                // "reference hex"

end subroutine test_get_hex_vol2


subroutine test_read_moab1
! Tests:
! - correct number of voxels found
  use tests_mod
  use source_data
  implicit none

        integer :: ents_alloc, ents_size, myerr
        iBase_EntityHandle :: t_entity_handles
        iBase_EntityHandle :: t_pointer_entity_handles
        real(dknd) :: volume, a, b

        pointer (t_pointer_entity_handles, t_entity_handles(1:*))

        SET_UP

        call read_moab(mesh, "1tet.vtk", t_pointer_entity_handles)

        call iMesh_dtor(%VAL(mesh), ierr)

        ASSERT_EQUAL(n_mesh_cells, 1)

        if (terr.eq.0) then
          write(*,*) "test_read_moab1: correctly read mesh"
        else
          write(*,*) "ERROR - test_read_moab1: unspecified error"
        endif

        deallocate(my_ener_phot)
        !deallocate(bias_list)
        deallocate(spectrum)
        deallocate(tot_list)

end subroutine test_read_moab1


subroutine test_read_moab2
! Tests:
! - correct number of voxels found
! - bias values are read from mesh
  use tests_mod
  use source_data
  implicit none

        integer :: ents_alloc, ents_size, myerr
        iBase_EntityHandle :: t_entity_handles
        iBase_EntityHandle :: t_pointer_entity_handles
        real(dknd) :: volume, a, b

        pointer (t_pointer_entity_handles, t_entity_handles(1:*))

        SET_UP

        call read_moab(mesh, "3vox.vtk", t_pointer_entity_handles)

        myerr = ierr

        call iMesh_dtor(%VAL(mesh), ierr)

        ASSERT_EQUAL(n_mesh_cells, 3)

        if (bias.eq.0.or.myerr.ne.0) then
          write(*,*) "ERROR - test_read_moab2: MOAB Error - ierr=", myerr
        elseif (terr.ne.0) then
          write(*,*) "ERROR - test_read_moab2: unspecified error"
        else
          write(*,*) "test_read_moab2: correctly read mesh with bias value tags"
        endif

        deallocate(my_ener_phot)
        deallocate(bias_list)
        deallocate(spectrum)
        deallocate(tot_list)

end subroutine test_read_moab2


subroutine test_sample_region_entity_tet
! Tests:
! - Sampled points fall within the reference tetrahedron
  use tests_mod
  use source_data
  implicit none

        integer :: ents_alloc, ents_size, myerr
        iBase_EntityHandle :: t_entity_handles
        iBase_EntityHandle :: t_pointer_entity_handles
        real(dknd) :: volume, a, b, l1, l2, l3, l4

        pointer (t_pointer_entity_handles, t_entity_handles(1:*))

        SET_UP

        call read_moab(mesh, "1tet.vtk", t_pointer_entity_handles)

        myerr = ierr

        if (myerr.ne.0) then
          write(*,*) "ERROR - test_sample_region_entity_tet: " &
                      // "MOAB Error - ierr=", myerr
        endif

        ! Check points are within the reference tet
        do i=1,1000
          call sample_region_entity(mesh, t_entity_handles(1))

          ! We use barycentric coords to check that point is in tet.
          ! The barycentric coords for the reference tet are
          !   l1 = 1-xxx-yyy-zzz; l2 = xxx; l3 = yyy; l4 = 1-l1-l2-l3;
          ! These are pre-calculated equations based on the tet's coords.
          l1 = 1-xxx-yyy-zzz
          l2 = xxx
          l3 = yyy
          l4 = 1-l1-l2-l3
          if (l1.lt.0.0.or.l2.lt.0.0.or.l3.lt.0.0.or.l4.lt.0.0 &
             .or.l1.gt.1.0.or.l2.gt.1.0.or.l3.gt.1.0.or.l4.gt.1.0) then
             terr = terr + 1
          endif
        enddo

        call iMesh_dtor(%VAL(mesh), ierr)

        if (terr.eq.0) then
          write(*,*) "test_sample_region_entity_tet: correctly read mesh"
        else
          write(*,*) "ERROR - test_sample_region_entity_tet: ", terr, &
              "points did not fall within the unit tetrahedron."
        endif

        deallocate(my_ener_phot)
        !deallocate(bias_list)
        deallocate(spectrum)
        deallocate(tot_list)

end subroutine test_sample_region_entity_tet


subroutine test_sample_region_entity_hex
! Tests:
! - Sampled points fall within a rotated unit hexahedron (rotated cube)
  use tests_mod
  use source_data
  implicit none

        integer :: ents_alloc, ents_size, myerr
        iBase_EntityHandle :: t_entity_handles
        iBase_EntityHandle :: t_pointer_entity_handles
        real(dknd) :: volume, a, b, x, y, z

        pointer (t_pointer_entity_handles, t_entity_handles(1:*))

        SET_UP

        call read_moab(mesh, "1hexRotated.vtk", t_pointer_entity_handles)

        myerr = ierr

        if (myerr.ne.0) then
          write(*,*) "ERROR - test_sample_region_entity_hex: " &
                      // "MOAB Error - ierr=", myerr
        endif

        ! Check points are within the rotated unit cube
        do i=1,1000
          call sample_region_entity(mesh, t_entity_handles(1))
          
          ! Vector math: A.v=r  -> v = A^-1.r
          ! Where: A = basis vectors; |b-a,c-a,d-a|
          !        r = (xxx,yyy,zzz) - a
          !        a,b,c,d,e,f,g,h are vertices of cube
          !        v = (x=[0..1],y=[0..1,z=[0..1]) if point is within cube
          ! Analytical solution for our reference cube is
          !  x =  0.57735 xxx + 0.57735  yyy + 0.57735  zzz
          !  y = -0.57735 xxx + 0.788675 yyy - 0.211325 zzz
          !  z = -0.57735 xxx - 0.211325 yyy + 0.788675 zzz
          x =  0.57735*xxx + 0.57735 *yyy + 0.57735 *zzz
          y = -0.57735*xxx + 0.788675*yyy - 0.211325*zzz
          z = -0.57735*xxx - 0.211325*yyy + 0.788675*zzz

          ASSERT_TRUE(x.le.1._dknd.and.x.ge.0._dknd.and.y.le.1._dknd.and.y.ge.0._dknd.and.z.le.1._dknd.and.z.ge.0._dknd)

        enddo

        call iMesh_dtor(%VAL(mesh), ierr)

        if (terr.ne.0) then
          write(*,*) "ERROR - test_sample_region_entity_hex: ", terr, &
              "points did not fall within the rotated unit cube."
        else
          write(*,*) "test_sample_region_entity_hex: correctly read mesh with bias value tags"
        endif

        deallocate(my_ener_phot)
        !deallocate(bias_list)
        deallocate(spectrum)
        deallocate(tot_list)

end subroutine test_sample_region_entity_hex

! End of test subroutines
