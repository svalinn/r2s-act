# regenerate the .rst files for modules in scripts/r2s/ and below
sphinx-apidoc -f -o r2s ../scripts/r2s
# then make html as usual
make html
