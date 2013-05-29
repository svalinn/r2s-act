!+ $Id: source.F90,v 1.1 2004/03/20 00:31:52 jsweezy Exp $
! Copyright LANL/UC/DOE - see file COPYRIGHT_INFO

! 
! Summary
! =======
! Adapted from source routine (`source_gamma_meshtal2.F90`) provided by 
! Dieter Leichtle from KIT.
! Changes have been made by Eric Relson with UW-Madison/CNERG goals in mind.
! 
! This source file implements photon source sampling on a mesh.  The voxel
! sampling technique is used, whereby a voxel is first chosen based on relative
! source strengths, and then a point is uniformly, randomly sampled within the
! voxel.  Hexahedral and tetrahedral voxels (and mixes there-of) are supported.
! 
! Subroutine source reads in the file `source.h5m` from the directory
! that MCNP is being run in.  This file is a MOAB mesh containing a mesh that
! overlays the problem geometry, and is tagged with photon source information:
! tags of the form `phtn_src_group_xxx`, where xxx is the 3-digit group number
! with leading zeros.
! These tags should give values of source density in photons/cm3/s.
! 
! Additionally, tags can be included for custom photon energy bins and for bias
! values assigned to each voxel.
! * Energy bins are tagged to the rootSet tag `PHTN_ERGS`
! * Bias values are tagged to each voxel with the tag `PHTN_BIAS`
! 
! Parameters (not currently implemented)
! --------------------------------------
! These features would be set in the r2s.cfg file.
! * ~~r: Particles starting in a void are resampled (within the same voxel).~~
! * ~~a: Resample entire particle when a particle would start in void. Requires
! u and r to be enabled. Can give incorrect results due to playing an
! unfair game.~~
! 
! ~~If the parameters line is not present, the default is to set u, m, c as True.
! If 'e' parameter exists, line 7 lists custom energy group boundaries, space
! delimited. This line start with the integer number of groups. ~~
! 
! ~~Note that correct normalization also depends on whether
! material rejection is being used.~~
! 
! Other notes
! --------------
! Voxel sampling and energy sampling use a sampling technique referred to as
! 'alias discrete' or 'alias' sampling.  This provides efficiency benefits
! over 'direct discrete' sampling of PDFs. Creation of the alias tables uses
! the algorithm described by Vose (1991).
! 
! The default energy bins are a 42 group structure.
! 
! An arbitrary range of bias values can be used since the source routine does
! the necessary re-normalization for voxel sampling.


module source_data
! Variables used/shared by most of the subroutines in this file.
  use mcnp_global
   
        implicit none

! Don't indent the #include!
#include "iMesh_f.h"

        ! MOAB related
        iMesh_Instance :: mesh
        iBase_EntitySetHandle :: root_set
        integer :: ierr
        iBase_EntityHandle, dimension(:), allocatable :: entity_handles
        ! Startup
        character*30 :: gammas_file = 'gammas'
        character*30 :: mesh_file = 'source.h5m'
        integer(i8knd) :: ikffl = 0 ! = local record of history #
        ! Parameters - these are toggled by gammas
        integer :: bias, samp_vox, samp_uni, debug, ergs, &
             mat_rej, cumulative, resample, uni_resamp_all
        ! Position sampling variables
        integer :: voxel, n_source_cells
        real(dknd), dimension(:), allocatable :: tot_list
        ! Voxel alias table variables
        real(dknd) :: sourceSum, n_inv, norm
        real(dknd), dimension(:), allocatable :: bins
        real(dknd), dimension(:), allocatable :: binsProbabilities
        integer(i4knd), dimension(:), allocatable :: aliases
        integer :: alias_bin
        ! Biasing variables
        real(dknd) :: bias_probability_sum
        real(dknd), dimension(:), allocatable :: bias_list
        ! Energy bins variables
        real(dknd), dimension(:,:), allocatable :: spectrum
        real(dknd), dimension(:), allocatable :: my_ener_phot
        integer :: n_ener_grps
        ! Energy bins alias table variables
        real(dknd), dimension(:,:), allocatable :: ergBinsProbabilities
        integer(i4knd), dimension(:,:), allocatable :: ergAliases
        ! Debug output variables
        integer(i8knd) :: npart_write = 0 ! = counter for debug output
        ! Other variables
        integer :: stat
        integer :: ii, kk, jj  ! current voxel's indices on structured mesh
        integer :: ic_s, ib_s, ih_s  ! for binary search
        integer :: i_ints, j_ints, k_ints, n_mesh_cells, n_active_mat
        real, dimension(:), allocatable :: i_bins, j_bins, k_bins
        integer, dimension(100) :: active_mat
        character*3000 :: line ! needed for reading active_mat from gammas

  contains 

        integer function getUnit()
        ! Get an unused unit number to assign to a file being opened
        ! via https://modelingguru.nasa.gov/docs/DOC-2052
           implicit none
           integer :: unit
           logical :: isOpen

           integer, parameter :: MIN_UNIT_NUMBER = 50
           integer, parameter :: MAX_UNIT_NUMBER = 99

           do unit = MIN_UNIT_NUMBER, MAX_UNIT_NUMBER
              inquire(unit = unit, opened = isOpen)
              if (.not. isOpen) then
                 getUnit = unit
                 return
              end if
           end do
        end function getUnit
       
end module source_data


subroutine source_setup
! Subroutine handles parsing of the 'gammas' file and related initializations
! 
  use source_data
  implicit none
 
        real(dknd) :: volume, phtn_total
        integer :: unitnum, voxel_topo, i, j
        iBase_TagHandle :: tagh

        ! Stores the list of volume entities returned by read_moab()
        iBase_EntityHandle :: myentity_handles, mypointer_entity_handles
        pointer (mypointer_entity_handles, myentity_handles(1:*))

        unitnum = getUnit()

        ! Read general date from the moab mesh
        call read_moab(mesh, mesh_file, mypointer_entity_handles)
        if (ierr.ne.0) then
          call expirx(1,'source_setup','Error reading MOAB mesh.')
        endif

        ! Copy entity handels to global variable
        ALLOCATE(entity_handles(1:n_mesh_cells))
        entity_handles(1:n_mesh_cells) = myentity_handles(1:n_mesh_cells)

        ALLOCATE(ergAliases(1:n_mesh_cells, 1:n_ener_grps))
        ALLOCATE(ergBinsProbabilities(1:n_mesh_cells, 1:n_ener_grps))

        ! Create alias tables for each voxel's energy distribution.
        ! Normalizes each row in spectrum.
        do i=1,n_mesh_cells
          tot_list(i) = sum(spectrum(i,1:n_ener_grps))
          do j=1,n_ener_grps
            spectrum(i,j) = spectrum(i,j) / tot_list(i)
          enddo
          call gen_erg_alias_table (n_ener_grps, spectrum(i,1:n_ener_grps), &
                      ergAliases(i,1:n_ener_grps), &
                      ergBinsProbabilities(i,1:n_ener_grps))
        enddo

        ! Calculate the number of source voxels.
        n_source_cells = 0
        do i=1,n_mesh_cells
          if (tot_list(i).gt.0) n_source_cells = n_source_cells + 1
        enddo
        write(*,*) "n_mesh_cells:", n_mesh_cells, &
                "n_source_cells:", n_source_cells

        ! Scale each entry in tot_list ([phtns/s/cc]) by the voxel's volume
        ! to get [phtns/s/voxel], giving the relative voxel source strengths.
        do i=1,n_mesh_cells
          if (tot_list(i).gt.0) then
            call iMesh_getEntTopo(%VAL(mesh), %VAL(entity_handles(i)), &
                  voxel_topo, ierr)
            if (voxel_topo.eq.iMesh_TETRAHEDRON) then
              call get_tet_vol(mesh, entity_handles(i), volume)
            elseif (voxel_topo.eq.iMesh_HEXAHEDRON) then
              call get_hex_vol(mesh, entity_handles(i), volume)
            else
              write(*,*) "Problematic voxel; topology is: ", voxel_topo
              call expirx(1,'source_setup','Invalid voxel type.')
            endif
            tot_list(i) = tot_list(i) * volume
          endif
        enddo

        ! Tag rootSet of mesh with total source strength (photons/s)
        call iMesh_getTagHandle(%VAL(mesh), "PHTN_SRC_TOTAL", tagh, ierr)
        if (ierr.ne.0) then
          call iMesh_createTag(%VAL(mesh), "PHTN_SRC_TOTAL", &
                  %VAL(1), %VAL(iBase_DOUBLE), tagh, ierr)
        endif

        phtn_total = sum(tot_list)
        call iMesh_setEntSetDblData(%VAL(mesh), %VAL(root_set), %VAL(tagh), &
                phtn_total, ierr)
        if (ierr.ne.0) then
                write(*,*) "ERROR - Failed to tag total photon source to " &
                        // "mesh. Error code:", ierr
        endif

        ! And save newly tagged mesh
        call iMesh_save(%VAL(mesh), %VAL(root_set), &
                mesh_file, "", ierr)
        if (ierr.ne.0) then
          write(*,*) "ERROR - Mesh saving error:", mesh_file
          return
        endif

        !call iMesh_dtor(%VAL(mesh), ierr)

        ! Generate alias table of voxels if needed
        if (samp_vox.eq.1) then
          call gen_voxel_alias_table
        endif

        ! Create new debug output file if debugging is enabled.
        if (debug.eq.1) then
          unitnum = getUnit()
          OPEN(unit=unitnum, file="source_debug", position='append', &
                        status='replace')
          CLOSE(unitnum)
        endif

end subroutine source_setup


subroutine read_moab (mymesh, filename, rpents)
! Read in the moab mesh, getting the root set and voxel entities, and looking
! for bias and energy tags.
! 
! Parameters
! ----------
! mymesh : iMesh_Instance
!     Mesh instance which will be initialized and then read
! filename : character array
!     Filename to read mesh data from. (.vtk or .h5m file)
! rpents : pointer to array of iBase_EntityHandle
!     Pointer to an array that will be filled with iBase_REGION entity
!     handles
! 
  use source_data
  implicit none

        ! Parameters
        iMesh_Instance, intent(INOUT) :: mymesh
        character(len=*), intent(IN) :: filename
        iBase_EntityHandle, intent(INOUT) :: rpents

        ! declarations
        integer i, j
        iBase_EntityHandle :: ents
        iBase_EntityHandle :: verts

        iBase_TagHandle :: ergtagh, tagh
        character*128 :: tagname
        
        integer :: ents_alloc, ents_size
        real(dknd) :: tag_data

        pointer (rpents, ents(1:*))

        ! create the Mesh instance
        call iMesh_newMesh("", mymesh, ierr)
        if (ierr.ne.0) then
          write(*,*) "ERROR - Failed to create mesh instance."
          return
        endif

        ! load the mesh
        call iMesh_getRootSet(%VAL(mymesh), root_set, ierr)
        if (ierr.ne.0) then
          write(*,*) "ERROR - Failed to get mesh rootSet."
          return
        endif

        ! Read mesh file
        call iMesh_load(%VAL(mymesh), %VAL(root_set), &
             filename, "", ierr)
        if (ierr.ne.0) then
          write(*,*) "ERROR - Mesh file load error:", filename
          return
        endif

        ! get all 3d elements
        ents_alloc = 0
        call iMesh_getEntities(%VAL(mymesh), %VAL(root_set), &
             %VAL(iBase_REGION), &
             %VAL(iMesh_ALL_TOPOLOGIES), rpents, ents_alloc, ents_size, &
             ierr)
        if (ierr.ne.0) then
          write(*,*) "ERROR - Failed to load volume entities for mesh."
          return
        endif
        n_mesh_cells = ents_size

        ! Initialize parameters to defaults.
        bias = 0
        samp_vox = 1
        samp_uni = 0
        debug = 0
        ergs = 0
        mat_rej = 0
        cumulative = 0
        resample = 0
        uni_resamp_all = 0

        ! Look for parameters in r2s.cfg
        ! TODO

        ! Look for custom energy groups tag.
        call iMesh_getTagHandle(%VAL(mymesh), "PHTN_ERGS", ergtagh, ierr)
        ! If ergs tag was found, we read custom ergs.  Otherwise 
        !  we use default energies.
        if (ierr.eq.0) then 
          ! Get n_ener_grps via length of data in the tag.
          !  This length is the number of boundaries (groups + 1)
          call iMesh_getTagSizeValues(%VAL(mymesh), %VAL(ergtagh), &
                n_ener_grps, ierr)
          n_ener_grps = n_ener_grps - 1
                
          ALLOCATE(my_ener_phot(1:n_ener_grps+1))
          
          call iMesh_getEntSetDblData(%VAL(mymesh), %VAL(root_set), &
                %VAL(ergtagh), my_ener_phot, ierr)
        else ! use default energy groups; 42 groups
          n_ener_grps = 42
          ALLOCATE(my_ener_phot(1:n_ener_grps+1))
          my_ener_phot = (/0.0,0.01,0.02,0.03,0.045,0.06,0.07,0.075,0.1,0.15, &
            0.2,0.3,0.4,0.45,0.51,0.512,0.6,0.7,0.8,1.0,1.33,1.34,1.5, &
            1.66,2.0,2.5,3.0,3.5,4.0,4.5,5.0,5.5,6.0,6.5,7.0,7.5,8.0, &
            10.0,12.0,14.0,20.0,30.0,50.0/)
        endif

        ! Look for biases tag
        call iMesh_getTagHandle(%VAL(mymesh), "PHTN_BIAS", tagh, ierr)
        if (ierr.eq.0) then
          bias = 1
          ALLOCATE(bias_list(1:n_mesh_cells))
          do i=1,n_mesh_cells
            call iMesh_getDblData(%VAL(mymesh), %VAL(ents(i)), &
                %VAL(tagh), tag_data, ierr)
            bias_list(i) = tag_data
          enddo
        endif

        ! Prepare to read in spectrum information
        ! set the spectrum array to: # of mesh cells * # energy groups
        ALLOCATE(spectrum(1:n_mesh_cells, 1:n_ener_grps))
        ALLOCATE(tot_list(1:n_mesh_cells))

        ! Fill spectrum
        do j=1, n_ener_grps
          ! Grab next tag handle
          write(tagname, '(a, i3.3)') "phtn_src_group_", j
          call iMesh_getTagHandle(%VAL(mymesh), tagname, tagh, ierr)
          if (ierr.eq.14) then ! 14 = iBase_TAG_NOT_FOUND
            write(*,*) "ERROR - Missing expected mesh tag:", tagname
            return
          endif
          ! Iterate through each voxel, grabbing and storing values
          do i=1, n_mesh_cells
            call iMesh_getDblData(%VAL(mymesh), %VAL(ents(i)), %VAL(tagh), &
                tag_data, ierr)
            spectrum(i,j) = tag_data
          enddo
        enddo
        
end subroutine read_moab


subroutine get_tet_vol (mymesh, tet_entity_handle, volume)
! Subroutine calculates volume of a tetrahedron entity on a MOAB mesh
! 
! Parameters
! ----------
! mymesh : iMesh_Instance
!     Mesh object
! tet_entity_handle : iBase_EntityHandle
!     Entity set handle
! volume : float
!     Stores the calculated volume
! 
! Notes
! -----
! Algorithm is from Wikipedia article for Tetrahedrons.
! For points A, B, C, D::
! 
!     vol = (1/6) * abs( (A-D) . ((B-D) x (C-D)) )
! 
  use source_data
  implicit none

        ! Parameters
        iMesh_Instance, intent(IN) :: mymesh
        iBase_EntityHandle, intent(IN) :: tet_entity_handle
        real(dknd), intent(OUT) :: volume
        ! Function type
        real(dknd) :: calc_tet_vol
        ! Other variables 
        integer :: iverts_alloc = 0
        integer :: iverts_size
        integer :: icoords_alloc = 0
        integer :: icoords_size
        iBase_EntityHandle :: verts, pointer_verts
        real(dknd) :: coords
        iBase_EntityHandle :: pointer_coords
        real(dknd), dimension(1:3) :: a, b, c, d
        ! cray pointers
        pointer (pointer_verts, verts(1,*))
        pointer (pointer_coords, coords(1,*))

        save iverts_alloc, icoords_alloc, pointer_verts, pointer_coords

        ! Get vertices' handles
        call iMesh_getEntAdj(%VAL(mymesh), %VAL(tet_entity_handle), &
              %VAL(iBase_VERTEX), pointer_verts, &
              iverts_alloc, iverts_size, ierr)

        ! Get all vertices' coordinates
        call iMesh_getVtxArrCoords(%VAL(mymesh), %VAL(pointer_verts), &
              !%VAL(4), iBase_INTERLEAVED, pointer_coords, &
              !icoords_alloc, icoords_size, ierr)
              %VAL(4), iBase_BLOCKED, pointer_coords, &
              icoords_alloc, icoords_size, ierr)

        a(1) = coords(1,1)
        b(1) = coords(1,2)
        c(1) = coords(1,3)
        d(1) = coords(1,4)
        a(2) = coords(1,5)
        b(2) = coords(1,6)
        c(2) = coords(1,7)
        d(2) = coords(1,8)
        a(3) = coords(1,9)
        b(3) = coords(1,10)
        c(3) = coords(1,11)
        d(3) = coords(1,12)

        volume = calc_tet_vol(a, b, c, d)
        
end subroutine get_tet_vol


real*8 function calc_tet_vol(a, b, c, d)
! Function returns the volume of a tetrahedron, given the vertex coordinates
! 
! Parameters
! ----------
! a, b, c, d - real(dknd)(1:3)
!     Coordinate lists for four points forming a tetrahedra
!
  use source_data
  implicit none
        
        ! Parameters
        real(dknd), dimension(1:3), intent(IN) :: a, b, c, d
        
        calc_tet_vol = abs( (a(3)-d(3)) * &
            ( b(1)*c(2)-b(2)*c(1)+b(2)*d(1)-c(2)*d(1)-b(1)*d(2)+c(1)*d(2)) + &
            (a(2)-d(2)) * &
            (b(3)*c(1)-b(1)*c(3)-b(3)*d(1)+c(3)*d(1)+b(1)*d(3)-c(1)*d(3)) + &
            (a(1)-d(1)) * &
            (b(2)*c(3)-b(3)*c(2)+b(3)*d(2)-c(3)*d(2)-b(2)*d(3)+c(2)*d(3)) ) &
            / 6._rknd

end function calc_tet_vol


subroutine get_hex_vol (mymesh, hex_entity_handle, volume)
! Subroutine calculates volume of a hexahedron entity on a MOAB mesh
! 
! Parameters
! ----------
! mymesh : iMesh_Instance
!     Mesh object
! entity_handle : iBase_EntityHandle
!     Entity set handle
! volume : float
!     Stores the calculated volume
! 
! Notes
! -----
! Current implementation assumes 8 vertext hex with square planar facets
! 
  use source_data
  implicit none
 
        ! Parameters
        iMesh_Instance, intent(IN) :: mymesh
        iBase_EntityHandle, intent(IN) :: hex_entity_handle
        real(dknd), intent(OUT) :: volume
        ! Function type
        real(dknd) :: calc_tet_vol
        ! Other variables 
        integer :: iverts_alloc = 0
        integer :: iverts_size
        integer :: icoords_alloc = 0
        integer :: icoords_size
        iBase_EntityHandle :: verts, pointer_verts
        real(dknd) :: coords
        iBase_EntityHandle :: pointer_coords
        real(dknd), dimension(1:3) :: a, b, c, d, e, f, g, h
        ! cray pointers
        pointer (pointer_verts, verts(1,*))
        pointer (pointer_coords, coords(1,*))

        save iverts_alloc, icoords_alloc, pointer_verts, pointer_coords

        ! Get vertices' handles
        iverts_alloc = 0
        call iMesh_getEntAdj(%VAL(mymesh), %VAL(hex_entity_handle), &
              %VAL(iBase_VERTEX), pointer_verts, &
              iverts_alloc, iverts_size, ierr)

        ! Get all vertices' coordinates
        icoords_alloc = 0
        call iMesh_getVtxArrCoords(%VAL(mymesh), %VAL(pointer_verts), &
              %VAL(8), iBase_BLOCKED, pointer_coords, &
              icoords_alloc, icoords_size, ierr)

        a = coords(1,1:24:8)
        b = coords(1,2:24:8)
        c = coords(1,3:24:8)
        d = coords(1,4:24:8)
        e = coords(1,5:24:8)
        f = coords(1,6:24:8)
        g = coords(1,7:24:8)
        h = coords(1,8:24:8)

        ! Adapted from get_tet_vol and
        ! measure.cpp's measure() case moab::MBHEX
        volume = calc_tet_vol(a, b, d, e) + &
                 calc_tet_vol(h, d, g, e) + &
                 calc_tet_vol(e, f, b, g) + &
                 calc_tet_vol(b, g, d, e) + &
                 calc_tet_vol(c, g, d, b)

end subroutine get_hex_vol


subroutine source
! Subroutine manages sampling of photons on mesh
! 
! Adapted from dummy source.F90 file.
! 
! Notes
! -----
! if nsr=0, subroutine source must be furnished by the user.
! at entrance, a random set of uuu,vvv,www has been defined.  the
! following variables must be defined within the subroutine:
! xxx,yyy,zzz,icl,jsu,erg,wgt,tme and possibly ipt,uuu,vvv,www.
! subroutine srcdx may also be needed.
  use mcnp_debug
  use mcnp_random
  use source_data
  implicit none

        integer :: i, j, m, icl_tmp
   
!------------------------------------------------------------------------------
!     In the first history (ikffl) read 'gammas' file. ikffl under MPI works ?
!------------------------------------------------------------------------------
        ikffl = ikffl + 1
        if (ikffl.eq.1) then ! if first particle ...
          ! Call setup subroutine
          call source_setup
          write(*,*) 'Source setup complete!'
        endif

        ! Call position sampling subroutine
        !  sampling subroutine must set:
        ! -voxel
        ! -xxx, yyy and zzz
10      call voxel_sample

        ! sample a new position if voxel has zero source strength
        if (tot_list(voxel).eq.0) goto 10

               
!       IPT = 2 for photons. JSU=TME=0 works well.
        ipt = 2 ! particle type: 2 = photon
        jsu = 0
        tme = 0

!----------------------------------------------------------------------------
!       Determine in which cell you are starting. 
!       Subroutine is copied from MCNP code (sourcb.F90). 
!       ICL and JUNF should be set to 0 for this part of the code to work.
!----------------------------------------------------------------------------
555     icl = 0
        junf = 0
        
  ! default for cel:  find the cell that contains xyz.
        if( icl.eq.0 ) then
          if( junf.eq.0 ) then ! if repeated structures are NOT used...
            do m=1,nlse         ! nlse = # cells in list lse
              icl = lse(klse+m) ! lse = cells already starting source particles
              call chkcel(icl,2,j)
              if( j.eq.0 )  goto 543
            enddo 
            do icl_tmp=1,mxa ! mxa = # cells in probelm
              icl = icl_tmp
              call chkcel(icl,2,j)
              if( j.eq.0 )  goto 540
            enddo
            icl = icl_tmp
          else               ! else, repeated structures are used
            do m=1,nlse         ! nlse = # cells in list lse
              icl = lse(klse+m) ! lse = cells already starting source particles
              if( jun(icl).ne.0 )  cycle 
              call chkcel(icl,2,j)
              if( j.eq.0 ) then
                if( mfl(1,icl).ne.0 )  call levcel
                goto 543
              endif
            enddo 
            do icl_tmp=1,mxa ! mxa = # cells in probelm
              icl = icl_tmp
              if( jun(icl).ne.0 )  cycle 
              call chkcel(icl,2,j)
              if( j.eq.0 )  goto 540
            enddo
            icl = icl_tmp
          endif
          call expirx(1,'sourcb','source point is not in any cell.')
          goto 543
540       continue
          nlse = nlse+1
          lse(klse+nlse) = icl
          if( junf.eq.0 )  goto 543
          if( mfl(1,icl).eq.0 )  goto 543
          call levcel
        elseif( icl.lt.0 ) then
          call levcel
        else
          if( krflg.eq.0 )  goto 543
          call chkcel(icl,2,j)
          if( j.ne.0 ) call errprn(1,-1,0,zero,zero,' ',' ', &
            & 'the source point is not in the source cell.')
        endif

!----------------------------------------------------------------------------
!       ICL should be set correctly at this point, this means everything is set.
!----------------------------------------------------------------------------

543     continue
        ! Rejection and resampling conditions

        ! no resampling
        if (resample.eq.0) then
          goto 544 ! Always accept position when resampling is disabled.
        ! rejection of non-void materials is enabled... TODO: untested
        elseif (mat_rej.eq.1) then
          do i=1,n_active_mat
            if (nmt(mat(icl)).eq.active_mat(i)) then
              goto 544 ! Position is ok; particle starts in activated material
            endif
          enddo
        ! void rejection with voxel sampling
        elseif (samp_vox.eq.1) then
          if (mat(icl).eq.0) then
            ! particle rejected... resample within the voxel
            call sample_region_entity(mesh, entity_handles(voxel))
            goto 555
          else
            goto 544
          endif
        ! void rejection with uniform sampling
        elseif (samp_uni.eq.1) then
          if (mat(icl).eq.0) then
            if (uni_resamp_all.eq.0) then
              ! particle rejected... resample within the voxel and recheck
              call sample_box
              goto 555
            else
              goto 10 ! sample anew
            endif
          else
            goto 544
          endif
        else
          goto 544 ! skip material rejection
        endif

        goto 10 ! particle rejected... sample anew
  
544     continue

        ! Determine photon energy
        call sample_erg (erg, voxel, n_ener_grps, n_mesh_cells, &
                        ergBinsProbabilities, ergAliases)

        ! Determine weight.
        if (samp_vox.eq.1) then
          if (bias.eq.1) then
            wgt = bias_list(voxel)
          else
            wgt = 1.0
          endif
        elseif (samp_uni.eq.1) then
          wgt = tot_list(voxel) 
        endif
        
        ! Debug output, if enabled
        if (debug.eq.1) then
          call print_debug
        endif

        return
 
end subroutine source


subroutine voxel_sample
! Sample photon position from alias table of voxels.
! 
  use source_data
  implicit none

        real(dknd) :: rand

        ! Sampling the alias table
        rand = rang() * n_mesh_cells
        alias_bin = INT(rand) + 1
        if ((rand+(1._dknd-alias_bin)).lt.binsProbabilities(alias_bin)) then
          voxel = alias_bin
        else
          voxel = aliases(alias_bin)
        endif
        
        ! Bad condition checking; Indicates problem with alias table creation.
        if (voxel.eq.-1) then
          call expirx(1,'voxel_sample','Invalid indice sampled.')
        endif
       
        ! If structured mesh ...
        !! We -=1 the value of the index 'voxel' to calc ii,jj,kk easily
        !voxel = voxel - 1
        !! Math to get mesh indices in each dimension
        !ii = voxel / (k_ints*j_ints)
        !jj = mod(voxel, k_ints*j_ints) / k_ints
        !kk = mod(mod(voxel, k_ints*j_ints), k_ints)
        !
        !voxel = voxel + 1
        
        ! If unstructured mesh ...
        call sample_region_entity(mesh, entity_handles(voxel))
        
end subroutine voxel_sample


integer function binary_search(pos, len, table)
! Performs binary search and returns the integer indice for searched table.
! 
! Parameters
! ----------
! pos : float
!     Search value/key
! len : integer
!     Number of bins in `table`
! table : list of floats
!     Sorted 1D list to be searched
! 
! Notes
! -----
! Copied from algorithm used elsewhere in MCNP code.
  use source_data
  implicit none

        real(dknd), intent(IN) :: pos
        integer, intent (IN) :: len
        real(dknd), intent(IN), dimension(1:len) :: table

        ic_s = 1
        ib_s = len
        do
           if( ib_s-ic_s.eq.1 .or. ib_s.eq.ic_s)  exit
           ih_s = (ic_s+ib_s)/2
           if( pos.ge.table(ih_s) ) then
              ic_s = ih_s
           else
              ib_s = ih_s
           endif
        enddo 
        
        binary_search = ic_s

end function binary_search


subroutine sample_box
! Uniformly samples within the extents of a hexahedral voxel
! 
! Notes
! -----
! ii, jj, kk are presumed to have been already determined, and have values
! in the range [1, i_ints/j_ints/k_ints].
  use source_data
  implicit none
 
!       Sample random point within the voxel
        xxx = i_bins(ii+1) + rang() * (i_bins(ii+2) - i_bins(ii+1))
        yyy = j_bins(jj+1) + rang() * (j_bins(jj+2) - j_bins(jj+1))
        zzz = k_bins(kk+1) + rang() * (k_bins(kk+2) - k_bins(kk+1))

end subroutine sample_box


subroutine sample_region_entity (mymesh, entity_handle)
! This subroutine retrieves the vertices of the sampled voxel, and calls
! the appropriate sampling subroutine to get a sampled point.
! 
! Parameters
! ----------
! mymesh : iMesh_Instance
!     Mesh object
! entity_handle : iBase_EntityHandle
!     Entity set handle
! 
  use source_data
  implicit none

        ! Parameters
        iMesh_Instance, intent(IN) :: mymesh
        iBase_EntityHandle, intent(IN) :: entity_handle
        ! Other variables 
        integer :: iverts_alloc = 0
        integer :: iverts_size
        integer :: icoords_alloc = 0
        integer :: icoords_size
        iBase_EntityHandle :: verts, pointer_verts
        real(dknd) :: coords
        iBase_EntityHandle :: pointer_coords
        ! cray pointers
        pointer (pointer_verts, verts(1,*))
        pointer (pointer_coords, coords(1,*))

        save iverts_alloc, icoords_alloc, pointer_verts, pointer_coords

        ! Get vertices' handles
        call iMesh_getEntAdj(%VAL(mymesh), %VAL(entity_handle), &
              %VAL(iBase_VERTEX), pointer_verts, &
              iverts_alloc, iverts_size, ierr)

        ! Get all vertices' coordinates
        call iMesh_getVtxArrCoords(%VAL(mymesh), %VAL(pointer_verts), &
              %VAL(iverts_size), iBase_BLOCKED, pointer_coords, &
              icoords_alloc, icoords_size, ierr)

        ! Call appropriate sampling routine
        if (icoords_size.eq.12) then
          call sample_tetrahedra(coords)
        elseif (icoords_size.eq.24) then
          call sample_hexahedra(coords)
        else
          ! Error
          call expirx(1, 'sample_region_entity', "Entity with invalid number of vertices.")
          continue
        endif

end subroutine sample_region_entity


subroutine sample_tetrahedra (co)
! This subroutine receives the four vertices of a tetrahedron and sets
! xxx, yyy, zzz, to values corresponding to a uniformly sampled point
! within the tetrahedron.
! 
! Parameters
! -----------
! co - list of 12 real*8 values
!     The x y z coordinates of four points for a tetrahedron.  These numbers
!     are in xxx.. yyy.. zzz.. order.
! 
! Notes
! ------
! The algorithm used is that described by Rocchini & Cignoni (2001)
! 
  use source_data
  implicit none

        ! Parameters
        real(dknd), dimension(1:12), intent(IN) :: co

        real(dknd) :: ss, tt, uu, temp

        ss = rang()
        tt = rang()
        uu = rang()

        if ((ss+tt).gt.1._rknd) then
          ss = 1._rknd - ss
          tt = 1._rknd - tt
        endif

        if ((ss+tt+uu).gt.1._rknd) then
          if ((tt+uu).gt.1._rknd) then
            temp = tt
            tt = 1 - uu
            uu = 1._rknd - temp - ss
          else
            temp = ss
            ss = 1._rknd - uu - tt
            uu = temp + tt + uu - 1._rknd
          endif
        endif

        ! For reference:
        !xxx = p1x + (p2x-p1x)*ss + (p3x-p1x)*tt + (p4x-p1x)*uu
        !yyy = p1y + (p2y-p1y)*ss + (p3y-p1y)*tt + (p4y-p1y)*uu
        !zzz = p1z + (p2z-p1z)*ss + (p3z-p1z)*tt + (p4z-p1z)*uu
        xxx = co(1) + (co(2)-co(1))*ss + (co(3)-co(1))*tt + (co(4)-co(1))*uu
        yyy = co(5) + (co(6)-co(5))*ss + (co(7)-co(5))*tt + (co(8)-co(5))*uu
        zzz = co(9) + (co(10)-co(9))*ss + (co(11)-co(9))*tt + &
                    (co(12)-co(9))*uu

end subroutine sample_tetrahedra


subroutine sample_hexahedra (co)
! This subroutine receives the eight vertices of a hexahedron and sets
! xxx, yyy, zzz, to values corresponding to a uniformly sampled point
! within the hexahedral voxel.
! 
! It is assumed that the hexahedron is a parallelepiped.
! 
! Parameters
! -----------
! co - list of 12 real*8 values
!     The x y z coordinates of four points for a hexaahedron.  These numbers
!     are in xxx.. yyy.. zzz.. order.
! 
! Notes
! ------
! The algorithm used is to sample distances along three edge vectors that
! originate at the first vertex of the hexahedron (MOAB canonical ordering)
! and add these three vectors to the first vertice's coordinates.
! 
  use source_data
  implicit none

        ! Parameters
        real(dknd), dimension(1:24), intent(IN) :: co

        real(dknd), dimension(1:3) :: a, b, c, d, e, f, g, h
        real(dknd), dimension(1:3) :: v1, v2, v3
        real(dknd) :: ss, tt, uu, temp

        a = co(1::8)
        b = co(2::8)
        ! c = co(3::8) ! c, f, g, h are unused
        d = co(4::8)
        e = co(5::8)
        ! f = co(6::8)
        ! g = co(7::8)
        ! h = co(8::8)
        
        ss = rang()
        tt = rang()
        uu = rang()

        ! Get 3 edge vectors that begin at point 'a'
        v1 = ss * (b - a)
        v2 = tt * (e - a)
        v3 = uu * (d - a)
        
        ! Sample random point within the voxel
        xxx = a(1) + v1(1) + v2(1) + v3(1)
        yyy = a(2) + v1(2) + v2(2) + v3(2)
        zzz = a(3) + v1(3) + v2(3) + v3(3)

end subroutine sample_hexahedra


subroutine sample_erg (myerg, myvoxel, n_grp, n_vox, probList, aliasesList)
! Sample the alias table of energy bins for the selected voxel. 
! 
! Parameters
! ----------
! myerg : float (OUT)
!     Sampled energy is stored in this variable
! myvoxel : int
!     Index of sampled voxel
! n_grp : int
!     Number of energy groups
! n_vox : int
!     Length of next two arrays
! probList : list of lists of floats
!     List of bin probabilities for energy PDF, for each voxel
! aliasesList : list of lists of integers
!     Alias indices for energy group, for each voxel
! 
  use source_data
  implicit none
  
        real(dknd), intent(OUT) :: myerg
        integer, intent(IN) :: myvoxel, n_grp, n_vox
        real(dknd), dimension(1:n_vox,1:n_grp), intent(IN) :: probList
        integer(i4knd), dimension(1:n_vox,1:n_grp), intent(IN) :: aliasesList

        integer :: j
        real(dknd) :: rand
    
        ! Sampling the alias table
        rand = rang() * n_grp
        alias_bin = INT(rand) + 1
        if ((rand + (1._dknd - alias_bin)).lt.probList(myvoxel,alias_bin)) then
          j = alias_bin
        else
          j = aliasesList(myvoxel,alias_bin)
        endif

        ! Bad condition checking; Indicates problem with alias table creation.
        if (j.eq.-1) then
          call expirx(1,'sample_erg','Invalid indice sampled.')
        endif
       
        myerg = my_ener_phot(j)+(1-rang())*(my_ener_phot(j+1)-my_ener_phot(j))

end subroutine sample_erg


subroutine gen_erg_alias_table (len, ergsList, myErgAliases, &
                                        myErgBinsProbabilities)
! Create alias table for energy bins of a single voxel
! 
! Parameters
! ----------
! len : int
!     length of ergsList
! ergsList : list of floats
!     ergsList values must total 1!
! myErgAliases : list of integers (OUT)
!     The generated alias indices for the energy PDF
! myErgBinsProbabilities : list of floats (OUT)
!     List of probabilities for each bin/alias pair.
! 
  use source_data
  implicit none
   
        integer, intent(IN) :: len
        real(dknd), dimension(1:len), intent(IN) :: ergsList
        integer(i4knd), dimension(1:len), intent(OUT) :: myErgAliases
        real(dknd), dimension(1:len), intent(OUT) :: myErgBinsProbabilities

        integer :: i
        real(dknd), dimension(1:len) :: mybins

        ! Create pairs of probabilities and erg bin indices
        do i=1,len
          mybins(i) = ergsList(i)
        enddo

        call gen_alias_table(mybins, myErgAliases(1:len), &
                  myErgBinsProbabilities(1:len), len)

end subroutine gen_erg_alias_table


!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
! Generate Alias Table of Voxels
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
subroutine gen_voxel_alias_table
! Generate alias table for voxels in the problem
! 
! Notes
! -----
! The resulting alias table is stored in lists `aliases` and 
! `binsProbabilities`.
! 
! tot_list does not have to be normalized prior to calling this subroutine
! 
  use source_data
  implicit none

        integer :: i
   
        ! Sum up a normalization factor
        sourceSum = sum(tot_list)
        write(*,*) "sourceSum:", sourceSum 

        ALLOCATE(bins(1:n_mesh_cells))
        ALLOCATE(aliases(1:n_mesh_cells))
        ALLOCATE(binsProbabilities(1:n_mesh_cells))

        ! make the unsorted list of bins
        bias_probability_sum = 0
        do i=1,n_mesh_cells
          ! the average bins(i) value assigned is n_inv
          bins(i) = tot_list(i) / sourceSum

          ! if biasing being done, get the quantity: sum(p_i*b_i)
          !  where for bin i, p_i is bin probability, b_i is bin bias
          if (bias.eq.1) then
            bias_probability_sum = & 
                              bias_probability_sum + bins(i) * bias_list(i)
          endif
        enddo

        ! if bias values were found, update the bins(i) values for biasing
        !  and then update convert the bias values into particle weights
        if (bias.eq.1) then
          do i=1,n_mesh_cells
            bins(i) = bins(i) * bias_list(i) / bias_probability_sum
            bias_list(i) = bias_probability_sum / bias_list(i)
            !!! bias_list(i) value is now a weight, rather than a bias factor
          enddo
        endif

        ! TODO: Insert void rejection code here.
        ! If adjusting probabilities, change the values in bins().
        ! If adjusting weights, 
        !   If biasing, change the values in bias_list
        !   Else (not biasing), we need a list of weights for each voxel
        !     ... suggest deallocating bias_list after its use above and then
        !         just using the weights list.
        !         Also need to set the weights to 1.0, initially.

        call gen_alias_table(bins, aliases, binsProbabilities, n_mesh_cells)

        write(*,*) 'Alias table of source voxels generated!'

end subroutine gen_voxel_alias_table


subroutine gen_alias_table (bins, aliases, probs_list, len)
! Subroutine generates an alias table
! 
! Parameters
! ----------
! bins : list of floats (INOUT)
!     PDF's absolute probabilities
! aliases : list of integers (OUT)
!     Filled with alias indices.
! probs_list : list of floats (OUT)
!     List of probabilities for each bin/alias pair.
! len : int
!     Number of bins in the alias table
! 
! Notes
! -----
! The sum of the probabilities in bins must be 1.
! 
! We implement the alias table creation algorithm described by Vose (1991).
! For reference::
! 
!   Vose:      Code:
!   p_j        bins(j)
!   large_l    ind_large(l)
!   small_s    ind_small(s)
!   prob_j     probs_list(j)
!   'bin' j    j
!   alias_j    aliases(j)
! 
  use mcnp_global
  implicit none
   
        ! subroutine argument variables
        integer, intent(in) :: len
        real(dknd), dimension(1:len), intent(INOUT) :: bins
        integer(i4knd), dimension(1:len), intent(OUT) :: aliases
        real(dknd), dimension(1:len), intent(OUT) :: probs_list

        ! internal variables
        integer :: largecnt, j,k,s,l
        integer, dimension(:), allocatable :: ind_small, ind_large
        real(dknd) :: n_inv 

        n_inv = 1._dknd / len
        
        ! Determine number of 'large' and 'small' bins
        largecnt = 0        
        do j=1,len
          if ( bins(j).gt.n_inv ) then
            largecnt = largecnt + 1
          endif
        enddo

        ALLOCATE( ind_small(1:(len-largecnt)) )
        ALLOCATE( ind_large(1:largecnt) )
                
        ! and store their indices in ind_small and ind_large
        l = 1
        s = 1
        do j=1,len
          if ( bins(j).gt.n_inv ) then
            ind_large(l) = j
            l = l + 1
          else
            ind_small(s) = j
            s = s + 1
          endif
        enddo

        ! Fill out aliases and prob_list
        do while (s.gt.1.and.l.gt.1)
          s = s - 1
          j = ind_small(s)
          l = l - 1
          k = ind_large(l)
          aliases(j) = k ! The alias bin
          probs_list(j) = bins(j) * len

          ! decrement the bin used as the alias
          bins(k) = bins(k) + (bins(j) - n_inv)

          if ( bins(k).gt.n_inv ) then
            ind_large(l) = k ! Redundant??
            l = l + 1
          else
            ind_small(s) = k
            s = s + 1
          endif
        enddo

        ! Handle any bins that require no alias
        do while (s.gt.1)
          s = s - 1
          j = ind_small(s)
          aliases(j) = -1 ! should never be used
          probs_list(ind_small(s)) = 1._dknd
        enddo

        ! Loop should only occur due to round-off errors
        ! Handles any bins in ind_large that require no alias
        do while (l.gt.1)
          l = l - 1
          k = ind_large(l)
          aliases(k) = -1 ! should never be used
          probs_list(ind_large(l)) = 1._dknd
        enddo

end subroutine gen_alias_table


subroutine print_debug
! Subroutine stores debug info in an array, and write the array to a file
! after every 10000 particles.
! 
  use source_data
  implicit none

        ! 
        integer :: unitdebug, statusdebug, i
        ! Array storing debug information
        real(dknd), dimension(1:10000,1:4) :: source_debug_array
        save source_debug_array
 
        ! Save information for debugging where source particles are started.
        npart_write = npart_write + 1
        source_debug_array(npart_write,1) = xxx
        source_debug_array(npart_write,2) = yyy
        source_debug_array(npart_write,3) = zzz
        source_debug_array(npart_write,4) = wgt

        ! Write debug information for 10000 histories to file
        if (npart_write.eq.10000) then
  
          write(*,*) 'writing to source debug file.'
          unitdebug = getUnit()
          OPEN(unit=unitdebug, file="source_debug", position='append')
          do i=1,10000
            write(unitdebug,*) source_debug_array(i,1:4)
          enddo
          
          CLOSE(unitdebug)
          npart_write = 0
        endif

end subroutine print_debug

