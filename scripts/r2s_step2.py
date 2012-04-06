#! /usr/bin/env python

from r2s.io import read_alara_phtn, write_gammas
from r2s import mcnp_n2p
from scdmesh import ScdMesh, ScdMeshError
from itaps import iMesh, iMeshExtensions

smesh = ScdMesh.fromFile(iMesh.Mesh(), "junk.h5m")

read_alara_phtn.read_to_h5m("phtn_src", smesh, isotope="TOTAL", coolingstep=0, \
        retag=True, totals=True)

write_gammas.gen_gammas_file_from_h5m(smesh)

# Set dagmc to True if input only contains the title card and data block
dagmc=False
mod = mcnp_n2p.ModMCNPforPhotons("simplebox-3_mcnp", dagmc)
mod.read()

if not dagmc:
    mod.change_block_1()
    mod.change_block_2()
mod.change_block_3()

mod.write_deck("inp_p")
