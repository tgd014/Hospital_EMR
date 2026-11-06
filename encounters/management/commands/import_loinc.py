
import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from encounters.models import LabTest


class Command(BaseCommand):
    help = "Import the official LOINC catalog from Loinc.csv."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            default="data/loinc/extracted/LoincTable/Loinc.csv",
            help="Path to the official Loinc.csv file.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            help="Number of records processed per batch.",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["file"])
        batch_size = options["batch_size"]

        if not csv_path.is_file():
            raise CommandError(
                f"LOINC CSV file not found: {csv_path.resolve()}"
            )

        if batch_size < 1:
            raise CommandError("--batch-size must be at least 1.")

        processed = 0
        created = 0
        updated = 0
        skipped = 0

        self.stdout.write(f"Reading LOINC catalog: {csv_path.resolve()}")

        try:
            with csv_path.open(
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as csv_file:
                reader = csv.DictReader(csv_file)

                required_columns = {
                    "LOINC_NUM",
                    "LONG_COMMON_NAME",
                }

                if not reader.fieldnames or not required_columns.issubset(
                    set(reader.fieldnames)
                ):
                    raise CommandError(
                        "The CSV is missing required columns: "
                        "LOINC_NUM and/or LONG_COMMON_NAME."
                    )

                batch = []

                for row in reader:
                    code = (row.get("LOINC_NUM") or "").strip()
                    long_name = (
                        row.get("LONG_COMMON_NAME") or ""
                    ).strip()

                    if not code or not long_name:
                        skipped += 1
                        continue

                    batch.append(
                        {
                            "loinc_code": code,
                            "long_common_name": long_name[:500],
                            "short_name": (
                                row.get("SHORTNAME") or ""
                            ).strip()[:255],
                            "component": (
                                row.get("COMPONENT") or ""
                            ).strip()[:500],
                            "property": (
                                row.get("PROPERTY") or ""
                            ).strip()[:100],
                            "time_aspect": (
                                row.get("TIME_ASPCT") or ""
                            ).strip()[:100],
                            "system": (
                                row.get("SYSTEM") or ""
                            ).strip()[:255],
                            "scale_type": (
                                row.get("SCALE_TYP") or ""
                            ).strip()[:100],
                            "method_type": (
                                row.get("METHOD_TYP") or ""
                            ).strip()[:255],
                            "test_class": (
                                row.get("CLASS") or ""
                            ).strip()[:100],
                            "status": (
                                row.get("STATUS") or ""
                            ).strip()[:50],
                        }
                    )

                    if len(batch) >= batch_size:
                        batch_created, batch_updated = self.save_batch(
                            batch
                        )
                        created += batch_created
                        updated += batch_updated
                        processed += len(batch)
                        batch.clear()

                        self.stdout.write(
                            f"Processed {processed:,} rows..."
                        )

                if batch:
                    batch_created, batch_updated = self.save_batch(batch)
                    created += batch_created
                    updated += batch_updated
                    processed += len(batch)

        except (OSError, UnicodeError, csv.Error) as exc:
            raise CommandError(
                f"Could not read the LOINC CSV: {exc}"
            ) from exc

        self.stdout.write(self.style.SUCCESS("LOINC import finished."))
        self.stdout.write(f"Rows imported or updated: {processed:,}")
        self.stdout.write(f"New catalog entries: {created:,}")
        self.stdout.write(f"Existing entries updated: {updated:,}")
        self.stdout.write(f"Rows skipped: {skipped:,}")
        self.stdout.write(
            f"Total catalog entries in database: {LabTest.objects.count():,}"
        )

    @transaction.atomic
    def save_batch(self, batch):
        codes = [item["loinc_code"] for item in batch]

        existing = {
            test.loinc_code: test
            for test in LabTest.objects.filter(loinc_code__in=codes)
        }

        to_create = []
        to_update = []

        for item in batch:
            code = item["loinc_code"]
            test = existing.get(code)

            if test is None:
                to_create.append(LabTest(**item))
                continue

            for field, value in item.items():
                if field != "loinc_code":
                    setattr(test, field, value)

            to_update.append(test)

        if to_create:
            LabTest.objects.bulk_create(
                to_create,
                batch_size=500,
            )

        if to_update:
            LabTest.objects.bulk_update(
                to_update,
                fields=[
                    "long_common_name",
                    "short_name",
                    "component",
                    "property",
                    "time_aspect",
                    "system",
                    "scale_type",
                    "method_type",
                    "test_class",
                    "status",
                ],
                batch_size=500,
            )

        return len(to_create), len(to_update)
