!+ $Id: source.F90,v 1.1 2004/03/20 00:31:52 jsweezy Exp $
! Copyright LANL/UC/DOE - see file COPYRIGHT_INFO

! - - - - - - NOTES ON MODIFICATIONS - - - - - - -
! Edits have been made by Eric Relson with CNERG goals in mind.
! -Scan 100 materials in multiple spots rather than 150 some places, 100
! elsewhere
! -Formerly: 42 energy groups instead of 24; highlight 24 to see all instances of
! changes...
! -Currently: up to 100 energy groups. Line 6 of the gammas_ener file should
! list the energy bin boundaries.
! -Increase size of 'line' from 150 to 3000.
!
! -removed tab characters


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
!        real(dknd),dimension(1000000,24) :: spectrum
        integer i_ints,j_ints,k_ints,n_mesh_cells,n_active_mat,n_ener_phot
        real,dimension(100):: i_bins,j_bins,k_bins
        integer,dimension(100) :: active_mat
        real,dimension(100) :: my_ener_phot !up to 100 energy groups (arbitrary)
        real(dknd),dimension(:,:), allocatable :: spectrum
        save spectrum,i_ints,j_ints,k_ints,n_active_mat,n_ener_phot, &
             i_bins,j_bins,k_bins,active_mat,my_ener_phot,tvol,ikffl                         
                ! IMPORTANT - make sure this is a long enough string.
        character*3000 :: line

                                                        
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

          do i=1,100
            my_ener_phot(i)=0
          enddo

          close(50)
          open(unit=50,form='formatted',file='gammas_ener')
          read(50,*) i_ints,j_ints,k_ints
          n_mesh_cells = i_ints * j_ints * k_ints

          read(50,*) (i_bins(i),i=1,i_ints+1)
          read(50,*) (j_bins(i),i=1,j_ints+1)
          read(50,*) (k_bins(i),i=1,k_ints+1)
          read(50,'(A)') line
          read(line,*,end=888) (active_mat(i),i=1,100)
          read(50,'(A)') line
          read(line,*,end=888) (my_ener_phot(i),i=1,1000)
   888    continue
          ! counting number of activated materials specified
          do i=1,100
            if (active_mat(i)==0) exit
          enddo
          n_active_mat=i-1

          do i=2,100
            if (my_ener_phot(i)==0) exit
          enddo
          ! -1 for value that is zero, -1 for x values -> x-1 bins defined
          n_ener_phot = i-1-1

          ! set the spectrum array to: # of mesh cells * # energy groups
          allocate(spectrum(n_mesh_cells,n_ener_phot))
          ! initiallizing spectrum array
          do i=1,n_mesh_cells
            do j=1,n_ener_phot !42 ! 24
              spectrum(i,j)=0.0
            enddo
          enddo
       

          ! what is going on here??? reading in mesh values prolly
                  ! 24ES12.5 means read in 24 #s, each 12 characters long,
                  !  in exponential form with non-zero leading char,
                  ! ... presumably includes a single space character.
          i=1
!          voxformat = '(' // n_mesh_cells_str //
          do
                        !read(50,'(24ES12.5)',iostat=stat) (spectrum(i,j),j=1,24) 
            read(50,*,iostat=stat) (spectrum(i,j),j=1,n_ener_phot) !24)
            if (stat /= 0) exit
!              write(*,'(i4,1x,24ES12.5)') i,(spectrum(i,j),j=1,24)
            i=i+1
          enddo

          close(50)

          write(*,*) 'Reading gammas_ener file completed!'

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
        if (spectrum(i,n_ener_phot).eq.0) goto 10


!
!---------------------------------------------------------------------------------
!        Use cumulative values in spectrum array for given i to sample the energy of the photon.
!---------------------------------------------------------------------------------
!
        
        r4=(1-rang())*spectrum(i,n_ener_phot) !42) !24)

        do j=1, n_ener_phot !42 !24
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

        wgt=spectrum(i,n_ener_phot) !42) !24)

        ipt=2
        jsu=0
        tme=0
!        
!---------------------------------------------------------------------------------
!        Determine in which cell you are starting. Subroutine is copied from MCNP code (sourcb.F90). 
!       ICL and JUNF should be set to 0 for this part of the code to work.
!---------------------------------------------------------------------------------
!
        icl=0
        junf=0
        
  ! default for cel:  find the cell that contains xyz.
470 continue
  if( icl==0 ) then
    if( junf==0 ) then ! if repeated structures are used...
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
      if (nmt(mat(icl)).eq.active_mat(i)) return
    enddo
!    write (*,'(i5,3es10.3,i5)') ikffl,xxx,yyy,zzz,nmt(mat(icl))
    goto 10

end subroutine source

