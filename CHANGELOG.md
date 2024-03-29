# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- internal areas added to choices in Area and AreaRelationship models


## [3.0.3]

### Changed
Added Linkedin contact type

## [3.0.2]
### Changed
Arearelationships can now be of type DEP, to account for countries depending on other countries (and areas dependencies, in general)

## [3.0.1]

### Changed
Migrations reset to __initial__ only.

### Added
``.gitlab-ci-yml`` added with flake8 syntax tests and release on pypi (with test)

## [3.0.0]
The main development focuses have been to keep up with latest Django
versions and to "modernize" the code base, adopting latest Python features (like type hinting), and doing some serious 
housekeeping. Python 2 is no longer supported. 
This release also implements a lot of new models which are not part of the Popolo specification (mildly out of scope), 
but we needed them in some projects which make use this package. Those new models can be safely ignored, and they could 
also be removed in the future, as we are considering the option of entirely decoupling them from `django-popolo`. 
That would probably be the right choice, but would also require a lot of development time which we currently don't have.

Below a semi-complete list of changes.

### Added
- Django 2.x support.
- Mild type hinting
- `Area.geometry` geo-spatial field (requires GeoDjango).
- `Area.coordinates` property.
- `RoleType` model to map structured roles for posts (off-spec).
- Shortcuts in Organization QuerySets to extract institutions and organs (IT locale only).
- Add `Makefile`


### Changed
- `add_classification` can now accept `allow_same_scheme` parameter, to allow multiple classifications with the same scheme
- Person can now receive `classifications`.
- Target latest 2 Django LTS versions (1.11 and 2.2 at the moment)
- Target the second-last Python version (3.7 at the moment)
- Require GeoDjango
- Use F-strings when possible
- Tests now cover all methods implemented in the models (possibly).
- original and normalized education levels and profession names are unique.
- original and normalized education levels and profession are now storable.
- `Organization` has a `thematic_classification` field (off-spec).
- `add_classification` and `add_classification_rel` methods decoupled.
- `LinkShortcutsMixin.update_links` method implemented.
- `SourceShortcutsMixin.update_sources` method implemented.
- `ContactDetailShortcutsMixin.update_contact_details` method implemented.
- Add `AKAs` choice to `OtherName.othername_type` choices.
- Adopted `factory_boy` package to generate model instances in tests.
- Implemented test "factories" for the main models (see `popolo.tests.factories` module).
- ClassificationShortcutMixin methods adjusted to work with nested Classification objects.
- Re-worked `update_classifications` method in ClassificationMixin.
- `update_other_names` and `update_identifiers` mixins implemented.
- `Membership.label` field max length increased to 512 characters.
- `Membership` class got methods to compute related apical roles and electoral events.
   - ``get_apicals``
   - ``get_electoral_event``
   - ``this_and_next_electoral_events``,

### Removed
- **Drop Python 2 support**
- `behaviors.models.Permalink.get_absolute_url` method removed. It was unused and relied on deprecated Django APIs.
- `@python_2_unicode_compatible` decorator in model classes (also removed from version 3.0 of Django).
- `management` sub-package (including Popit importer, which was broken anyway) is removed.

### Deprecated
- `Area.geom` field (superseded by `Area.geometry`). 
  Read-only backward compatibility is provided by `geom` property.
- `Area.gps_lat` field (superseded by `Area.geometry`). 
  Read-only backward compatibility is provided by `gps_lat` property.
- `Area.gps_lon` field (superseded by `Area.geometry`). 
  Read-only backward compatibility is provided by `gps_lon` property.


## [2.4.0]

### Added
- `electoral_result` foreign key added to `Membership`.

## [2.3.0]

### Added
- `Profession` and `EducationLevel` models added.
- `profession` and `education_level` foreign keys added to `Person`, referring to `Profession` and `EducationLevel`.

## [2.2.1]

### Fixed
- Classification code and descr fields can now be null, in order to use this class for tagging.
- constituency_descr_tmp and electoral_list_descr_tmp moved from Area to Membership.
- role fields max_length in Membership and Post objects increased to 512.
- get_former_parents and get_former_children moment_date parameter can be null.
- get_former_parents and get_former_children FIP classification_type corrected.

## [2.2.0]

### Changed
- `constituency_descr` and `electoral_list_descr` fields
  **temporarily** added to Membership in order to store relevant
  information contained in the Openpolitici dataset (will be removed
  when the whole subject will be refactored).
- Multiple overlapping memberships are possible if the `allow_overlap`
  flag is specified.

## [2.1.0]

### Added
- `birth_location` and `birth_location_area` fields added to Person.
- person helper methods to add roles and memberships.
- helper methods of the previous pointcheck for overlapping dates, in order 
  to allow duplicate roles or memberships for the same Organizations and Posts.

## 2.0.1 [YANKED]

### Fixed
- `str` method added to LinkRel, SourceRel and ClassificationRel classes.
- fixed ordering of queryset results in determining overlapping dates
  in `add_other_names`, that resulted in tests failing on some 
  platforms.
- `str` for ClassificationRel, LinkRel and SourceRel now correctly 
  ouput a string, not a tuple.


## [2.0.0]

Compatibility with Popit importer broken!
Due to changes in how Links and Sources are modeled, the Popit 
importer is not working any longer.

### Added
- Area class refined
- Area class shortcuts methods implemented and tested
- AreaRelationship class added to map generic relationships among Areas
- Classification added for 
- Links, Sources and Classifications are related to generic objects through *Rel…classes, in order to minimize 
  unnecessary repetitions in the tables.
- Shortcuts to filter type of areas added to AreaQuerySet.

### Changed
- Common methods and testcases oved into Dateframeable and DateframeableTestCase
- Unicity of ContactDetail, OtherName and Identifier is enforced in the `add_x` shortcut methods. Identifiers validation
  take into account overlapping dates intervals. Overlapping identical values are merged into a single identifier whose 
  start and end dates are extended.
- IdentifierQueryset added to handle date filters for identifiers
- `popolo.utils.PartialDate` and `popolo.utils.PartialDatesInterval` added to handle partial dates computations and 
  comparisons.
- opdm-service project layout now follows our template at https://gitlab.depp.it/openpolis/django-project-template.
- `add_identifiers` tests now encompass many use cases.

### Removed
- The importers were removed, due to broken backward compatibility introduced in the models.

## 1.2.1 - 2017-09-20

### Added
- ElectoralEvent shortcuts to create ElectoralResults added.

## 1.2.0 - 2017-09-20

### Added
- ElectoralEvent and ElectoralResult classes added.
- personal relationships modelling added.

### Changed
- models and tests refactored in order to distribute shortcuts and tests through mixins.
- source added to Identifier.
- tests now encompass on_behalf_of relations.

## 1.1.0 - 2017-09-16

### Added
- Event class added to instances.

### Changed
- Main entities primary keys are now numerical IDs.
- django-popolo models aligned to popolo schemas.

## 1.0.1 - 2017-09-14

### Added
- Italian translation in models and admin.

### Changed
- Area and inline AreaI18Names admin classes.
- `models.py` code readability increased.

## 1.0.0 - 2017-09-13

### Added
- added tests for importer.

### Changed
- `popit` importer substituted by the `popolo_json` importer.
- simplified `popolo_create_from_popit` management task.
- updated travis matrix to latest python (3.6) and django (1.11) releases.

### Fixed
- `urls.py` is now compatible with django 1.8>, and does not cause errors in django 1.11.

[Unreleased]: https://gitlab.depp.it/openpolis/django-popolo/compare/v3.0.0...master
[3.0.0]: https://gitlab.depp.it/openpolis/django-popolo/compare/v2.4.0...v3.0.0
[2.4.0]: https://gitlab.depp.it/openpolis/django-popolo/compare/v2.3.0...v2.4.0
[2.3.0]: https://gitlab.depp.it/openpolis/django-popolo/compare/v2.2.1...v2.3.0
[2.2.1]: https://gitlab.depp.it/openpolis/django-popolo/compare/v2.2.0...v2.2.1
[2.2.0]: https://gitlab.depp.it/openpolis/django-popolo/compare/v2.1.0...v2.2.0
[2.1.0]: https://gitlab.depp.it/openpolis/django-popolo/compare/v2.0.0...v2.1.0
[2.0.0]: https://gitlab.depp.it/openpolis/django-popolo/compare/v1.0...v2.0.0
