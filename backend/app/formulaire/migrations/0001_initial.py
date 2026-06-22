import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Candidat",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("nom", models.CharField(max_length=150, verbose_name="Nom")),
                ("prenom", models.CharField(max_length=150, verbose_name="Prénom")),
                (
                    "email",
                    models.EmailField(
                        max_length=254, unique=True, verbose_name="Email"
                    ),
                ),
                (
                    "parcours",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text=(
                            "Structure JSON : {'sections': [{'id': ..., 'titre': ..., "
                            "'postes': [{'id': ..., 'texte': ..., 'sous_postes': "
                            "[{'id': ..., 'texte': ...}]}]}]}"
                        ),
                        verbose_name="Parcours professionnel",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Créé le"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Mis à jour le"),
                ),
            ],
            options={
                "verbose_name": "Candidat",
                "verbose_name_plural": "Candidats",
                "ordering": ["-updated_at"],
            },
        ),
    ]
