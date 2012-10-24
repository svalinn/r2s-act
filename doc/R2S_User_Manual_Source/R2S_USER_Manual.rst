###############################################################################
University of Wisconsin Rigorous Two Step Activation Work Flow (UW-R2S) User Manual
###############################################################################

...............................................................................

.. contents:: Table of Contents

...............................................................................

===============================================================================
Introduction
===============================================================================
_______________________________________________________________________________
The Rigorous Two Step (R2S) Method
_______________________________________________________________________________

The Rigorous Two Step (R2S) method is used to determine the photon fluxs that result from neutron activation of materials for a given geometry. The first step of this method is neutron transport over some geometry, in order to calculate flux distributions in space and energy. Using this neutron flux distribution and information about the isotopes present within the geometry, material activation calculations can be done in order to calculate a distribution of photon sources strengths in space and energy. The second step of R2S is doing a photon transport calculation these decay photons, in order to determine a photon flux distribution in space and energy. The "two step" part of the name specifies that neutron and photon transport steps are done seperately, as opposed to the Direct One Step (D1S) method which preforms both transport calculations simotaneously.
 
_______________________________________________________________________________
University of Wisconsin Rigorous Two Step Activation Work Flow (UW-R2S)
_______________________________________________________________________________

UW-R2S is composed of a series of scripts written in the Python programming langauge to facilitate R2S calculations in complex 3D geometries. The end product of UW-R2S is a single Cartesian mesh file with each voxel tagged with:

1. neutron fluxes for every neutron energy group, total neutron flux (neutrons/cm^2/s)
2. material fraction for every material in the geometry
3. photon source strength for every photon energy group (photons/cm^2/s)
4. total photon source strength (photons/s)
5. photon flux and or dose for every photon energy group, total flux and/or dose (photons/cm^2/s, any dose units)

The backbone of UW-R2S are the physics codes used for transport and activation. The Direct Accelerated Monte Carlo (DAG-MC) version of MCNP5 (Los Alamos National Laboratory), known as DAG-MCNP5 (UW-Madison) is used for both neutron and photon transport. This allows for geometery and materials information to be specified using CAD software, namely CubIt (Sandia National Laboratory). For a photon transport step, a custom compiled version of DAG-MCNP5, with a custom source.F90, is used. Analytic and Laplacian Adaptive Radioactivity Analysis (ALARA), developed at UW-Madison is used for material activation.

...............................................................................

===============================================================================
Set-up and Dependencies
===============================================================================

UW-R2S has numerous dependencies:

1. Python
2. DAG-MCNP5 compiled with UW-R2S source.F90
3. CubIt
4. ALARA
5. Mesh Oriented Data Base (MOAB)
6. PyTAPS, the Python interface for ITAPS, (Interoperable Technologies for Advanced Petascale Simulations)

Aside from MCNP5 and CubIT, availible from RSICC, all other codes are open source with well documented installation instructions.

...............................................................................

===============================================================================
Running UW-R2S
===============================================================================

UW-R2S contains 2 wrapper scripts (r2s\_step1.py, r2s\_step2.py) that call all necessary scripts in the correct order. One can imagine cases were a user would want to run certain scripts indivially, which is also an option. The suggested workflow, using the wrapper scripts is detailed below:

1. Create geometry. Using CubIt, create the geometry specify materials by adding volumes to materials groups. Groups should be formated like "mat_X_rhoY" where X is the material number and Y is either mass density (must be negative) or atom density (must be positive). Instructions for doing this can be found in the DAG-MCNP user manual. Be sure to remember to imprint and merge all of the geometry. Once completed, export the geometry as a .sat file and specify and ACIS version of 1600. Next, write and MCNP input file for your problem, including everything but the geometry. Alternatively, if the geometry already exists in the form of an MCNP input file, MCNP2CAD can be used to convert the geometry information from the MCNP input file into a .sat file. Once the .sat file exists, it can be converted to an .h5m file using dagmc\_preproc. This is not necessary, but it prevents DAG-MCNP5 from having to process the .sat file every time it is run. Using a .h5m file also allows for the use of of a DAG-MCNP5 version that is not build against CubIt.

2. Create/Run DAG-MCNP input file. Other than the geometry cards, the rest of the DAG-MCNP input file should be identical to that of a native MCNP input file. DAG-MCNP5 input files must contain an FMESH4 tally of the geometry of interest for neutron activation. The output from this tally will appear in a MCNP meshtal output file, in units of neutrons/cm2/source particle. This output need to be converted to flux, by multiplying by the total neutron source strength, oftentimes refered to as the neutron normalization factor, which has units of source particles/time. The reccommended way of doing this is to use and FM tally multiplier card  to specify the neutron normalization factor on the FMESH4 tally, which will result in a meshtal file with fluxes in the correct units. If this is not done, normalization can be done using the read_meshtal.py script, but this is not a default option in r2s_step1.py.

3. Run r2s_setup.py. This script creates a configuration files called "r2s.cfg" and "alara_snippet" 

4. Modify r2s.cfg to suit the problem. The configuration file allows the user to specify the names of files used by and created by r2s_step1.py, ALARA, and r2s_step2.py, if desired, and also important parameters. The file r2s.cfg is printed with default file names and parameters and also some instructive annotations. Typically there is no reason to change the file names aside from personal preference. In order to better understand the parameters specified, users should consult the "R2S Step 1" and "R2S Step 2" protion of this file.

5. Create ALARA materials library. The script mats2ALARA.py can be used to convert MCNP materials defintions to ALARA materials defintions. However, generally speaking activation defintions should be much more detailed than transport definitions, as minor impurities can dominate activations. ALARA material libraries rely on isotope libraries. ALARA element libaries can be converted to isotope libraries using alara_ele2iso.py.

6. Modify ALARA snippet. The ALARA snippet file is appended to the ALARA geometry file produced by r2s_step1.py to created the full ALARA input file. Most of the entries in the default snipppet produced r2s_setup.py need not be changed. However, every problem will have a different irradiation schedule so special attention should be taken to change this from default irradiation schedule. The ALARA snippet file also specifies the isotope library, material library, and data libraries. These libaries, or links to them must be present in the folder that ALARA is run out of. The default activation and photon source libraries are both specified as "FENDL2" in the ALARA snippet. However, soft links to these files must be named "FENDL2.bin" and "FENDL2.gam" for the activtion and photon source libraries, respectively.

7. Run r2s_step1.py. This script is a wrapper script that reads the meshtal, geometry, MCNP neutron input file, and alara_snippet file specified in r2s.cfg and outputs a complete ALARA input file and a structed mesh file tagged with neutron fluxes and materials.

8. Run ALARA. Asssuming the ALARA snippet file was written corrrectly and appended, this step should be a single command. ALARA reads in the geometry, material, and irradiation scheduling information from the ALARA input file and outputs a file containing photon source strengths (phtn_src) for every voxel and energy group.

9. Run r2s_step2.py. This script takes an ALARA phtn_src, tags the information onto the structured mesh file from step 1 and creates a "gammas" file used to specify the photon source distribution for the gamma transport step. It also modified the MCNP neutron input file to create an MCNP photon input file. However this file may need additional user attention before running DAG-MCNP, especially if the photon tally region is different from the neutron tally region.
11. Run DAG-MCNP with Source.F90 on
10. Run read_meshtal.py with the -m flag in order to tag the photon flux/dose

...............................................................................

===============================================================================
R2S Step 1
===============================================================================

The script r2s_step1.py automatically run all of the Step 1 scripts in the proper order, using the file names and parameters specified in the r2s.cfg file. Certain use cases my required running this script individually. The steps that r2s_step1.py runs are detailed below. Description of the individual scripts are found in "Scripts run by r2s_step1.py"

_______________________________________________________________________________
r2s_step1.py
_______________________________________________________________________________

**Purpose**: This script is a wrapper script that reads the meshtal, geometry, MCNP neutron input file, and alara_snippet file specified in r2s.cfg and outputs a complete ALARA input file and a structed mesh file tagged with neutron fluxes and materials.
**Inputs**: r2s.cfg
**Outputs**: ALARA input file, structured mesh with neutron fluxes and uncertainties, materials and uncertainties.
**Command Line Syntax**: ./r2s_step1.py
**Options**: None
**Path**: r2s-act/scripts/r2s_step1.py

_______________________________________________________________________________
Scripts run by r2s_step1.py
_______________________________________________________________________________
This scripts are listed in chronological order of when they are run. Most of these scripts can be run with a -h flag for usage and command line options.

...............................................................................
r2s/io/read_meshtal.py:
...............................................................................

**Purpose**: This script reads in an MCNP mesthtal file and 
**Inputs**: MCNP meshtal file
**Outputs**: Structure mesh tagged with fluxes and errors
**Command Line Syntax**: 
**Options**:
**Path**:r2s-act/scripts/r2s/io/read_mesthal.py

...............................................................................
mmgrid.py
...............................................................................

**Purpose**: This script is used calculate average material definitions for each mesh voxel. Most geometries do not conform to the Cartestian mesh dictatied by MCNP fmesh4 tallies. Voxels that contain multiple volumes are likely to contain mulitple materials, so the ALARA materials assigned to these voxels must be a mixture of materials from the MCNP files. This script uses Monte Carlo ray-tracing to determine the volume fractions of each material in each voxel and then writes corresponding ALARA geometry and materials entries, and tags mesh will the material defintions.

**Inputs**: geometry file (.sat or .h5m), structured mesh file

**Outputs**: ALARA geometery and materials entries

**Command Line Syntax**: mmgrid.py [options] geometry_file [structured_mesh_file]

**Options**:
  -h, --help            help message and exit
  -n NUMRAYS            Set N. N^2 rays fired per row.  Default N=20
  -g, --grid            Use grid of rays instead of randomly selected starting
                        points
  -o OUTPUT_FILENAME, --output=OUTPUT_FILENAME
                        Output file name, default=mmgrid_output.h5m
  -q, --quiet           Suppress non-error output from mmgrid
  -d NDIVS, --divs=NDIVS
                        Number of mesh divisions to use when inferring mesh
                        size, default=10
  -a ALARA_GEOM_FILE, --alara=ALARA_GEOM_FILE
                        Write alara geom to specified file name

**Path**: r2s-act/scripts/r2s/mmgrid.py

...............................................................................

...............................................................................

**Purpose**:
**Inputs**:
**Outputs**:
**Command Line Syntax**:
**Options**:
**Path**:


r2s/io/write_alara_fluxin.py: Writes an ALARA fluxin file based on flux-tagged structured
                              mesh from read_meshtal

r2s/io/write_alara_geom.py: Writes ALARA geometry description for a structured mesh with
                            material data

_______________________________________________________________________________
Parameters for r2s_step1.py
_______________________________________________________________________________

# The number of rays per mesh row to fire
# during Monte Carlo generation of the macromaterial grid.
# Raising this number will reduce material errors, but 
# also increase the runtime of r2s_step1.
mmgrid_rays = 10

# If step2setup is 1, runs the r2s_step2setup.py script at the end of 
#  r2s_step1.py.  r2s_step2setup.py creates folders for all cooling steps
#  and isotopes specified
step2setup = 0

...............................................................................

===============================================================================
R2S Step 2
===============================================================================

_______________________________________________________________________________
r2s_step2.py
_______________________________________________________________________________

_______________________________________________________________________________
Scripts run by r2s_step2.py
_______________________________________________________________________________

...............................................................................

===============================================================================
Other Scripts Pertainent to the R2S work flow.
===============================================================================

r2s/alara_ele2iso.py: Converts ALARA element library file to isotope library file.

r2s/tag_ebins.py: Tags mesh with energy bins boundaries provided in a separate file.



