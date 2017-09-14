# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

