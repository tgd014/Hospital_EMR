from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from encounters.models import RxNormMedication


class Command(BaseCommand):
    help = "Import active RxNorm clinical and branded drug concepts from RXNCONSO.RRF."

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True, help="Path to the RxNorm prescribe/rrf/RXNCONSO.RRF file")

    def handle(self, *args, **options):
        source = Path(options["source"])
        if not source.is_file():
            raise CommandError(f"RxNorm source file not found: {source}")

        allowed_types = {"SCD", "SBD"}
        batch = []
        seen = set()
        imported = 0

        with source.open("r", encoding="utf-8") as rows:
            for line_number, line in enumerate(rows, start=1):
                columns = line.rstrip("\r\n").split("|")
                if len(columns) < 18:
                    continue
                rxcui, language, _, _, _, _, _, _, _, _, _, source_name, term_type, _, name, _, suppressed, _ = columns[:18]
                if (
                    language != "ENG"
                    or source_name != "RXNORM"
                    or term_type not in allowed_types
                    or suppressed == "Y"
                    or not rxcui
                    or not name
                    or rxcui in seen
                ):
                    continue

                seen.add(rxcui)
                batch.append(RxNormMedication(rxcui=rxcui, name=name[:500], term_type=term_type))
                if len(batch) >= 1000:
                    RxNormMedication.objects.bulk_create(
                        batch,
                        update_conflicts=True,
                        update_fields=["name", "term_type"],
                        unique_fields=["rxcui"],
                    )
                    imported += len(batch)
                    batch.clear()

        if batch:
            RxNormMedication.objects.bulk_create(
                batch,
                update_conflicts=True,
                update_fields=["name", "term_type"],
                unique_fields=["rxcui"],
            )
            imported += len(batch)

        self.stdout.write(self.style.SUCCESS(f"Imported or updated {imported} RxNorm concepts."))
