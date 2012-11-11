!+ $Id: source.F90,v 1.1 2004/03/20 00:31:52 jsweezy Exp $
! Copyright LANL/UC/DOE - see file COPYRIGHT_INFO

! Adapted from source routine (source_gamma_meshtal2.F90) provided by 
!  Dieter Leichtle from KIT.
! Changes have been made by Eric Relson with UW-Madison/CNERG goals in mind.
! 
! This source file implements photon source sampling on a cartesian mesh.
! Two photon position sampling methods are avaiable: 
!             (1) voxel sampling and (2) uniform sampling
!
! Subroutine source reads in the file 'gammas' from the directory
!  that MCNP is being run in.  The gammas file has two parts - a header and
!  a listing of information for each voxel.
!
! HEADER:
! The header starts with 5 lines containing the following information:
! 1: Number of intervals for x, y, z
! 2: Mesh coordinates for x direction
! 3: Mesh coordinates for y direction
! 4: Mesh coordinates for z direction
! 5: List of activated materials; use of this info requires the m parameter.
! These are optionally followed by a parameters line (line 6). This line begins 
!  with a 'p', and single character parameters, separated by spaces, follow.
! The currently supported parameters are (order does not matter):
! u: enable uniform sampling
! v: enable voxel sampling
! m: enable source position rejection based on activated materials
! e: read in custom list of energy bin boundaries
! d: enable debug output to file source_debug. Dumps xxx,yyy,zzz,wgt every 10k
!       particles
! c: treat bins for each voxel as cumulative
! b: flag indicating bias values are used; only valid with voxel sampling
!
! An example parameter line: p u d m e
! If the parameters line is not present, the default is to set u, m, c as True.
! If 'e' parameter exists, line 7 lists custom energy group boundaries, space
!  delimited. This line start with the integer number of groups. The default
!  energy bins are a 42 group structure.
! All subsequent lines are for voxels.
! 
! VOXEL LINES:
! Two formats are supported, cumulative bins, or non-cumulative bins. In both
!  cases, lines list bin values from low energy to high energy, delimited by
!  spaces.
! Note that the normalization for voxel and uniform sampling is different, and 
!  will result in differing gammas files. In general, for voxel sampling,
!  normalization is based on the average source strength in photons/voxel/s; 
!  For uniform sampling, we want average source strength in phtons/cm3/s.
! As an exercise to verify that the gammas files are being generated correctly,
!  do a test problem and verify that you get the same average energy per source
!  particle in all test cases, and that all uniform sampling test cases have a
!  weight of 1.0 per source particle. (See the summary table in MCNP output)
! Note that correct normalization also depends on whether
!  material rejection is being used.
! In either case, the last bin can be followed by a bias value for the voxel.
!  An arbitrary range of bias values can be used since the source routine does
!  the necessary re-normalization for voxel sampling.
! 
! Other notes:
! Voxel sampling and energy sampling use a sampling technique referred to as
!  'alias discrete' or 'alias table' sampling.  This provides efficiency
!  benefits over 'direct discrete' sampling. Creation of the alias tables uses
!  the heap sort algorithm.

module source_data
! Variables used/shared by most of the subroutines in this file.
  use mcnp_global
   
        character*30 :: gammas_file = 'gammas'
        integer(i8knd) :: ikffl = 0 ! = local record of history #
        ! Parameters - these are toggled by gammas
        integer :: bias, samp_vox, samp_uni, debug, ergs, mat_rej, cumulative
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
        integer :: ii,kk,jj
        ! Debug output variables
        integer(i8knd) :: npart_write = 0 ! = counter for debug output
        ! Other variables
        integer :: stat
        integer :: i_ints, j_ints, k_ints, n_mesh_cells, n_active_mat
        real,dimension(:),allocatable :: i_bins, j_bins, k_bins
        integer,dimension(100) :: active_mat
        character*3000 :: line ! needed for reading active_mat from gammas
        ! Saved variables will be unchanged next time source is called
        !save spectrum,i_ints,j_ints,k_ints,n_active_mat,n_ener_grps, &
        save i_ints, j_ints, k_ints, n_active_mat, n_ener_grps, &
             i_bins, j_bins, k_bins, active_mat, my_ener_phot, ikffl, pairs, &
             pairsProbabilities, n_mesh_cells, bias, bias_probability_sum, &
             ergPairsProbabilities, ergPairs, tot_list, bias_list, &
             ii, kk, jj, voxel
       
end module source_data


subroutine source_setup
  ! subroutine handles parsing of the 'gammas' file and related initializations
  use source_data
   
 
        CLOSE(50)
        OPEN(unit=50,form='formatted',file=gammas_file)

        ! Read first 5 lines of gammas
        call read_header(50)

        ! Look for parameters line, and read parameters if found.
        call read_params(50)

        ! If ergs flag was found, we call read_custom_ergs.  Otherwise 
        !  we use default energies.
        if (ergs.eq.1) then
          call read_custom_ergs(50)
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
          read(50,*,iostat=stat) (spectrum(i,j), j=1,bias + n_ener_grps)
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

        CLOSE(50)
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
          OPEN(UNIT=57, FILE="source_debug", ACCESS="APPEND", STATUS="REPLACE")
          CLOSE(57)
        endif

end subroutine source_setup


subroutine read_header (myunit)
! Read in first 5 lines of gammas file
! These lines contain the x,y,z mesh intervals
!  and the list of active materials
  use source_data
        
        integer,intent(IN) :: myunit

        ! initialize an empty array
        do i=1,100
          active_mat(i)=0
        enddo

        ! read first line
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
! Line should start with a 'p' and have single characters
!  that are space delimited.
! Set various parameters to 1 (true) if they exist.
  use source_data

        integer,intent(IN) :: myunit

        character,dimension(1:30) :: letter
        character*30 :: paramline

        ! Initialize parameters such that gammas format specified by Leichtle
        !  will be read correctly without a parameters line.
        bias = 0
        samp_vox = 1
        samp_uni = 0
        debug = 0
        ergs = 0
        mat_rej = 1
        cumulative = 1

        ! Read enough characters to fill paramline
        read(myunit,'(A)') paramline

        do i=1,30 ! fill list of parameters with placeholder character
          letter(i) = " "
        enddo

        ! Place individual characters in a list
        read(paramline,*,end=876) (letter(i),i=1,30)
876     continue

        if (letter(1).ne.'p') then
          backspace(myunit)
          return
        endif 

        ! If parameters present, we assume everything is disabled initially
        samp_vox = 0
        mat_rej = 0
        cumulative = 0

        do i=2,30
          SELECT CASE (letter(i))
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
          CASE DEFAULT
            write(*,*) " "
            write(*,*) "Invalid parameter!: ", letter(i)
          END SELECT

        enddo

        ! Biasing in conjunction with uniform sampling not supported
        if (samp_uni.eq.1) bias = 0

end subroutine read_params


subroutine read_custom_ergs (myunit)
! Read line from gammas file to get a custom set of energy bins
  use source_data
        
        integer,intent(IN) :: myunit

        read(myunit,*) n_ener_grps ! reads an integer for # of grps
        backspace(myunit) ! dirty hack since read(myunit,*,advance='NO') is invalid
        ALLOCATE(my_ener_phot(1:n_ener_grps+1))
        read(myunit,*,end=888) n_erg_grps, (my_ener_phot(i),i=1,n_ener_grps+1)
888     continue

end subroutine read_custom_ergs


subroutine source
  ! adapted from dummy source.F90 file.
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
        if (mat_rej.eq.1) then
          do i=1,n_active_mat
            if (nmt(mat(icl)).eq.active_mat(i)) then
              goto 544 ! Position is ok; particle starts in activated material
            endif
          enddo
        elseif (samp_vox.eq.1) then
          if (nmt(mat(icl)).eq.0) then
            ! particle rejected... resample within the voxel
            call sample_within_voxel
            goto 555
          else
            goto 544
          endif
        else
          goto 544 ! skip material rejection
        endif

        goto 10 ! particle rejected... sample anew.
  
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
        
        ! Debug output if enabled
        if (debug.eq.1) then
          call print_debug
        endif

        return
 
end subroutine source


subroutine voxel_sample
! Sample photon position from alias table of voxels.
  use source_data
        ! Sampling the alias table
        alias_bin = INT(rang() * n_mesh_cells) + 1
        if (rang().lt.pairsProbabilities(alias_bin)) then
          voxel = pairs(alias_bin,1) - 1
        else
          voxel = pairs(alias_bin,2) - 1
        endif
       
        ! Math to get mesh indices in each dimension
        ! We -1'd the value of the index 'voxel' so next three lines are easy
        ii = voxel / (k_ints*j_ints)
        jj = mod(voxel, k_ints*j_ints) / k_ints
        kk = mod(mod(voxel, k_ints*j_ints), k_ints)

        voxel = voxel + 1

        call sample_within_voxel
        
end subroutine voxel_sample


subroutine sample_within_voxel
! Samples within the extents of a voxel
! ii, jj, kk are presumed to have been already determined.
  use source_data
 
!       Sample random spot within the voxel
        xxx = i_bins(ii+1)+rang()*(i_bins(ii+2)-i_bins(ii+1))
        yyy = j_bins(jj+1)+rang()*(j_bins(jj+2)-j_bins(jj+1))
        zzz = k_bins(kk+1)+rang()*(k_bins(kk+2)-k_bins(kk+1))

end subroutine sample_within_voxel


subroutine uniform_sample
! Uniformly sample photon position in the entire volume of the mesh tally.
  use source_data

        ! Choose position
        xxx = i_bins(1)+rang()*(i_bins(i_ints+1)-i_bins(1))
        yyy = j_bins(1)+rang()*(j_bins(j_ints+1)-j_bins(1))
        zzz = k_bins(1)+rang()*(k_bins(k_ints+1)-k_bins(1))

        ! Identify corresponding voxel
        do ii=1,i_ints
          if (i_bins(ii).le.xxx.and.xxx.lt.i_bins(ii+1)) exit
        enddo
        do jj=1,j_ints
          if (j_bins(jj).le.yyy.and.yyy.lt.j_bins(jj+1)) exit
        enddo
        do kk=1,k_ints
          if (k_bins(kk).le.zzz.and.zzz.lt.k_bins(kk+1)) exit
        enddo

        voxel = (kk-1)+(jj-1)*k_ints+(ii-1)*j_ints*k_ints+1

end subroutine uniform_sample


subroutine sample_erg (myerg, myvoxel, n_grp, n_vox, probList, pairsList)
! Sample the alias table of energy bins for the selected voxel. 
  use source_data
        real(dknd),intent(OUT) :: myerg
        integer,intent(IN) :: myvoxel, n_grp, n_vox
        real(dknd),dimension(1:n_vox,1:n_grp), intent(IN) :: probList
        integer(i4knd),dimension(1:n_vox,1:n_grp,1:2),intent(IN) :: pairsList

    
        ! Sampling the alias table
        alias_bin = INT(rang() * n_grp) + 1
        if (rang().lt.probList(myvoxel,alias_bin)) then
          j = pairsList(myvoxel,alias_bin,1)
        else
          j = pairsList(myvoxel,alias_bin,2)
        endif
       
        myerg = my_ener_phot(j)+(1-rang())*(my_ener_phot(j+1)-my_ener_phot(j))

end subroutine sample_erg


subroutine gen_erg_alias_table (len, ergsList, myErgPairs, &
                                        myErgPairsProbabilities)
! Create alias table for energy bins of a single voxel
! len is the length of ergsList
! ergsList values must total 1!
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
            !spectrum(i,2) = bias_probability_sum / spectrum(i,2)
            ! !!! spectrum(i,2) value is now a weight, rather than a probabilty
            bias_list(i) = bias_probability_sum / bias_list(i)
            !!! bias_list(i) value is now a weight, rather than a probabilty
          enddo
        endif

        call gen_alias_table(bins, pairs, pairsProbabilities, n_mesh_cells)

        write(*,*) 'Alias table of source voxels generated!'

end subroutine gen_voxel_alias_table


subroutine gen_alias_table(bins, pairs, probs_list, len)
! note that bins is a list of pairs of the form (probability,value)
!  The sum of the probabilities in bins must be 1.
  use mcnp_global
   
        ! subroutine argument variables
        real(dknd),dimension(1:len,1:2),intent(inout) :: bins
        integer(i4knd),dimension(1:len,1:2), intent(out) :: pairs
        real(dknd),dimension(1:len), intent(out) :: probs_list
        integer, intent(in) :: len

        ! internal variables
        real(dknd) :: n_inv 

        ! do an initial sort
        call heap_sort(bins, len)

        ! With each pass through the following loop, we ignore another bin
        !  (the j'th bin) by setting its probability vaue to -1.
        ! pairs stores the two possible values for each alias table bin
        ! probs_list stores the probability of the first value in the
        !  alias table bin being used
        n_inv = 1._dknd / len

        do j=1,len

          ! resort last bin
          call sort_for_alias_table(bins, len)

          ! Lowest bin is less than 1/n, and thus needs a second bin with
          !  which to fill the alias bin.
          if ( bins(j,1).lt.n_inv ) then
            probs_list(j) = bins(j,1) * len
            pairs(j,1) = bins(j,2)

            ! don't need to store second probability
            pairs(j,2) = bins(len,2)

            bins(len,1) = bins(len,1) - (n_inv - bins(j,1))
            
          ! Lowest bin should never have a probablity > 1/n, I think?
          else if (bins(j,1).gt.n_inv) then
            !write(*,*) "Problem generating alias table. See source.F90"
            pairs(j,1) = bins(j,2)
            pairs(j,2) = 0
            probs_list(j) = 1.0

            bins(j,1) = bins(j,1) - n_inv

          ! Lowest bin is exactly 1/n
          else ! (bins(j,1).eq.1) ! single possible value for given bin
            probs_list(j) = 1.0
            pairs(j,1) = bins(j,2)
            pairs(j,2) = 0

          endif

          bins(j,1) = -1.3 ! Immunity to sorting for already-used bins

        enddo

end subroutine gen_alias_table


subroutine sort_for_alias_table(bins, length)
! subroutine locates where to move the last bin in bins to,
! such that bins is presumably completely sorted again.
  use mcnp_global

        integer,intent(IN) :: length
        real(dknd),intent(INOUT),dimension(1:length,1:2) :: bins

        ! Method's variables
        integer :: cnt, i
        real(dknd),dimension(1,1:2) :: temp

        if (bins(length,1).lt.bins(length-1,1)) then
 
          ! The logic in this do loop may be problematic at 
          !  cnt = length or cnt = 1...
          do cnt=length-1,1,-1
            if (bins(length,1).ge.bins(cnt,1)) exit
          enddo
          
          temp(1,1:2) = bins(length,1:2)
          bins(cnt+1:length,1:2) = bins(cnt:length-1,1:2)
          bins(cnt,1:2) = temp(1,1:2)

        else
          continue
        endif

end subroutine sort_for_alias_table


!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!  Heap Sort Algorithm
!  The below methods (heap_sort, heapify, sifDown, doSwap)
!   implement the heap sort algorithm as described on the Wikipedia page
!   for 'Heap Sort' circa May 2012.
!  This algorithm is used for initially sorting data before creating
!   an alias table.  The code is included in this file to avoid the need
!   to make modifications to default compiling procedures for MCNP
!   (e.g. no need to add additional source files to a makefile)

subroutine heap_sort(a, len)
! Method implements the heap sort algorithm with subroutines
! heapify and siftDown.
  use mcnp_global

        real(dknd),dimension(1:len,1:2),intent(INOUT) :: a
        integer,intent(IN) :: len

        integer :: ende ! Beyond ende, the list is sorted
                        ! Before ende, the list is a binary heap

        call heapify(a, len)

        ende = len

        do while (ende.gt.1)
          ! putting the root (aka top aka largest value) of heap at end
          call doSwap(a, len, ende, 1)

          ende = ende - 1
          ! 
          call siftDown(a, len, 1, ende)
          
        enddo

end subroutine heap_sort


subroutine heapify(a, len)
! Method creates a binary heap from an unsorted list
  use mcnp_global

        real(dknd),dimension(1:len,1:2),intent(INOUT) :: a
        integer,intent(IN) :: len

        integer :: start

        start = len / 2 ! last parent node; note indexing is from 1

        do while (start.ge.1)
          call siftDown(a, len, start, len)
          start = start - 1
        enddo

end subroutine heapify


subroutine siftDown(a, len, start, ende)
! siftDown compares a parent with its two child and swaps
! with the larger child if either is greater than the parent
  use mcnp_global

        real(dknd),dimension(1:len,1:2),intent(INOUT) :: a
        integer,intent(IN) :: len, start, ende

        integer :: root, child, swap

        root = start

        do while ( (root * 2).le.ende)
          child = root * 2
          swap = root

          ! if first child is larger than the parent
          if (a(swap,1).lt.a(child,1)) then
            swap = child
          endif

          ! if 2nd child exists and 2nd child is larger than first child
          if ( ((child+1).le.ende).and.(a(swap,1).lt.a(child+1,1)) ) then
            swap = child + 1
          endif

          if (swap.ne.root) then
            call doSwap(a, len, root, swap)
            root = swap
          else
            root = ende+1
          endif

        enddo

end subroutine siftDown


subroutine doSwap(a, len, i, j)
! Method swaps the elements in array a at positions i and j.
  use mcnp_global

        integer,intent(IN) :: len, i, j
        real(dknd),dimension(1:len,1:2),intent(INOUT) :: a

        real(dknd),dimension(1:2) :: temp

        temp(1:2) = a(i,1:2)
        a(i,1:2) = a(j,1:2)
        a(j,1:2) = temp

end subroutine doSwap 


subroutine print_debug
! subroutine stores debug info in an array, and write the array to a file
!  after every 10000 particles.
  use source_data

        ! Debugging stuff
        real(dknd),dimension(1:10000,1:4) :: source_debug_array
        save source_debug_array
 
        ! Write information for debugging where source particles are started.
        npart_write = npart_write + 1
        source_debug_array(npart_write,1) = xxx
        source_debug_array(npart_write,2) = yyy
        source_debug_array(npart_write,3) = zzz
        source_debug_array(npart_write,4) = wgt
        if (npart_write.eq.10000) then
  
          write(*,*) 'writing to source debug file.'
          OPEN(UNIT=57, FILE="source_debug", ACCESS="APPEND")!, STATUS="REPLACE")
          do i=1,10000
            write(57,*) source_debug_array(i,1:4)
          enddo
          
          CLOSE(57)
          npart_write = 0
        endif

end subroutine print_debug
