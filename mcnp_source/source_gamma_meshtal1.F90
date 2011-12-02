!+ $Id: source.F90,v 1.1 2004/03/20 00:31:52 jsweezy Exp $
! Copyright LANL/UC/DOE - see file COPYRIGHT_INFO

subroutine source
  ! R2S mesh version
  ! sampling from gamma source file with cartesian coordinates
  ! 20110301 DL
  ! modified version for repeated structures
  ! (compare R2S cell version)
  ! 20110314 DL
  ! modified version for new file format (to deal with real FLUX
  ! values in FISPACT): -1 for no gammas; 24 cum. gamma groups
  ! values have been written with format "%1.3E " (C/C++)
  ! use idum(4) to select gammas.t##
  ! 20110323 DL
  ! check that gamma originates from material (or activated material)
  !
  ! dummy subroutine.  aborts job if source subroutine is missing.
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
  real(dknd),dimension(1000000,24) :: spectrum
  real(dknd),dimension(25) :: ener_phot
  character name*10,pf*2
  save tvol,ikffl, iflnum
! 
!-----------------------------------------------------------
!	Read Xmin,Xmax,Ymin,Ymax,Zmin,Zmax from RDUM ARRAY
!       and number of intervals in X, Y, Z from IDUM ARRAY.
!       Set bins for photon energy groups.
!-----------------------------------------------------------
!
  xmin=rdum(1)
  xmax=rdum(2)
  ymin=rdum(3)
  ymax=rdum(4)
  zmin=rdum(5)
  zmax=rdum(6)
  i_int=idum(1)
  j_int=idum(2)
  k_int=idum(3)

  data ener_phot/0.0,0.01,0.02,0.05,0.1,0.2,0.3,0.4,0.6,0.8,1.0, &
       1.22,1.44,1.66,2.0,2.5,3.0,4.0,5.0,6.5,8.0,10.0,12.0,14.0,20.0/
!        
!-----------------------------------------------------------------------------
!  In the first history (ikffl) read 'gammas' file. ikffl under MPI works ?
!-----------------------------------------------------------------------------
!
        iflnum = idum(4)
        ikffl=ikffl+1
        if (ikffl.eq.1) then

          close(50)
          write(pf,'(i2)') iflnum
          name='gammas.t'//trim(adjustl(pf))
          open(unit=50,form='formatted',file=name)

          do i=1,1000000
            do j=1,24
              spectrum(i,j)=0.0
            enddo
          enddo
        
          i=1
          ii=0
          do
            read(50,'(ES10.3)',advance="no",iostat=stat) spectrum(i,1)
!            write(*,'(ES11.5)') spectrum(i,1)
            if (spectrum(i,1) .lt. 0) then
              backspace(50)
              read(50,'(ES10.3)',advance="yes",iostat=stat) spectrum(i,1)
              spectrum(i,24)=0.0
            else
              backspace(50)
              read(50,'(24ES10.3)',advance="yes",iostat=stat) (spectrum(i,j),j=1,24)
              ii=ii+1
            endif                        
            if (stat /= 0) exit
            i=i+1
          enddo

          close(50)
          ! do we need rdum(7) at this stage of the routine
          tvol=(xmax-xmin)*(ymax-ymin)*(zmax-zmin)*rdum(7)
                    
          write(*,*) 'Reading gammas file completed!'
          write(*,*) 'Volume used in WGT is ',tvol

        endif

!        
!------------------------------------------------------------------------------
!  Sample homogeneously in the whole volume of the mesh tally. 
!  If void was hit, resample.
!------------------------------------------------------------------------------
!

10      r1=rang()
        r2=rang()
        r3=rang()
! c program adressing:
!  adr=z+y*k_ints+x*j_ints*k_ints+i_mat*i_ints*j_ints*k_ints;
        ii=int(r1*i_int)
        jj=int(r2*j_int)
        kk=int(r3*k_int)
        i=kk+jj*k_int+ii*j_int*k_int+1
!        write(*,'(4i)') ii,jj,kk,i
        if (spectrum(i,24).eq.0.0) goto 10

        xxx=xmin+r1*(xmax-xmin)
        yyy=ymin+r2*(ymax-ymin)
        zzz=zmin+r3*(zmax-zmin)
        lev = 0

!     write(*,'(3f)') xxx,yyy,zzz
!-----------------------------------------------------------------------
!     Determine cell of the source point; if it is a void cell, resample
!-----------------------------------------------------------------------
! mod. 20110301 DL
! check for multi-level cells and identify lowest level cell number
!
  j=1
  if (junf==0) then
          ! there is no repeated structure in the geometry. Check simply.
          do m=1,nlse
            icl_tmp = lse(klse+m)
            jsu = 0
            call chkcel(icl_tmp,2,j)
            if (j==0) then
! write (6,*) 'Source: junf=0 found in current list of cells', icl_tmp
            icl = icl_tmp
            goto 30
            endif
          end do
          do icl_tmp=1,mxa
            jsu = 0
            call chkcel(icl_tmp,2,j)
            if (j==0) then 
! write (6,*) 'Source: junf=0 found new cell', icl_tmp
            goto 25
            endif
          end do
!          icl=icl_tmp
  else
          ! there is repeated structure. Check for correct level.
! write (6,*) 'Source: junf<>0' 
          do m=1,nlse 
            icl_tmp = lse(klse+m)
            if( jun(icl_tmp)/=0 )  cycle 
            jsu = 0
            call chkcel(icl_tmp,2,j)
            if( j==0 ) then
              icl = icl_tmp
              if( mfl(1,icl_tmp)==0 )  goto 30
! write (6,*) 'Source: old source cell found, ready for call LEVCEL',icl
              call levcel
              goto 30
            endif
          end do 
          do icl_tmp=1,mxa
            if( jun(icl_tmp)/=0 )  cycle 
            jsu = 0
            call chkcel(icl_tmp,2,j)
            if( j==0 )  go to 25
          end do
  endif
  goto 10

25  continue
    icl = icl_tmp
! write (6,*) 'Source: (25) found cell no.',icl
    nlse = nlse+1
    lse(klse+nlse) = icl
    if( junf==0 ) goto 30
    if( mfl(1,icl)==0 ) goto 30 
! write (6,*) 'Source: (25) new source cell found, ready for call LEVCEL'
    call levcel
  
30  continue

! Cell for source position found (icl)!

    if (mat(icl) == 0) goto 10
!        
!------------------------------------------------------------------------------
!  Use cumulative values in spectrum array for given i to sample the energy
!  of the photon.
!------------------------------------------------------------------------------
!

        r4=rang()*spectrum(i,24)
!        write (*,'(es10.3)') r4
!        write (*,'(24es10.3)') (spectrum(i,j),j=1,24)
!        write (*,'(25es10.3)') (ener_phot(j),j=1,25)
        do j=1,24
          if (r4.le.spectrum(i,j)) exit
        enddo

        r5=rang()
        erg=ener_phot(j)+r5*(ener_phot(j+1)-ener_phot(j))

!        write(*,*) xxx,yyy,zzz,erg                             

!        
!------------------------------------------------------------------------------
!  Determine weight.
!  Intensities (neutron fluence in given meshtal voxel)
!  spectrum (total number of produced gammas, if neutron fluence is 1 everywhere)
!  tvol (nonzero cells/all cells  factor).
!  IPT=2 for photons. JSU=TME=0 works well.
!------------------------------------------------------------------------------
!

  wgt=spectrum(i,24)*tvol

  ipt=2
  jsu=0
  tme=0
  return
end subroutine source

