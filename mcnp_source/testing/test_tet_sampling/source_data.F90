module source_data
! Variables used/shared by most of the subroutines in this file.
  use mcnp_global
   
        character*30 :: gammas_file = 'gammas'
        integer(i8knd) :: ikffl = 0 ! = local record of history #
        ! Parameters - these are toggled by gammas
        integer :: bias, samp_vox, samp_uni, debug, ergs, &
             mat_rej, cumulative, resample, uni_resamp_all
        ! Position sampling variables
        integer :: voxel, n_source_cells
        real(dknd),dimension(:),allocatable :: tot_list
        ! Voxel alias table variables
        real(dknd) :: sourceSum, n_inv, norm
        real(dknd),dimension(:,:), allocatable :: bins
        real(dknd),dimension(:),allocatable :: pairsProbabilities
        integer(i4knd),dimension(:,:), allocatable :: pairs
        integer :: alias_bin
        ! Biasing variables
        real(dknd) :: bias_probability_sum
        real(dknd),dimension(:),allocatable :: bias_list
        ! Energy bins variables
        real(dknd),dimension(:,:), allocatable :: spectrum
        real(dknd),dimension(:),allocatable :: my_ener_phot
        integer :: n_ener_grps
        ! Energy bins alias table variables
        real(dknd),dimension(:,:),allocatable :: ergPairsProbabilities
        integer(i4knd),dimension(:,:,:),allocatable :: ergPairs
        ! Debug output variables
        integer(i8knd) :: npart_write = 0 ! = counter for debug output
        ! Other variables
        integer :: stat
        integer :: ii, kk, jj
        integer :: i_ints, j_ints, k_ints, n_mesh_cells, n_active_mat
        real,dimension(:),allocatable :: i_bins, j_bins, k_bins
        integer,dimension(100) :: active_mat
        character*3000 :: line ! needed for reading active_mat from gammas

  contains 

        integer function getUnit()
        ! Get an unused unit number to assign to a file being opened
        ! via https://modelingguru.nasa.gov/docs/DOC-2052
           implicit none
           integer :: unit
           logical :: isOpen

           integer, parameter :: MIN_UNIT_NUMBER = 50
           integer, parameter :: MAX_UNIT_NUMBER = 99

           do unit = MIN_UNIT_NUMBER, MAX_UNIT_NUMBER
              inquire(unit = unit, opened = isOpen)
              if (.not. isOpen) then
                 getUnit = unit
                 return
              end if
           end do
        end function getUnit
       
end module source_data



