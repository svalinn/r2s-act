User-facing scripts:

r2s_setup.py: Generates a per-problem r2s.cfg file and an ALARA snippet file.
              These two files can be hand-edited to specify the files and input
              values for running r2s_step1.py and r2s_step2.py.

r2s_step1.py: Converts an MCNP (or DAG-MCNP) neutron problem input, and its 
              associated meshtal file, into a set of ALARA inputs files.

r2s_step2.py: Converts a set of ALARA output files into an MCNP (or DAG-MCNP)
              photon problem.

scdmesh.py: Module for representation of structured rectilinear hex meshes
            through PyTAPS; uses the PyTAPS structured mesh extension functions.

scdmesh_convert.py: Utility script to convert old-stype hex meshes into scdmeshes.

==================================================
r2s package contents (most may be invoked as scripts by advanced users): 

r2s/alias.py: Module providing alias table generation and alias sampling method, used 
              by write_gammas.

r2s/mmgrid.py: Python replacement for mmGridGen; uses Monte Carlo techniques to
               estimate material fractions, given a structured mesh and a CAD geometry.

r2s/mcnp_n2p.py: Modifies MCNP neutron problem definition, creating the corresponding
                 photon problem to use with custom source.F90.

r2s/alara_ele2iso.py: Converts ALARA element library file to isotope library file.

r2s/tag_ebins.py: Tags mesh with energy bins boundaries provided in a separate file.

r2s/tag_for_viz.py: Script to prepare visuzliations of volume fractions produced by
                    mmGridGen.  (Not needed for newer workflows, should probably
                    be moved to legacy/)

r2s/data_transfer/read_alara_phtn.py: Turn ALARA photon source output and converts 
                                      it to MOAB representation.

r2s/data_transfer/write_gammas.py: Takes photon source data on a mesh (as 
               produced by PhtnSrcToH5M.py), normalizes source information, and
               generates the 'gammas' file for our custom source.F90 routine.

r2s/data_transfer/read_meshtal.py: Parses an MCNP meshtal output file and 
                                   creates a structured mesh

r2s/data_transfer/write_alara_fluxin.py: Writes an ALARA fluxin file based on 
                              flux-tagged structured mesh from read_meshtal.

r2s/data_transfer/write_alara_geom.py: Writes ALARA geometry description for a
                              structured mesh with material data.

==================================================
legacy/ -- retired scripts that may still be useful for compatibility with problems
           that used older verisons of this workflow.  Should not be used for new 
           problems.

legacy/moab2alara.py: Converts mmgrid output to ALARA geometry and materials definitions.

legacy/FluxParse.py: A script to parse raw MCNP mesh tally files to ALARA flux-in format.
              This is the first step of the workflow.


==================================================

legacy/alt_photon_src: files related to older approach to doing photon source definitions,
using a very elaborate sdef card instead of a custom source routine.

alt_photon_src/obj_phtn_src.py:
Script defines a class for handling the phtn_src file output from ALARA 2.9+.  
Methods parse the file into three equal-length lists: headers (isotope identifiers), cooling steps,
and source strengths in each mesh cell.  
Currently supports up to 994 mesh elements with the gen_sdef_probabilities method.
May eventually convert phtn_src to a format that can be input into MCNP with a source.F90 routine.

alt_photon_src/parse_phtn.py
Script demos the use of obj_phtn_src.py
