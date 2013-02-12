!+ $Id: mcnp_random.F90,v 1.3 2006/10/03 02:10:16 mashnik Exp $
! Copyright LANS/LANL/DOE - see file COPYRIGHT_INFO
!
! This module contains code from within MCNP5, namely the rang() function.
! The modules here are placeholders for testing a custom source routine,
!  and are the bare minimum needed.
!

module mcnp_debug
  ! Description:
  !
  ! This module contains 2 arrays which may be useful for
  ! debugging & development -- idum, rdum.
  !
  ! These arrays may be filled via the IDUM and RDUM imput
  ! cards, and are written/read to the runtpe file.
  !
  ! This module is "use"d in every subroutine & function
  ! in MCNP, so the variables idum & rdum are globally
  ! accessible.
  !
  ! DO NOT, UNDER ANY CIRCUMSTANCES, USE "IDUM" OR "RDUM" IN ANY CODING
  ! WHICH IS TO BE RELEASED TO USERS, RELEASED TO RSICC, OR CHECKED-IN 
  ! TO THE CODE REPOSITORY
  !----------------------------------------------------------------------
  
!  use mcnp_params,   only:  i4knd, dknd

  public
  save

!  integer, parameter    ::  n_idum = 50 != Length of IDUM.
!  integer, parameter    ::  n_rdum = 50 != Length of RDUM
!
!  integer(i4knd)  ::  idum(1:n_idum) = 0 != Data from IDUM card.
!  real(dknd)      ::  rdum(1:n_rdum) = 0 != Data from RDUM card.


end module mcnp_debug


module mcnp_random
  !=======================================================================
  ! Description:
  !  mcnp_random.F90 -- random number generation routines
  !=======================================================================
  !  This module contains:
  !
  !   * Constants for the RN generator, including initial RN seed for the
  !     problem & the current RN seed
  !
  !   * MCNP interface routines:
  !     - random number function:           rang()
  !     - RN initialization for problem:    RN_init_problem
  !     - RN initialization for particle:   RN_init_particle
  !     - get info on RN parameters:        RN_query
  !
  !   * Routines internal to this module:
  !     - skip-ahead in the RN sequence:    RN_skip_ahead
  !
  !   * Unit tests:             RN_test_basic, RN_test_skip, RN_test_mixed
  !
  !   * For interfacing with the rest of MCNP, arguments to/from these
  !     routines will have types of I8 or I4.
  !     Any args which are to hold random seeds, multipliers,
  !     skip-distance will be type I8, so that 63 bits can be held without
  !     truncation.
  !
  ! Revisions:
  ! * 10-04-2001 - F Brown, initial mcnp version
  ! * 06-06-2002 - F Brown, mods for extended generators
  !=======================================================================
  use mcnp_debug

  !-------------------
  ! MCNP output units
  !-------------------
  integer, private, parameter ::  iuo  = 32    ! mcnp output
  integer, private, parameter ::  jtty =  6    ! mcnp terminal

  !-----------------------------------
  ! Private functions for this module
  !-----------------------------------
  private ::  RN_skip_ahead

  !---------------------------------------------------
  ! Kinds for LONG INTEGERS (64-bit) & REAL*8 (64-bit)
  !---------------------------------------------------
  integer, private, parameter :: R8 = selected_real_kind( 15, 307 )
  integer, private, parameter :: I8 = selected_int_kind(  18 )

  !-------------------------------------
  ! Constants for standard RN generators
  !-------------------------------------
  type, private :: RN_GEN
    integer          :: index
    integer(I8)      :: mult        ! generator (multiplier)
    integer(I8)      :: add         ! additive constant
    integer          :: log2mod     ! log2 of modulus, must be <64
    integer(I8)      :: stride      ! stride for particle skip-ahead
    integer(I8)      :: initseed    ! default seed for problem
    character(len=8) :: name
  end type RN_GEN

  integer,      private, parameter :: n_RN_GEN = 4
  type(RN_GEN), private, SAVE      :: standard_generator(n_RN_GEN)
  character(len=20), private       :: printseed

  !-----------------------------------------------------------------
  !   * Linear multiplicative congruential RN algorithm:
  !
  !            RN_SEED = RN_SEED*RN_MULT + RN_ADD  mod RN_MOD
  !
  !   * Default values listed below will be used, unless overridden
  !-----------------------------------------------------------------
  integer,     private, SAVE ::   &
    &  RN_INDEX   = 1,            &
    &  RN_BITS    = 48
  integer(I8), private, SAVE ::   &
    &  RN_MULT    = 5_I8**19,     &
    &  RN_ADD     = 0_I8,         &
    &  RN_STRIDE  = 152917,       &
    &  RN_SEED0   = 5_I8**19,     &
    &  RN_MOD     = 2_I8**48,     &
    &  RN_MASK    = 2_I8**48 - 1_I8, &
    &  RN_PERIOD  = 2_I8**46
  real(R8),    private, SAVE ::  &
    &  RN_NORM    = 1.0_R8/2._R8**48

  !------------------------------------
  ! Private data for a single particle
  !------------------------------------
  integer(I8), private :: &
    &  RN_SEED,                  &   ! current seed
    &  RN_COUNT,                 &   ! current counter
    &  RN_NPS                        ! current particle number

  common                /RN_THREAD/   RN_SEED, RN_COUNT, RN_NPS
  save                  /RN_THREAD/
  !$OMP THREADprivate ( /RN_THREAD/ )

  !------------------------------------------
  ! Shared data, to collect info on RN usage
  !------------------------------------------
  integer(I8), private, SAVE ::  &
    &  RN_COUNT_TOTAL   = 0,     &   ! total RN count all particles
    &  RN_COUNT_STRIDE  = 0,     &   ! count for stride exceeded
    &  RN_COUNT_MAX     = 0,     &   ! max RN count all particles
    &  RN_COUNT_MAX_NPS = 0          ! part index for max count

  !---------------------------------------------------------------------
  ! Reference data:  Seeds for case of init.seed = 1,
  !                  Seed numbers for index 1-5, 123456-123460
  !---------------------------------------------------------------------
  integer(I8), private, parameter, dimension(10,n_RN_GEN) ::  &
    &  RN_CHECK = reshape(  (/ &
    ! ***** 1 ***** mcnp standard gen *****
    &      19073486328125_I8,      29763723208841_I8,     187205367447973_I8, &
    &     131230026111313_I8,     264374031214925_I8,     260251000190209_I8, &
    &     106001385730621_I8,     232883458246025_I8,      97934850615973_I8, &
    &     163056893025873_I8, &
    ! ***** 2 *****
    & 9219741426499971446_I8,  666764808255707375_I8, 4935109208453540924_I8, &
    & 7076815037777023853_I8, 5594070487082964434_I8, 7069484152921594561_I8, &
    & 8424485724631982902_I8,   19322398608391599_I8, 8639759691969673212_I8, &
    & 8181315819375227437_I8, &
    ! ***** 3 *****
    & 2806196910506780710_I8, 6924308458965941631_I8, 7093833571386932060_I8, &
    & 4133560638274335821_I8,  678653069250352930_I8, 6431942287813238977_I8, &
    & 4489310252323546086_I8, 2001863356968247359_I8,  966581798125502748_I8, &
    & 1984113134431471885_I8, &
    ! ***** 4 *****
    & 3249286849523012806_I8, 4366192626284999775_I8, 4334967208229239068_I8, &
    & 6386614828577350285_I8, 6651454004113087106_I8, 2732760390316414145_I8, &
    & 2067727651689204870_I8, 2707840203503213343_I8, 6009142246302485212_I8, &
    & 6678916955629521741_I8  /),  (/10,n_RN_GEN/)  )
  !---------------------------------------------------------------------

CONTAINS

  function rang()
    ! Description:
    ! MCNP random number generator
    !
    ! ***************************************
    ! ***** modifies RN_SEED & RN_COUNT *****
    ! ***************************************
    implicit none
    real(R8) ::  rang

    RN_SEED  = iand( iand( RN_MULT*RN_SEED, RN_MASK) + RN_ADD,  RN_MASK)
    rang     = RN_SEED * RN_NORM
    RN_COUNT = RN_COUNT + 1

    return
  end function rang
  !-------------------------------------------------------------------
  subroutine RN_init_problem( new_seed,                 &
    &                         new_stride,         new_part1,         &
    &                         new_count_total,    new_count_stride,  &
    &                         new_count_max,      new_count_max_nps, &
    &                         new_standard_gen,   output )
    ! Description:
    ! * initialize MCNP random number parameters for problem,
    !   based on user input.  This routine should be called
    !   only from the main thread, if OMP threading is being used.
    !
    ! * all args are optional
    !
    ! * for initial & continue runs, these args should be set:
    !     new_standard_gen - index of built-in standard RN generator,
    !                        from RAND gen=   (or dbcn(14)
    !     new_seed   - from RAND seed=        (or dbcn(1))
    !     new_stride - from RAND stride=      (or dbcn(13))
    !     new_part1  - from RAND hist=        (or dbcn(8))
    !     output     - logical, print RN seed & mult if true
    !
    ! * for continue runs only, these should also be set:
    !     new_count_total   - from "rnr"   at end of previous run
    !     new_count_stride  - from nrnh(1) at end of previous run
    !     new_count_max     - from nrnh(2) at end of previous run
    !     new_count_max_nps - from nrnh(3) at end of previous run
    !
    ! * check on size of long-ints & long-int arithmetic
    ! * check the multiplier
    ! * advance the base seed for the problem
    ! * set the initial particle seed
    ! * initialize the counters for RN stats

    implicit none
    integer,     intent(in), OPTIONAL :: new_standard_gen
    integer(I8), intent(in), OPTIONAL :: new_seed,          new_stride,      &
      &                                  new_part1,         new_count_total, &
      &                                  new_count_stride,  new_count_max,   &
      &                                  new_count_max_nps
    logical,     intent(in), OPTIONAL :: output
    integer(I8) ::  npart1, itemp1, itemp2, itemp3, itemp4, itemp5
    logical     ::  print_info

    ! - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    ! parameters for standard generators
    !
    standard_generator(1) = &
    & RN_GEN( 1,               5_I8**19, 0_I8, 48, 152917_I8, 5_I8**19, 'mcnp std' )
    !
    standard_generator(2) = &
    & RN_GEN( 2, 9219741426499971445_I8, 1_I8, 63, 152917_I8, 1_I8,     'LEcuyer1' )
    !
    standard_generator(3) = &
    & RN_GEN( 3, 2806196910506780709_I8, 1_I8, 63, 152917_I8, 1_I8,     'LEcuyer2' )
    !
    standard_generator(4) = &
    & RN_GEN( 4, 3249286849523012805_I8, 1_I8, 63, 152917_I8, 1_I8,     'LEcuyer3' )
    ! - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    ! set defaults, override if input supplied: seed, mult, stride
    npart1     = 1
    print_info = .false. !.true.
    RN_COUNT_TOTAL   = 0
    RN_COUNT_MAX     = 0
    RN_COUNT_MAX_NPS = 0
    RN_COUNT_STRIDE  = 0
    if( present(new_standard_gen) ) then
      !if( new_standard_gen<1 .or. new_standard_gen>n_RN_GEN ) then
      !  call expire( 0, 'RN_init_problem', &
      !    & ' ***** ERROR: illegal index for built-in RN generator')
      !endif
      RN_INDEX   = new_standard_gen
      RN_MULT    = standard_generator(RN_INDEX)%mult
      RN_ADD     = standard_generator(RN_INDEX)%add
      RN_STRIDE  = standard_generator(RN_INDEX)%stride
      RN_SEED0   = standard_generator(RN_INDEX)%initseed
      RN_BITS    = standard_generator(RN_INDEX)%log2mod
      RN_MOD     = ishft( 1_I8,       RN_BITS )
      RN_MASK    = ishft( not(0_I8),  RN_BITS-64 )
      RN_NORM    = 2._R8**(-RN_BITS)
      if( RN_ADD==0 ) then
        RN_PERIOD  = ishft( 1_I8, RN_BITS-2 )
      else
        RN_PERIOD  = ishft( 1_I8, RN_BITS )
      endif
    endif
    if( present(new_seed) ) then
      if( new_seed>0 )    RN_SEED0  = new_seed
    endif
    if( present(new_stride) ) then
      if( new_stride>0 )    RN_STRIDE = new_stride
    endif
    if( present(new_part1) ) then
      if( new_part1>0 )    npart1    = new_part1
    endif
    if( present(output)            )  print_info       = output
    if( present(new_count_total)   )  RN_COUNT_TOTAL   = new_count_total
    if( present(new_count_stride)  )  RN_COUNT_STRIDE  = new_count_stride
    if( present(new_count_max)     )  RN_COUNT_MAX     = new_count_max
    if( present(new_count_max_nps) )  RN_COUNT_MAX_NPS = new_count_max_nps

    if( print_info ) then
      write(printseed,'(i20)') RN_SEED0
      write( iuo,1) RN_INDEX, RN_SEED0, RN_MULT, RN_ADD, RN_BITS, RN_STRIDE
      write(jtty,2) RN_INDEX, adjustl(printseed)
    endif
1   format( &
      & /,' ***************************************************', &
      & /,' * Random Number Generator  = ',i20,             ' *', &
      & /,' * Random Number Seed       = ',i20,             ' *', &
      & /,' * Random Number Multiplier = ',i20,             ' *', &
      & /,' * Random Number Adder      = ',i20,             ' *', &
      & /,' * Random Number Bits Used  = ',i20,             ' *', &
      & /,' * Random Number Stride     = ',i20,             ' *', &
      & /,' ***************************************************',/)
2   format(' comment. using random number generator ',i2,', initial seed = ',a20)

    ! double-check on number of bits in a long int
    !if( bit_size(RN_SEED)<64 ) then
    !  call expire( 0, 'RN_init_problem', &
    !    & ' ***** ERROR: <64 bits in long-int, can-t generate RN-s')
    !endif
    itemp1 = 5_I8**25
    itemp2 = 5_I8**19
    itemp3 = ishft(2_I8**62-1_I8,1) + 1_I8
    itemp4 = itemp1*itemp2
    !if( iand(itemp4,itemp3)/=8443747864978395601_I8 ) then
    !  call expire( 0, 'RN_init_problem', &
    !    & ' ***** ERROR: can-t do 64-bit integer ops for RN-s')
    !endif

    if( npart1/=1_I8 ) then

      ! advance the problem seed to that for new_part1
      RN_SEED0 = RN_skip_ahead( RN_SEED0, (npart1-1_I8)*RN_STRIDE )

      if( print_info ) then
        itemp1 = RN_skip_ahead( RN_SEED0, RN_STRIDE )
        write(printseed,'(i20)') itemp1
        write( iuo,3) npart1,  RN_SEED0, itemp1
        write(jtty,4) npart1,  adjustl(printseed)
      endif
3     format( &
        & /,' ***************************************************', &
        & /,' * Random Number Seed will be advanced to that for *', &
        & /,' * previous particle number = ',i20,             ' *', &
        & /,' * New RN Seed for problem  = ',i20,             ' *', &
        & /,' * Next Random Number Seed  = ',i20,             ' *', &
        & /,' ***************************************************',/)
4     format(' comment. advancing random number to particle ',i10, &
        &', initial seed = ',a20)
    endif

    ! set the initial particle seed
    RN_SEED  = RN_SEED0
    RN_COUNT = 0
    RN_NPS   = 0

    return
  end subroutine RN_init_problem
 
  function RN_skip_ahead( seed, skip )
    ! Description:
    ! advance the seed "skip" RNs:   seed*RN_MULT^n mod RN_MOD

    implicit none
    integer(I8) :: RN_skip_ahead
    integer(I8), intent(in)  :: seed, skip
    integer(I8) :: nskip, gen, g, inc, c, gp, rn

    ! add period till nskip>0
    nskip = skip
    do while( nskip<0_I8 )
      nskip = nskip + RN_PERIOD
    enddo

    ! get gen=RN_MULT^n,  in log2(n) ops, not n ops !
    nskip = iand( nskip, RN_MASK )
    gen   = 1
    g     = RN_MULT
    inc   = 0
    c     = RN_ADD
    do while( nskip>0_I8 )
      if( btest(nskip,0) )  then
        gen = iand( gen*g, RN_MASK )
        inc = iand( inc*g, RN_MASK )
        inc = iand( inc+c, RN_MASK )
      endif
      gp    = iand( g+1,  RN_MASK )
      g     = iand( g*g,  RN_MASK )
      c     = iand( gp*c, RN_MASK )
      nskip = ishft( nskip, -1 )
    enddo
    rn = iand( gen*seed, RN_MASK )
    rn = iand( rn + inc, RN_MASK )
    RN_skip_ahead = rn
    return
  end function RN_skip_ahead


end module mcnp_random


module mcnp_global

  use mcnp_debug
  use mcnp_random

! Kind parameters:
  integer,parameter :: i1knd = selected_int_kind( 2)        != 1-byte integer kind
  integer,parameter :: i4knd = selected_int_kind( 9)        != 4-byte integer kind
  integer,parameter :: i8knd = selected_int_kind(18)        != 8-byte integer kind
  integer,parameter :: rknd  = selected_real_kind( 6, 37)   != real kind
  integer,parameter :: dknd  = selected_real_kind(15,307)   != 8-byte real kind

        integer(i4knd) :: ipt
        real(dknd) :: xxx,yyy,zzz,wgt,erg

end module mcnp_global


!+ $Id: mcnp_debug.F90,v 1.2 2006/10/03 02:10:16 mashnik Exp $
! Copyright LANS/LANL/DOE - see file COPYRIGHT_INFO


