This test problem is used to verify that voxel sampling resamples a voxel when particles are started in a void.  This is done with a single voxel with a central cylindrical void.

To run the test problem:

``../../mcnp5p_refactor i=void_rejection_test.inp``

Then, plot the results (requires that matplotlib is installed):

``python verification.py``

The resulting plot should be a square filled with points, but no points within an internal circle.  If this is not the case, then void rejection is probably not functioning correctly.
