!

subroutine tet_sample(p1x,p2x,p3x,p4x,p1y,p2y,p3y,p4y,p1z,p2z,p3z,p4z)
! This subroutine receives the four points of a tetrahedron and sets
! xxx, yyy, zzz, to values corresponding to a uniformly sampled point
! within the tetrahedron.
! 
! Parameters
! -----------
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

      !if ((ss+tt+uu).le.1._rknd) then
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

end subroutine tet_sample
