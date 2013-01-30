cd resample_slab_uv
rm out? runtp? meshta? -f
~/DAG-MCNP/5.1.51/trunk/Source/src/mcnp5 i=mcnp.inp
cd ..
cd resample_slab_ua
rm out? runtp? meshta? -f
~/DAG-MCNP/5.1.51/trunk/Source/src/mcnp5 i=mcnp.inp
cd ..
cd resample_slab_vv
rm out? runtp? meshta? -f
~/DAG-MCNP/5.1.51/trunk/Source/src/mcnp5 i=mcnp.inp
cd ..
gvim -p resample_slab_uv/meshtal resample_slab_ua/meshtal resample_slab_vv/meshtal
