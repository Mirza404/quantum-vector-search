# Build the FENS graduation project report.
#
#   make           - build the submission-named PDF
#   make clean     - remove all generated build artefacts
#   make watch     - rebuild on every save (requires entr)
#
# Uses pdflatex + bibtex with IEEEtran.bst. No latexmk, no biber dependency.

JOB := SoftwareEngineering_QuantumVectorSearch_Mahmutovic_Kikanovic_Musanovic_Abdulahovic_2026
TEX := main.tex

PDFLATEX := pdflatex -interaction=nonstopmode -halt-on-error -file-line-error
BIBTEX   := bibtex

.PHONY: all clean watch force

all: $(JOB).pdf

# Rebuild even when Make thinks nothing changed (useful after editing something
# Make doesn't track, or just to be sure).
force:
	@$(MAKE) --no-print-directory clean
	@$(MAKE) --no-print-directory all

$(JOB).pdf: $(TEX) chapters/*.tex references.bib $(wildcard figures/*)
	$(PDFLATEX) -jobname=$(JOB) $(TEX)
	-$(BIBTEX) $(JOB)
	$(PDFLATEX) -jobname=$(JOB) $(TEX)
	$(PDFLATEX) -jobname=$(JOB) $(TEX)

clean:
	rm -f $(JOB).aux $(JOB).log $(JOB).toc $(JOB).lof $(JOB).lot \
	      $(JOB).bbl $(JOB).blg $(JOB).out $(JOB).fls $(JOB).fdb_latexmk \
	      report.aux report.log report.toc report.lof report.lot \
	      report.bbl report.blg report.out report.fls report.fdb_latexmk \
	      chapters/*.aux $(JOB).pdf

watch:
	@command -v entr >/dev/null || { echo "install 'entr' first"; exit 1; }
	find . -name '*.tex' -o -name '*.bib' | entr -c make
