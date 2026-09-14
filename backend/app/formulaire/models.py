import uuid

from django.db import models
from django.utils import timezone
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
    xp_duration_start = models.IntegerField(
        blank=True, null=True, verbose_name="Durée d'expérience initiale (années)",
        help_text="Valeur initiale saisie au moment de la création"
    )

    # Dossier de compétences complet en JSON
    dossier = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Dossier de compétences",
    )  # Note: JSONField handles mutable default properly via callable

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(default=timezone.now, verbose_name="Mis à jour le")

    class Meta:
        verbose_name = "Candidat"
        verbose_name_plural = "Candidats"
        ordering = ("-updated_at",)

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    def save(self, *args, **kwargs):
        # Toujours mettre à jour updated_at au moment de l'enregistrement (sans microsecondes)
        self.updated_at = timezone.now().replace(microsecond=0)

        # Truncate created_at to seconds si c'est la première sauvegarde
        if not self.pk:
            self.created_at = timezone.now().replace(microsecond=0)
        # S'assurer que updated_at est toujours sauvegardé, même avec update_fields
        if 'update_fields' in kwargs:
            update_fields = kwargs['update_fields']
            if 'updated_at' not in update_fields:
                kwargs['update_fields'] = list(update_fields) + ['updated_at']

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

    @property
    def xp_duration_calculated(self) -> int | None:
        """
        Calcule la durée d'expérience actuelle basée sur :
        - La valeur initiale (xp_duration_start) renseignée à la création
        - Le nombre d'années écoulées depuis la création (created_at à maintenant)

        Retourne :
            int: Durée calculée en années complètes
            None: Si xp_duration_start n'est pas défini
        """
        if self.xp_duration_start is None or self.created_at is None:
            return None

        # Calculer les années complètes écoulées depuis la création
        now = timezone.now()
        years_elapsed = (now - self.created_at).days / 365.25
        years_elapsed_full = int(years_elapsed)

        # Retourner la durée initiale + années écoulées
        return self.xp_duration_start + years_elapsed_full

    def update_xp_duration(self) -> bool:
        """
        Met à jour le champ xp_duration avec la valeur calculée (xp_duration_calculated).
        Appelle save() pour persister le changement en base de données.

        Retourne :
            bool: True si une mise à jour a eu lieu, False sinon
        """
        calculated = self.xp_duration_calculated
        if calculated is None:
            return False

        if self.xp_duration != calculated:
            self.xp_duration = calculated
            self.save(update_fields=['xp_duration', 'updated_at'])
            return True

        return False
