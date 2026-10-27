# Fusion des migrations de Souha (profession) et de Yasmine (relation familiale).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("predictor", "0001_occupation_account"),
        ("predictor", "0002_relationshipprediction_income"),
    ]

    operations = []
