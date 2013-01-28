############
# See README.rst in docs/
############

# Makefile for Sphinx documentation
#

GH_PAGES_SOURCES = docs/_themes docs/_sphinxext docs/index.rst docs/conf.py docs/rebuild.sh docs/r2s-userguide.rst scripts/r2s/*.py scripts/r2s/io/*.py docs/gen_source_gamma_doc.py mcnp_source/*.F90

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXAPIDOC  = docs/rebuild.sh
SPHINXAPIDOCCLEAN = rm scripts/r2s/mcnp/*
PAPER         =
BUILDDIR      = docs/_build

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d $(BUILDDIR)/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) docs/
# the i18n builder cannot share the environment and doctrees with the others
I18NSPHINXOPTS  = $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .

.PHONY: help gh-pages gh-preview clean html dirhtml singlehtml pickle json htmlhelp qthelp devhelp epub latex latexpdf text man changes linkcheck doctest gettext

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@echo "  html       to make standalone HTML files via sphinx + sphinx-apidoc"
	@echo "  gh-pages   to make standalone HTML files and push these to gh-pages branch on GitHub."
	@echo "  gh-preview to make standalone HTML files in gh-pages branch, but not push to GitHub."
	@echo "  dirhtml    to make HTML files named index.html in directories"
	@echo "  singlehtml to make a single large HTML file"
	@echo "  pickle     to make pickle files"
	@echo "  json       to make JSON files"
	@echo "  htmlhelp   to make HTML files and a HTML help project"
	@echo "  qthelp     to make HTML files and a qthelp project"
	@echo "  devhelp    to make HTML files and a Devhelp project"
	@echo "  epub       to make an epub"
	@echo "  latex      to make LaTeX files, you can set PAPER=a4 or PAPER=letter"
	@echo "  latexpdf   to make LaTeX files and run them through pdflatex"
	@echo "  text       to make text files"
	@echo "  man        to make manual pages"
	@echo "  texinfo    to make Texinfo files"
	@echo "  info       to make Texinfo files and run them through makeinfo"
	@echo "  gettext    to make PO message catalogs"
	@echo "  changes    to make an overview of all changed/added/deprecated items"
	@echo "  linkcheck  to check all external links for integrity"
	@echo "  doctest    to run all doctests embedded in the documentation (if enabled)"

clean:
	-rm -rf $(BUILDDIR)/*
	rm scripts/r2s/mcnp/*

html:
	$(SPHINXAPIDOC)
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(BUILDDIR)/html
	$(SPHINXAPIDOCCLEAN)
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."

gh-pages:
	git checkout gh-pages
	# Clean out _build from docs/
	rm -rf docs/_build 
	# Clean out contents of _build/html/ from repo root.
	rm -rf _sources _static r2s
	git checkout master $(GH_PAGES_SOURCES)
	git reset HEAD
	$(SPHINXAPIDOC)
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(BUILDDIR)/html
	$(SPHINXAPIDOCCLEAN)
	mv -fv docs/_build/html/* .
	rm -rf $(GH_PAGES_SOURCES)
	rm -rf doc/_build doc/r2s
	rm -rf scripts/r2s/*.py scripts/r2s/io/*.py mcnp_source/*.F90
	# Empty docs directory but preserve .gitignore
	mv docs/.gitignore stashed.gitignore ; rm -rf docs/* ; mv stashed.gitignore docs/.gitignore
	echo nojekyll > .nojekyll
	git add --all
	# Commit and push gh-pages, and switch back to master
	git commit -m "Generated gh-pages for `git log master -1 --pretty=short --abbrev-commit`" && git push origin gh-pages
	git checkout master

gh-preview:
	git checkout gh-pages
	# Clean out _build from docs/
	rm -rf docs/_build 
	# Clean out contents of _build/html/ from repo root.
	rm -rf _sources _static r2s
	git checkout master $(GH_PAGES_SOURCES)
	git reset HEAD
	$(SPHINXAPIDOC)
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(BUILDDIR)/html
	$(SPHINXAPIDOCCLEAN)
	mv -fv docs/_build/html/* .
	rm -rf $(GH_PAGES_SOURCES)
	rm -rf doc/_build doc/r2s
	rm -rf scripts/r2s/*.py scripts/r2s/io/*.py mcnp_source/*.F90
	# Empty docs directory but preserve .gitignore
	mv docs/.gitignore stashed.gitignore ; rm -rf docs/* ; mv stashed.gitignore docs/.gitignore
	echo nojekyll > .nojekyll

dirhtml:
	$(SPHINXAPIDOC)
	$(SPHINXBUILD) -b dirhtml $(ALLSPHINXOPTS) $(BUILDDIR)/dirhtml
	$(SPHINXAPIDOCCLEAN)
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/dirhtml."

singlehtml:
	$(SPHINXAPIDOC)
	$(SPHINXBUILD) -b singlehtml $(ALLSPHINXOPTS) $(BUILDDIR)/singlehtml
	$(SPHINXAPIDOCCLEAN)
	@echo
	@echo "Build finished. The HTML page is in $(BUILDDIR)/singlehtml."

pickle:
	$(SPHINXAPIDOC)
	$(SPHINXBUILD) -b pickle $(ALLSPHINXOPTS) $(BUILDDIR)/pickle
	$(SPHINXAPIDOCCLEAN)
	@echo
	@echo "Build finished; now you can process the pickle files."

json:
	$(SPHINXAPIDOC)
	$(SPHINXBUILD) -b json $(ALLSPHINXOPTS) $(BUILDDIR)/json
	$(SPHINXAPIDOCCLEAN)
	@echo
	@echo "Build finished; now you can process the JSON files."

htmlhelp:
	$(SPHINXAPIDOC)
	$(SPHINXBUILD) -b htmlhelp $(ALLSPHINXOPTS) $(BUILDDIR)/htmlhelp
	$(SPHINXAPIDOCCLEAN)
	@echo
	@echo "Build finished; now you can run HTML Help Workshop with the" \
	      ".hhp project file in $(BUILDDIR)/htmlhelp."

qthelp:
	$(SPHINXAPIDOC)
	$(SPHINXBUILD) -b qthelp $(ALLSPHINXOPTS) $(BUILDDIR)/qthelp
	$(SPHINXAPIDOCCLEAN)
	@echo
	@echo "Build finished; now you can run "qcollectiongenerator" with the" \
	      ".qhcp project file in $(BUILDDIR)/qthelp, like this:"
	@echo "# qcollectiongenerator $(BUILDDIR)/qthelp/R2S-ACT.qhcp"
	@echo "To view the help file:"
	@echo "# assistant -collectionFile $(BUILDDIR)/qthelp/R2S-ACT.qhc"

devhelp:
	$(SPHINXAPIDOC)
	$(SPHINXBUILD) -b devhelp $(ALLSPHINXOPTS) $(BUILDDIR)/devhelp
	$(SPHINXAPIDOCCLEAN)
	@echo
	@echo "Build finished."
	@echo "To view the help file:"
	@echo "# mkdir -p $$HOME/.local/share/devhelp/R2S-ACT"
	@echo "# ln -s $(BUILDDIR)/devhelp $$HOME/.local/share/devhelp/R2S-ACT"
	@echo "# devhelp"

epub:
	$(SPHINXAPIDOC)
	$(SPHINXBUILD) -b epub $(ALLSPHINXOPTS) $(BUILDDIR)/epub
	$(SPHINXAPIDOCCLEAN)
	@echo
	@echo "Build finished. The epub file is in $(BUILDDIR)/epub."

latex:
	$(SPHINXAPIDOC)
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) $(BUILDDIR)/latex
	$(SPHINXAPIDOCCLEAN)
	@echo
	@echo "Build finished; the LaTeX files are in $(BUILDDIR)/latex."
	@echo "Run \`make' in that directory to run these through (pdf)latex" \
	      "(use \`make latexpdf' here to do that automatically)."

latexpdf:
	$(SPHINXAPIDOC)
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) $(BUILDDIR)/latex
	$(SPHINXAPIDOCCLEAN)
	@echo "Running LaTeX files through pdflatex..."
	$(MAKE) -C $(BUILDDIR)/latex all-pdf
	@echo "pdflatex finished; the PDF files are in $(BUILDDIR)/latex."

text:
	$(SPHINXAPIDOC)
	$(SPHINXBUILD) -b text $(ALLSPHINXOPTS) $(BUILDDIR)/text
	$(SPHINXAPIDOCCLEAN)
	@echo
	@echo "Build finished. The text files are in $(BUILDDIR)/text."

man:
	$(SPHINXAPIDOC)
	$(SPHINXBUILD) -b man $(ALLSPHINXOPTS) $(BUILDDIR)/man
	$(SPHINXAPIDOCCLEAN)
	@echo
	@echo "Build finished. The manual pages are in $(BUILDDIR)/man."

texinfo:
	$(SPHINXAPIDOC)
	$(SPHINXBUILD) -b texinfo $(ALLSPHINXOPTS) $(BUILDDIR)/texinfo
	$(SPHINXAPIDOCCLEAN)
	@echo
	@echo "Build finished. The Texinfo files are in $(BUILDDIR)/texinfo."
	@echo "Run \`make' in that directory to run these through makeinfo" \
	      "(use \`make info' here to do that automatically)."

info:
	$(SPHINXAPIDOC)
	$(SPHINXBUILD) -b texinfo $(ALLSPHINXOPTS) $(BUILDDIR)/texinfo
	$(SPHINXAPIDOCCLEAN)
	@echo "Running Texinfo files through makeinfo..."
	make -C $(BUILDDIR)/texinfo info
	@echo "makeinfo finished; the Info files are in $(BUILDDIR)/texinfo."

gettext:
	$(SPHINXAPIDOC)
	$(SPHINXBUILD) -b gettext $(I18NSPHINXOPTS) $(BUILDDIR)/locale
	$(SPHINXAPIDOCCLEAN)
	@echo
	@echo "Build finished. The message catalogs are in $(BUILDDIR)/locale."

changes:
	$(SPHINXAPIDOC)
	$(SPHINXBUILD) -b changes $(ALLSPHINXOPTS) $(BUILDDIR)/changes
	$(SPHINXAPIDOCCLEAN)
	@echo
	@echo "The overview file is in $(BUILDDIR)/changes."

linkcheck:
	$(SPHINXAPIDOC)
	$(SPHINXBUILD) -b linkcheck $(ALLSPHINXOPTS) $(BUILDDIR)/linkcheck
	$(SPHINXAPIDOCCLEAN)
	@echo
	@echo "Link check complete; look for any errors in the above output " \
	      "or in $(BUILDDIR)/linkcheck/output.txt."

doctest:
	$(SPHINXAPIDOC)
	$(SPHINXBUILD) -b doctest $(ALLSPHINXOPTS) $(BUILDDIR)/doctest
	$(SPHINXAPIDOCCLEAN)
	@echo "Testing of doctests in the sources finished, look at the " \
	      "results in $(BUILDDIR)/doctest/output.txt."
