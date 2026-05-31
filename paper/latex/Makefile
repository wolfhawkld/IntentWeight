PYTHON := ../../.venv/bin/python

.PHONY: generate validate pdf clean

generate:
	$(PYTHON) ../experiments/scripts/task36_12_migrate_latex.py
	$(PYTHON) ../experiments/scripts/task36_12_generate_latex_figures.py

validate: generate
	$(PYTHON) ../experiments/scripts/task36_12_validate_latex.py

pdf: validate
	latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

clean:
	latexmk -C
