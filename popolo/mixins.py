from django.contrib.contenttypes.fields import ReverseGenericManyToOneDescriptor
from django.db.models.fields.related_descriptors import ReverseManyToOneDescriptor

from popolo import models as popolo_models
from popolo.exceptions import OverlappingDateIntervalException
from popolo.utils import PartialDatesInterval, PartialDate


class ContactDetailsShortcutsMixin:
    contact_details: ReverseGenericManyToOneDescriptor

    def add_contact_detail(self, **kwargs):
        value = kwargs.pop("value")
        obj, created = self.contact_details.get_or_create(value=value, defaults=kwargs)
        return obj

    def add_contact_details(self, contacts):
        for obj in contacts:
            self.add_contact_detail(**obj)

    def update_contact_details(self, new_contacts):
        """update contact_details,
        removing those not present in new_contacts
        overwriting those present and existing,
        adding those present and not existing

        :param new_contacts: the new list of contact_details
        :return:
        """
        existing_ids = set(self.contact_details.values_list("id", flat=True))
        new_ids = set(n["id"] for n in new_contacts if "id" in n)

        # remove objects
        delete_ids = existing_ids - new_ids
        self.contact_details.filter(id__in=delete_ids).delete()

        # update objects
        for id_ in new_ids & existing_ids:
            u_name = list(filter(lambda x: x.get("id", None) == id_, new_contacts))[0].copy()

            self.contact_details.filter(pk=u_name.pop("id")).update(**u_name)

        # add objects
        for new_contact in new_contacts:
            if "id" not in new_contact:
                self.add_contact_detail(**new_contact)


class OtherNamesShortcutsMixin:
    other_names: ReverseGenericManyToOneDescriptor

    def add_other_name(
        self, name, othername_type="ALT", overwrite_overlapping=False, extend_overlapping=True, **kwargs
    ):
        """Add other_name to the instance inheriting the mixin

        Names without dates specification may be added freely.

        A check for date interval overlaps is performed between the
        name that's to be added and all existing names that
        use the same scheme. Existing names are extracted ordered by
        ascending `start_date`.

        As soon as an overlap is found (first match):
        * if the name has the same value,
          then it is by default treated as an extension and date intervals
          are *extended*;
          this behaviour can be turned off by setting the
          `extend_overlapping` parameter to False, in which case the
          interval is not added and an exception is raised
        * if the name has a different value,
          then the interval is not added and an Exception is raised;
          this behaviour can be changed by setting `overwrite_overlapping` to
          True, in which case the new identifier overwrites the old one, both
          by value and dates

        Since **order matters**, multiple intervals need to be sorted by
        start date before being inserted.

        :param name:
        :param othername_type:
        :param overwrite_overlapping: overwrite first overlapping
        :param extend_overlapping: extend first overlapping (touching)
        :param kwargs:
        :return: the instance just added if successful
        """

        # names with no date interval specified are added immediately
        # the tuple (othername_type, name) must be unique
        if kwargs.get("start_date", None) is None and kwargs.get("end_date", None) is None:
            i, created = self.other_names.get_or_create(othername_type=othername_type, name=name, defaults=kwargs)
            return i
        else:
            # the type was used
            # check if dates intervals overlap
            from popolo.utils import PartialDatesInterval
            from popolo.utils import PartialDate

            # get names having the same type
            same_type_names = self.other_names.filter(othername_type=othername_type).order_by("-end_date")

            # new name dates interval as PartialDatesInterval instance
            new_int = PartialDatesInterval(start=kwargs.get("start_date", None), end=kwargs.get("end_date", None))

            is_overlapping_or_extending = False

            # loop over names of the same type
            for n in same_type_names:
                # existing name dates interval as PartialDatesInterval instance
                n_int = PartialDatesInterval(start=n.start_date, end=n.end_date)

                # compute overlap days
                #  > 0 means crossing
                # == 0 means touching
                #  < 0 meand not overlapping
                overlap = PartialDate.intervals_overlap(new_int, n_int)

                if overlap >= 0:
                    # detect "overlaps" and "extensions",

                    if n.name != name:
                        # only crossing dates is a proper overlap
                        if overlap > 0:
                            if overwrite_overlapping:
                                # overwrites existing identifier
                                n.start_date = kwargs.get("start_date", None)
                                n.end_date = kwargs.get("end_date", None)
                                n.note = kwargs.get("note", None)
                                n.source = kwargs.get("source", None)

                                # save i and exit the loop
                                n.save()
                                is_overlapping_or_extending = True
                                break
                            else:
                                # block insertion
                                raise OverlappingDateIntervalException(
                                    n,
                                    "Name could not be created, "
                                    "due to overlapping dates ({0} : {1})".format(new_int, n_int),
                                )

                    else:
                        if extend_overlapping:
                            # extension, get new dates for i
                            if new_int.start.date is None or n_int.start.date is None:
                                n.start_date = None
                            else:
                                n.start_date = min(n.start_date, new_int.start.date)

                            if new_int.end.date is None or n_int.end.date is None:
                                n.end_date = None
                            else:
                                n.end_date = max(n.end_date, new_int.end.date)

                            # save i and exit the loop
                            n.save()
                            is_overlapping_or_extending = True
                            break
                        else:
                            # block insertion
                            raise OverlappingDateIntervalException(
                                n,
                                "Name could not be created, "
                                "due to overlapping dates ({0} : {1})".format(new_int, n_int),
                            )

            # no overlaps, nor extensions, the identifier can be created
            if not is_overlapping_or_extending:
                return self.other_names.create(othername_type=othername_type, name=name, **kwargs)

    def add_other_names(self, names):
        """add other static names

        :param names: list of dicts containing names' parameters
        :return:
        """
        for n in names:
            self.add_other_name(**n)

    def update_other_names(self, new_names):
        """update other_names,
        removing those not present in new_names
        overwriting those present and existing,
        adding those present and not existing

        :param new_names: the new list of other_names
        :return:
        """
        existing_ids = set(self.other_names.values_list("id", flat=True))
        new_ids = set(n["id"] for n in new_names if "id" in n)

        # remove objects
        delete_ids = existing_ids - new_ids
        self.other_names.filter(id__in=delete_ids).delete()

        # update objects
        for id_ in new_ids & existing_ids:
            u_name = list(filter(lambda x: x.get("id", None) == id_, new_names))[0].copy()

            self.other_names.filter(pk=u_name.pop("id")).update(**u_name)

        # add objects
        for new_name in new_names:
            if "id" not in new_name:
                self.add_other_name(**new_name)


class IdentifierShortcutsMixin:
    identifiers: ReverseGenericManyToOneDescriptor

    def add_identifier(
        self,
        identifier,
        scheme,
        overwrite_overlapping=False,
        merge_overlapping=False,
        extend_overlapping=True,
        same_scheme_values_criterion=False,
        **kwargs,
    ):
        """Add identifier to the instance inheriting the mixin

        A check for date interval overlaps is performed between the
        identifier that's to be added and all existing identifiers that
        use the same scheme. Existing identifiers are extracted ordered by
        ascending `start_date`.

        As soon as an overlap is found (first match):
        * if the identifier has the same value,
          then it is by default treated as an extension and date intervals
          are *extended*;
          this behaviour can be turned off by setting the
          `extend_overlapping` parameter to False, in which case the
          interval is not added and an exception is raised
        * if the identifier has a different value,
          then the interval is not added and an Exception is raised;
          this behaviour can be changed by setting `overwrite_overlapping` to
          True, in which case the new identifier overwrites the old one, both
          by value and dates

        Since **order matters**, multiple intervals need to be sorted by
        start date before being inserted.

        :param identifier:
        :param scheme:
        :param overwrite_overlapping: overwrite first overlapping
        :param extend_overlapping: extend first overlapping (touching)
        :param merge_overlapping: get last start_date and first end_date
        :parma same_scheme_values_criterion: True if overlap is computed
            only for identifiers with same scheme and values
            If set to False (default) overlapping is computed for
            identifiers having the same scheme.
        :param kwargs:
        :return: the instance just added if successful
        """

        # get identifiers having the same scheme,
        same_scheme_identifiers = self.identifiers.filter(scheme=scheme)

        # add identifier if the scheme is new
        if same_scheme_identifiers.count() == 0:
            i, created = self.identifiers.get_or_create(scheme=scheme, identifier=identifier, **kwargs)
            return i
        else:
            # the scheme is used
            # check if dates intervals overlap
            from popolo.utils import PartialDatesInterval
            from popolo.utils import PartialDate

            # new identifiere dates interval as PartialDatesInterval instance
            new_int = PartialDatesInterval(start=kwargs.get("start_date", None), end=kwargs.get("end_date", None))

            is_overlapping_or_extending = False

            # loop over identifiers belonging to the same scheme
            for i in same_scheme_identifiers:

                # existing identifier interval as PartialDatesInterval instance
                i_int = PartialDatesInterval(start=i.start_date, end=i.end_date)

                # compute overlap days
                #  > 0 means crossing
                # == 0 means touching
                #  < 0 meand not overlapping
                overlap = PartialDate.intervals_overlap(new_int, i_int)

                if overlap >= 0:
                    # detect "overlaps" and "extensions"

                    if i.identifier != identifier:

                        # only crossing dates is a proper overlap
                        # when same
                        if not same_scheme_values_criterion and overlap > 0:
                            if overwrite_overlapping:
                                # overwrites existing identifier
                                i.start_date = kwargs.get("start_date", None)
                                i.end_date = kwargs.get("end_date", None)
                                i.identifier = identifier
                                i.source = kwargs.get("source", None)

                                # save i and exit the loop
                                i.save()

                                is_overlapping_or_extending = True
                                break
                            else:
                                # block insertion
                                if new_int.start.date is None and new_int.end.date is None and i_int == new_int:
                                    return
                                else:
                                    raise OverlappingDateIntervalException(
                                        i,
                                        "Identifier could not be created, "
                                        "due to overlapping dates ({0} : {1})".format(new_int, i_int),
                                    )
                    else:
                        # same values

                        # same scheme, same date intervals, skip
                        if i_int == new_int:
                            is_overlapping_or_extending = True
                            continue

                        # we can extend, merge or block
                        if extend_overlapping:
                            # extension, get new dates for i
                            if new_int.start.date is None or i_int.start.date is None:
                                i.start_date = None
                            else:
                                i.start_date = min(i.start_date, new_int.start.date)

                            if new_int.end.date is None or i_int.end.date is None:
                                i.end_date = None
                            else:
                                i.end_date = max(i.end_date, new_int.end.date)

                            # save i and break the loop
                            i.save()
                            is_overlapping_or_extending = True
                            break
                        elif merge_overlapping:
                            nonnull_start_dates = list(
                                filter(lambda x: x is not None, [new_int.start.date, i_int.start.date])
                            )
                            if len(nonnull_start_dates):
                                i.start_date = min(nonnull_start_dates)

                            nonnull_end_dates = list(
                                filter(lambda x: x is not None, [new_int.end.date, i_int.end.date])
                            )
                            if len(nonnull_end_dates):
                                i.end_date = max(nonnull_end_dates)

                            i.save()
                            is_overlapping_or_extending = True
                        else:
                            # block insertion
                            if new_int.start.date is None and new_int.end.date is None and i_int == new_int:
                                return
                            else:
                                raise OverlappingDateIntervalException(
                                    i,
                                    "Identifier with same scheme could not be created, "
                                    "due to overlapping dates ({0} : {1})".format(new_int, i_int),
                                )

            # no overlaps, nor extensions, the identifier can be created
            if not is_overlapping_or_extending:
                return self.identifiers.get_or_create(scheme=scheme, identifier=identifier, **kwargs)

    def add_identifiers(self, identifiers, update=True):
        """ add identifiers and skip those that generate exceptions

        Exceptions generated when dates overlap are gathered in a
        pipe-separated array and returned.

        :param identifiers:
        :param update:
        :return:
        """
        exceptions = []
        for i in identifiers:
            try:
                self.add_identifier(**i)
            except Exception as e:
                exceptions.append(str(e))
                pass

        if len(exceptions):
            raise Exception(" | ".join(exceptions))

    def update_identifiers(self, new_identifiers):
        """update identifiers,
        removing those not present in new_identifiers
        overwriting those present and existing,
        adding those present and not existing

        :param new_identifiers: the new list of identifiers
        :return:
        """
        existing_ids = set(self.identifiers.values_list("id", flat=True))
        new_ids = set(n["id"] for n in new_identifiers if "id" in n)

        # remove objects
        delete_ids = existing_ids - new_ids
        self.identifiers.filter(id__in=delete_ids).delete()

        # update objects
        for id_ in new_ids & existing_ids:
            u_name = list(filter(lambda x: x.get("id", None) == id_, new_identifiers))[0].copy()

            self.identifiers.filter(pk=u_name.pop("id")).update(**u_name)

        # add objects
        for new_identifier in new_identifiers:
            if "id" not in new_identifier:
                self.add_identifier(**new_identifier)


class ClassificationShortcutsMixin:
    classifications: ReverseGenericManyToOneDescriptor

    def add_classification(self, scheme, code=None, descr=None, allow_same_scheme=False, **kwargs):
        """Add classification to the instance inheriting the mixin
        :param scheme: classification scheme (ATECO, LEGAL_FORM_IPA, ...)
        :param code:   classification code, internal to the scheme
        :param descr:  classification textual description (brief)
        :param allow_same_scheme: allows same scheme multiple classifications (for labels)
        :param kwargs: other params as source, start_date, end_date, ...
        :return: the classification instance just added
        """
        # classifications having the same scheme, code and descr are considered
        # overlapping and will not be added
        if code is None and descr is None:
            raise Exception("At least one between descr " "and code must take value")

        # first create the Classification object,
        # or fetch an already existing one
        c, created = popolo_models.Classification.objects.get_or_create(
            scheme=scheme, code=code, descr=descr, defaults=kwargs
        )

        # then add the ClassificationRel to classifications
        self.add_classification_rel(c, allow_same_scheme, **kwargs)

    def add_classification_rel(self, classification, allow_same_scheme=False, **kwargs):
        """Add classification (rel) to the instance inheriting the mixin

        :param classification: existing Classification instance or ID
        :param allow_same_scheme: allows same scheme multiple classifications (for labels)
        :param kwargs: other params: start_date, end_date, end_reason
        :return: the ClassificationRel instance just added
        """
        # then add the ClassificationRel to classifications
        if not isinstance(classification, int) and not isinstance(classification, popolo_models.Classification):
            raise Exception("classification needs to be an integer ID or a Classification instance")

        multiple_values_schemes = getattr(self, 'MULTIPLE_CLASSIFICATIONS_SCHEMES', [])

        if isinstance(classification, int):
            # add classification_rel only if self is not already classified with classification of the same scheme
            cl = popolo_models.Classification.objects.get(id=classification)
            same_scheme_classifications = self.classifications.filter(classification__scheme=cl.scheme)
            if allow_same_scheme or not same_scheme_classifications or cl.scheme in multiple_values_schemes:
                c, created = self.classifications.get_or_create(classification_id=classification, **kwargs)
                return c
        else:
            # add classification_rel only if self is not already classified with classification of the same scheme
            same_scheme_classifications = self.classifications.filter(classification__scheme=classification.scheme)
            if allow_same_scheme or not same_scheme_classifications or classification.scheme in multiple_values_schemes:
                c, created = self.classifications.get_or_create(classification=classification, **kwargs)
                return c

        # return None if no classification was added
        return None

    def add_classifications(self, new_classifications, allow_same_scheme=False):
        """ add multiple classifications
        :param new_classifications: classification ids to be added
        :param allow_same_scheme: allows same scheme multiple classifications (for labels)
        :return:
        """
        # add objects
        for new_classification in new_classifications:
            if "classification" in new_classification:
                self.add_classification_rel(**new_classification, allow_same_scheme=allow_same_scheme)
            else:
                self.add_classification(**new_classification, allow_same_scheme=allow_same_scheme)

    def update_classifications(self, new_classifications):
        """update classifications,
        removing those not present in new_classifications
        overwriting those present and existing,
        adding those present and not existing

        :param new_classifications: the new list of classification_rels
        :return:
        """

        existing_ids = set(self.classifications.values_list("classification", flat=True))
        new_ids = set(n.get("classification", None) for n in new_classifications)

        # remove objects
        delete_ids = existing_ids - set(new_ids)
        self.classifications.filter(classification__in=delete_ids).delete()

        # update objects (reference to already existing only)
        self.add_classifications([{"classification": c_id["classification"]} for c_id in new_classifications])

        # update or create objects
        # for id in new_ids:
        #     u = list(filter(lambda x: x['classification'].id == id, new_classifications))[0].copy()
        #     u.pop('classification_id', None)
        #     u.pop('content_type_id', None)
        #     u.pop('object_id', None)
        #     self.classifications.update_or_create(
        #         classification_id=id,
        #         content_type_id=ContentType.objects.get_for_model(self).pk,
        #         object_id=self.id,
        #         defaults=u
        #     )


class LinkShortcutsMixin:
    links: ReverseGenericManyToOneDescriptor

    def add_link(self, url, **kwargs):
        note = kwargs.pop("note", "")
        link, created = popolo_models.Link.objects.get_or_create(url=url, note=note, defaults=kwargs)

        # then add the LinkRel to links
        self.links.get_or_create(link=link)

        return link

    def add_links(self, links):
        """TODO: clarify usage"""
        for link in links:
            if "link" in link:
                self.add_link(**link["link"])
            else:
                self.add_link(**link)

    def update_links(self, new_links):
        """update links, (link_rels, actually)
        removing those not present in new_links
        overwriting those present and existing,
        adding those present and not existing

        :param new_links: the new list of link_rels
        :return:
        """
        existing_ids = set(self.links.values_list("id", flat=True))
        new_ids = set(link.get("id", None) for link in new_links)

        # remove objects
        delete_ids = existing_ids - set(new_ids)
        self.links.filter(id__in=delete_ids).delete()

        # update or create objects
        for id_ in new_ids:
            ul = list(filter(lambda x: x.get("id", None) == id_, new_links)).copy()
            for u in ul:
                u.pop("id", None)
                u.pop("content_type_id", None)
                u.pop("object_id", None)

                # update underlying link
                u_link = u["link"]
                l, created = popolo_models.Link.objects.get_or_create(url=u_link["url"], note=u_link["note"])

                # update link_rel
                self.links.update_or_create(link=l)


class SourceShortcutsMixin:
    sources: ReverseGenericManyToOneDescriptor

    def add_source(self, url, **kwargs):
        note = kwargs.pop("note", "")
        s, created = popolo_models.Source.objects.get_or_create(url=url, note=note, defaults=kwargs)

        # then add the SourceRel to sources
        self.sources.get_or_create(source=s)

        return s

    def add_sources(self, sources):
        """TODO: clarify usage"""
        for s in sources:
            if "source" in s:
                self.add_source(**s["source"])
            else:
                self.add_source(**s)

    def update_sources(self, new_sources):
        """update sources,
        removing those not present in new_sources
        overwriting those present and existing,
        adding those present and not existing

        :param new_sources: the new list of link_rels
        :return:
        """
        existing_ids = set(self.sources.values_list("id", flat=True))
        new_ids = set(link.get("id", None) for link in new_sources)

        # remove objects
        delete_ids = existing_ids - new_ids
        self.sources.filter(id__in=delete_ids).delete()

        # update or create objects
        for id_ in new_ids:
            ul = list(filter(lambda x: x.get("id", None) == id_, new_sources)).copy()
            for u in ul:
                u.pop("id", None)
                u.pop("content_type_id", None)
                u.pop("object_id", None)

                # update underlying source
                u_source = u["source"]
                l, created = popolo_models.Source.objects.get_or_create(url=u_source["url"], note=u_source["note"])

                # update source_rel
                self.sources.update_or_create(source=l)


class OwnerShortcutsMixin:
    ownerships: ReverseManyToOneDescriptor

    def add_ownership(
        self,
        organization: "popolo_models.Organization",
        allow_overlap: bool = False,
        percentage: float = 0.0,
        **kwargs,
    ) -> "popolo_models.Ownership":
        """
        Add this instance as "owner" of the given `Organization`

        Multiple ownerships to the same organization can be added
        only when start/end dates are not overlapping, or if overlap is explicitly allowed
        through the `allow_overlap` parameter.

        :param organization: The owned `Organization`.
        :param allow_overlap: Allow start/end date overlap of already existing ownerships.
        :param percentage: The ownership share.
        :param kwargs: Additional args to be passed when creating the `Ownership`.
        :return: The created `Ownership`.
        """

        # New dates interval as PartialDatesInterval instance
        new_interval = PartialDatesInterval(start=kwargs.get("start_date", None), end=kwargs.get("end_date", None))

        is_overlapping = False

        # Loop over already existing ownerships of the same organization
        same_org_ownerships = self.ownerships.filter(owned_organization=organization, percentage=percentage)
        for ownership in same_org_ownerships:

            # Existing identifier interval as PartialDatesInterval instance
            interval = PartialDatesInterval(start=ownership.start_date, end=ownership.end_date)

            # Get overlap days:
            #  > 0 means crossing
            # == 0 means touching (considered non overlapping)
            #  < 0 means not overlapping
            overlap = PartialDate.intervals_overlap(new_interval, interval)

            if overlap > 0:
                is_overlapping = True

        if not is_overlapping or allow_overlap:
            obj = self.ownerships.create(owned_organization=organization, percentage=percentage, **kwargs)
            return obj
