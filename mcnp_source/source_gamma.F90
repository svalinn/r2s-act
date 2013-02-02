!+ $Id: source.F90,v 1.1 2004/03/20 00:31:52 jsweezy Exp $
! Copyright LANL/UC/DOE - see file COPYRIGHT_INFO

! 
! Summary
! =======
! Adapted from source routine (`source_gamma_meshtal2.F90`) provided by 
! Dieter Leichtle from KIT.
! Changes have been made by Eric Relson with UW-Madison/CNERG goals in mind.
! 
! This source file implements photon source sampling on a cartesian mesh.
! Two photon position sampling methods are avaiable: 
! 
! (1) voxel sampling
! (2) uniform sampling
! 
! Subroutine source reads in the file `gammas` from the directory
! that MCNP is being run in.  The `gammas` file has two parts - a header and
! a listing of information for each voxel.
! 
! Header lines
! ------------
! The header section can be preceded by any number of comment line starting with
! the # character.
! 
! The header lines are 5 lines containing the following information:
! 
! 1. Number of intervals for x, y, z
! 2. Mesh coordinates for x direction
! 3. Mesh coordinates for y direction
! 4. Mesh coordinates for z direction
! 5. List of activated materials; use of this info requires the m parameter
! 
! These are optionally followed by a parameters line (line 6). This line begins 
! with a 'p', and single character parameters, separated by spaces, follow.
! The currently supported parameters are (order does not matter):
! 
! * u: Enable uniform sampling.
! * v: Enable voxel sampling.
! * m: Enable source position rejection based on activated materials.
! * e: Read in custom list of energy bin boundaries.
! * d: Enable debug output to file source_debug. Dumps xxx,yyy,zzz,wgt every 10k
!   particles.
! * c: Treat bins for each voxel as cumulative.
! * b: Flag indicating bias values are used; only valid with voxel sampling.
! * r: Particles starting in a void are resampled (within the same voxel).
! * a: Resample entire particle when a particle would start in void. Requires
!   u and r to be enabled. Can give incorrect results due to playing an
!   unfair game.
! 
! An example parameter line: `p u d m e`
! 
! If the parameters line is not present, the default is to set u, m, c as True.
! If 'e' parameter exists, line 7 lists custom energy group boundaries, space
! delimited. This line start with the integer number of groups. The default
! energy bins are a 42 group structure.
! All subsequent lines are for voxels.
! 
! Voxel lines
! -------------
! Two formats are supported, cumulative bins, or non-cumulative bins. In both
! cases, lines list bin values from low energy to high energy, delimited by
! spaces.
! 
! Note that the normalization for voxel and uniform sampling is different, and 
! will result in differing gammas files. In general, for voxel sampling,
! normalization is based on the average source strength in photons/voxel/s; 
! For uniform sampling, we want average source strength in phtons/cm3/s.
! 
! If the R2S-ACT workflow is not being used to generate the gammas file,
! one should verify that the gammas files are being generated correctly.
! To do this, use a simple test problem to verify that you get the same 
! average energy per source
! particle in all test cases, and that all uniform sampling test cases have a
! weight of 1.0 per source particle. (See the summary table in MCNP output)
! 
! Note that correct normalization also depends on whether
! material rejection is being used.
! 
! In either case, the last bin can be followed by a bias value for the voxel.
! An arbitrary range of bias values can be used since the source routine does
! the necessary re-normalization for voxel sampling.
! 
! Other notes
! --------------
! Voxel sampling and energy sampling use a sampling technique referred to as
! 'alias discrete' or 'alias' sampling.  This provides efficiency benefits
! over 'direct discrete' sampling of PDFs. Creation of the alias tables uses
! the algorithm described by Vose (1991).

module source_data
! Variables used/shared by most of the subroutines in this file.
  use mcnp_global
   
        character*30 :: gammas_file = 'gammas'
        integer(i8knd) :: ikffl = 0 ! = local record of history #
        ! Parameters - these are toggled by gammas
        integer :: bias, samp_vox, samp_uni, debug, ergs, &
             mat_rej, cumulative, resample, uni_resamp_all
        ! Position sampling variables
        integer :: voxel, n_source_cells
        real(dknd),dimension(:),allocatable :: tot_list
        ! Voxel alias table variables
        real(dknd) :: sourceSum, n_inv, norm
        real(dknd),dimension(:,:), allocatable :: bins
        real(dknd),dimension(:),allocatable :: pairsProbabilities
        integer(i4knd),dimension(:,:), allocatable :: pairs
        integer :: alias_bin
        ! Biasing variables
        real(dknd) :: bias_probability_sum
        real(dknd),dimension(:),allocatable :: bias_list
        ! Energy bins variables
        real(dknd),dimension(:,:), allocatable :: spectrum
        real(dknd),dimension(:),allocatable :: my_ener_phot
        integer :: n_ener_grps
        ! Energy bins alias table variables
        real(dknd),dimension(:,:),allocatable :: ergPairsProbabilities
        integer(i4knd),dimension(:,:,:),allocatable :: ergPairs
        ! Debug output variables
        integer(i8knd) :: npart_write = 0 ! = counter for debug output
        ! Other variables
        integer :: stat
        integer :: ii, kk, jj
        integer :: i_ints, j_ints, k_ints, n_mesh_cells, n_active_mat
        real,dimension(:),allocatable :: i_bins, j_bins, k_bins
        integer,dimension(100) :: active_mat
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
   
 
        integer :: unitnum, statusnum

        unitnum = getUnit()
        OPEN(unit=unitnum,form='formatted',file=gammas_file)

        ! Read first 5 lines of gammas
        call read_header(unitnum)

        ! Look for parameters line, and read parameters if found.
        call read_params(unitnum)

        ! If ergs flag was found, we call read_custom_ergs.  Otherwise 
        !  we use default energies.
        if (ergs.eq.1) then
          call read_custom_ergs(unitnum)
          write(*,*) "The following custom energy bins are being used:"
          do i=1,n_ener_grps
            write(*,'(2es11.3)') my_ener_phot(i), my_ener_phot(i+1)
            enddo
        else ! use default energy groups; 42 groups
          n_ener_grps = 42
          ALLOCATE(my_ener_phot(1:n_ener_grps+1))
          my_ener_phot = (/0.0,0.01,0.02,0.03,0.045,0.06,0.07,0.075,0.1,0.15, &
            0.2,0.3,0.4,0.45,0.51,0.512,0.6,0.7,0.8,1.0,1.33,1.34,1.5, &
            1.66,2.0,2.5,3.0,3.5,4.0,4.5,5.0,5.5,6.0,6.5,7.0,7.5,8.0, &
            10.0,12.0,14.0,20.0,30.0,50.0/)
        endif

        ! Prepare to read in spectrum information
        ! set the spectrum array to: # of mesh cells * # energy groups
        ALLOCATE(spectrum(1:n_mesh_cells, 1:bias + n_ener_grps))
        ALLOCATE(tot_list(1:n_mesh_cells))
        if (bias.eq.1) ALLOCATE(bias_list(1:n_mesh_cells))
         
        ! reading in source strength and alias table for each voxel 
        i = 1 ! i keeps track of # of voxel entries
        do
          read(unitnum,*,iostat=stat) (spectrum(i,j), j=1,bias + n_ener_grps)
          if (stat.ne.0) then
            i = i - 1
            exit ! exit the do loop
          endif
          if (bias.eq.1) bias_list(i) = spectrum(i,bias+n_ener_grps)
          i = i + 1
        enddo
        
        ! Check for correct number of voxel entries in gammas file.
        if (i.ne.n_mesh_cells) write(*,*) 'ERROR: ', i, ' voxels found in ' // &
                        'gammas file. ', n_mesh_cells, ' expected.'

        CLOSE(unitnum)
        WRITE(*,*) 'Reading gammas file completed!'

        ALLOCATE(ergPairs(1:n_mesh_cells, 1:n_ener_grps, 1:2))
        ALLOCATE(ergPairsProbabilities(1:n_mesh_cells, 1:n_ener_grps))

        ! Create bins list.  Depending on if cumulative probabilities
        !  were supplied, convert to individual bin probabilities so that
        !  alias table of erg bins can be generated, too.
        if (cumulative.eq.1) then
          do i=1,n_mesh_cells
            tot_list(i) = spectrum(i,n_ener_grps)
            do j=n_ener_grps,2,-1
              spectrum(i,j) = (spectrum(i,j) - spectrum(i,j-1)) / tot_list(i)
            enddo
            spectrum(i,1) = spectrum(i,1) / tot_list(i)
            call gen_erg_alias_table (n_ener_grps, spectrum(i,1:n_ener_grps), &
                        ergPairs(i,1:n_ener_grps,1:2), &
                        ergPairsProbabilities(i,1:n_ener_grps))
          enddo
        else
          do i=1,n_mesh_cells
            tot_list(i) = sum(spectrum(i,1:n_ener_grps))
            do j=1,n_ener_grps
              spectrum(i,j) = spectrum(i,j) / tot_list(i)
            enddo
            call gen_erg_alias_table (n_ener_grps, spectrum(i,1:n_ener_grps), &
                        ergPairs(i,1:n_ener_grps,1:2), &
                        ergPairsProbabilities(i,1:n_ener_grps))
          enddo
        endif

        ! We calculate the number of source voxels.
        n_source_cells = 0
        do i=1,n_mesh_cells
          if (tot_list(i).gt.0) n_source_cells = n_source_cells + 1
        enddo
        write(*,*) "n_mesh_cells:", n_mesh_cells, &
                "n_source_cells:", n_source_cells

        ! Generate alias table of voxels if needed
        if (samp_vox.eq.1) then
          call gen_voxel_alias_table
        endif

        ! Create new debug output file if debugging is enabled.
        if (debug.eq.1) then
          unitnum = getUnit()
          OPEN(unit=unitnum, file="source_debug", access="APPEND", &
                        status="REPLACE")
          CLOSE(unitnum)
        endif

end subroutine source_setup


subroutine read_header (myunit)
! Read in first 5 lines of gammas file, as well as comment lines
! 
! Parameters
! ----------
! myunit : int
!     Unit number for an opened file (i.e. file 'gammas')
! 
! Notes
! -----
! First 5 non-comment  lines contain the x,y,z mesh intervals
! and the list of active materials
! 
! Also skips over any comment lines (beginning with # character) at start of
! file.
! 
  use source_data
        
        integer,intent(IN) :: myunit
        character :: letter
        character*30 :: commentline

        ! initialize an empty 'activated materials' array
        do i=1,100
          active_mat(i)=0
        enddo

        ! Read and skip over comment lines
        do
          letter = " "
          read(myunit,'(A)') commentline
          read(commentline,*,end=976) letter
976       continue

          if (letter.ne.'#') then
            backspace(myunit)
            exit
          endif
        enddo

        ! read first parameter line
        read(myunit,*) i_ints,j_ints,k_ints
        n_mesh_cells = i_ints * j_ints * k_ints

        ALLOCATE(i_bins(1:i_ints+1))
        ALLOCATE(j_bins(1:j_ints+1))
        ALLOCATE(k_bins(1:k_ints+1))

        ! read lines 2,3,4,5
        read(myunit,*) (i_bins(i),i=1,i_ints+1)
        read(myunit,*) (j_bins(i),i=1,j_ints+1)
        read(myunit,*) (k_bins(i),i=1,k_ints+1)
        read(myunit,'(A)') line
        read(line,*,end=887) (active_mat(i),i=1,100)
887     continue

        ! counting number of activated materials specified
        do i=1,100
          if (active_mat(i).eq.0) exit
        enddo
        n_active_mat = i-1

end subroutine read_header


subroutine read_params (myunit)
! Read in the parameters line, if there is one.
! 
! Parameters
! ----------
! myunit : int
!     Unit number for an opened file (i.e. file 'gammas')
! 
! Notes
! -----
! Line should start with a 'p' and have single characters
! that are space delimited.
! 
! Set various parameters to 1 (true) if they exist.
  use source_data

        integer,intent(IN) :: myunit

        character,dimension(1:30) :: letters
        character*30 :: paramline

        ! Initialize parameters to defaults.
        ! Defaults are chosen such that gammas format specified by Leichtle
        !  will hopefully be read correctly without a parameters line.
        !  (untested)
        bias = 0
        samp_vox = 1
        samp_uni = 0
        debug = 0
        ergs = 0
        mat_rej = 1
        cumulative = 1
        resample = 0
        uni_resamp_all = 0

        ! Read enough characters to fill paramline
        read(myunit,'(A)') paramline

        ! fill list of parameters with placeholder character
        do i=1,30
          letters(i) = " "
        enddo

        ! Place individual characters in a list
        read(paramline,*,end=876) (letters(i),i=1,30)
876     continue

        ! No parameter line found
        if (letters(1).ne.'p') then
          backspace(myunit)
          return
        endif 

        ! If parameters present, we assume everything is disabled initially
        samp_vox = 0
        mat_rej = 0
        cumulative = 0

        do i=2,30
          SELECT CASE (letters(i))
          CASE (' ') ! indicates all parameters have been handled.
            exit
          CASE ('e')
            write(*,*) "Custom energy bins will be read."
            ergs = 1
          CASE ('m')
            write(*,*) "Material-based rejection enabled."
            mat_rej = 1
          CASE ('b')
            write(*,*) "Biased sampling of source voxels is enabled."
            bias = 1
          ! only want one type of sampling enabled.
          CASE ('v')
            write(*,*) "Voxel sampling enabled."
            samp_uni = 0
            samp_vox = 1
          CASE ('u')
            write(*,*) "Uniform sampling enabled."
            samp_uni = 1
            samp_vox = 0
          CASE ('d')
            write(*,*) "Debug output of starting positions enabled."
            debug = 1
          CASE ('c')
            write(*,*) "Enabled reading of cumulative energy bins."
            cumulative = 1
          CASE ('r')
            write(*,*) "Enabled resampling for void and/or material rejection."
            resample = 1
          CASE ('a')
            write(*,*) "Uniform sampling will resample entire problem if" // &
              "void is hit"
            uni_resamp_all = 1
          CASE DEFAULT
            write(*,*) " "
            write(*,*) "Invalid parameter!: ", letters(i)
          END SELECT

        enddo

        ! Biasing in conjunction with uniform sampling not supported
        if (samp_uni.eq.1) bias = 0

end subroutine read_params


subroutine read_custom_ergs (myunit)
! Read line from gammas file to get a custom set of energy bins

! Parameters
! ----------
! myunit : int
!     Unit number for an opened file (i.e. file 'gammas')
! 
! Notes
! ------
! N/A
  use source_data
        
        integer,intent(IN) :: myunit

        read(myunit,*) n_ener_grps ! reads an integer for # of grps
        backspace(myunit) ! bit of a hack since read(myunit,*,advance='NO') is invalid Fortran
        ALLOCATE(my_ener_phot(1:n_ener_grps+1))
        read(myunit,*,end=888) n_erg_grps, (my_ener_phot(i),i=1,n_ener_grps+1)
888     continue

end subroutine read_custom_ergs


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
        ! -ii, jj, and kk
10      if (samp_vox.eq.1) then
          call voxel_sample
        elseif (samp_uni.eq.1) then
          call uniform_sample
        endif

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
        !
        if (resample.eq.0) then
          goto 544 ! Always accept position when resampling is disabled.
        ! rejection of non-void materials is enabled...
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
            call sample_hexahedra
            goto 555
          else
            goto 544
          endif
        ! void rejection with uniform sampling
        elseif (samp_uni.eq.1) then
          if (mat(icl).eq.0) then
            if (uni_resamp_all.eq.0) then
              ! particle rejected... resample within the voxel and recheck
              call sample_hexahedra
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
                        ergPairsProbabilities, ergPairs)

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

        real(dknd) :: rand

        ! Sampling the alias table
        rand = rang() * n_mesh_cells
        alias_bin = INT(rand) + 1
        if ((rand+(1._dknd-alias_bin)).lt.pairsProbabilities(alias_bin)) then
          voxel = pairs(alias_bin,1)
        else
          voxel = pairs(alias_bin,2)
        endif
        
        ! Bad condition checking; Indicates problem with alias table creation.
        if (voxel.eq.-1) then
          call expirx(1,'voxel_sample','Invalid indice sampled.')
        endif
       
        ! We -=1 the value of the index 'voxel' to calc ii,jj,kk easily
        voxel = voxel - 1
        ! Math to get mesh indices in each dimension
        ii = voxel / (k_ints*j_ints)
        jj = mod(voxel, k_ints*j_ints) / k_ints
        kk = mod(mod(voxel, k_ints*j_ints), k_ints)
        
        voxel = voxel + 1
        
        call sample_hexahedra
        
end subroutine voxel_sample


subroutine uniform_sample
! Uniformly sample photon position in the entire volume of the mesh tally.
  use source_data

        ! Choose position
        xxx = i_bins(1)+rang()*(i_bins(i_ints+1)-i_bins(1))
        yyy = j_bins(1)+rang()*(j_bins(j_ints+1)-j_bins(1))
        zzz = k_bins(1)+rang()*(k_bins(k_ints+1)-k_bins(1))

        ! Identify corresponding voxel (sets ii, jj, kk)
        do ii=1,i_ints
          if (i_bins(ii).le.xxx.and.xxx.lt.i_bins(ii+1)) exit
        enddo
        do jj=1,j_ints
          if (j_bins(jj).le.yyy.and.yyy.lt.j_bins(jj+1)) exit
        enddo
        do kk=1,k_ints
          if (k_bins(kk).le.zzz.and.zzz.lt.k_bins(kk+1)) exit
        enddo

        ! ii, jj, kk are shifted into the range [1, i_ints/j_ints/k_ints].
        ii = ii - 1
        jj = jj - 1
        kk = kk - 1

        voxel = (kk)+(jj)*k_ints+(ii)*j_ints*k_ints + 1

end subroutine uniform_sample


subroutine sample_hexahedra
! Samples within the extents of a voxel
! 
! Notes
! -----
! ii, jj, kk are presumed to have been already determined, and have values
! in the range [1, i_ints/j_ints/k_ints].
  use source_data
 
!       Sample random spot within the voxel
        xxx = i_bins(ii+1)+rang()*(i_bins(ii+2)-i_bins(ii+1))
        yyy = j_bins(jj+1)+rang()*(j_bins(jj+2)-j_bins(jj+1))
        zzz = k_bins(kk+1)+rang()*(k_bins(kk+2)-k_bins(kk+1))

end subroutine sample_hexahedra


subroutine sample_tetrahedra(p1x,p2x,p3x,p4x,p1y,p2y,p3y,p4y,p1z,p2z,p3z,p4z)
! This subroutine receives the four points of a tetrahedron and sets
! xxx, yyy, zzz, to values corresponding to a uniformly sampled point
! within the tetrahedron.
! 
! Parameters
! -----------
! The x y z coordinates of four points for a tetrahedron
! 
! Notes
! ------
! The algorithm used is that described by Rocchini & Cignoni (2001)
! 
  use source_data

      real(dknd), intent(IN) :: p1x, p2x, p3x, p4x, p1y, p2y, p3y, p4y, &
                p1z, p2z, p3z, p4z

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

      xxx = p1x + (p2x-p1x)*ss + (p3x-p1x)*tt + (p4x-p1x)*uu
      yyy = p1y + (p2y-p1y)*ss + (p3y-p1y)*tt + (p4y-p1y)*uu
      zzz = p1z + (p2z-p1z)*ss + (p3z-p1z)*tt + (p4z-p1z)*uu

end subroutine sample_tetrahedra


subroutine sample_erg (myerg, myvoxel, n_grp, n_vox, probList, pairsList)
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
!     List of alias pair probabilities for energy PDF, for each voxel
! pairsList : list of lists of [int, int] pairs
!     Bin and alias indices for energy group, for each voxel

  use source_data
        real(dknd),intent(OUT) :: myerg
        integer,intent(IN) :: myvoxel, n_grp, n_vox
        real(dknd),dimension(1:n_vox,1:n_grp), intent(IN) :: probList
        integer(i4knd),dimension(1:n_vox,1:n_grp,1:2),intent(IN) :: pairsList

        real(dknd) :: rand
    
        ! Sampling the alias table
        rand = rang() * n_grp
        alias_bin = INT(rand) + 1
        if ((rand + (1._dknd - alias_bin)).lt.probList(myvoxel,alias_bin)) then
          j = pairsList(myvoxel,alias_bin,1)
        else
          j = pairsList(myvoxel,alias_bin,2)
        endif

        ! Bad condition checking; Indicates problem with alias table creation.
        if (j.eq.-1) then
          call expirx(1,'sample_erg','Invalid indice sampled.')
        endif
       
        myerg = my_ener_phot(j)+(1-rang())*(my_ener_phot(j+1)-my_ener_phot(j))

end subroutine sample_erg


subroutine gen_erg_alias_table (len, ergsList, myErgPairs, &
                                        myErgPairsProbabilities)
! Create alias table for energy bins of a single voxel
! 
! Parameters
! ----------
! len : int
!     length of ergsList
! ergsList : list of floats
!     ergsList values must total 1!
! myErgPairs : list of [int, int] (OUT)
!     The generated pairs of bin and alias indices for the energy PDF
! myErgPairsProbabilities : list of floats (OUT)
!     List of probabilities for first bin in each alias pair.
! 
  use source_data
   
        integer,intent(IN) :: len
        real(dknd),dimension(1:len),intent(IN) :: ergsList
        integer(i4knd),dimension(1:len,1:2),intent(OUT) :: myErgPairs
        real(dknd),dimension(1:len), intent(OUT) :: myErgPairsProbabilities

        integer :: i
        real(dknd),dimension(1:len,1:2) :: mybins

        ! Create pairs of probabilities and erg bin indices
        do i=1,len
          mybins(i,1) = ergsList(i)
          mybins(i,2) = i
        enddo

        call gen_alias_table(mybins, myErgPairs(1:len,1:2), &
                  myErgPairsProbabilities(1:len), len)

end subroutine gen_erg_alias_table


!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
! Generate Alias Table of Voxels
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
subroutine gen_voxel_alias_table
! Generate alias table for voxels in the problem
! 
! Notes
! -----
! The resulting alias table is stored in lists `pairs` and `pairsProbabilities`.
! 
! tot_list does not have to be normalized prior to calling this subroutine
  use source_data
   
        ! Note that the first entry for each voxel in 'gammas' is
        ! a relative probability of that voxel being the source location.
        ! If biasing is used, the second entry is the bias value of the voxel
        ! Sum up a normalization factor
        sourceSum = sum(tot_list)
        write(*,*) "sourceSum:", sourceSum 

        ALLOCATE(bins(1:n_mesh_cells,1:2))
        ALLOCATE(pairs(1:n_mesh_cells, 1:2))
        ALLOCATE(pairsProbabilities(1:n_mesh_cells))

        ! make the unsorted list of bins
        bias_probability_sum = 0
        do i=1,n_mesh_cells
          ! the average bin(i,1) value assigned is n_inv
          bins(i,1) = tot_list(i) / sourceSum
          bins(i,2) = i

          ! if biasing being done, get the quantity: sum(p_i*b_i)
          !  where for bin i, p_i is bin probability, b_i is bin bias
          if (bias.eq.1) then
            bias_probability_sum = & 
                              bias_probability_sum + bins(i,1) * bias_list(i)
          endif
        enddo

        ! if bias values were found, update the bin(i,1) values for biasing
        !  and then update the bias values so that they are now particle wgt
        if (bias.eq.1) then
          do i=1,n_mesh_cells
            bins(i,1) = bins(i,1) * bias_list(i) / bias_probability_sum
            bias_list(i) = bias_probability_sum / bias_list(i)
            !!! bias_list(i) value is now a weight, rather than a probabilty
          enddo
        endif

        call gen_alias_table(bins, pairs, pairsProbabilities, n_mesh_cells)

        write(*,*) 'Alias table of source voxels generated!'

end subroutine gen_voxel_alias_table


subroutine gen_alias_table (bins, pairs, probs_list, len)
! Subroutine generates an alias table
! 
! Parameters
! ----------
! bins : list of [int, float] pairs (INOUT)
!     PDF's bin indices and absolute probabilities.
! pairs : list of [int, int] pairs (OUT)
!     Filled with pairs of bin and alias indices.
! probs_list : list of floats (OUT)
!     List of probabilities for first bin in each alias pair.
! len : int
!     Number of bins in the alias table
! 
! Notes
! -----
! note that bins is a list of pairs of the form (probability,value)
! The sum of the probabilities in bins must be 1.
! 
! We implement the alias table creation algorithm described by Vose (1991).
! For reference::
! 
!   Vose:      Code:
!   p_j        bins(j,1)
!   large_l    ind_large(l)
!   small_s    ind_small(s)
!   prob_j     probs_list(j)
!   'bin' j    pairs(j,1)
!   alias_j    pairs(j,2)
! 
  use mcnp_global
   
        ! subroutine argument variables
        real(dknd),dimension(1:len,1:2),intent(INOUT) :: bins
        integer(i4knd),dimension(1:len,1:2), intent(OUT) :: pairs
        real(dknd),dimension(1:len), intent(OUT) :: probs_list
        integer, intent(in) :: len

        ! internal variables
        integer :: largecnt, j,k,s,l
        integer,dimension(:),allocatable :: ind_small, ind_large
        real(dknd) :: n_inv 

        n_inv = 1._dknd / len
        
        ! Determine number of 'large' and 'small' bins
        largecnt = 0        
        do j=1,len
          if ( bins(j,1).gt.n_inv ) then
            largecnt = largecnt + 1
          endif
        enddo

        ALLOCATE( ind_small(1:(len-largecnt)) )
        ALLOCATE( ind_large(1:largecnt) )
                
        ! and store their indices in ind_small and ind_large
        l = 1
        s = 1
        do j=1,len
          if ( bins(j,1).gt.n_inv ) then
            ind_large(l) = j
            l = l + 1
          else
            ind_small(s) = j
            s = s + 1
          endif
        enddo

        ! Fill out pairs and prob_list
        do while (s.gt.1.and.l.gt.1)
          s = s - 1
          j = ind_small(s)
          l = l - 1
          k = ind_large(l)
          pairs(j,1) = bins(j,2)
          pairs(j,2) = bins(k,2) ! The alias bin
          probs_list(j) = bins(j,1) * len

          ! decrement the bin used as the alias
          bins(k,1) = bins(k,1) + (bins(j,1) - n_inv)

          if ( bins(k,1).gt.n_inv ) then
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
          pairs(j,1) = bins(j,2)
          pairs(j,2) = -1 ! should never be used
          probs_list(ind_small(s)) = 1._dknd
        enddo

        ! Loop should only occur due to round-off errors
        ! Handles any bins in ind_large that require no alias
        do while (l.gt.1)
          l = l - 1
          k = ind_large(l)
          pairs(k,1) = bins(k,2)
          pairs(k,2) = -1 ! should never be used
          probs_list(ind_large(l)) = 1._dknd
        enddo

end subroutine gen_alias_table


subroutine print_debug
! Subroutine stores debug info in an array, and write the array to a file
! after every 10000 particles.
! 
  use source_data

        !
        integer :: unitdebug, statusdebug
        ! Array storing debug information
        real(dknd),dimension(1:10000,1:4) :: source_debug_array
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
          OPEN(unit=unitdebug, file="source_debug", access="APPEND")
          do i=1,10000
            write(57,*) source_debug_array(i,1:4)
          enddo
          
          CLOSE(unitdebug)
          npart_write = 0
        endif

end subroutine print_debug
