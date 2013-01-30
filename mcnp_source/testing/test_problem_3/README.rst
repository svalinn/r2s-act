Intro
------
Updated 1-30-2012

This test is to compare resampling within the voxel (during uniform sampling) with resampling the entire problem. We also compare with voxel sampling/voxel resampling. That is, three tests:

* uniform sampling, resample voxel (uv)
* uniform sampling, resample entire problem (ua)
* voxel sampling, resample voxel (vv)

Run test
--------
Run the tests with `./run_slab_tests.sh`.  gvim will open with three tabs showing the resulting meshtally files.  Expected results ::

        ua            vv            uv
        7.24967E-05   5.83892E-04   7.24251E-05
        8.94282E-05   7.21529E-04   8.93813E-05
        9.14388E-05   7.37926E-04   9.14459E-05
        8.91902E-05   7.23459E-04   8.91839E-05
        7.19423E-05   5.85370E-04   7.20832E-05
        7.23990E-05   5.80770E-04   7.26439E-05
        8.99487E-05   7.19822E-04   8.97783E-05
        9.18258E-05   7.41229E-04   9.18563E-05
        8.89459E-05   7.22244E-04   8.87474E-05
        7.21967E-05   5.83422E-04   7.21596E-05

We get the same result in both ua and uv since the voxels all have equal void fractions.  The vv case has the same shape, but different numbers due to using the same gammas file contents.

If uv and ua don't match, there's probably a bug...

Problem description
-------------------
The geometry of the test is an RPP, with a central non-void slab, and void (imp:p=1) on either side, surounded by graveyard.::

  x ->
  y .
  z ^

Materials::

  __________________
  | v  | mat  | v  |
  | o  |      | o  |
  | i  |      | i  |
  | d  |      | d  |
  |____|______|____|

The mesh tally (1-group flux) being used is 2x1x5::

  __________________
  |___1____|__6____|
  |____2___|___7___|
  |___3____|__8____|
  |____4___|___9___|
  |___5____|__10___|

So we have a bunch of part-void voxels (50% void 50% material for now...)

We expect to get the same results on both half of the problem ::
  1<2<3>4>5, and 1 = 6, 3 = 8, etc.

We expect to get the same relative distribution of results for both uniform and voxel sampling; e.g.::
  1(vv)/3(vv) == 1(uv)/3(uv), etc.

Since the source lines in the three gammas files are all the same, the actual result in vv is different from uv and ua.
This is due to voxel sampling dealing with *total voxel source strengths* and uniform sampling dealing with *average volumetric source strength*.

