############
# See README.rst in docs/
############

# Makefile for Sphinx documentation
#

GH_PAGES_SOURCES = docs/_themes docs/_sphinxext docs/index.rst docs/conf.py docs/rebuild.sh docs/r2s-userguide.rst scripts/r2s/*.py scripts/r2s/io/*.py docs/gen_sourceF90_doc.py mcnp_source/*.F90

# You can set these variables from the command line.
SPHINXOPTS =
SPHINXBUILD = sphinx-build
PAPER =
BUILDDIR = docs/_build

# Internal variables.
PAPEROPT_a4 = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS = -d $(BUILDDIR)/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) docs/
# the i18n builder cannot share the environment and doctrees with the others
I18NSPHINXOPTS = $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .

.PHONY: help gh-push gh-revert

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo " gh-push to push changes from gh-preview to gh-pages branch on GitHub."
	@echo " gh-revert to discard changes from gh-pages and return to master branch."

gh-push:
	rm -rf $(GH_PAGES_SOURCES)
	rm -rf doc/_build doc/r2s
	rm -rf scripts/r2s/*.py scripts/r2s/io/*.py mcnp_source/*.F90
	git add --all
	git commit -m "Generated gh-pages for `git log master -1 --pretty=short --abbrev-commit`" && git push origin gh-pages
	git checkout master

gh-revert:
	git checkout -f --
	rm -rf $(GH_PAGES_SOURCES)
	rm -rf doc/_build doc/r2s
	rm -rf scripts/r2s/*.py scripts/r2s/io/*.py mcnp_source/*.F90
	git checkout master



