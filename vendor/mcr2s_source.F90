
                       ! Copyright Culham Centre For Fusion Energy
! Modification for MCNP written by Andrew Davis
! 05/11/2010
! subroutine to be called by source.F90
! to ceate shutdown photons
! following variables must be defined within the subroutine:
! xxx,yyy,zzz,icl,jsu,erg,wgt,tme and possibly ipt,uuu,vvv,www.
! subroutine srcdx may also be needed.
subroutine mcr2s_source
use mcnp_global
use mcnp_debug
!implicit none
integer :: i,j,k,testb,item
! storage for cell, fill and universe
integer :: location(100,3), nummatch
double precision :: test,ergt,ergrn
double precision :: xmin,xmax,ymin,ymax,zmin,zmax,totvol
!!!!!!!!!!!!!!!!!!!!!!!!
!    always defined    !
  jsu=0
!    source is a cell  !
  ipt=2 
! source is photons    !
  tme=0
!   time independent   !
!!!!!!!!!!!!!!!!!!!!!!!!

! write(*,*) 'MCR2S Source'




! write(*,*) 'Call', nps

xmin=mcr2s_data(1,1)
xmax=mcr2s_data(idum(2),2)
ymin=mcr2s_data(1,3)
ymax=mcr2s_data(idum(2),4)
zmin=mcr2s_data(1,5)
zmax=mcr2s_data(idum(2),6)



! this is not the first time into the subroutine so
! no need to allocate arrays etc.

! write(*,*) nps

! 
100 continue

   lev=0


   test=rang()
   ergt=rang()
   ergrn=rang()

   xxx=xmin+rang()*(xmax-xmin)
   yyy=ymin+rang()*(ymax-ymin)
   zzz=zmin+rang()*(zmax-zmin)

! find out where xxx, yyy and zzz lie in the mesh
 
! determine the corrective factor to account for non-normalised
! probability

! which  means make the probability of being born in each
! pr(x)=1 rather than pr(x) =1/number of bins

! since distribution is uniform in x,y and z
! we must sum the volumes where s(i) is greater
! than 0, and introduce a multiplication factor
! which is vol(i)/total

! however this is done in the if (rereadflag section)

! determine the volume of the voxel

 do i = 1,idum(2)
   if(( xxx .gt. mcr2s_data(i,1)).and.( xxx .le. mcr2s_data(i,2)))then
     if(( yyy .gt. mcr2s_data(i,3)).and.( yyy .le. mcr2s_data(i,4))) then
       if(( zzz .gt. mcr2s_data(i,5)).and.( zzz .le. mcr2s_data(i,6)))then
          wgt=mcr2s_data(i,7)*(mcr2s_vol(idum(2)+1)/mcr2s_vol(i))
          EXIT
        endif
     endif
   endif
 enddo

 if(wgt.eq.0.0)then
  goto 100 
  ! abandon this photon
 endif

 4000 continue
icl=0

if(idum(3).eq.2)then

!  call mcr2s_uni_cell
!  call levcel
  call findlv

elseif(idum(3).eq.1)then
  jnum=0
  k=1
  do 20, j=1,mxa
    jnum=j
    testb=mcr2s_cell(i,k)
     if ((testb.eq.0).and.(k.eq.6)) then
      goto 100
     elseif((testb.eq.0).and.(k.lt.6)) then
      k=k+1
      goto 20
     endif
     item=namchg(1,testb)
      call chkcel(item,2,j)
       if (j.eq.0) then
        goto 30
       elseif ((j.ne.0).and.(k.lt.6)) then
        k=k+1
        goto 20
        write(*,*) 'not in this cell going to have to go through them all'
       elseif (k.eq.6) then
        goto 100
       endif
20   enddo
 goto 100
30   continue
!   write(*,*) icl

!   write(*,*) icl

   icl=item
   numcl=jnum

endif

if(icl.eq.0)then
 goto 100
endif


!check for the material of the cell
   if(ioid.ne.0) then
    continue
   elseif(mat(icl).eq.0)then
     goto 100
     ! we do not create photons in void
   endif
! if void then start process again.


! cell assigned and material checked

! this bit is an iterative subroutine to check
! what material a cell has, if it has a material of 0
! ie void, then it regenerates an xxx,yyy,zzz for 
! that voxel, and checks again, this is to cope with
! things like annular vacuum channels 
     
  if(mcr2s_data(i,7).lt.1e-24)then
       goto 100
       !source strength cutoff
  endif

! additional correction to weight to correct for the lowest energy group
! which is too low for mcnp to sample from

  wgt=wgt*(1.0-mcr2s_data(i,8))
!  write(*,*) i
! assign the energy of the particle
  if(ergt.le.mcr2s_data(i,8)) then
       goto 100
! energy too low to sample
!   write(*,*) i
   elseif(ergt.gt.mcr2s_data(i,8).and.ergt.le.mcr2s_data(i,9)) then
       erg=0.01+ergrn*(0.02-0.01)
   elseif(ergt.gt.mcr2s_data(i,9).and.ergt.le.mcr2s_data(i,10))then
       erg=0.02+ergrn*(0.05-0.02)
   elseif(ergt.gt.mcr2s_data(i,10).and.ergt.le.mcr2s_data(i,11))then
       erg=0.05+ergrn*(0.1-0.05) 
   elseif(ergt.gt.mcr2s_data(i,11).and.ergt.le.mcr2s_data(i,12))then
       erg=0.1+ergrn*(0.2-0.1) 
   elseif(ergt.gt.mcr2s_data(i,12).and.ergt.le.mcr2s_data(i,13))then
       erg=0.2+ergrn*(0.3-0.2) 
   elseif(ergt.gt.mcr2s_data(i,13).and.ergt.le.mcr2s_data(i,14))then
       erg=0.3+ergrn*(0.4-0.3)
   elseif(ergt.gt.mcr2s_data(i,14).and.ergt.le.mcr2s_data(i,15))then
       erg=0.4+ergrn*(0.6-0.4) 
   elseif(ergt.gt.mcr2s_data(i,15).and.ergt.le.mcr2s_data(i,16))then
       erg=0.6+ergrn*(0.8-0.6)
   elseif(ergt.gt.mcr2s_data(i,16).and.ergt.le.mcr2s_data(i,17))then
       erg=0.8+ergrn*(1.0-0.8)
   elseif(ergt.gt.mcr2s_data(i,17).and.ergt.le.mcr2s_data(i,18))then
       erg=1.0+ergrn*(1.22-1.0)
   elseif(ergt.gt.mcr2s_data(i,18).and.ergt.le.mcr2s_data(i,19))then
       erg=1.22+ergrn*(1.44-1.22)
   elseif(ergt.gt.mcr2s_data(i,19).and.ergt.le.mcr2s_data(i,20))then
       erg=1.44+ergrn*(1.66-1.44)
   elseif(ergt.gt.mcr2s_data(i,20).and.ergt.le.mcr2s_data(i,21))then
       erg=1.66+ergrn*(2.0-1.66)
   elseif(ergt.gt.mcr2s_data(i,21).and.ergt.le.mcr2s_data(i,22))then
       erg=2.0+ergrn*(2.5-2.0)
   elseif(ergt.gt.mcr2s_data(i,22).and.ergt.le.mcr2s_data(i,23))then
       erg=2.5+ergrn*(3.0-2.5)
   elseif(ergt.gt.mcr2s_data(i,23).and.ergt.le.mcr2s_data(i,24))then
       erg=3.0+ergrn*(4.0-3.0)
   elseif(ergt.gt.mcr2s_data(i,24).and.ergt.le.mcr2s_data(i,25))then
       erg=4.0+ergrn*(5.0-4.0)
   elseif(ergt.gt.mcr2s_data(i,25).and.ergt.le.mcr2s_data(i,26))then
       erg=5.0+ergrn*(6.5-5.0)
   elseif(ergt.gt.mcr2s_data(i,26).and.ergt.le.mcr2s_data(i,27))then
       erg=6.5+ergrn*(8.0-6.5) 
   elseif(ergt.gt.mcr2s_data(i,27).and.ergt.le.mcr2s_data(i,28))then
      erg=8.0+ergrn*(10.0-8.0)
   elseif(ergt.gt.mcr2s_data(i,28).and.ergt.le.mcr2s_data(i,29))then
      erg=10.0+ergrn*(12.0-10.0)
   elseif(ergt.gt.mcr2s_data(i,29).and.ergt.le.mcr2s_data(i,30))then
      erg=12.0+ergrn*(14.0-12.0)
   elseif(ergt.gt.mcr2s_data(i,30).and.ergt.le.mcr2s_data(i,31))then
      erg=14.0+ergrn*(24.0-14.0)
   elseif(ergt.gt.mcr2s_data(i,31))then 
!  if fails select another random number
     write(*,*) 'guru meditation - magic has happened'
     write(*,*) nps,ergt,i,mcr2s_data(i,7),mcr2s_data(i,31)
     goto 100
   endif

! all parameters defined


if(icl.gt.0)then 
 continue
else
 goto 100 
endif


if(idum(8).eq.1)then
 write(*,*) icl,ncl(icl),lev,ll,mat(icl)
endif


return

end subroutine mcr2s_source

