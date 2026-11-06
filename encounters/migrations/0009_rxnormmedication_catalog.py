# RxNorm catalog concepts imported from the local prescribable release.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("encounters", "0008_medicationprescription"),
    ]

    operations = [
        migrations.CreateModel(
            name="RxNormMedication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("rxcui", models.CharField(db_index=True, max_length=20, unique=True)),
                ("name", models.CharField(db_index=True, max_length=500)),
                ("term_type", models.CharField(max_length=10)),
            ],
            options={
                "verbose_name": "RxNorm Medication",
                "verbose_name_plural": "RxNorm Medication Catalog",
                "ordering": ["name"],
            },
        ),
        migrations.AddField(
            model_name="medicationprescription",
            name="rxnorm_medication",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="prescriptions", to="encounters.rxnormmedication"),
        ),
    ]
