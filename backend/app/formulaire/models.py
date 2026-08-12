import uuid

from django.db import models
from django.utils.text import slugify


class Candidat(models.Model):
    """Représente un candidat avec son dossier de compétences structuré en JSON."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=150, verbose_name="Nom")
    prenom = models.CharField(max_length=150, verbose_name="Prénom")
    slug = models.SlugField(max_length=200, null=True, blank=True, verbose_name="Slug (prénom-nom)")
    email = models.EmailField(unique=True, verbose_name="Email")

    # Header info
    trigramme = models.CharField(max_length=10, blank=True, verbose_name="Trigramme")
    poste = models.CharField(max_length=150, blank=True, verbose_name="Poste")
    xp_duration = models.IntegerField(blank=True, null=True, verbose_name="Durée d'expérience (années)")

    # Dossier de compétences complet en JSON
    dossier = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Dossier de compétences",
    )  # Note: JSONField handles mutable default properly via callable

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")

    class Meta:
        verbose_name = "Candidat"
        verbose_name_plural = "Candidats"
        ordering = ("-updated_at",)

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.prenom}-{self.nom}")
        super().save(*args, **kwargs)

    def get_display_url_edit(self):
        """Retourne l'URL affichée avec le slug pour la page d'édition (pour le breadcrumb/navbar)."""
        return f"/candidat/{self.slug}/modifier/"

    def get_display_url_detail(self):
        """Retourne l'URL affichée avec le slug pour la page de détail."""
        return f"/candidat/{self.slug}/detail/"

    def get_sections(self):
        """Retourne la liste des sections du parcours (pour compatibilité)."""
        return self.dossier.get("sections", [])
