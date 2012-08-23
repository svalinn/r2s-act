This folder contains modified versions of custom source.F90 files and a link to the custom-compiled dag-mcnp executables that use these custom source.F90 files.

As of May 21, 2012, the most up to date/capable source.F90 and executable are source_gamma_voxel_alias.F90 and mcnp5p_voxel, respectively.
----------

The different source.F90 versions:

From KIT (Germany): (originals are in mcnp_source/vendor folder)
a) source_gamma_meshtal1.F90
b) source_gamma_meshtal2.F90

Extensively modified from KIT originals
c) source_gamma_meshtal2_alias.F90
d) source_gamma_voxel_alias.F90


More information about each file:
a) Not used (uses RDUM and IDUm cards in MCNP; have not tried to get this working)
b) Original was modified from 24 energy groups to 42 groups and to use dynamic array allocation for the phtn source information. The file it looks for is called 'gammas'
c) Modifications to read a different format gammas file so that an alias table is used to chose the photon energy.  This is provides a small speedup (~1-3%). Looks for file 'gammas_alias' instead.
d) Derived from source_gamma_meshtal2.F90; Implements alias table sampling of voxels, as well as alias table sampling of photon energies. Also implements biasing. Uses 'gammas' file that can include bias values and custom energy bins, and stores energy bins in alias table format.

----------
You must be in the svn-dagmc group to access the modified executables. If on CAE, ideally use the links in the r2s-act/mcnp_source folder. The actual executables are managed by Eric Relson (5-21-2012).

Custom-compiled dag-mcnp/mcnp5 executable links:
e) mcnp5p_uniform: compiled with source_gamma_meshtal2.F90
f) mcnp5p_uniform_alias: compiled with source_gamma_meshtal2_alias.F90
g) mcnp5p_voxel: compiled with source_gamma_voxel_alias.F90

----------
One should be able to use the mcnp5p links for running problems.

Alternately, to use one of these in a custom compile of MCNP/DAG-MCNP, one can link the files in the repository to the
DAG-MCNP/5.1.51/trunk/Source/src folder like this:
ln -s *path to this folder*/source_gamma_meshtal2.F90 source.F90

(or you could copy the file to that folder, but it won't get updated when changes happen in the repository)

To *compile* MCNP/DAG-MCNP:

We call the build scripts from within the /5.1.51/trunk/Source folder.
Since we are using some custom code, the .o files are in the way... use 'clean' (But this also gives an error so we build twice...); do the following two commands:
1:
>> ../scripts/build_dagmc clean
<< error messages...
2:
>> ../scripts/build_dagmc
<< Success!

You can now call the mcnp5 executable in Source/src.

If you make further modifications to the same source.F90, you can usually recompile directly with the second command above (clean is not needed).

You can make it easy to call my using an alias command in your .bashrc file, e.g.
alias mcnp5p='$HOME/DAG-MCNP/5.1.51/trunk/Source/src/mcnp5'
----

