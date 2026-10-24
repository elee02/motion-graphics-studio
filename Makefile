# ============================================================================
# MOTION GRAPHICS STUDIO - MAKEFILE
# Usage:
#   make status EP=001-fourier-visualized
#   make preview EP=001-fourier-visualized
#   make build EP=001-fourier-visualized
#   make new EP=002-quantum-spin TITLE="Quantum Spin Visualized"
# ============================================================================

EP ?= 001-fourier-visualized
TITLE ?= Untitled Educational Episode
PYTHON := $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python3; fi)

.PHONY: status preview build new clean

status:
	$(PYTHON) -m packages.pipeline_cli.studio status $(EP)

preview:
	$(PYTHON) -m packages.pipeline_cli.studio preview $(EP)

build:
	$(PYTHON) -m packages.pipeline_cli.studio build $(EP)

new:
	$(PYTHON) -m packages.pipeline_cli.studio init-episode $(EP) --title "$(TITLE)"

clean:
	rm -rf episodes/*/renders episodes/*/dist
