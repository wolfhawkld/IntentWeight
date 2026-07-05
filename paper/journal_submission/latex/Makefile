PYTHON := .venv/bin/python

.PHONY: sync all anonymous supplement title evidence validate audit clean

sync:
	cd ../../.. && $(PYTHON) paper/experiments/scripts/task36_12_migrate_latex.py
	cd ../../.. && $(PYTHON) paper/experiments/scripts/task36_12_generate_latex_figures.py
	cd ../../.. && $(PYTHON) paper/experiments/scripts/task66_build_journal_submission.py

all: anonymous supplement title

evidence:
	cd ../../.. && $(PYTHON) paper/experiments/scripts/task51_experiment_validation.py
	cd ../../.. && $(PYTHON) paper/experiments/scripts/task43_audit_manuscript_tables_figures.py
	cd ../../.. && $(PYTHON) paper/experiments/scripts/task67_validate_paper_evidence.py

anonymous:
	latexmk -pdf -interaction=nonstopmode -halt-on-error anonymous_manuscript.tex

supplement:
	latexmk -pdf -interaction=nonstopmode -halt-on-error supplementary_material.tex

title:
	latexmk -pdf -interaction=nonstopmode -halt-on-error title_page.tex

validate: all
	cd ../../.. && $(PYTHON) paper/experiments/scripts/task66_validate_journal_submission.py

audit: sync evidence
	$(MAKE) clean
	$(MAKE) validate

clean:
	latexmk -C anonymous_manuscript.tex
	latexmk -C supplementary_material.tex
	latexmk -C title_page.tex
