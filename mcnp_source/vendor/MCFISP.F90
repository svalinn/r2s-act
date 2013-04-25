subroutine source
!
! ********************************************************
! * This source routine is for decay gamma transport     *
! * calculations for T-426 shutdown dose rate experiment *
! * dose rate calculation.                               *
! *                                                      *
! * MCNP4C                 Yixue Chen   December 2000    *
! ********************************************************
!
!........................................................
!........................................................
!
! ----------------------------------------------------------------------
! at entrance, a random set of uuu,vvv,www has been defined. the
! following variables must be defined within the subroutine:
! xxx,yyy,zzz,icl,jsu,erg,wgt,tme and possibly uuu,vvv,www.
!-----------------------------------------------------------------------
        save tgamma,egroup,srccl,ngamma,volume,factor,tvol
        real xmin,xmax,ymin,ymax,zmin,zmax,terg,factor,tvol,tvolflux
        real tgamma(2000),egroup(25),ngamma(50000),energy(25), &
                normerg(25),cmlerg(25),volume(2000)
        character temp*80
        integer npoint,num,srccl(2000)
!
!***********************************************************
! READ DATA FROM MCNP INPUT FILE AND G_SOURCE FILE
!***********************************************************
!
!-----------------------------------------------------------
! Read rmin,rmax,Zmin,Zmax from RDUM ARRAY.
!-----------------------------------------------------------
        xmin=rdum(1)
        xmax=rdum(2)
        ymin=rdum(3)
        ymax=rdum(4)
        zmin=rdum(5)
        zmax=rdum(6)
!--------------------------------------------------
!       Read the numbers of total source cells.
!--------------------------------------------------
        num=idum(1)
!--------------------------------------------------------
!       Read info of the source cell number from g_source
!--------------------------------------------------------
!--------read the source cell number-----------
        read(50,60,end=15)temp
        read(50,fmt=70)(srccl(i),i=1,num)
   70   format(8(i5,1x))
!--------------------------------------------------------
!------ read a blank line and a heading line-----------
        read(50,60)temp
!------ read the volume of the source cell-----------------
        read(50,fmt=80)(volume(i),i=1,num)
!----------------------
!       read a blank line and a heading line
        read(50,*)
        read(50,60)temp
!-----------------------
!       read the photon flux of the source cells.
        read(50,fmt=80)(tgamma(i),i=1,num)
   80    format(5(e11.5,1x))
!--------------------------------------------
!       read a blank line and a heading line
        read(50,*)
        read(50,60) temp
!------------ read energy group------------read(50,100)(egroup(i),i=1,25)
  100   format(7(f5.2,2x))
!------ read photon spectra of all the source cells.
        read(50,*)
        read(50,60) temp
   60   format(a80)
        nvalue=num*25
        read(50,110)(ngamma(i),i=1,nvalue)
  110   format(5(e11.5,1x))

!------------------------------------------------------------------
!      Uniform sampling of a large volume enclosing all source cell
!      limited by xmin,xmax, ymin,ymax zmin,zmax
!-------------------------------------------------------------------
   15   continue
        r1=rang()
        xxx=xmin+r1*(xmax-xmin)
        r2=rang()
        yyy=ymin+r2*(ymax-ymin)
        r3=rang()
        zzz=zmin+r3*(zmax-zmin)
!-----------------------------------------------------------------------
!      Check the point is within a source cell or not, then get icl value
!-----------------------------------------------------------------------jnum=0
        do 20, i=1, num
          jnum=i
          item=namchg(1,srccl(i))
          call chkcel(item,2,j)
          if (j.eq.0) goto 30
   20   enddo
        goto 15
   30   continue
        icl=item
        numcl=jnum
!---------------------------------------------------------------------------
!      Get the weight of the particle according to the photon flux
!      of the cell icl. Then multiply a factor so as to normalizie
!      the tallies to one source particle*weight.
!---------------------------------------------------------------------------
!      Calculate the factor to normalize the tallies
!      factor=volume/volume*flux
!----------------------------------------------------tvol=0.0
        tvolflux=0.0
        do 81,i=1,num
          tvol=tvol+volume(i)
          tvolflux=tvolflux+volume(i)*tgamma(i)
   81   enddo
        factor=tvol/tvolflux
!----------------------------------------------------
!      Calcultate the weight of the source cell icl
!
        wgt=tgamma(numcl)*tvol
        if (wgt .eq. 0.0) then
          write(32, 311) srccl(numcl)
          goto 15
        endif
  311   format ("Warning: the intensity of source cell ",i5," is 0.0")
!-------------------------------------------------------------------------------
!      Calculate the erg value.
!      First locate the erg spectra position of the source cell icl according
!      to the variable numcl in the array ngamma. Then read its spectra from
!      ngamma to array energy. So the erg is obtained.
!-------------------------------------------------------------------------------
        npoint=0
        npoint=(numcl-1)*25
        terg=0.0
        do 120, i=1,25
          energy(i)=ngamma(i+npoint)
          if(i.eq.1) then
            cmlerg(i)=0.0
            goto 115
          endif
          cmlerg(i)=energy(i)+cmlerg(i-1)
  115     continue
          terg=terg+energy(i)
  120   enddo
        do 130,i=1,25
          normerg(i)=cmlerg(i)/terg
  130   enddo
        r5=rang()
        do 140,i=1,25
          ipoint=i
          if(r5.lt.normerg(i)) goto 150
  140   enddo
  150   continue
        r6=rang()
        erg=egroup(ipoint-1)+r6*(egroup(ipoint)-egroup(ipoint-1))
!----------------------------------------------------
        jsu=0
        tme=0.0
        return
        end

