import uuid

from django.db import models


class Candidat(models.Model):
    """Représente un candidat avec son parcours professionnel structuré en JSON."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=150, verbose_name="Nom")
    prenom = models.CharField(max_length=150, verbose_name="Prénom")
    email = models.EmailField(unique=True, verbose_name="Email")
    parcours = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Parcours professionnel",
        help_text=(
            "Structure JSON : {'sections': [{'id': ..., 'titre': ..., 'postes': "
            "[{'id': ..., 'texte': ..., 'sous_postes': [{'id': ..., 'texte': ...}]}]}]}"
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")

    class Meta:
        verbose_name = "Candidat"
        verbose_name_plural = "Candidats"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    def get_sections(self):
        """Retourne la liste des sections du parcours."""
        return self.parcours.get("sections", [])
