Intro
------
This folder provides a framework for implementing methods of uniformly sampling random points in arbitrary tetrahedrons.  Multiple methods are stored here, so that their relative efficiencies can be compared (with each other, and other discovered methods).

We do this testing in Fortran, with timing to verify efficiency.

Proving uniformity is based on assumed veracity of references, and visual inspection via plotting in Mathematica and/or Python. (more rigorous approaches may tackled later)

Current conclusion
-------------------
Method 1 samples 1e9 positions in about 64 seconds. (on Hova, at 2.67 GHz)
Method 2 is slower by a factor of about 5.5.

How tests are set up
---------------------
Each subfolder has a code file, e.g. `tetsample.F90`, which is compiled along with `source_data.F90` and `mcnp_placeholder.F90`, and then used in test programs `test_speed.F90` and `test_correct_pos.F90`.

Each folder contains the scripts `build_and_run.sh` and `build_and_plot.sh`.  Run these to test the method in the folder.

`build_and_plot.sh`/`test_correct_pos.F90`/`plot_tet_points` take 5000 samples and plot the points.  Additionally, the four points of the sampled tetrahedron are also plotted (in red), and are used to verify that the points fall within the tetrahedron.

`build_and_run.sh` times the cpu time spent sampling particles for 10 different tetrahedra stored `in points.txt`.

Methods
--------
The literature...

Method 1
========
Rocchini & Cignoni (2001) describe how to sample uniformly within the 'reference' tetrahedron using 3 random variates.  See 'Generating Random Points in Tetrahedron' (2001) in the CNERG Zotero database, as well as the accompanying Mathematica notebook in Zotero.

We can modify this sampling to apply to any tetrahedron.  Wolfram/MathWorld describes how to pick points in a triangle. (http://mathworld.wolfram.com/TrianglePointPicking.html)  We sample a point p, corresponding with a postion (x,y) as::
        p = a1*v1 + a2*v2

Where v1 and v2 are the vectors from one point on the triangle to the other two points on the triangle; and a1, a2 are uniform variates in the interval [0,1].

::
  px = a1*v1x + a2*v2x
  py = a1*v1y + a2*v2y

However, if we just sample a1 and a2, we actually sample a parallelogram, equivalent to two of our triangles... To sample only our triangle, we need to filter and discard/transform those points not in the triangle.
What Rocchini and Cignoni describe is a method for transforming these points in the 3D case.  Rocchini and Cignoni describe a 2 step method.  The first step is in fact the transform for the 2D case.

Method 2
=========
From John Burkardt's Virginia Tech IT Department class lecture 'Computational Geometry Lab: MONTE CARLO ON TETRAHEDRONS'

We are told to use 4 random variates to get the barycentric coordinates of our sampled point.
This point has barycentric cooardinates (L1,L2,L3,L4), with sum(L1,L2,L3,L4)=1.0.

Via http://en.wikipedia.org/wiki/Barycentric_coordinates_%28mathematics%29 we learn that in the 2D case an x,y coordinate is found by scaling the triangle's x,y vertice values (v1,v2,v3,v4; where v1 is the point (x1,y1)) by the barycentric coordinate values as::

        x=L1*x1 + L2*x2 + L3*x3
        y=L1*y1 + L2*y2 + L3*y3

Or in 3D::

        x=L1*x1 + L2*x2 + L3*x3 + L4*x4
        y=L1*y1 + L2*y2 + L3*y3 + L4*y4
        z=L1*z1 + L2*z2 + L3*z3 + L4*z4



Analysis of methods
-------------------
Here, observations on speed of different methods are noted.

Method 1
========
Rocchini & Cignoni's method results in 1e9 samplings in 64s on Hova(2.67 GHz)

Method 2
========
This method results in 1e9 samplings in about 355s on Hova(2.67 GHz)

- This is a factor of ~5.5 slower than method 1.
- The natural logarithms take about 70% of the CPU time
  - Tested by removing the log() calls
- The four random numbers takes about 10% of the CPU time
  - Tested by sampling an extra 4 number (without using log() on these #s)

