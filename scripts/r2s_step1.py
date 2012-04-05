#! /usr/bin/env python

from r2s.io import read_meshtal, write_alara_fluxin, write_alara_geom
from r2s import mmgrid
from pydagmc import dagmc

smesh = read_meshtal.read_meshtal('meshtal')
#smesh.mesh.save( 'parsed_meshtal.vtk' )

dagmc.load( 'hemispheres_preproc.h5m' )

grid = mmgrid.mmGrid( smesh )
grid.generate( 10, False )
grid.createTags()

smesh.mesh.save('alldata.vtk')

write_alara_geom.write_alara_geom( 'alara_geom', smesh )
write_alara_fluxin.write_alara_fluxin( 'alara_fluxin', smesh )
