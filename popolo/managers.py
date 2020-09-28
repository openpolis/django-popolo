from django.db import models
from datetime import datetime

from popolo import models as popolo_models


class HistoricAreaManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

    def comuni_with_prov_and_istat_identifiers(self, d=None, filters=None, excludes=None):
        """Return the list of comuni active at a given date,
        with the name and identifier, plus the ISTAT_CODE_COM identifier valid at a given time
        and province and region information

        :param d: the date
        :param filters: a list of filters, in the form of dict
        :param excludes: a list of exclude in the form of dict
        :return: a list of Area objects, annotated with these fields:
         - id
         - identifier
         - name
         - istat_identifier
         - prov_id
         - prov_name
         - prov_identifier
         - reg_id
         - reg_name
         - reg_identifier
        """
        if d is None:
            d = datetime.strftime(datetime.now(), '%Y-%m-%d')

        ar_qs = popolo_models.AreaRelationship.objects.filter(classification="FIP")
        ar_qs = (
            ar_qs.filter(start_date__lte=d, end_date__gte=d)
            | ar_qs.filter(start_date__lte=d, end_date__isnull=True)
            | ar_qs.filter(start_date__isnull=True, end_date__gte=d)
            | ar_qs.filter(start_date__isnull=True, end_date__isnull=True)
        )

        prev_provs = {
            a["source_area_id"]: {
                "prov_id": a["dest_area_id"],
                "prov": a["dest_area__identifier"],
                "prov_name": a["dest_area__name"],
            }
            for a in ar_qs.values(
                "source_area_id", "source_area__name", "dest_area_id", "dest_area__name", "dest_area__identifier"
            )
        }

        current_regs = {
            a["id"]: {
                "reg_id": a["parent__parent_id"],
                "reg_identifier": a["parent__parent__identifier"],
                "reg_name": a["parent__parent__name"],
            }
            for a in popolo_models.Area.objects.comuni()
            .current(d)
            .values("id", "parent__parent_id", "parent__parent__name", "parent__parent__identifier")
        }

        current_provs = {
            a["id"]: {"prov_id": a["parent_id"], "prov": a["parent__identifier"], "prov_name": a["parent__name"]}
            for a in popolo_models.Area.objects.comuni()
            .current(d)
            .values("id", "parent_id", "parent__name", "parent__identifier")
        }

        provs = {}
        for a_id, prov_info in current_provs.items():
            if a_id in prev_provs:
                prov_id = prev_provs[a_id]["prov_id"]
                prov = prev_provs[a_id]["prov"]
                prov_name = prev_provs[a_id]["prov_name"]
            else:
                prov_id = current_provs[a_id]["prov_id"]
                prov = current_provs[a_id]["prov"]
                prov_name = current_provs[a_id]["prov_name"]

            provs[a_id] = {"prov_id": prov_id, "prov": prov, "prov_name": prov_name}

        current_comuni_qs = popolo_models.Area.objects.comuni().current(moment=d)

        current_comuni_qs = (
            current_comuni_qs.filter(
                identifiers__scheme="ISTAT_CODE_COM", identifiers__start_date__lte=d, identifiers__end_date__gte=d
            )
            | current_comuni_qs.filter(
                identifiers__scheme="ISTAT_CODE_COM",
                identifiers__start_date__lte=d,
                identifiers__end_date__isnull=True,
            )
            | current_comuni_qs.filter(
                identifiers__scheme="ISTAT_CODE_COM",
                identifiers__start_date__isnull=True,
                identifiers__end_date__isnull=True,
            )
            | current_comuni_qs.filter(
                identifiers__scheme="ISTAT_CODE_COM",
                identifiers__start_date__isnull=True,
                identifiers__end_date__gte=d,
            )
        )

        if filters:
            for f in filters:
                current_comuni_qs = current_comuni_qs.filter(**f)
        if excludes:
            for e in excludes:
                current_comuni_qs = current_comuni_qs.exclude(**e)

        current_comuni = current_comuni_qs.values("id", "name", "identifier", "identifiers__identifier")

        results_list = []
        for com in current_comuni:
            c = self.model(id=com["id"], name=com["name"], identifier=com["identifier"])
            c.istat_identifier = com["identifiers__identifier"]
            c.prov_name = provs[com["id"]]["prov_name"]
            c.prov_id = provs[com["id"]]["prov_id"]
            c.prov_identifier = provs[com["id"]]["prov"]
            c.reg_name = current_regs[com["id"]]["reg_name"]
            c.reg_id = current_regs[com["id"]]["reg_id"]
            c.reg_identifier = current_regs[com["id"]]["reg_identifier"]

            results_list.append(c)

        return results_list
