# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

## [1.2.0] - 2017-09-20

### Added
- ElectoralEvent and ElectoralResult classes added;
- personal relationships modelling added

### Changed
- models and tests refactored in order to distribute shortcuts and tests through mixins
- source added to Identifier
- tests now encompass on_behalf_of relations


## [1.1.0] - 2017-09-16

### Added
- Event class added to instances

### Changed
- Main entities primary keys are now numerical IDs
- django-popolo models aligned to popolo schemas


## [1.0.1] - 2017-09-14

### Added
- italian translation in models and admin

### Changed
- Area and inline AreaI18Names admin classes
- models code readability increased


## [1.0.0] - 2017-09-13

### Added
- added tests for importer

### Changed
- `popit` importer substituted by the `popolo_json` importer
- simplified `popolo_create_from_popit` management task
- updated travis matrix to latest python (3.6) and django (1.11)
releases


### Fixed
- `urls.py` is now compatible with django 1.8>,
and does not cause errors in django 1.11

