#Setup
import linecache
import os
import unittest
import itertools

import FluxParse

izip = itertools.izip_longest

class FluxParseTest( unittest.TestCase ):

    def test_fluxin(self):
        ExpectedFluxin=open('testing/expected_fluxin', 'r')
        FluxParse.main('testing/test_meshtal 5e13 -o actual_fluxin -p mesh.vtk'.split())
        ActualFluxin=open('actual_fluxin', 'r')
        for lineno, (i1,i2) in enumerate( izip(ActualFluxin, ExpectedFluxin), 
                                          start=1 ):
            self.assertEqual( i1, i2, 'Unequal line number {0}'.format(lineno) )
        os.remove('actual_fluxin')
        os.remove('mesh.vtk')

    def test_backwards_fluxes(self):  
        ExpectedFluxinBack=open('testing/expected_fluxin_back', 'r')
        FluxParse.main( 'testing/test_meshtal 5e13 -o actual_fluxin_back -b -p mesh.vtk'.split() )
        ActualFluxinBack=open('actual_fluxin_back', 'r')
        for lineno, (i1,i2) in enumerate( izip(ActualFluxinBack, ExpectedFluxinBack),
                                          start=1 ):
            self.assertEqual( i1, i2, 'Unequal line number {0}'.format(lineno) )
        os.remove('actual_fluxin_back')   
        os.remove('mesh.vtk')

    def test_vtk(self):
        expected_mesh=open('testing/expected_mesh.vtk', 'r')
        FluxParse.main('testing/test_meshtal 5e13 -p mesh.vtk'.split())
        actual_mesh=open('mesh.vtk', 'r')
        for lineno, (i1,i2) in enumerate( izip(actual_mesh, expected_mesh),
                                          start=1 ):
            self.assertEqual( i1, i2, 'Unequal line number {0}'.format(lineno) )
        os.remove('ALARAflux.in')
        os.remove('mesh.vtk')
