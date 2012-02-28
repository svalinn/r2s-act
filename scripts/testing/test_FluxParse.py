#Setup
import linecache
import os
import FluxParse

def test_fluxin():
    ExpectedFluxin=open('testing/expected_fluxin', 'r')
    ExpectedFluxinLines=ExpectedFluxin.readlines()
    os.system('./FluxParse.py testing/test_meshtal 5e13 -o actual_fluxin')
    ActualFluxin=open('actual_fluxin', 'r')
    ActualFluxinLines=ActualFluxin.readlines()
    assert len(ActualFluxinLines) == len(ExpectedFluxinLines)
    for x in [1, 500, 1000, 1500]:
        assert ActualFluxinLines[x] == ExpectedFluxinLines[x]
    os.remove('actual_fluxin')
    os.remove('mesh.vtk')

def test_backwards_fluxes():  
    ExpectedFluxinBack=open('testing/expected_fluxin_back', 'r')
    ExpectedFluxinBackLines=ExpectedFluxinBack.readlines()
    os.system('./FluxParse.py testing/test_meshtal 5e13 -o actual_fluxin_back -b')
    ActualFluxinBack=open('actual_fluxin_back', 'r')
    ActualFluxinBackLines=ActualFluxinBack.readlines()
    assert len(ActualFluxinBackLines) == len(ExpectedFluxinBackLines)
    for x in [1, 500, 1000, 1500]:
        assert ActualFluxinBackLines[x] == ExpectedFluxinBackLines[x]
    os.remove('actual_fluxin_back')   
    os.remove('mesh.vtk')

def test_vtk():
    expected_mesh='testing/expected_mesh.vtk'
    os.system('./FluxParse.py testing/test_meshtal 5e13')
    actual_mesh='mesh.vtk'
    for x in [5557,57794 ,67132, 85836, 104061, 150079, 182191]:
         assert linecache.getline(expected_mesh, x)==\
                linecache.getline(actual_mesh, x)
    os.remove('ALARAflux.in')
    os.remove('mesh.vtk')

    
    
