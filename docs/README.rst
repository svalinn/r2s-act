docs/ folder readme
==================
This folder is where documentation of the r2s-act code is managed and built using Sphinx.

To rebuild documentation, make sure you are on the `master` branch.
Run `make gh-pages` in the base level of the repository (not in `docs/`).
This will automatically switch to `gh-pages`,
pull the latest documentation source from `master`, rebuild, and push to Github.

To rebuild documentation without updating Github, run `docs/rebuild.sh` in top level of the repo. (`make html` doesn't grab docstrings)

A few other notes:

- Some extensions for sphinx (numpydoc in particular) are used. These are stored in `docs/_sphinxext`
- sphinx-apidoc grabs the docstrings from scripts in r2s/ and r2s/io/
- numpydoc is used, which enables docstring formatting with section headings
  - valid section headings are Parameters, Returns, Notes, See Also, Examples, References
  - For further guidance on the proper doc-string format, see:
    https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt#method-docstrings
- We are using a modified implementation of the 
  'build and push to gh-pages and return to branch' approach 
  from here:
  http://blog.nikhilism.com/2012/08/automatic-github-pages-generation-from.html
  - Since the documentation location varies, and we are using sphinx-apidoc
    various changes were made to the Makefile. Future additions may require
    some trial and error...


