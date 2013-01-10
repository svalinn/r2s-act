docs folder readme
==================
This folder is where sphinx documentation of the r2s-act code is managed.

To rebuild documentation, run `rebuild.sh`

A few notes:
- sphinx-apidoc grabs the docstrings from scripts in r2s/ and r2s/io/
- numpydoc is used, which enables docstring formatting with section headings
  - valid section headings are Parameters, Returns, Notes, See Also, Examples, References
  - For further guidance on the proper doc-string format, see: https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt#method-docstrings
- Using the 'build and push to gh-pages and return to branch' approach from here: http://blog.nikhilism.com/2012/08/automatic-github-pages-generation-from.html


