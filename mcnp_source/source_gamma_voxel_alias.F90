!+ $Id: source.F90,v 1.1 2004/03/20 00:31:52 jsweezy Exp $
! Copyright LANL/UC/DOE - see file COPYRIGHT_INFO

! This source file implements photon source sampling via alias table 
!  sampling of voxels listed in the external file 'gammas'.
! - - - - - - NOTES ON MODIFICATIONS - - - - - - -
! Edits have been made by Eric Relson with CNERG goals in mind.
! Major changes:
! -Uses direct discrete sampling of voxels, rather than sampling space
!  uniformly, or using alias table sampling.
! -Biasing of voxel selection is possible.
! -Changed energy sampling to use alias sampling. Correspondingly, the gammas
!  file now stores an alias table for each voxel. CPU time benefits are small.
!  Downside is that gammas file is ~50% larger, and spectrum array takes 3x as
!  much memory.
! Other changes:
! -Scan 100 materials in multiple spots rather than 150 some places, 100
!  elsewhere
! -Supports custom source energy bins. Line 6 of the gammas file can
!  optionally begin with 'e' and the number of energy groups, followed
!  by the energy bin boundary energies.
! -Increase size of 'line' from 150 to 3000.
! -Rejection based on non-activated material is disabled

subroutine source
  ! adapted from dummy source.F90 file.
  ! if nsr=0, subroutine source must be furnished by the user.
  ! at entrance, a random set of uuu,vvv,www has been defined.  the
  ! following variables must be defined within the subroutine:
  ! xxx,yyy,zzz,icl,jsu,erg,wgt,tme and possibly ipt,uuu,vvv,www.
  ! subroutine srcdx may also be needed.
  use mcnp_global
  use mcnp_debug
  use mcnp_random
  implicit real(dknd) (a-h,o-z)
        ! Voxel alias table variables
        real(dknd) :: sourceSum, n_inv 
        real(dknd),dimension(:,:), allocatable :: bins
        real(dknd),dimension(:),allocatable :: pairsProbabilities
        integer(i4knd),dimension(:,:), allocatable :: pairs
        integer :: voxel, alias_bin
        ! Biasing variables
        integer :: bias
        real(dknd) :: bias_probability_sum
        character :: read_bias
        ! Energy bins variables
        real(dknd),dimension(:,:), allocatable :: spectrum
        real(dknd),dimension(:),allocatable :: my_ener_phot
        integer :: n_ener_grps
        ! Other variables
        integer stat
        integer :: i_ints,j_ints,k_ints,n_mesh_cells,n_active_mat,&
             n_source_cells
        real,dimension(:),allocatable:: i_bins,j_bins,k_bins
        integer,dimension(100) :: active_mat
        ! Saved variables will be unchanged next time source is called
        save spectrum,i_ints,j_ints,k_ints,n_active_mat,n_ener_grps, &
             i_bins,j_bins,k_bins,active_mat,my_ener_phot,tvol,ikffl,pairs, &
             pairsProbabilities, n_mesh_cells, bias, bias_probability_sum

        ! IMPORTANT - make sure this is a long enough string.
        character*3000 :: line
        character :: read_ergs
                                                        
!        
!------------------------------------------------------------------------------
!       In the first history (ikffl) read 'gammas' file. ikffl under MPI works ?
!------------------------------------------------------------------------------
!
        ikffl=ikffl+1
        if (ikffl.eq.1) then ! if first particle ...
                   
          do i=1,100
            active_mat(i)=0
          enddo

          close(50)
          open(unit=50,form='formatted',file='gammas')

          ! read first line
          read(50,*) i_ints,j_ints,k_ints
          n_mesh_cells = i_ints * j_ints * k_ints

          ALLOCATE(i_bins(1:i_ints+1))
          ALLOCATE(j_bins(1:j_ints+1))
          ALLOCATE(k_bins(1:k_ints+1))

          ! read lines 2,3,4,5
          read(50,*) (i_bins(i),i=1,i_ints+1)
          read(50,*) (j_bins(i),i=1,j_ints+1)
          read(50,*) (k_bins(i),i=1,k_ints+1)
          read(50,'(A)') line
          read(line,*,end=887) (active_mat(i),i=1,100)
887       continue

          ! counting number of activated materials specified
          do i=1,100
            if (active_mat(i)==0) exit
          enddo
          n_active_mat=i-1

          ! We read in the energy bins if there is an 'e' starting the next line
          ! Otherwise we reset this line ('record') and go on to reading the
          !  bias information and gamma spectrum, and use default energies.
          read(50,'(A1)',advance='NO') read_ergs ! reads first character
          if (read_ergs.eq.'e') then
            read(50,*) n_ener_grps ! reads an integer
            backspace(50) ! dirty hack since read(50,*,advance='NO') is invalid
            ALLOCATE(my_ener_phot(1:n_ener_grps+1))
            read(50,*,end=888) read_ergs, n_erg_grps, &
                        (my_ener_phot(i),i=1,n_ener_grps+1)
888         continue

            write(*,*) "The following custom energy bins are being used:"
            DO i=1,n_ener_grps
              write(*,'(2es11.3)') my_ener_phot(i), my_ener_phot(i+1)
            ENDDO
            
          else ! use default energy groups
            backspace(50) ! we reset the file to the beginning of the record we
                            ! read into 'line'.
            n_ener_grps = 42
            ALLOCATE(my_ener_phot(1:n_ener_grps+1))
            my_ener_phot=(/0.0,0.01,0.02,0.03,0.045,0.06,0.07,0.075,0.1,0.15, &
              0.2,0.3,0.4,0.45,0.51,0.512,0.6,0.7,0.8,1.0,1.33,1.34,1.5, &
              1.66,2.0,2.5,3.0,3.5,4.0,4.5,5.0,5.5,6.0,6.5,7.0,7.5,8.0, &
              10.0,12.0,14.0,20.0,30.0,50.0/)
          endif

          ! We look for a 'b' starting the next line.
          ! If not found, we reset this line ('record') and proceed to read
          !  spectrum information
          bias = 0
          read(50,'(A1)',advance='NO') read_bias ! reads first character
          if (read_bias.eq.'b') then
            ! We set bias to 1 and use it both for conditionals and as
            !  an offset value for array indices for the spectrum array
            bias = 1
            write(*,*) "Biased sampling of source voxels is being used."

          else ! no biasing was used
            backspace(50) ! we reset the file to the beginning of the record we
                            ! read into 'line'.
          endif

          ! Prepare to read in spectrum information
          ! set the spectrum array to: # of mesh cells * # energy groups
          ALLOCATE(spectrum(1:n_mesh_cells, 1 + bias + 3 * n_ener_grps))
          ! initiallizing spectrum array
          do i=1,n_mesh_cells
            do j=1,1 + bias + 3 * n_ener_grps
              spectrum(i,j)=0.0
            enddo
          enddo
       
          ! reading in source strength and alias table for each voxel 
          i=1
          do
            read(50,*,iostat=stat) (spectrum(i,j),j=1, 1 + bias + 3 * n_ener_grps)
            if (stat /= 0) exit ! exit the do loop
            i=i+1
          enddo

          close(50)

          write(*,*) 'Reading gammas file completed!'

          !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
          ! Generate Alias Table
          !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
          ! Note that the first entry for each voxel in 'gammas' is
          ! a relative probability of that voxel being the source location

          ! Sum up a normalization factor
          sourceSum = 0.0_rknd
          n_source_cells = 0
          do i=1,n_mesh_cells
            sourceSum = sourceSum + spectrum(i,1)
            if (spectrum(i,1).gt.0) n_source_cells = n_source_cells + 1
          enddo

          write(*,*) "sourceSum:", sourceSum, "n_source_cells:", n_source_cells

          ALLOCATE(bins(1:n_mesh_cells,1:2))

          ! make the unsorted list of bins
          bias_probability_sum = 0
          do i=1,n_mesh_cells
            ! the average bin(i,1) value assigned is n_inv
            ! bins(i,1) = spectrum(i,1) / sourceSum * n_mesh_cells
            ! bins(i,1) = spectrum(i,1) / n_source_cells !* &
            bins(i,1) = spectrum(i,1) / sourceSum
!                    (real(n_mesh_cells)/real(n_source_cells))
            bins(i,2) = i
            if (bias.eq.1) then
              bias_probability_sum = & 
                                bias_probability_sum + bins(i,1) * spectrum(i,2)
            endif
          enddo

          ! if bias values were found, update the bin(i,1) values for biasing
          !  and then update the bias values so that they are now particle wgt
          if (bias.eq.1) then
            do i=1,n_mesh_cells
              bins(i,1) = bins(i,1) * spectrum(i,2) / bias_probability_sum
              spectrum(i,2) = bias_probability_sum / spectrum(i,2)
            enddo
          endif

          ! do an initial sort
          call heap_sort(bins, n_mesh_cells)

          ! With each pass through the following loop, we ignore another bin
          !  (the j'th bin) by setting its probability vaue to -1.
          ! pairs stores the two possible values for each alias table bin
          ! pairsProbabilities stores the probability of the first value in the
          !  alias table bin being used
          ALLOCATE(pairs(1:n_mesh_cells, 1:2))
          ALLOCATE(pairsProbabilities(1:n_mesh_cells))
          n_inv = (1._dknd/n_mesh_cells)
          
          do j=1,n_mesh_cells

            ! resort last bin
            call sort_for_alias_table(bins, n_mesh_cells)

            ! Lowest bin is less than 1/n, and thus needs a second bin with
            !  which to fill the alias bin.
            if ( bins(j,1).lt.n_inv ) then
              pairsProbabilities(j) = bins(j,1) * n_mesh_cells
              pairs(j,1) = bins(j,2)

              ! don't need to store second probability
              pairs(j,2) = bins(n_mesh_cells,2)

              bins(n_mesh_cells,1) = bins(n_mesh_cells,1) - (n_inv - bins(j,1))
              
            ! Lowest bin should never have a probablity > 1/n, I think?
            else if (bins(j,1).gt.n_inv) then
              !write(*,*) "Problem generating alias table. See source.F90"
              pairs(j,1) = bins(j,2)
              pairs(j,2) = 0
              pairsProbabilities(j) = 1.0

              bins(j,1) = bins(j,1) - n_inv

            ! Lowest bin is exactly 1/n
            else ! (bins(j,1).eq.1) ! single possible value for given bin
              pairsProbabilities(j) = 1.0
              pairs(j,1) = bins(j,2)
              pairs(j,2) = 0

            end if

            bins(j,1) = -1.3 ! Immunity to sorting for already-used bins
!            j = j + 1

          enddo

          write(*,*) 'Alias table of source voxels generated!'

        endif

!
!---------------------------------------------------------------------------------
!        Sample in the volume of the mesh tally.
!       The same number of hits homogeneously in volume.
!       ~Weight is adjusted, apparently.
!---------------------------------------------------------------------------------
!

        ! Sampling the alias table
10      alias_bin = INT(rang() * n_mesh_cells) + 1
        if (rang().lt.pairsProbabilities(alias_bin)) then
          voxel = pairs(alias_bin,1) - 1
        else
          voxel = pairs(alias_bin,2) - 1
        endif
       
        ! We -1'd the value of voxel so the next three lines are easy
        ii= voxel / (k_ints*j_ints) + 1
        jj= mod(voxel, k_ints*j_ints) / k_ints + 1
        kk= mod(mod(voxel, k_ints*j_ints), k_ints) + 1

        voxel = voxel + 1
 
!       Sample random spot within the voxel
        xxx=i_bins(ii)+rang()*(i_bins(ii+1)-i_bins(ii))
        yyy=j_bins(jj)+rang()*(j_bins(jj+1)-j_bins(jj))
        zzz=k_bins(kk)+rang()*(k_bins(kk+1)-k_bins(kk))

! c program adressing (but starts with 0, in fortran not possible, therefore ii-1 .. and final result +1):
!   adr=z+y*k_ints+x*j_ints*k_ints+i_mat*i_ints*j_ints*k_ints;

        i=(kk-1)+(jj-1)*k_ints+(ii-1)*j_ints*k_ints+1
      
!        OPEN(UNIT=57, FILE="source_debug2", ACCESS="APPEND") !, STATUS="REPLACE")
!        write(57,*) alias_bin, voxel, i, ii
!        CLOSE(57)
        
        ! sample a new position if voxel has zero source strength
        if (spectrum(voxel,1).eq.0) goto 10


!
!-------------------------------------------------------------------------------
!       Sample the alias table of energy bins for the selected voxel. 
!-------------------------------------------------------------------------------
!
        
        ! choose energy bins alias table indice   
        r4 = INT(rang() * n_ener_grps) * 3 

        ! three values are associated with the alias bin:
        ! -probability of the first secondary bin
        ! -energy bin # of the first secondary bin
        ! -energy bin # of the second secondary bin
        ! second rand chooses first or second bin in alias table bin
        if ( rang().le.spectrum(i, INT(1 + bias + r4     + 1)) ) then
          j = INT( spectrum(i, INT(1 + bias + r4 + 1 + 1)) )
        else
          j = INT( spectrum(i, INT(1 + bias + r4 + 2 + 1)) )
        endif

        erg=my_ener_phot(j)+(1-rang())*(my_ener_phot(j+1)-my_ener_phot(j))

!        
!-------------------------------------------------------------------------------
!        Determine weight.
!       IPT=2 for photons. JSU=TME=0 works well.
!-------------------------------------------------------------------------------
!

        ! wgt=spectrum(i,1) 
        if (bias.eq.1) then
          !wgt = bias_probability_sum / spectrum(voxel,2)
          wgt = spectrum(voxel,2)
        else
          wgt=1.0
        endif
        ! we calculate the weight based on the biasing

! Write information for debugging where source particles are started.
!        OPEN(UNIT=57, FILE="source_debug", ACCESS="APPEND")!, STATUS="REPLACE")
!        write(57,*) xxx, yyy, zzz, wgt, i, voxel, jj
!        CLOSE(57)

        !        write(57,*) xxx, yyy, zzz, wgt, alias_bin, voxel, ii
        ipt=2 ! particle type: 2 = photon
        jsu=0
        tme=0

! The following is exactly as it was received from KIT
!        
!-------------------------------------------------------------------------------
!        Determine in which cell you are starting. Subroutine is copied from MCNP code (sourcb.F90). 
!       ICL and JUNF should be set to 0 for this part of the code to work.
!-------------------------------------------------------------------------------
!
        icl=0
        junf=0
        
  ! default for cel:  find the cell that contains xyz.
470 continue
  if( icl==0 ) then
    if( junf==0 ) then ! if repeated structures are NOT used...
      do m=1,nlse 
        icl = lse(klse+m)
        call chkcel(icl,2,j)
        if( j==0 )  goto 543
      end do 
      do icl_tmp=1,mxa
        icl = icl_tmp
        call chkcel(icl,2,j)
        if( j==0 )  goto 540
      end do
      icl = icl_tmp
    else ! else, repeated structures are used
      do m=1,nlse 
        icl = lse(klse+m)
        if( jun(icl)/=0 )  cycle 
        call chkcel(icl,2,j)
        if( j==0 ) then
          if( mfl(1,icl)/=0 )  call levcel
          goto 543
        endif
      end do 
      do icl_tmp=1,mxa
        icl = icl_tmp
        if( jun(icl)/=0 )  cycle 
        call chkcel(icl,2,j)
        if( j==0 )  goto 540
      end do
      icl = icl_tmp
    endif
    call expirx(1,'sourcb','source point is not in any cell.')
    goto 543
540 continue
    nlse = nlse+1
    lse(klse+nlse) = icl
    if( junf==0 )  goto 543
    if( mfl(1,icl)==0 )  goto 543
    call levcel
  elseif( icl<0 ) then
    call levcel
  else
    if( krflg==0 )  goto 543
    call chkcel(icl,2,j)
    if( j/=0 ) call errprn(1,-1,0,zero,zero,' ',' ',&
      & 'the source point is not in the source cell.')
  endif
!        
!---------------------------------------------------------------------------------
!       ICL should be set correctly at this point, this means everything is set.
!---------------------------------------------------------------------------------
!
543 continue
    do i=1,n_active_mat
      !if (nmt(mat(icl)).eq.active_mat(i)) then
              return
      !endif
    enddo
!    write (*,'(i5,3es10.3,i5)') ikffl,xxx,yyy,zzz,nmt(mat(icl))
    goto 10

end subroutine source


! subroutine locates where to move the last bin in bins to,
! such that bins is presumably completely sorted again.
subroutine sort_for_alias_table(bins, length)
    use mcnp_global

    implicit none

    integer,intent(IN) :: length
    real(dknd),intent(INOUT),dimension(1:length,1:2) :: bins

    ! Method's variables
    integer :: cnt, i
    real(dknd),dimension(1,1:2) :: temp

    if (bins(length,1).lt.bins(length-1,1)) then
 
      ! The logic in this do loop may be problematic at 
      !  cnt = length or cnt = 1...
      do cnt=length,1,-1
        if (bins(length,1).GE.bins(cnt-1,1)) exit
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
    
          implicit none

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
    
          implicit none

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
    
          implicit none

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
    
          implicit none

          integer,intent(IN) :: len, i, j
          real(dknd),dimension(1:len,1:2),intent(INOUT) :: a

          real(dknd),dimension(1:2) :: temp

          temp(1:2) = a(i,1:2)
          a(i,1:2) = a(j,1:2)
          a(j,1:2) = temp

end subroutine doSwap 
