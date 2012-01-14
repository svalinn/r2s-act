#Setup
from itaps import iBase,iMesh
import os
import reTagMesh

MeshtalInput=open('test_files/test_meshtal', 'r')
MeshtalInputLines=MeshtalInput.readlines()

ExpectedFluxin=open('test_files/expected_fluxin', 'r')
ExpectedFluxinLines=ExpectedFluxin.readlines()

ExpectedFluxinBack=open('test_files/expected_fluxin_back', 'r')
ExpectedFluxinBackLines=ExpectedFluxinBack.readlines()

ExpectedALARAin=open('test_files/expected_ALARA.in', 'r')
ExpectedALARAinLines=ExpectedALARAin.readlines()


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
    p=int(len(ActualFluxinLines)/2)
    q=int(len(ActualFluxinLines)/3)
    for x in [1, p, q]:
        assert ActualFluxinLines[x] == ExpectedFluxinLines[x]
    os.remove('actual_fluxin')

def test_PrintHightoLow():
    reTagMesh.PrintHightoLow(MeshtalInputLines, 14, 512, 175, 5e13, 'actual_fluxin_back')
    ActualFluxinBack=open('actual_fluxin_back', 'r')
    ActualFluxinBackLines=ActualFluxinBack.readlines()
    assert len(ActualFluxinBackLines) == len(ExpectedFluxinBackLines)
    p=int(len(ActualFluxinBackLines)/2)
    q=int(len(ActualFluxinBackLines)/3)
    for x in [1, p, q]:
        assert ActualFluxinBackLines[x] == ExpectedFluxinBackLines[x]
    os.remove('actual_fluxin_back')

def test_entire_program ():
    os.system('python reTagMesh.py test_files/test_matFracs.h5m -m test_files/test_meshtal -n 5e13 -v 125')
    #testing fluxin file
    ActualFluxin=open('ALARAflux.in', 'r')
    ActualFluxinLines=ActualFluxin.readlines()
    assert len(ActualFluxinLines) == len(ExpectedFluxinLines)
    p=int(len(ActualFluxinLines)/2)
    q=int(len(ActualFluxinLines)/3)
    for x in [1, p, q]:
        assert ActualFluxinLines[x] == ExpectedFluxinLines[x]
    
    #testing ALARA.in file
    ActualALARAin=open('ALARA.in', 'r')
    ActualALARAinLines=ActualALARAin.readlines()
    for x in [3, 3108, 3189, 3234]:
        print x
        assert ActualALARAinLines[x] == ExpectedALARAinLines[x]
        
    #deleting all output files
    for x in ['ALARAflux.in','ALARA.in','matFracs_results', 'mesh.vtk']:
        os.remove(x)
    


       
######################################
#Step 1: Testing using atypical input
######################################

#def test_check_meshpoints(MeshtalInputLines, m, j, k, mesh)
#    assert not



    




