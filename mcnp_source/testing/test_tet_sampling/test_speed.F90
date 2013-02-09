!+
! Whooo!
!
module methods

        use mcnp_global

        real(dknd) :: P1X,P2X,P3X,P4X,P1Y,P2Y,P3Y,P4Y,P1Z,P2Z,P3Z,P4Z

contains

subroutine time_sampling(n)
!
      !use mcnp_global
      !
      integer(i8knd), intent(in) :: n
      !
      ! integer :: t1s, t2s, cr, cm
      real(dknd) :: t1, t2
      integer(i8knd) :: i

      ! ! First initialize the system_clock
      ! CALL system_clock(count_rate=cr)
      ! CALL system_clock(count_max=cm)
      ! rate = REAL(cr)

      call CPU_TIME(t1)
      !call SYSTEM_CLOCK(t1s)

      do i=1,n
        call tet_sample(P1X,P2X,P3X,P4X,P1Y,P2Y,P3Y,P4Y,P1Z,P2Z,P3Z,P4Z)
        !write(*,*) xxx, yyy, zzz
      enddo

      call CPU_TIME(t2)
      !call SYSTEM_CLOCK(t2s)

      !write(*,*) "For n=", len , " cpu time of    ", t2-t1
      !write(*,*) "For ", len , " cpu time of    ", t2-t1, "heap sort in", th-t1
      !write(*,*) "For ", len , " system time of ", (t2s-t1s)/rate
      write(*,*) "For samples n=", n, "Time taken:", t2-t1

end subroutine time_sampling

end module methods


program benchmark

      !
      use methods
        integer :: i,j
        character :: letter
        character*30 :: commentline

        call RN_init_problem() ! init random number generated to defaults

        open(unit=50, form='formatted', file= "/filespace/groups/" // &
                "cnerg/users/relson/test_tetra_sampling/points.txt")

        ! skip comment lines
        ! Read and skip over comment lines
        do
          letter = " "
          read(50,'(A)') commentline
          read(commentline,*,end=976) letter
976       continue

          if (letter.ne.'#') then
            backspace(50)
            exit
          endif
        enddo

        do j=1,10
          write(*,*) "Arbitrary tetrahedron number", j
          ! Read point coordinates
          read(50,*) P1X,P1Y,P1Z, P2X,P2Y,P2Z, P3X,P3Y,P3Z, P4X,P4Y,P4Z

          !call gen_table(10000) 
          do i=1,8
              call time_sampling(10_i8knd**i)
          enddo
        enddo
        !call time_sampling()

        close(50)

end program benchmark
