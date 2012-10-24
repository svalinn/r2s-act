###############################################################################
University of Wisconsin Rigorous Two Step Activation Work Flow (UW-R2S) User Manual
###############################################################################

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

===============================================================================
Running UW-R2S
===============================================================================

UW-R2S contains 2 wrapper scripts (r2s\_step1.py, r2s\_step2.py) that call all necessary scripts in the correct order. One can imagine cases were a user would want to run certain scripts indivially, which is also an option. The suggested workflow, using the wrapper scripts is detailed below:

1. Create geometry. Using CubIt, create the geometry specify materials by adding volumes to materials groups. Groups should be formated like:

mat_n_rho_x

where n is the material number and x is either mass density (must be negative) or atom density (must be positive). Instructions for doing this can be found in the DAG-MCNP user manual. Be sure to remember to imprint and merge all of the geometry. Once completed, export the geometry as a .sat file and specify and ACIS version of 1600. Next, write and MCNP input file for your problem, including everything but the geometry. Alternatively, if the geometry already exists in the form of an MCNP input file, MCNP2CAD can be used to convert the geometry information from the MCNP input file into a .sat file. Once the .sat file exists, it can be converted to an .h5m file using dagmc\_preproc. This is not necessary, but it prevents DAG-MCNP5 from having to process the .sat file every time it is run. Using a .h5m file also allows for the use of of a DAG-MCNP5 version that is not build against CubIt.

2. Run r2s_setup.py. This script creates a configuration file called r2s.cfg.
3. Modify r2s.cfg to suit the problem. The configuration file allows the user to specify the names of files used by and created by r2s.cfg, and also important parameters, detailed in the r2s.cfg section.
4. Run r2s_step1.py
5. Run ALARA
6. Run r2s_step2.py
7. Run read_meshtal.py to mesh with final photon fluxes

===============================================================================
Step 1 Scripts and Parameters
===============================================================================

_______________________________________________________________________________
Scripts
_______________________________________________________________________________




