import re
import zipfile
from pathlib import Path
from io import TextIOWrapper

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from encounters.models import ProcedureCatalog


FISCAL_YEAR = "2027"
ORDER_FILE_NAME = "icd10pcs_order_2027.txt"
CODE_PATTERN = re.compile(r"^[A-Z0-9]{7}$")


class Command(BaseCommand):
    help = "Import the CMS ICD-10-PCS order file into the procedure catalog."

    def add_arguments(self, parser):
        parser.add_argument(
            "source",
            help="CMS order-file ZIP or extracted icd10pcs_order_2027.txt",
        )

    def handle(self, *args, **options):
        source = Path(options["source"])
        if not source.is_file():
            raise CommandError(f"File not found: {source}")

        if zipfile.is_zipfile(source):
            self._import_zip(source)
        else:
            with source.open("r", encoding="utf-8-sig", errors="replace") as stream:
                self._import_stream(stream)

    def _import_zip(self, source):
        try:
            with zipfile.ZipFile(source) as archive:
                member = next(
                    name
                    for name in archive.namelist()
                    if name.rsplit("/", 1)[-1] == ORDER_FILE_NAME
                )
                with archive.open(member) as raw_stream:
                    stream = TextIOWrapper(
                        raw_stream,
                        encoding="utf-8-sig",
                        errors="replace",
                    )
                    self._import_stream(stream)
        except (zipfile.BadZipFile, StopIteration) as exc:
            raise CommandError(
                f"The ZIP must contain {ORDER_FILE_NAME}."
            ) from exc

    def _import_stream(self, stream):
        existing = {
            item.code: item
            for item in ProcedureCatalog.objects.all()
        }
        creates = []
        updates = []
        imported_codes = set()

        for line in stream:
            if len(line) < 77:
                continue

            code = line[6:13].strip().upper()
            if not CODE_PATTERN.fullmatch(code):
                continue

            abbreviated_title = line[16:76].strip()
            full_title = line[77:].strip() if len(line) > 77 else ""
            if not full_title:
                full_title = abbreviated_title
            if not full_title:
                continue

            imported_codes.add(code)
            item = existing.get(code)
            if item is None:
                creates.append(
                    ProcedureCatalog(
                        code=code,
                        abbreviated_title=abbreviated_title[:200],
                        full_title=full_title[:500],
                        fiscal_year=FISCAL_YEAR,
                        is_active=True,
                    )
                )
            else:
                item.abbreviated_title = abbreviated_title[:200]
                item.full_title = full_title[:500]
                item.fiscal_year = FISCAL_YEAR
                item.is_active = True
                updates.append(item)

        if not imported_codes:
            raise CommandError("No seven-character ICD-10-PCS codes were found.")

        with transaction.atomic():
            ProcedureCatalog.objects.all().update(is_active=False)
            ProcedureCatalog.objects.bulk_create(creates, batch_size=1000)
            ProcedureCatalog.objects.bulk_update(
                updates,
                fields=["abbreviated_title", "full_title", "fiscal_year", "is_active"],
                batch_size=1000,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {len(imported_codes):,} ICD-10-PCS {FISCAL_YEAR} entries "
                f"({len(creates):,} new, {len(updates):,} refreshed)."
            )
        )
