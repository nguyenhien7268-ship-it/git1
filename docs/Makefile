# Makefile for Sphinx documentation

SPHINXBUILD   = sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# User-friendly commands
.PHONY: help html clean

help:
	@echo "Please use 'make <target>' where <target> is one of:"
	@echo "  html       to make standalone HTML files"
	@echo "  clean      to remove build artifacts"

html:
	$(SPHINXBUILD) -b html $(SOURCEDIR) $(BUILDDIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."

clean:
	rm -rf $(BUILDDIR)/*
	@echo "Build artifacts removed."
