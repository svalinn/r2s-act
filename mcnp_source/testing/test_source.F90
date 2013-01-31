!+
! This program runs a set of tests on the individual subroutines for a 
!  mesh-based photon source sampling routine in MCNP.
! In lieu of packaging a unit testing framework, current tests are ad-hoc
!  checks using conditionals.
!
module tests_mod
! Module contains all tests
        use mcnp_global
        use source_data
        integer :: testunitnum

contains 

! Beginning of test subroutines

subroutine test_read_custom_ergs
! Reads in values from 'test_ergs_list.txt' and matches them to expected values 
        integer :: n_grps = 42
        real(dknd),dimension(1:43) :: test_ener_phot
        real(dknd) :: a, b

        testunitnum = getUnit()
        OPEN(unit=testunitnum, form='formatted', file='test_ergs_list.txt')
        call read_custom_ergs(testunitnum)
        CLOSE(testunitnum)

        test_ener_phot = (/0.0,0.01,0.02,0.03,0.045,0.06,0.07,0.075,0.1,0.15, &
            0.2,0.3,0.4,0.45,0.51,0.512,0.6,0.7,0.8,1.0,1.33,1.34,1.5, &
            1.66,2.0,2.5,3.0,3.5,4.0,4.5,5.0,5.5,6.0,6.5,7.0,7.5,8.0, &
            10.0,12.0,14.0,20.0,30.0,50.0/)

        do i=1,n_grps+1
          !assert
          a = test_ener_phot(i)
          b = my_ener_phot(i)
          if (abs(a-b).gt.(1e-4*max(a,b))) then
            write(*,*) "Mismatch in custom energies!", test_ener_phot(i), &
                ' ', my_ener_phot(i)
            return
          endif
        enddo

        write(*,*) "test_custom_ergs: successfully read bins"

end subroutine test_read_custom_ergs


subroutine test_read_header
! Reads in multiple sets of 5 header lines from 'test_header.txt'.
! Tests that active_mat array is properly created
        testunitnum = getUnit()
        OPEN(unit=testunitnum, form='formatted', file='test_header.txt')

        ! Test 1: 5 entries in materials line; verify rest of array is zeros
        call read_header(testunitnum)
        if (active_mat(6).ne.0.or.active_mat(100).ne.0) then
          write(*,*) "ERROR - test_read_header test #1"
          return
        endif
        
        ! Because read_header is responsible for allocating these arrays,
        !  we need to deallocate them before the next test
        deallocate(i_bins)
        deallocate(j_bins)
        deallocate(k_bins)

        ! Test 2: 105 entries in materials line; read first 100
        call read_header(testunitnum)
        if (active_mat(6).ne.1.or.active_mat(100).ne.5) then
          write(*,*) "ERROR - test_read_header test #2"
          return
        endif

        CLOSE(testunitnum)

        write(*,*) "test_read_header: successfully tested"

end subroutine test_read_header


subroutine test_read_params
! Reads in several combinations of parameter specifications from the file
!  'test_params.txt'.
        
        integer :: cnt = 1

        testunitnum = getUnit()
        OPEN(unit=testunitnum, form='formatted', file='test_params.txt')

        do ! assertions
          ! Test: 'p u v'
          call read_params(testunitnum)
          if (bias.eq.0.and.samp_uni.eq.0.and.samp_vox.eq.1) then
            cnt = cnt + 1
          else 
            exit
          endif
          ! Test: 'p'
          call read_params(testunitnum)
          if (samp_vox.eq.0.and.mat_rej.eq.0.and.cumulative.eq.0) then
            cnt = cnt + 1
          else 
            exit
          endif
          ! Test: 'p v u b'
          call read_params(testunitnum)
          if (samp_vox.eq.0.and.samp_uni.eq.1.and.bias.eq.0) then
            cnt = cnt + 1
          else 
            exit
          endif
          ! Test: 'p b'
          call read_params(testunitnum)
          if (bias.eq.1) then
            cnt = cnt + 1
          else 
            exit
          endif
          ! Test: 'p d'
          call read_params(testunitnum)
          if (debug.eq.1) then
            cnt = cnt + 1
          else 
            exit
          endif
          ! Test: 'p e'
          call read_params(testunitnum)
          if (ergs.eq.1) then
            cnt = cnt + 1
          else 
            exit
          endif
          ! Test: 'p m'
          call read_params(testunitnum)
          if (mat_rej.eq.1) then
            cnt = cnt + 1
          else 
            exit
          endif
          ! Test: 'p c'
          call read_params(testunitnum)
          if (cumulative.eq.1) then
            cnt = cnt + 1
          else 
            exit
          endif
          ! Test: 'p v'
          call read_params(testunitnum)
          if (samp_vox.eq.1) then
            cnt = cnt + 1
          else 
            exit
          endif
          ! Test: 'p u'
          call read_params(testunitnum)
          if (samp_uni.eq.1) then
            cnt = cnt + 1
          else 
            exit
          endif
          ! Test: 'p b u'
          call read_params(testunitnum)
          if (samp_uni.eq.1.and.bias.eq.0) then
            cnt = cnt + 1
          else 
            exit
          endif
          ! Test: 'p u r'
          call read_params(testunitnum)
          if (samp_uni.eq.1.and.resample.eq.1) then
            cnt = cnt + 1
          else 
            exit
          endif
          exit

        enddo

        CLOSE(testunitnum)

        if (cnt.lt.13) then
          write(*,*) "ERROR - test_read_params completed tests:", i, "/ 13"
        else 
          write(*,*) "test_read_params: successfully tested parameters parsing"
        endif

end subroutine test_read_params


subroutine test_gen_erg_alias_table
! Fake (normalized) probabiltiies are supplied to gen_erg_alias_table, and the
!  resulting probList and pairsList are matched to expected result.
        real(dknd),dimension(1:10) :: binList
        integer(i4knd),dimension(1:10,1:2) :: pairsList, expectedPairsList
        real(dknd),dimension(1:10) :: probList, expectedProbList
        real(dknd) :: a, b

        binList = (/ .01,.04,.05,.07,.09,.1,.13,.2,.22,.09 /)

        expectedPairsList = reshape( (/ 1,2,3,4,5,6,7,8,9,10,8,9,9,9, &
                                9,-1,-1,7,8,9 /), shape(expectedPairsList))

        expectedProbList = (/ 9.9999997E-002,0.3999999,0.5000000, &
                 0.7000000,0.9000000,1.0000000, &
                 1.0000000,0.7000000,0.6000000, &
                 0.9000000 /)
 
        call gen_erg_alias_table(10, binList, pairsList, probList)

        do i=1,10
          !assert
          a = probList(i)
          b = expectedProbList(i)
          if (abs(a-b).gt.(1e-5*max(a,b))) then
            write(*,*) "ERROR - test_gen_erg_alias_table: " // &
                                "discrepancy in table's probabilities", a, b
            write(*,*) "Full list of expected probabilities:", expectedProbList
            write(*,*) "Full list of actual probabilities:", probList
            return
          endif
          if (pairsList(i,1).ne.expectedPairsList(i,1)) then
            write(*,*) "ERROR - test_gen_erg_alias_table: " // &
                                "mismatch in table's bin pairs"
            write(*,*) "Expected:", expectedPairsList
            write(*,*) "Result:", pairsList
            write(*,*) "Full list of expected probabilities:", expectedProbList
            write(*,*) "Full list of actual probabilities:", probList
            return
          endif
        enddo

        write(*,*) "test_gen_erg_alias_table: successfully " // &
                                "created expected alias table"

end subroutine test_gen_erg_alias_table


subroutine test_erg_sampling_distrib
! Subroutine does 'testcnt' energy samplings for ten energy bins, and finds
!  the largest relative error in bin sampling frequency.
        real(dknd),dimension(1:10) :: binList
        integer(i4knd),dimension(1:10) :: tallyList
        integer(i4knd),dimension(1:1,1:10,1:2) :: pairsList
        real(dknd),dimension(1:1,1:10) :: probList
        real(dknd) :: a, b, testerg, maxdev, val
        integer(i4knd) :: nbins, cnt, talcnt, testcnt

        nbins = 10
        binList = (/ .01,.04,.05,.07,.09,.1,.13,.2,.22,.09 /)
        tallyList = (/ 0,0,0,0,0,0,0,0,0,0 /)
        
        call gen_erg_alias_table(nbins, binList, pairsList(1,1:10,1:2), &
                                              probList(1,1:10) )

        testcnt = 100000
        do cnt=1,testcnt
          ! Sample an energy, testerg
          call sample_erg (testerg, 1, nbins, 1, probList, pairsList)

          ! Tally the energy bin corresponding with testerg
          do talcnt=1,nbins
            if (testerg.lt.my_ener_phot(talcnt + 1)) then
              tallyList(talcnt) = tallyList(talcnt) + 1
              exit
            endif
          enddo

        enddo
        
        maxdev = 0
        do talcnt=1,nbins
          val = abs(tallyList(talcnt)/binList(talcnt) - testcnt) / testcnt
          if (val.gt.maxdev) then
            maxdev = val
          endif
        enddo

        write(*,'(a,a,es10.3)') " test_erg_sampling_distrib: maximum ", &
                "relative error in bin sampling frequency - ", maxdev
        write(*,*) tallyList

end subroutine test_erg_sampling_distrib


subroutine test_uniform_sample
! Tests that sampled positions are within problem; does 1e4 test samplings.
        deallocate(i_bins)
        deallocate(j_bins)
        deallocate(k_bins)

        testunitnum = getUnit()
        OPEN(unit=testunitnum, form='formatted', file='test_header.txt')

        call read_header(testunitnum)
        
        do i=1,10000
          call uniform_sample
          if (xxx.lt.i_bins(1).or.xxx.gt.i_bins(i_ints+1)) then
            write(*,*) "ERROR - test_uniform_sample: xxx out of bounds"
            return
          endif
          if (yyy.lt.j_bins(1).or.yyy.gt.j_bins(j_ints+1)) then
            write(*,*) "ERROR - test_uniform_sample: yyy out of bounds"
            return
          endif
          if (zzz.lt.k_bins(1).or.zzz.gt.k_bins(k_ints+1)) then
            write(*,*) "ERROR - test_uniform_sample: zzz out of bounds"
            return
          endif
        enddo

        write(*,*) "test_uniform_sample: successfully sampled 1e4 positions"

end subroutine test_uniform_sample

! End of test subroutines
end module tests_mod


program test_source
! Main program that runs all of the test subroutines
        use tests_mod

        call RN_init_problem() ! init random number generator to defaults

        write(*,*) "Running Fortran tests --"
        call test_read_custom_ergs
        call test_read_header
        call test_read_params
        call test_gen_erg_alias_table
        call test_erg_sampling_distrib
        call test_uniform_sample

end program test_source
