# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SPHINXPROJ    = PacketWeaver
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile apidoc uml-core all show

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

apidoc:
	rm -f source/apidoc/*  # -f to success even when the files do not exist yet
	sphinx-apidoc -T -f -o source/apidoc ../../packetweaver ../../packetweaver/ability

uml-core:
	pyreverse -o png -p pw_core ../core
	mkdir -p build # make sure the build folder exists
	mv classes_pw_core.png packages_pw_core.png build/

show:
	xdg-open build/html/index.html

all: apidoc uml-core html

