# Generated by Django 5.2 on 2025-04-22 05:40

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notes", "0002_note_is_public"),
    ]

    operations = [
        migrations.AlterField(
            model_name="note",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid4, editable=False, primary_key=True, serialize=False
            ),
        ),
    ]
