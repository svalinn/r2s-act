#! /usr/bin/env python
#Setup
from itaps import iBase,iMesh
import reTagMesh
MeshtalInput=open('test_meshtal1', "r")
MeshtalInputLines=MeshtalInput.readlines()

#####################################
#Step 1: Testing using typical input 
#####################################
def test_FindFirstLine():
    assert reTagMesh.FindFirstLine(MeshtalInputLines)==14
   
def test_MeshPointCount():
    assert reTagMesh.MeshPointCount(MeshtalInputLines, 14) ==27

def test_EnergyGroupCount():
    assert reTagMesh.EnergyGroupCount(MeshtalInputLines, 14, 27) ==175




    
if __name__=='__main__':
    test_FindFirstLine()
    test_MeshPointCount()
    test_EnergyGroupCount()
