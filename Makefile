PHONY: clean clean-test clean-pyc clean-build docs help
.DEFAULT_GOAL := help

django-admin-args = --pythonpath=. --settings=test_settings

help:  ## Display this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} \
		/^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } \
		/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)

##@ Manage

migrations: ## create a new migration
	django-admin makemigrations $(django-admin-args) popolo

##@ Dependencies

install-requirements:	## Install development dependecies
	pip install ".[test,dev]"

##@ Cleanup

clean: clean-pyc clean-test ## Remove all build, test, coverage and Python artifacts

clean-pyc: ## Remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## Remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

##@ Linting and formatting

black:	## format all Python code using black
	black popolo

lint: ## check code style with flake8
	flake8 popolo

##@ Testing

test: ## run tests quickly with the default Python
	django-admin test $(django-admin-args) popolo.tests

coverage: ## check code coverage quickly with the default Python
	coverage run `which django-admin` test $(django-admin-args) popolo.tests
	coverage report -m

coverage-html: | coverage
	coverage html
	$(BROWSER) htmlcov/index.html
