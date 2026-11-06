from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("encounters", "0009_rxnormmedication_catalog"),
    ]

    operations = [
        migrations.AlterField(
            model_name="medicationprescription",
            name="medication_name",
            field=models.CharField(max_length=500),
        ),
    ]
