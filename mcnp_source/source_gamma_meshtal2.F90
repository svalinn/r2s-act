!+ $Id: source.F90,v 1.1 2004/03/20 00:31:52 jsweezy Exp $
! Copyright LANL/UC/DOE - see file COPYRIGHT_INFO

! - - - - - - NOTES ON MODIFICATIONS - - - - - - -
! Edits have been made by Eric Relson with CNERG goals in mind.
! -Scan 100 materials in multiple spots rather than 150 some places, 100
!  elsewhere
! -Supports custom source energy bins. Line 6 of the gammas_ener file can
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
        integer stat
        integer(i8knd) :: ikffl = 0
        real(dknd),dimension(:,:), allocatable :: spectrum
        real(dknd),dimension(:),allocatable :: my_ener_phot
        integer i_ints,j_ints,k_ints,n_mesh_cells,n_active_mat,n_ener_grps
        real,dimension(100):: i_bins,j_bins,k_bins
        integer,dimension(100) :: active_mat
        save spectrum,i_ints,j_ints,k_ints,n_active_mat,n_ener_grps, &
             i_bins,j_bins,k_bins,active_mat,my_ener_phot,tvol,ikffl                         
                ! IMPORTANT - make sure this is a long enough string.
        character*3000 :: line
        character :: read_ergs

                                                        
!        
!---------------------------------------------------------------------------------
!        In the first history (ikffl) read 'gammas' file. ikffl under MPI works ?
!---------------------------------------------------------------------------------
!
        ikffl=ikffl+1
        if (ikffl.eq.1) then

                   
          do i=1,100
            active_mat(i)=0
          enddo

          close(50)
          open(unit=50,form='formatted',file='gammas') ! 'gammas_ener')
          read(50,*) i_ints,j_ints,k_ints
          n_mesh_cells = i_ints * j_ints * k_ints

          read(50,*) (i_bins(i),i=1,i_ints+1)
          read(50,*) (j_bins(i),i=1,j_ints+1)
          read(50,*) (k_bins(i),i=1,k_ints+1)
          read(50,'(A)') line
          read(line,*,end=887) (active_mat(i),i=1,100)
   887    continue

          ! counting number of activated materials specified
          do i=1,100
            if (active_mat(i)==0) exit
          enddo
          n_active_mat=i-1

          ! We read in the energy bins if there is an 'e' starting the next line
          ! Otherwise we reset this line ('record') and go on to reading the
          !  gamma spectrum, and use default energies.
          read(50,'(A1)',advance='NO') read_ergs ! reads first character
          if (read_ergs.eq.'e') then
            read(50,*) n_ener_grps ! reads an integer
            backspace(50) ! dirty hack since read(50,*,advance='NO') is invalid
            ALLOCATE(my_ener_phot(1:n_ener_grps+1))
            read(50,*,end=888) read_ergs, n_erg_grps, &
                        (my_ener_phot(i),i=1,n_ener_grps+1)
   888      continue
            write(*,*) read_ergs, n_erg_grps

            write(*,*) "The following custom energy bins are being used:"
            DO i=1,n_ener_grps
              write(*,'(2es11.3)') my_ener_phot(i), my_ener_phot(i+1)
            ENDDO
            
          else ! use default energy groups
            backspace(50) ! we reset the file to the beginning of the record we
                            ! read into 'line'.
            n_ener_grps = 42
            ALLOCATE(my_ener_phot(1:42+1))
            my_ener_phot=(/0.001,0.01,0.02,0.03,0.045,0.06,0.07,0.075,0.1,0.15,&
              0.2,0.3,0.4,0.45,0.51,0.512,0.6,0.7,0.8,1.0,1.33,1.34,1.5, &
              1.66,2.0,2.5,3.0,3.5,4.0,4.5,5.0,5.5,6.0,6.5,7.0,7.5,8.0, &
              10.0,12.0,14.0,20.0,30.0,50.0/)
          endif

          ! set the spectrum array to: # of mesh cells * # energy groups
          allocate(spectrum(n_mesh_cells,n_ener_grps))
          ! initiallizing spectrum array
          do i=1,n_mesh_cells
            do j=1,n_ener_grps
              spectrum(i,j)=0.0
            enddo
          enddo
       

          ! reading in phtn source info from rest of the file
          i=1
          do
            read(50,*,iostat=stat) (spectrum(i,j),j=1,n_ener_grps)
            if (stat /= 0) exit ! exit the do loop
            i=i+1
          enddo

          close(50)

          write(*,*) 'Reading gammas file completed!'

        endif

!
!---------------------------------------------------------------------------------
!        Sample in the volume of the mesh tally.
!       The same number of hits homogeneously in volume.
!       ~Weight is adjusted, apparently.
!---------------------------------------------------------------------------------
!

10      xxx=i_bins(1)+rang()*(i_bins(i_ints+1)-i_bins(1))
        yyy=j_bins(1)+rang()*(j_bins(j_ints+1)-j_bins(1))
        zzz=k_bins(1)+rang()*(k_bins(k_ints+1)-k_bins(1))

        do ii=1,i_ints
          if (i_bins(ii).le.xxx.and.xxx.lt.i_bins(ii+1)) exit
        enddo
        do jj=1,j_ints
          if (j_bins(jj).le.yyy.and.yyy.lt.j_bins(jj+1)) exit
        enddo
        do kk=1,k_ints
          if (k_bins(kk).le.zzz.and.zzz.lt.k_bins(kk+1)) exit
        enddo

! c program adressing (but starts with 0, in fortran not possible, therefore ii-1 .. and final result +1):
!   adr=z+y*k_ints+x*j_ints*k_ints+i_mat*i_ints*j_ints*k_ints;

        i=(kk-1)+(jj-1)*k_ints+(ii-1)*j_ints*k_ints+1
!        if (spectrum(i,24).eq.0) goto 10
        if (spectrum(i,n_ener_grps).eq.0) goto 10


!
!---------------------------------------------------------------------------------
!        Use cumulative values in spectrum array for given i to sample the energy of the photon.
!---------------------------------------------------------------------------------
!
        
        r4=(1-rang())*spectrum(i,n_ener_grps) 

        do j=1, n_ener_grps 
          if (r4.lt.spectrum(i,j)) exit
        enddo

        erg=my_ener_phot(j)+(1-rang())*(my_ener_phot(j+1)-my_ener_phot(j))

!        
!---------------------------------------------------------------------------------
!        Determine weight. Intensities (neutron fluence in given meshtal voxel), spectrum (total number 
!       of produced gammas, if neutron fluence is 1 everywhere), tvol (nonzero cells/all cells  factor).
!       IPT=2 for photons. JSU=TME=0 works well.
!---------------------------------------------------------------------------------
!

        wgt=spectrum(i,n_ener_grps) 

        ipt=2 ! particle type: 2 = photon
        jsu=0 ! current surface
        tme=0 ! particle time
!        
!---------------------------------------------------------------------------------
!        Determine in which cell you are starting. Subroutine is copied from MCNP code (sourcb.F90). 
!       ICL and JUNF should be set to 0 for this part of the code to work.
!---------------------------------------------------------------------------------
!
        icl=0  ! current cell 
        junf=0 ! flag for repeated structures
        
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
      ! if (nmt(mat(icl)).eq.active_mat(i)) then
              return
      ! endif
    enddo
!    write (*,'(i5,3es10.3,i5)') ikffl,xxx,yyy,zzz,nmt(mat(icl))
    goto 10

end subroutine source

