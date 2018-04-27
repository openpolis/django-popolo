# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Changed
- update_classifications method in ClassificationMixin refactored
- factory_boy used to generate instances in tests
- update_other_names and update_identifiers mixins implemented
- add_membership using ``electoral_event`` kwarg test added

## [2.4.0]
### Added
- ``electoral_result`` foreign key added to ``Membership``

## [2.3.0]
### Added
- ``Profession`` and ``EducationLevel`` models added
- ``profession`` and ``education_level`` foreign keys added to ``Person``, referring to 
  ``Profession`` and ``EducationLevel``

## [2.2.1]
### Fixed
- Classification code and descr fields can now be null, in order to use this class for tagging
- constituency_descr_tmp and electoral_list_descr_tmp moved from Area to Membership
- role fields max_length in Membership and Post objects increased to 512
- get_former_parents and get_former_children moment_date parameter can be null
- get_former_parents and get_former_children FIP classification_type corrected

## [2.2.0]
### Changed
- ``constituency_descr`` and ``electoral_list_descr`` fields
  **temporarily** added to Membership in order to store relevant
  information contained in the Openpolitici dataset (will be removed
  when the whole subject will be refactored)
- Multiple overlapping memberships are possible if the ``allow_overlap``
  flag is specified

## [2.1.0]
### Added
- ``birth_location`` and ``birth_location_area`` fields added to Person
- person helper methods to add roles and memberships 
- helper methods of the previous pointcheck for overlapping dates, in order 
  to allow duplicate roles or memberships for the same Organizations and Posts

## [2.0.1]
### Fixed
- ``str`` method added to LinkRel, SourceRel and ClassificationRel 
    classes.
- fixed ordering of queryset results in determining overlapping dates
  in ``add_other_names``, that resulted in tests failing on some 
  platforms
- ``str`` for ClassificationRel, LinkRel and SourceRel now correctly 
  ouput a string, not a tuple


## [2.0.0]

Compatibility with Popit importer broken!
Due to changes in how Links and Sources are modeled, the Popit 
importer is not working any longer.

### Added
- Area class refined
- Area class shortcuts methods implemented and tested
- AreaRelationship class added to map generic relationships among Areas
- Classification added for 
- Links, Sources and Classifications are related to generic objects
  through *Rel…classes, in order to minimize non-necessary repetitions
  in the tables.
- Shortcuts to filter type of areas added to AreaQuerySet


### Changed
- Common methods and testcases oved into Dateframeable and DateframeableTestCase
- Unicity of ContactDetail, OtherName and Identifier is enforced in the 
  ``add_x`` shortcut methods. Identifiers validation take into account
  overlapping dates intervals. Overlapping identical values are merged 
  into a single identifier whose start and end dates are extended.
- IdentifierQueryset added to handle date filters for identifiers
- ``popolo.utils.PartialDate`` and ``popolo.utils.PartialDatesInterval``
  added to handle partial dates computations and comparisons.
- opdm-service project layout now follows our template at 
  https://github.com/openpolis/django-project-template.
- ``add_identifiers`` tests now encompass many use cases.

### Removed
- The importers were removed, due to broken back-compatibility 
  introduced in the models.

## [1.2.1] - 2017-09-20

### Added
- ElectoralEvent shortcuts to create ElectoralResults added 


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

