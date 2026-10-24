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

.PHONY: status preview build new clean

status:
	python3 -m packages.pipeline_cli.studio status $(EP)

preview:
	python3 -m packages.pipeline_cli.studio preview $(EP)

build:
	python3 -m packages.pipeline_cli.studio build $(EP)

new:
	python3 -m packages.pipeline_cli.studio init-episode $(EP) --title "$(TITLE)"

clean:
	rm -rf episodes/*/renders episodes/*/dist
