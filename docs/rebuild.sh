# This script handles preparing for and running sphinx-apidoc.
# This script is called by make, and probably never needs to be called manually
# This script meant to be run from r2s-act/, NOT from r2s-act/docs/
# See docs/README.rst

# create fake list of functions and docstrings from source_gamma.F90
mkdir scripts/r2s/mcnp/
echo pass > scripts/r2s/mcnp/__init__.py
python docs/gen_source_gamma_doc.py mcnp_source/source_gamma.F90 scripts/r2s/mcnp/source_gamma_doc.py

# regenerate the .rst files for modules in scripts/r2s/ and below
sphinx-apidoc -f -o docs/r2s scripts/r2s
