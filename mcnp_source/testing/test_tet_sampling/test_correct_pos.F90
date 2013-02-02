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

      !call CPU_TIME(t1)
      !call SYSTEM_CLOCK(t1s)

      do i=1,n
        call tet_sample(P1X,P2X,P3X,P4X,P1Y,P2Y,P3Y,P4Y,P1Z,P2Z,P3Z,P4Z)
        !write(*,*) xxx, yyy, zzz
        call print_points
      enddo

      !call CPU_TIME(t2)
      !call SYSTEM_CLOCK(t2s)

      !write(*,*) "For samples n=", n, "Time taken:", t2-t1

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

        do j=1,1
          write(*,*) "Arbitrary tetrahedron number", j
          ! Read point coordinates
          read(50,*) P1X,P1Y,P1Z, P2X,P2Y,P2Z, P3X,P3Y,P3Z, P4X,P4Y,P4Z

          !call gen_table(10000) 
        enddo
        
        OPEN(UNIT=57, FILE="source_points", ACCESS="APPEND", STATUS="REPLACE")
        write(57,*) P1X,P1Y,P1Z 
        write(57,*) P2X,P2Y,P2Z 
        write(57,*) P3X,P3Y,P3Z 
        write(57,*) P4X,P4Y,P4Z
        CLOSE(57)

        call time_sampling(5000_i8knd)

        close(50)

end program benchmark


subroutine print_points
! subroutine stores debug info in an array, and write the array to a file
!  after every 1000 particles.
  use source_data

        ! Array storing debug information
        real(dknd),dimension(1:1000,1:3) :: source_points_array
        save source_points_array
 
        ! Save information for debugging where source particles are started.
        npart_write = npart_write + 1
        source_points_array(npart_write,1) = xxx
        source_points_array(npart_write,2) = yyy
        source_points_array(npart_write,3) = zzz

        ! Write debug information for 10000 histories to file
        if (npart_write.eq.1000) then
  
          write(*,*) "writing to source points file, 'source_points'."
          OPEN(UNIT=57, FILE="source_points", ACCESS="APPEND")!, STATUS="REPLACE")
          do i=1,1000
            write(57,*) source_points_array(i,1:3)
          enddo
          
          CLOSE(57)
          npart_write = 0
        endif

end subroutine print_points
