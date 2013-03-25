University of Wisconsin-Madison Rigorous Two Step Activation Work Flow (R2S-ACT)
________________________________________________________________________________
The Rigorous Two Step (R2S) method is used to determine the photon fluxes that result from neutron activation of materials for a given geometry.
This repository is set of scripts used to carry out an R2S workflow using the DAG-MCNP and ALARA codes. For more information on the workflow itself, see the user-guide_.

.. _user-guide: http://svalinn.github.com/r2s-act/r2s-userguide.html


This Repository
=================
R2S-ACT is primarily a set of Python scripts, located in the `scripts/` folder.
Additionally, R2S-ACT implements mesh-based photon source sampling in DAG-MCNP, using a custom `source.F90` module.  This source routine and related files are in `mcnp_source/`.
Documentation is a mix of static and automatically generated content, located in `docs/`, and is rebuilt with Sphinx, via the `rebuild.sh` script.

Dependencies
===============================================================================
R2S-ACT has numerous dependencies:

1. Python 2.6+
2. DAG-MCNP5 compiled with a custom R2S-ACT `source.F90` file from `mcnp_source/`, from https://github.com/svalinn/DAGMC
3. CubIt, from RSICC, http://rsicc.ornl.gov/
4. ALARA, from https://github.com/svalinn/ALARA
5. Mesh Oriented Data Base (MOAB), from https://svn.mcs.anl.gov/repos/ITAPS/MOAB/trunk
6. PyTAPS, the Python interface for ITAPS, (Interoperable Technologies for Advanced Petascale Simulations), from http://pypi.python.org/pypi/PyTAPS/1.4
7. PyNE, *Python for Nuclear Engineering*, from http://pynesim.org/
   (Has its own dependencies listed at https://github.com/pyne/pyne)

Aside from MCNP5 and CubIt, available from RSICC, all other codes are open source with well documented installation instructions.

The user guide and other documentation is available at http://svalinn.github.com/r2s-act/ .
Building the documentation requires Sphinx, from http://sphinx-doc.org

Although not a dependency, the visualization program VisIT (Lawrence Livermore National Laboratory) is useful for visualizing results data stored on MOAB meshes in the .vtk format.
Executables are available at https://wci.llnl.gov/codes/visit/.
