# Build the IEEE MOST 2027 paper outside VS Code and check the page limit.
#   make        -> build/main.pdf (latexmk + BibTeX)
#   make pages  -> print the page count of build/main.pdf
#   make check  -> fail if the PDF has more than MAX_PAGES pages (references included)
#   make clean  -> remove build/

MAIN      := main
OUTDIR    := build
PDF       := $(OUTDIR)/$(MAIN).pdf
MAX_PAGES := 8

LATEXMK := latexmk -pdf -outdir=$(OUTDIR) -interaction=nonstopmode -halt-on-error -file-line-error

.PHONY: all pdf pages check fonts clean

all: pdf

pdf:
	$(LATEXMK) $(MAIN).tex

# Page count: pdfinfo (poppler) if available, else pypdf through uv.
define PAGECOUNT
$$(if command -v pdfinfo >/dev/null 2>&1; then \
	pdfinfo $(PDF) | awk '/^Pages:/ {print $$2}'; \
else \
	uv run --quiet --with pypdf python -c "import pypdf,sys; print(len(pypdf.PdfReader(sys.argv[1]).pages))" $(PDF); \
fi)
endef

pages: pdf
	@echo "$(PDF): $(PAGECOUNT) pages"

check: pdf
	@n=$(PAGECOUNT); \
	if [ "$$n" -gt $(MAX_PAGES) ]; then \
		echo "FAIL: $$n pages > $(MAX_PAGES) (limit includes references)"; exit 1; \
	else \
		echo "OK: $$n pages <= $(MAX_PAGES)"; \
	fi

# Submission rule: all fonts embedded (every row of pdffonts must say "yes" under "emb").
fonts: pdf
	@pdffonts $(PDF)

clean:
	latexmk -C -outdir=$(OUTDIR) $(MAIN).tex
	rm -rf $(OUTDIR)
