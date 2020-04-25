.PHONY: help  clean-all clean-pyc clean-build

.DEFAULT: help
help:
	@echo "make help"
	@echo "       shows this."
	@echo ""
	@echo "make clean-build"
	@echo "       removes build directories"
	@echo "make clean-all"
	@echo "       runs all clean methods"

# Clean:

clean-all: clean-pyc clean-build

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
	find . -name '.pytest_cache' -exec rm -fr {} +

clean-build:
	rm -rf ./build
	rm -rf ./*.egg-info
	rm -rf ./dist
