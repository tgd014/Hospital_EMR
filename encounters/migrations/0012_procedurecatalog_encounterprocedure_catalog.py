import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("encounters", "0011_encounterprocedure"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProcedureCatalog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.CharField(max_length=7, unique=True)),
                ("abbreviated_title", models.CharField(blank=True, max_length=200)),
                ("full_title", models.CharField(max_length=500)),
                ("fiscal_year", models.CharField(default="2027", max_length=4)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Procedure Catalog Entry",
                "verbose_name_plural": "Procedure Catalog",
                "ordering": ["full_title"],
            },
        ),
        migrations.AddField(
            model_name="encounterprocedure",
            name="catalog_procedure",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="encounter_procedures",
                to="encounters.procedurecatalog",
            ),
        ),
        migrations.AddField(
            model_name="encounterprocedure",
            name="procedure_snapshot",
            field=models.CharField(blank=True, default="", max_length=500),
            preserve_default=False,
        ),
    ]
