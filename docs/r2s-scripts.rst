
_______________________________________________________________________________
Scripts run by r2s_step1.py
_______________________________________________________________________________
This scripts are listed in chronological order of when they are run. Most of these scripts can be run with a -h flag for usage and command line options.

...............................................................................
read_meshtal.py:
...............................................................................

:Purpose: This script reads in an MCNP meshtal file and creates a structured mesh tagged with the fluxes and errors for each energy group
:Inputs: MCNP meshtal file
:Outputs: Structure mesh tagged with fluxes and errors
:Syntax: `./read_meshtal.py <meshtal file> [options]`
:Options:
 -h, --help         show this help message and exit
 -o MESH_OUTPUT     Name of mesh output file, default=flux_mesh.h5m
 -n NORM            Normalization factor, default=1
 -m MESH_FILE       Preexisting mesh on which to tag fluxes
:Path: `r2s-act/scripts/r2s/data_transfer/read_meshtal.py`

...............................................................................
write_alara_fluxin.py
...............................................................................

:Purpose: This script reads the neutron fluxes off a structured mesh file (created by `read_meshtal.py`) and prints an `ALARA_fluxin` file.
:Inputs: Structured mesh
:Outputs: ALARA fluxin file
:Syntax: `./write_alara_fluxin.py <structured mesh> [options]`
:Options:  -b              Print to ALARA fluxin in fluxes in  decreasing energy.
                           Default=False
          -o FLUXIN_NAME  Name of ALARA fluxin output file, default=ALARAflux.in
:Path: `r2s-act/scripts/r2s/data_transfer/write_alara_fluxin.py`

...............................................................................
mmgrid.py
...............................................................................

:Purpose: This script is used calculate average material definitions for each mesh voxel. Most geometries do not conform to the Cartesian mesh dictated by MCNP fmesh4 tallies. Voxels that contain multiple volumes are likely to contain multiple materials, so the ALARA materials assigned to these voxels must be a mixture of materials from the MCNP files. This script uses Monte Carlo ray-tracing to determine the volume fractions of each material in each voxel and then writes corresponding ALARA geometry and materials entries, and tags mesh with the material  definitions. The first required argument should be a DagMC-loadable geometry.  The optional second argument must be a file with a single structured mesh.  In the absence of the second argument, mmgrid will attempt to infer the shape of the DagMC geometry and create a structured grid to match it, with NDVIS divisions on each side.
:Inputs: geometry file (.sat or .h5m), structured mesh file
:Outputs: ALARA geometery and materials entries
:Syntax: `mmgrid.py [options] geometry_file [structured_mesh_file]`
:Options:
  -h, --help                                   help message and exit
  -n NUMRAYS                                   Set N. N^2 rays fired per row.  Default N=20
  -g, --grid                                   Use grid of rays instead of randomly selected starting points
  -o Output_file                               Output file name, default=mmgrid_output.h5m
  -q, --quiet                                  Suppress non-error output from mmgrid
  -d NDIVS                                     Number of mesh divisions to use when inferring mesh size, default=10
  -a GEOM_FILE                                 Write alara geom to specified file name
:Path: `r2s-act/scripts/r2s/mmgrid.py`


...............................................................................
write_alara_geom.py
...............................................................................

:Purpose: This script takes the structured mesh with materials from `mmgrid.py` and creates a file (alara_geom) with ALARA geometry and materials entries.
:Inputs: Structured mesh tagged with materials entries
:Outputs: alara_geom, a file with ALARA geometry and materials 
:Syntax: `./write_alara_geom.py`
:Options: None
:Path: `r2s-act/scripts/r2s/data_transfer/write_alara_geom.py`



_______________________________________________________________________________
Scripts run by r2s_step2.py
_______________________________________________________________________________


...............................................................................
read_alara_phtn.py
...............................................................................

:Purpose: The script reads an ALARA phtn_src file and writes the source strengths to the structured mesh specified by the -p option.
:Inputs: ALARA pthn_src, structured mesh from Step 1
:Outputs: structured mesh tagged with source strengths
:Syntax: `./read_alara_phtn.py [options] arg`
:Options:
  -p PHTNSRCFILE        The photon source strengths are read from FILENAME.
  -m MESHFILE           File to write source information to, or file name for saving a modified mesh.
  -i ISOTOPE            The isotope string identifier or 'TOTAL'. Default: TOTAL
  -c COOLINGSTEP        The cooling step number or string identifier. (0 is first cooling step)  Default: 0
  -r, --retag           Option enables retagging of .h5m meshes. Default: False
  -t, --totals          Option enables adding the total photon source strength for all energy groups as a tag for each voxel. Default: False
:Path: `r2s-act/scripts/r2s/data_transfer/read_alara_phtn.py`


...............................................................................
write_gammas.py
...............................................................................

:Purpose: This script reads a structured mesh tagged with photon sources strengths and generates a gammas file for use as a source distribution file for photon transport.
:Inputs: structured mesh file with photon source strengths
:Outputs: gammas file
:Syntax: `write_gammas.py input-h5m-file [options]`
:Options:
  -h                  Show message and exit
  -o OUTPUT           Option specifies the name of the 'gammas'file. Default: gammas
  -a                  Generate the gammas file with an alias table of energy bins for each voxel. Default: False. Default file name changes to 'gammas_alias.' Creates the file gammas with the photon energy bins for each voxel stored as alias tables. Reads directly from phtn_src file. Each voxel's line corresponds with an alias table of the form: [total source strength, p1, g1a, g1b, p2, g2a, g2b ... pN, gNa, gNb] Where each p#, g#a, g#b are the info for one bin in the alias table.
:Path: `r2s-act/scripts/r2s/data_transfer/write_gammas.py`

...............................................................................
mcnp_n2p.py
...............................................................................

:Purpose: This script reads an MCNP neutron input file and writes a corresponding photon input file.
:Inputs: MNCP neutron input file
:Outputs: 
:Syntax: `mcnp_n2p.py INPUTFILE [options]`
:Options:
  -h              Show help message and exit
  -o OUTPUT       File name to write modified MCNP input to. Default is to append input file name with '_p'.
  -d              Add flag to parse file like a DAG-MCNP5 file (which has only title card and block 3 cards). Default: False
:Path: `/r2s-act/scripts/r2s/mcnp_n2p.py`

...............................................................................
