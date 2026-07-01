PYTHON := .venv/bin/python

.PHONY: sync all anonymous title validate audit clean

sync:
	cd ../../.. && $(PYTHON) paper/experiments/scripts/task36_12_migrate_latex.py
	cd ../../.. && $(PYTHON) paper/experiments/scripts/task36_12_generate_latex_figures.py
	cd ../../.. && $(PYTHON) paper/experiments/scripts/task66_build_journal_submission.py

all: anonymous title

anonymous:
	latexmk -pdf -interaction=nonstopmode -halt-on-error anonymous_manuscript.tex

title:
	latexmk -pdf -interaction=nonstopmode -halt-on-error title_page.tex

validate: all
	cd ../../.. && $(PYTHON) paper/experiments/scripts/task66_validate_journal_submission.py

audit: sync
	$(MAKE) clean
	$(MAKE) validate

clean:
	latexmk -C anonymous_manuscript.tex
	latexmk -C title_page.tex
