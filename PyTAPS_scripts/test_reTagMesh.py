#! /usr/bin/env python
import reTagMesh
import test_meshtal1
import test_reTagMesh.py

#####################################
#Step 1: Testing using typical input 
#####################################
def test_FindFirstLine():
    assert reTagMesh.FindFirstLine(test_meshtal1) ==14

def test_MeshPointCount():
    assert reTagMesh.MeshPointCount(test_meshtal1, 14) ==27

def test_EnergyGroupCount():
    assert reTagMesh.EnergyGroupCount(test_meshtal1, 14, 27) ==175




