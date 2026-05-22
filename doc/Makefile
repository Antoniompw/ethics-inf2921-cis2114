MAIN     = main
BUILDDIR = build
LATEX    = pdflatex
BIBTEX   = bibtex
FLAGS    = -interaction=nonstopmode -halt-on-error -output-directory=$(BUILDDIR)
export BIBINPUTS = .

.PHONY: all clean view

all: $(MAIN).pdf

$(BUILDDIR):
	mkdir -p $(BUILDDIR)

$(MAIN).pdf: $(MAIN).tex references.bib | $(BUILDDIR)
	$(LATEX) $(FLAGS) $(MAIN).tex
	$(BIBTEX) $(BUILDDIR)/$(MAIN)
	$(LATEX) $(FLAGS) $(MAIN).tex
	$(LATEX) $(FLAGS) $(MAIN).tex
	cp $(BUILDDIR)/$(MAIN).pdf $(MAIN).pdf

figures/:
	mkdir -p figures

clean:
	rm -rf $(BUILDDIR)

view: $(MAIN).pdf
	xdg-open $(MAIN).pdf &
