# This is mean to be run from r2s-act/, NOT from r2s-act/docs/
# See docs/README.rst

# regenerate the .rst files for modules in scripts/r2s/ and below
sphinx-apidoc -f -o docs/r2s scripts/r2s
# then make html as usual
make html
