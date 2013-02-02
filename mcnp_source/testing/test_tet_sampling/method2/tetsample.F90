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

      real(dknd) :: ss, tt, uu, vv, mysum

      ss = log(rang())
      tt = log(rang())
      uu = log(rang())
      vv = log(rang())

      if ((ss+tt).gt.1._rknd) then
        ss = 1._rknd - ss
        tt = 1._rknd - tt
      endif

      mysum = ss + tt + uu + vv

      ss = ss / mysum
      tt = tt / mysum
      uu = uu / mysum
      vv = vv / mysum

      xxx = p1x*ss + p2x*tt + p3x*uu + p4x*vv
      yyy = p1y*ss + p2y*tt + p3y*uu + p4y*vv
      zzz = p1z*ss + p2z*tt + p3z*uu + p4z*vv

end subroutine tet_sample
