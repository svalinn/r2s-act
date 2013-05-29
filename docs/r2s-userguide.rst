University of Wisconsin Rigorous Two Step Activation Work Flow (R2S-ACT) User Manual
####################################################################################

.. contents:: Table of Contents

...............................................................................

===============================================================================
Introduction
===============================================================================
_______________________________________________________________________________
The Rigorous Two Step (R2S) Method
_______________________________________________________________________________

The Rigorous Two Step (R2S) method is used to determine the photon fluxes that result from neutron activation of materials for a given geometry. The first step of this method is neutron transport over some geometry in order to calculate flux distributions in space and energy. Using this neutron flux distribution and the isotopic composition of each part of the geometry, material activation calculations can be done in order to calculate a distribution of photon source strengths in space and energy. The second step of R2S is doing a photon transport calculation on these decay photons, in order to determine a photon flux distribution in space and energy. The "two step" part of the name specifies that neutron and photon transport steps are done separately, as opposed to the Direct One Step (D1S) method which performs both transport calculations simultaneously.
 
_______________________________________________________________________________
University of Wisconsin Rigorous Two Step Activation Work Flow (R2S-ACT)
_______________________________________________________________________________

R2S-ACT is composed of a series of scripts written in the Python programming language to facilitate R2S calculations in complex 3D geometries. The end product of R2S-ACT is a single Cartesian MOAB mesh file with each voxel tagged with:

1. neutron fluxes and relative errors for every neutron energy group, total neutron flux (neutrons/cm^2/s)
2. material fractions and relative errors for every material in the geometry
3. photon source strengths for every photon energy group (photons/cm^3/s)
4. total photon source strength over the entire geometry (photons/s)
5. photon flux and/or dose for every photon energy group and relative errors, total flux and/or dose (photons/cm^3/s, any dose units)

The backbone of R2S-ACT is the physics codes used for transport and activation. The Direct Accelerated Geometry Monte Carlo (DAG-MC) version of MCNP5 (Los Alamos National Laboratory), known as DAG-MCNP5 (UW-Madison) is used for both neutron and photon transport. This allows for geometry and materials information to be specified using CAD software, namely CubIt (Sandia National Laboratory). For the photon transport step, a custom compiled version of DAG-MCNP5, with a custom source.F90, is used. Analytic and Laplacian Adaptive Radioactivity Analysis (ALARA), developed at UW-Madison, is used for material activation.

...............................................................................

===============================================================================
Set-up and Dependencies
===============================================================================
The R2S-ACT code is available at https://github.com/svalinn/r2s-act.

R2S-ACT has numerous dependencies:

1. Python 2.6+
2. DAG-MCNP5 compiled with R2S-ACT `mcnp_source/source_gamma.F90`, from https://github.com/svalinn/DAGMC
3. CubIt, from https://cubit.sandia.gov/
4. ALARA, from https://github.com/svalinn/ALARA
5. Mesh Oriented Data Base (MOAB), from svn.mcs.anl.gov/repos/ITAPS/MOAB/trunk
6. PyTAPS, the Python interface for ITAPS, (Interoperable Technologies for Advanced Petascale Simulations), from http://pypi.python.org/pypi/PyTAPS/1.4
7. PyNE, *Python for Nuclear Engineering*, from http://pynesim.org/
   (Has its own dependencies listed at https://github.com/pyne/pyne)

Aside from MCNP5 and CubIt, available from RSICC, all other codes are open source with well documented installation instructions.

You will need to add the `r2s-act/scripts` directory to the PYTHONPATH variable.
In unix, this can be done by modifying the .bashrc file, adding the following line::

    export PYTHONPATH=*install_directory*/r2s-act/scripts/:$PYTHONPATH

The user guide and other documentation is available at http://svalinn.github.io/r2s-act/ .
Building the documentation requires Sphinx, from http://sphinx-doc.org

Although not a dependency, the visualization program VisIT (Lawrence Livermore National Laboratory) is useful for visualizing results data stored on MOAB meshes in the .vtk format.
Executables are available at https://wci.llnl.gov/codes/visit/.

_______________________________________________________________________________
Compiling DAG-MCNP5 with R2S-ACT source.F90
_______________________________________________________________________________
In MCNP5, fixed source information is typically specified with the SDEF card. However, the SDEF card is limited to 1000 distributions. Building DAG-MCNP5 against R2S-ACT source.F90 allow for an unlimited number of distributions. This is necessary because in the R2S-ACT work flow, every mesh point is a particle source and generally high resolution spacial and energy information is sought after. To use the R2S-ACT source.F90 version, no source cards (SDEF, SI, SP, etc.) appears in the input file. Instead, this version reads in a file (`gammas`) that contain all of the source information. This file is automatically generated by the R2S work flow. Technically this version is only necessary for the photon transport step (and not the neutron transport step), however if the MCNP input includes a source definition, the problem run like normal. Thus the same executable can be used for bother regular, and R2S-ACT photon transport calculations. Instructions for compiling DAG-MCNP5 with R2S-ACT source.F90 appear below.

1. Navigate to the `trunk/Source/src` folder of DAG-MCNP5.
2. Delete the file `source.F90`
3. Create a soft link (named `source.F90`) to the file `source_gamma_refactor.F90`, found in the folder `r2s-act/mcnp_source/`.
4. Build DAG-MCNP5 in the usual fashion.

...............................................................................

===============================================================================
Running R2S-ACT
===============================================================================

R2S-ACT contains 2 wrapper scripts (r2s_step1.py, r2s_step2.py) that call all necessary scripts in the correct order. User setup is still potentially required for numerous details. These include materials, meshing, MCNP input files, and and irradiation details for ALARA.

In some cases, users may want to run certain scripts individually. To do this, users should consult the R2S Step 1 and R2S Step 2 section of this manual for information about running these individual scripts. The work flow using the wrapper scripts is detailed below:

Executive Summary
-----------------
1. Create geometry, and prepare it for DAGMCNP and/or unstructured mesh.
2. Run neutron transport problem.
3. Setup the problem with `r2s_setup.py`, and make any changes needed to `r2s.cfg` and the ALARA snippet file.
4. Create ALARA materials library file.
5. Run `r2s_step1.py`.
6. Run ALARA.
7. Run `r2s_step2.py`.
8. Set up photon transport (e.g. tallies) and run modified MCNP/DAGMCNP with mesh-sampling source.F90.
9. Examine results; Use `read_meshtal.py` to tag photon mesh tallies to the mesh for visualization.


Full Summary
------------
**1. Create geometry.** Using CubIt, create the geometry and specify materials by adding volumes to materials groups. Group names should be formatted like "mat_X_rhoY" where X is the material number and Y is either mass density (negative value) or atom density (positive volume). Instructions for doing this can be found in the `DAG-MCNP5 user manual <http://svalinn.github.io/DAGMC/doc/usersguide/index.html>`. Be sure to remember to imprint and merge all of the geometry. Once completed, export the geometry as a .sat file (Standard ACIS Text format) and when prompted specify an ACIS version of 1900 and the "export attributes" option. Alternatively, if the geometry already exists in the form of an MCNP input file, MCNP2CAD can be used to convert the geometry information from the MCNP input file into a .sat file. If the geometry contains small features, users may need to specify a smaller tolerance for merging surfaces (using the -t flag).

Once the .sat file exists, it can be converted to an .h5m file (binary format MOAB mesh file) using dagmc_preproc or mbconvert. This is not necessary, but it prevents DAG-MCNP5 from having to process the .sat file every time it is run. Using a .h5m file also allows for the use of of a DAG-MCNP5 version that is not built against CubIt. In either case, either DAG-MCNNP or dagmc_preproc/mbconvert creates a faceted representation of the geometry. Users can specify the maximum distance between the points in the geometry and the faceted representation on the geometry. This is known as the faceting tolerance. In dagmc_preproc, this is specified with the -f flag. In DAG-MCNP5 this can be specified on the command line by using ftol=faceting_tolerace (e.g. ftol=1E-4). In addtion, dagmc_preproc can also be used to specify a length tolerance using the -l flag. The length tolerance is the maximum length of a facet edge.

**2. Create DAG-MCNP5 input file and run neutron transport calculation.** Other than the geometry cards, the rest of the DAG-MCNP5 input file should be identical to that of a native MCNP input file. Make sure the material numbers in the input file match the numbers of the material groups in CubIt. 

For neutron activation, the MCNP/DAG-MCNP5 input file must contain a type 4 FMESH tally over the geometry of interest. Both structured (native MCNP) and unstructured mesh tallies are supported.

If a native mesh tally is used, the tally results appear in a MCNP `meshtal` output file.  Otherwise, with an unstructured mesh tally, results are tagged directly to the mesh.

The output from the type 4 mesh tally will have units of *neutrons/cm^2/source particle*. This output needs to be converted to flux, by multiplying by the total neutron source strength  (referred to as the neutron normalization factor) which has units of *source particles/second*. The recommended way of doing this is to use and FM tally multiplier card  to specify the neutron normalization factor on the FMESH4 tally, which will result in a `meshtal` file with fluxes in the correct units. If this is not done, normalization can be done when fluxes are tagged to mesh using the `read_meshtal.py` script.

**3. Run r2s_setup.py.** This script creates two configuration files called `r2s.cfg` and `alara_snippet` in whatever folder the script is run from. It is best to run all subsequent scripts out of this folder.

**4. Modify r2s.cfg to suit the problem.** The configuration file allows the user to specify important parameters and also the names of files used by and created by `r2s_step1.py`, ALARA, and `r2s_step2.py`. The file `r2s.cfg` is printed with default file names and parameters and also some instructive annotations. Typically there is no reason to change the file names aside from personal preference. In order to better understand the parameters specified, users should consult the "Step 1 Parameters" and "Step 2 Parameters" portion of this file. Of particular note, if an unstructured mesh is being used in the problem, the *structuredmesh* entry in `r2s.cfg` should be set to *False*.

**5. Create ALARA materials library.** The script `mats2ALARA.py` can be used to convert MCNP materials definitions to ALARA materials definitions. However, generally speaking activation definitions should be much more detailed than transport definitions, as minor impurities can dominate activations. ALARA material libraries rely on isotope libraries. A script to write both MCNP and ALARA definitions for R2S style problems is currently in development.

**6. Modify ALARA snippet.** The ALARA snippet file contains all of the information needed to run ALARA, apart from the geometry and materials information. It is appended to the ALARA geometry/materials file produced by `r2s_step1.py` to create the full ALARA input file. Most of the entries in the default snipppet produced by `r2s_setup.py` need not be changed. However, every problem will have a different irradiation schedule so special attention should be taken to change this from the default irradiation schedule. The keywords for ALARA input files are documented in the `ALARA Manual<https://trac.cae.wisc.edu/trac/svalinn/wiki/ALARAInputFileSyntax>`. The ALARA snippet file also specifies the isotope library, material library, and data libraries. These libaries, or links to them must be present in the folder that ALARA is run out of. The default activation and photon source libraries are both specified as "FENDL2" in the ALARA snippet. However, soft links to these files must be named `FENDL2.bin` and `FENDL2.gam` for the activation and photon source libraries, respectively.

**7. Run r2s_step1.py.** This script is a wrapper script that reads the meshtal, geometry, MCNP neutron input file, and `alara_snippet` file specified in `r2s.cfg` and outputs a structured mesh file tagged with neutron fluxes with relative errors, material fractions with relative errors, and a complete ALARA input file.

**8. Run ALARA.** ALARA reads in the geometry, material, and irradiation schedule information from the ALARA input file and outputs a file containing photon source strengths (phtn_src) for every voxel and energy group. In addition, ALARA can calculate isotopic inventories, decay heat, and more (see ALARA user manual), which is printed to standard output by default. This output can be piped to an output file. Assuming the ALARA snippet file was written correctly and appended the command for this step will be `/path/to/ALARA/ alara_geom > output_file`. Currently, ALARA does not print out phtn_src entries for entries of material "void." This causes indexing problems in Step 2. To get around this, use SED or some text editor to replace "void" with "pseudo_void"  (or something similar). Then make an entry in the ALARA material library for "pseudo_void" and assign the density to be equal to zero. This produces output that is mathematically correct.

**9. Run r2s_step2.py.** Like `r2s_step1.py`, this script is a wrapper for several other scripts. This script takes an ALARA phtn_src file, tags the information onto the structured mesh file from Step 1 and creates a `gammas` file used to specify the photon source distribution for the gamma transport step. It also modifies the MCNP neutron input file to create an MCNP photon input file. However this file may need additional user attention before running DAG-MCNP5, especially if the photon tally region is different from the neutron tally region. Flux to dose conversion factors should be added if dose results are desired.

**11. Run DAG-MCNP5, complied with R2S-ACT source.F90.** The custom compiled version of DAG-MCNP5 reads the `gammas` file (must be present within the same folder), and output as a meshtal file with photon fluxes and/or doses.

**10. Run read_meshtal.py.** Run this script with the -m flag in order tag photon fluxes and/or doses onto the mesh with the rest of the information on it. This script is run by `r2s_step1.py`, so more information about this script can be found in the "Scripts run by r2s_step1.py" section of this manual.

**12. Visualize Results.** To visualize results, stuctured mesh .h5m files must be first converted to .vtk viles. This can be done using the MOAB mbconvert tool (syntax: `mbconvert <mesh_file.h5m> <mesh_file.vtk>`). The best way of visualizing the results on the resulting .vtk file is using VisIT. Fluxes/doses are best viewed as "pseudo color" or "volume" plots. The geometry can be superimposed onto these plots. To do this, save the geometry as a .stl file in CubIt. Then open this file in VisIt and visualize it as a "mesh" plot. It is often useful to visualize results during intermediate steps of the work flow. For example it may be useful to visualize the neutron flux distribution and errors prior to continuing with the work flow.

...............................................................................

===============================================================================
R2S Step 1
===============================================================================

This section provides details on the Step 1 scripts, in chronological order of when they are run.

_______________________________________________________________________________
r2s_setup.py
_______________________________________________________________________________

:Purpose: The script creates two set-up files used in the R2S work flow: `r2s.cfg` and `alara_snippet`.
:Inputs: None
:Outputs: `r2s.cfg`, `alara_snippet`.
:Syntax: `./r2s_setup.py`
:Options: None
:Path: `r2s-act/scripts/r2s_setup.py`

_______________________________________________________________________________
r2s_step1.py
_______________________________________________________________________________

:Purpose: This script is a wrapper script that reads the meshtal, geometry, MCNP neutron input file, and alara_snippet file specified in `r2s.cfg` and outputs a complete ALARA input file and a structured mesh file tagged with neutron fluxes and materials.
:Inputs: `r2s.cfg`
:Outputs: ALARA input file, structured mesh with neutron fluxes and uncertainties, materials and uncertainties.
:Syntax: `./r2s_step1.py`
:Options: None
:Path: `r2s-act/scripts/r2s_step1.py`

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
:Path: `r2s-act/scripts/r2s/io/read_meshtal.py`

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
:Path: `r2s-act/scripts/r2s/io/write_alara_fluxin.py`

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
:Path: `r2s-act/scripts/r2s/io/write_alara_geom.py`


_______________________________________________________________________________
Step 1 Parameters
_______________________________________________________________________________

These settings can be modified in a problem's `r2s.cfg` file.

:mmgrid_rays: The number of rays per mesh row to fire during Monte Carlo generation of the macromaterial grid. Raising this number will reduce material errors, but also increase the runtime of r2s_step1.
:step2setup: If step2setup is 1, runs the `r2s_step2setup.py` script at the end of `r2s_step1.py`.  `r2s_step2setup.py` creates folders for all cooling steps and isotopes specified.

...............................................................................

===============================================================================
R2S Step 2
===============================================================================

This section provides details on the Step 2 scripts, in chronological order of when they are run.

_______________________________________________________________________________
r2s_step2.py
_______________________________________________________________________________

:Purpose: This script takes the phtn_src file produced by ALARA and tags the source strengths onto the structured mesh. It also creates the 'gammas' file and converts the MCNP neutron input file to a photon input file.
:Inputs: structured mesh from Step 1, pthn_src file, MCNP neutron input file
:Outputs: structured mesh with source strengths, gammas file, MCNP photon input file
:Syntax: `./r2s_step2.py`
:Options: None
:Path: `r2s-act/scripts/r2s_step2.py`

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
:Path: `r2s-act/scripts/r2s/io/read_alara_phtn.py`


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
:Path: `r2s-act/scripts/r2s/io/write_gammas.py`

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

_______________________________________________________________________________
Step 2 Parameters
_______________________________________________________________________________

These settings can be modified in a problem's `r2s.cfg` file.

:photon_isotope: Specify what isotope should be considered for activation (for reading phtn_src file). The default is all isotopes, TOTAL.
:photon_cooling: The cooling step to read from `phtn_src` file. Numeric or string identifiers matching those in the ALARA input can be used. Numbering starts with 0 for "shutdown", and follows the order listed in the ALARA input.
:sampling: determines the sampling method used. For uniform sampling, specify "u"; for voxel sampling specify "v" (default). Voxel sampling is probably preferable for most cases, and is required if source biasing is being used.
:photon_bias: 0 for false, 1 for true. If true, the gammas file will try to include voxel bias values from the mesh (stored as PHTN_BIAS tag). Currently requires **sampling** to be "v". (Note that bias values are tagged to the mesh using a script like `tag_bias_example.py`)
:custom_ergbins: 0 for false, 1 for true. If **custom_ergbins** is 1, custom energy bins will be looked for on the mesh, and included in gammas file if found. (default: false; default 42 group structure is used)
:cumulative: 0 for false, 1 for true. **cumulative** determines the format for listing energy bin probabilities for each voxel in gammas file. Default is 0 (false), which is corresponds with sequential bins, and is preferred.

...............................................................................

===============================================================================
Other Scripts Pertinent to the R2S work flow.
===============================================================================
This section lists the command line interfaces for individual scripts.  In the case of most scripts, these command line interfaces are out of date.

_______________________________________________________________________________
mats2ALARA.py
_______________________________________________________________________________

:Purpose: This script reads an MCNP input file and prints out an ALARA matlib file. Material definitions are taken from material cards and densities are taken from cell cards. If a material appears in multiple cells with different densities an ALARA material definition will be printed for each density.
:Other Instructions: This script also reads metadata that can be specified in the MCNP input file and prints this same metadata to the ALARA matlib file. This metadata must appear in the lines directly above the material definition in the form "C X:Y" or "c X:Y" where X is "name", "source", or "comments", and Y is the corresponding metadata. The "name" and "source" metadata must appear on a single line. The "comment" metadata can span any arbitrary number of lines, each new line starting with "C" or "c". Any or all of the 3 metadata flags can be used, but there must be no blank lines between metadata lines (i.e. no lines that contain only "C" or "c").
    In the resulting matlib file metadata will be in the form "# X:Y". In additional entry will appear in the form "mat number: X" where X is the material number in the MCNP input. The name of the material in the matlib is the same as the "name" metadata. For materials with multiple densities, if "name" is present every material will have the same name. For this reason it is not advisable to specify "name" metadata for multidensity materials. If the "name" metadata does not appear, the material will be named in the form "matX_rho-Y" where X is the MCNP material number and Y is the mass density associated with the material. Note that even when atom density is specifed in the cell card the mass density is printed.
:Usage: This script relies on the PyNE materials class and its methods. The MCNP inp is read into a PyNE material. Metadata is stored in the attrs.
:Inputs: MCNP input file
:Outputs: ALARA materials definitions
:Syntax: `./mats2ALARA.py <mcnp_input_file>`
:Options:
  -h, --help  show this help message and exit
  -o OUTPUT   Name of materials output file, default=matlib.out

:Path: `r2s-act/scripts/tools/mats2ALARA.py`

_______________________________________________________________________________
get_mesh_values.py
_______________________________________________________________________________

:Purpose: This script is used to print the value of a tag on a structured mesh. The script will automatically search for a tag in the for tag_name+_error. If it exists, the error value will be appended to the answer: value (plus/minus) error
:Inputs: Structured mesh
:Outputs: value with error to standard output
:Syntax: `./get_value.py <structured_mesh> <x_value> <y_value> <z_value> <tag_name>`
:Options:
  -h, --help  show help message and exit
:Path: `r2s-act/scripts/tools/mats2ALARA.py`

_______________________________________________________________________________
wwinp_to_h5m.py
_______________________________________________________________________________

:Purpose: This script creates a structured .h5m tagged with weight window lower bounds from a MCNP WWINP file.
:Inputs: MCNP WWINP file
:Outputs Tagged structured mesh
:Syntax: ./wwinp_to_h5m <wwinp> options
:Options:
  -h, --help  show this help message and exit
  -o OUTPUT   Name of ALARA matlib output file, default=wwinp.h5m
:Path:`r2s-act/scripts/tools/wwinp_to_h5m.py`

_______________________________________________________________________________
h5m_to_wwinp.py
_______________________________________________________________________________

:Purpose: This scripts read an .h5m mesh tagged with weight window lower bounds and output a MCNP wwinp file.
:Additional Instructions: When printing a WWINP created using the magic.py -t option, the -t option must be used for this scripts as well.
:Inputs: Structured mesh file tagged with weight window lower bounds
:Outputs: MCNP WWINP file
:Syntax: ./h5m_to_wwinp <h5m file. [options]
:Options:
  -h, --help      show this help message and exit
  -o OUTPUT_NAME  Name of WWINP output file, default=wwinp.out
  -t              If multiple energy groups exist, only use Total
                  default=False
:Path:`r2s-act/scripts/tools/magic.py`

_______________________________________________________________________________
magic.py
_______________________________________________________________________________

:Purpose: This script reads in a flux mesh with N energy groups and generates weight windows using the MAGIC global variance reduction technique for either each of the N energy groups or the total. Additionally, a preexisting weight window mesh can be specified. This allows for iterations of the MAGIC method, each improving the weight windows.
:Inputs: Structured mesh tagged with fluxes, optional structured mesh tagged with lower weight window bounds.
:Outputs: Structured mesh tagged with lower weight window bounds.
:Syntax: ./magic.py <flux mesh> [options]
:Options:
  -h, --help      show this help message and exit
  -w WW_MESH      Preexisting WW mesh file to apply magic to, 
                  default=none
  -o OUTPUT_MESH  Name of WWINP output file, default=magic_ww.h5m
  -t              If multiple energy groups exist, only use Total
                  default=False
  -n NULL_VALUE   WW value for voxels with error > tolerance (on
                  the first iteration only), default=0
  -e TOLERANCE    Specify the maximum allowable relative error for
                  creating ww files from MAGIC or overwriting
                  existing ww values, default=0.1
:Path:`r2s-act/scripts/tools/magic.py`

____________________________________________________________________
tag_ebins.py
____________________________________________________________________

:Purpose: If custom energy groups are desired for activation and photon transport, a separate file listing the energy bins boundaries (one per line) can be provided to this script. Otherwise, the default 42 group structure will be used.
:Inputs: Step 1 mesh, energy file: a list of the energy bins for each photon energy group, with a single energy per line
:Outputs: None (tags the .h5m mesh)
:Syntax: `./tag_ebins.py <energy_file> <mesh_file> [options]`
:Options: None
:Path: `r2s-act/scripts/r2s/tag_ebins.py`

______________________________________________
r2s_step2setup.py
______________________________________________

:Purpose: For each combination of cooling step and isotope listed in the `r2s.cfg` file, this script creates new folders with copies of `r2s.cfg`, the MCNP inputs, and the .h5m mesh file.
:Inputs: Looks for `r2s.cfg` file
:Outputs: Creates directories containing files
:Syntax: `./r2s_step2setup.py`
:Options: None
:Path: `r2s-act/scripts/r2s_step2setup.py`

...............................................................................

Fin.
