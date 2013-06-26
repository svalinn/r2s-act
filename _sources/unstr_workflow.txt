Running the unstructured workflow for R2S-ACT
==============================================
Using the unstructured workflow requires only minimal changes.
There are two parts to the unstructured R2S-ACT workflow.  The first of these is to set the `structuredmesh` variable in the `r2s.cfg` file.  This will ensure that all the workflow scripts treat the mesh being used as an unstructured mesh.  The second is to run photon transport with a MCNP or DAG-MCNP executable compiled with the custom source routine in `source_moab.F90`.

The above assumes that an unstructured mesh is used in the neutron transport step to create an unstructured mesh tally.

Unstructured mesh tallies
--------------------------
To summarize the setup of an unstructured mesh tally:

1. Create unstructured mesh in CubIT and save to the default .cub format
2. Use `mbconvert` to convert from .cub to .h5m
3. In the DAG-MCNP input, you need FC and FMESH cards (example follows this list)
4. Run neutron transport.

Example FMESH card for unstructured tally::

        FC4 dagmc inp=mesh.h5m out=mesh.h5m
        FMESH4:n  geom=dag
               emesh=(low to high)

Where mesh.h5m is the mesh file created in step 2.

More scraps of information
----------------------------

* r2s-act/mcnp_source/README.rst
* https://github.com/svalinn/DAGMC/issues/48

