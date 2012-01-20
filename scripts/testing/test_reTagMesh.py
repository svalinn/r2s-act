#Setup
from itaps import iBase,iMesh
import os
import reTagMesh

MeshtalInput=open('testing/test_meshtal', 'r')
MeshtalInputLines=MeshtalInput.readlines()

ExpectedFluxin=open('testing/expected_fluxin', 'r')
ExpectedFluxinLines=ExpectedFluxin.readlines()

ExpectedFluxinBack=open('testing/expected_fluxin_back', 'r')
ExpectedFluxinBackLines=ExpectedFluxinBack.readlines()

ExpectedALARAin=open('testing/expected_ALARA.in', 'r')
ExpectedALARAinLines=ExpectedALARAin.readlines()

ExpectedMatFracsResults=open('testing/expected_matFracs_results', 'r')
ExpectedMatFracsResultsLines=ExpectedMatFracsResults.readlines()

ExpectedMesh=iMesh.Mesh()
ExpectedMesh.load('testing/expected_mesh.vtk')
ExpectedFracs=ExpectedMesh.getTagHandle("FRACTIONS")


#####################################
#Step 1: Testing using typical input 
#####################################
def test_FindFirstLine():
    assert reTagMesh.FindFirstLine(MeshtalInputLines)==14 #m
   
def test_MeshPointCount():
    assert reTagMesh.MeshPointCount(MeshtalInputLines, 14) ==512 #j

def test_EnergyGroupCount():
    assert reTagMesh.EnergyGroupCount(MeshtalInputLines, 14, 512) ==175 #k

def test_PrintLowtoHigh():
    reTagMesh.PrintLowtoHigh(MeshtalInputLines, 14, 512, 175, 5e13, 'actual_fluxin')
    ActualFluxin=open('actual_fluxin', 'r')
    ActualFluxinLines=ActualFluxin.readlines()
    assert len(ActualFluxinLines) == len(ExpectedFluxinLines)
    for x in [1, 500, 1000, 1500]:
        assert ActualFluxinLines[x] == ExpectedFluxinLines[x]
    os.remove('actual_fluxin')

def test_PrintHightoLow():
    reTagMesh.PrintHightoLow(MeshtalInputLines, 14, 512, 175, 5e13, 'actual_fluxin_back')
    ActualFluxinBack=open('actual_fluxin_back', 'r')
    ActualFluxinBackLines=ActualFluxinBack.readlines()
    assert len(ActualFluxinBackLines) == len(ExpectedFluxinBackLines)
    for x in [1, 500, 1000, 1500]:
        assert ActualFluxinBackLines[x] == ExpectedFluxinBackLines[x]
    os.remove('actual_fluxin_back')

def test_entire_program ():
    os.system('python reTagMesh.py testing/test_matFracs.h5m -m testing/test_meshtal -n 5e13 -v 125')
    #testing fluxin file
    ActualFluxin=open('ALARAflux.in', 'r')
    ActualFluxinLines=ActualFluxin.readlines()
    assert len(ActualFluxinLines) == len(ExpectedFluxinLines)
    for x in [1, 500, 1000, 1500]:
        assert ActualFluxinLines[x] == ExpectedFluxinLines[x]
    
    #testing ALARA.in file
    ActualALARAin=open('ALARA.in', 'r')
    ActualALARAinLines=ActualALARAin.readlines()
    for x in [3, 3108, 3189, 3234]:
        assert ActualALARAinLines[x] == ExpectedALARAinLines[x]

    #testing matFracs_results file
    ActualMatFracsResults=open('matFracs_results', 'r')
    ActualMatFracsResultsLines=ActualMatFracsResults.readlines()
    for x in [9, 124, 188, 513]:
        assert ActualMatFracsResultsLines[x]==ExpectedMatFracsResultsLines[x]

    #testing mesh.vtk file
    ActualMesh=iMesh.Mesh()
    ActualMesh.load('mesh.vtk')
    AcutalFracs=ActualMesh.getTagHandle("FRACTIONS")
    for x in [70, 150, 300, 350, 400]:
        for y in [1, 2]:
            assert ExpectedFracs[ExpectedMesh.getEntities(iBase.Type.region)][x][y] == AcutalFracs[ActualMesh.getEntities(iBase.Type.region)][x][y]    
        
    #deleting all output files
    for x in ['ALARAflux.in','ALARA.in','matFracs_results', 'mesh.vtk']:
        os.remove(x)
     
######################################
#Step 2: Testing using atypical input
######################################

#def test_check_meshpoints(MeshtalInputLines, m, j, k, mesh)
    



    




