!+

program test_source
! Main program that runs all of the test subroutines
        use tests_mod
        use mcnp_random

        call RN_init_problem() ! init random number generator to defaults

        !write(*,*) "Running Fortran tests --"
        !call test_read_custom_ergs
        !call test_read_header
        !call test_read_params
        !call test_gen_erg_alias_table
        !call test_erg_sampling_distrib
        !call test_uniform_sample

        !call read_moab("125hex.vtk")
        !call read_moab("n_fluxes_and_materials.vtk")
        call test_get_tet_vol

end program test_source
