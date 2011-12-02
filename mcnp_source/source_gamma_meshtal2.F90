!+ $Id: source.F90,v 1.1 2004/03/20 00:31:52 jsweezy Exp $
! Copyright LANL/UC/DOE - see file COPYRIGHT_INFO

! - - - - - - NOTES ON MODIFICATIONS - - - - - - -
! Edits have been made by Eric Relson with CNERG goals in mind.
! -Scan 150 materials in multiple spots rather than 150 some places, 100
! elsewhere
! -42 energy groups instead of 24; highlight 24 to see all instances of
! changes...
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
        real(dknd),dimension(1000000,42) :: spectrum
!        real(dknd),dimension(25) :: ener_phot ! 24 + 1 = 25
        real(dknd),dimension(43) :: ener_phot ! 42 + 1 = 43
        integer i_ints,j_ints,k_ints,n_active_mat
        real,dimension(100):: i_bins,j_bins,k_bins
        integer,dimension(100) :: active_mat
        save spectrum,ener_phot,i_ints,j_ints,k_ints,n_active_mat, &
             i_bins,j_bins,k_bins,active_mat,tvol,ikffl
        character*250 :: line

                                                        
!        
!----------------------------------------------------------------------------------------------------
!	In the first history (ikffl) read 'gammas' file. ikffl under MPI works ?
!----------------------------------------------------------------------------------------------------
!
        ikffl=ikffl+1
        if (ikffl.eq.1) then

! bins for photon energy groups.
!        data ener_phot/0.0,0.01,0.02,0.05,0.1,0.2,0.3,0.4,0.6,0.8,1.0, &
 !            1.22,1.44,1.66,2.0,2.5,3.0,4.0,5.0,6.5,8.0,10.0,12.0,14.0,20.0/
        data ener_phot/0.0,0.01,0.02,0.03,0.045,0.06,0.07,0.075,0.1,0.15, &
              0.2,0.3,0.4,0.45,0.51,0.512,0.6,0.7,0.8,1.0,1.33,1.34,1.5, &
              1.66,2.0,2.5,3.0,3.5,4.0,4.5,5.0,5.5,6.0,6.5,7.0,7.5,8.0, &
              10.0,12.0,14.0,20.0,30.0,50.0/
                   
          do i=1,100
            active_mat(i)=0
          enddo

          close(50)
          open(unit=50,form='formatted',file='gammas')
          read(50,*) i_ints,j_ints,k_ints
          read(50,*) (i_bins(i),i=1,i_ints+1)
          read(50,*) (j_bins(i),i=1,j_ints+1)
          read(50,*) (k_bins(i),i=1,k_ints+1)
          read(50,'(A)') line
          read(line,*,end=888) (active_mat(i),i=1,150)
   888    continue
          ! counting number of activated materials specified
          do i=1,150
            if (active_mat(i)==0) exit
          enddo
          n_active_mat=i-1

!          print*,i_ints,j_ints,k_ints
!          print*,(i_bins(i),i=1,i_ints+1)
!          print*,(j_bins(i),i=1,j_ints+1)
!          print*,(k_bins(i),i=1,k_ints+1)
!          print*,(active_mat(i),i=1,n_active_mat)
!          print*,n_active_mat

          ! initiallizing a spectrum array
          do i=1,1000000
            do j=1,42 ! 24
              spectrum(i,j)=0.0
            enddo
          enddo
       

          ! what is going on here??? reading in mesh values prolly
          i=1
          do
            read(50,'(24ES12.5)',iostat=stat) (spectrum(i,j),j=1,42) !24)
            if (stat /= 0) exit
!              write(*,'(i4,1x,24ES12.5)') i,(spectrum(i,j),j=1,24)
            i=i+1
          enddo

          close(50)

          write(*,*) 'Reading gammas file completed!'

        endif

!
!----------------------------------------------------------------------------------------------------
!	Sample in the volume of the mesh tally.
!       The same number of hits homogeneously in volume.
!       ~Weight is adjusted, apparently.
!----------------------------------------------------------------------------------------------------
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
        if (spectrum(i,48).eq.0) goto 10

!        print*,i_bins(1),i_bins(i_ints+1),i_bins(i_ints+1)-i_bins(1)
!        print*,j_bins(1),j_bins(j_ints+1),j_bins(j_ints+1)-j_bins(1)
!        print*,k_bins(1),k_bins(k_ints+1),k_bins(k_ints+1)-k_bins(1)
!        print*,ii,jj,kk,i


!
!----------------------------------------------------------------------------------------------------
!	Use cumulative values in spectrum array for given i to sample the energy of the photon.
!----------------------------------------------------------------------------------------------------
!

        r4=(1-rang())*spectrum(i,42) !24)

        do j=1, 42 !24
          if (r4.lt.spectrum(i,j)) exit
        enddo

        erg=ener_phot(j)+(1-rang())*(ener_phot(j+1)-ener_phot(j))

!        
!----------------------------------------------------------------------------------------------------
!	Determine weight. Intensities (neutron fluence in given meshtal voxel), spectrum (total number 
!       of produced gammas, if neutron fluence is 1 everywhere), tvol (nonzero cells/all cells  factor).
!       IPT=2 for photons. JSU=TME=0 works well.
!----------------------------------------------------------------------------------------------------
!

        wgt=spectrum(i,42) !24)


        ipt=2
        jsu=0
        tme=0
!        
!----------------------------------------------------------------------------------------------------
!	Determine in which cell you are starting. Subroutine is copied from MCNP code (sourcb.F90). 
!       ICL and JUNF should be set to 0 for this part of the code to work.
!----------------------------------------------------------------------------------------------------
!
        icl=0
        junf=0
        
  ! default for cel:  find the cell that contains xyz.
470 continue
  if( icl==0 ) then
    if( junf==0 ) then
      do m=1,nlse 
        icl = lse(klse+m)
        call chkcel(icl,2,j)
        if( j==0 )  goto 543
      end do 
      do icl_tmp=1,mxa
        icl = icl_tmp
        call chkcel(icl,2,j)
        if( j==0 )  go to 540
      end do
      icl = icl_tmp
    else
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
        if( j==0 )  go to 540
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
!----------------------------------------------------------------------------------------------------
!       ICL should be set correctly at this point, this means everything is set.
!----------------------------------------------------------------------------------------------------
!
543 continue
    do i=1,n_active_mat
      if (nmt(mat(icl)).eq.active_mat(i)) return
    enddo
!    write (*,'(i5,3es10.3,i5)') ikffl,xxx,yyy,zzz,nmt(mat(icl))
    goto 10

end subroutine source

