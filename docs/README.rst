docs/ folder readme
==================
This folder is where documentation of the r2s-act code is managed and built using Sphinx.

Note: If you are adding a *new* page (.rst file), the file name needs to be added to the Makefile in the GH_PAGES_SOURCES list.

**The actual documentation is located at** http://svalinn.github.com/r2s-act

To rebuild documentation, make sure you are on the `master` branch.
Run `make gh-preview` in the base level of the repository (**not** in `docs/`).
This will automatically switch to the `gh-pages` branch,
pull the latest documentation source from `master`, and rebuild HTML.
After you inspect pages produced, you can either run `make gh-push` to push to Github, or `make gh-revert` to discard changes and return to the `master` branch.

Running `make gh-pages` will combine the above two steps without providing the chance to preview before pushing to Github, and so is not recommmended.

To rebuild documentation for local viewing (and without updating Github), run `make html` in top level of the repo. This can be re-run as errors.  The created files can be deleted with `make clean`, but git will ignore the files regardless.

A few other notes:

- Some extensions for sphinx (numpydoc in particular) are used. These are stored in `docs/_sphinxext`
- sphinx-apidoc grabs the docstrings from scripts in r2s/ and r2s/data_transfer/
  - the `docs/rebuild.sh` script handles the calls to sphinx-apidoc
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
- docstrings for Fortran code are created with the `docs/gen_source_gamma_doc.py` script, which creates a fake Python script which sphinx-apidoc grabs docstrings from `source_gamma.F90` and `source_moab.F90`.

