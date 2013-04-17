!+

program test_source
! Main program that runs all of the test subroutines
        use tests_mod
        use mcnp_random

        call RN_init_problem() ! init random number generator to defaults

        write(*,*) "Running Fortran tests --"
        !call test_read_custom_ergs
        !call test_read_params
        call test_gen_erg_alias_table
        call test_erg_sampling_distrib

        ! Attempt to get around 'ambiguous reference' errors.
        iBase_REGION_t = iBase_REGION
        iMesh_TETRAHEDRON_t = iMesh_TETRAHEDRON
        iMesh_HEXAHEDRON_t = iMesh_HEXAHEDRON
        call test_get_tet_vol
        call test_get_hex_vol1
        call test_get_hex_vol2
        call test_read_moab1
        call test_read_moab2
        call test_sample_region_entity_tet
        call test_sample_region_entity_hex

end program test_source
