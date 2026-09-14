"""
Commande de gestion Django pour mettre à jour automatiquement xp_duration
pour tous les candidats qui ont une xp_duration_start.

Usage:
    python manage.py update_xp_durations [--dry-run]

Options:
    --dry-run: Afficher les mises à jour sans les appliquer
"""

from django.core.management.base import BaseCommand
from formulaire.models import Candidat


class Command(BaseCommand):
    help = "Mettre à jour automatiquement xp_duration pour tous les candidats"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            help='Afficher les mises à jour sans les appliquer',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # Récupérer tous les candidats avec xp_duration_start
        candidats = Candidat.objects.filter(xp_duration_start__isnull=False).all()

        if not candidats.exists():
            self.stdout.write(
                self.style.WARNING("Aucun candidat avec xp_duration_start trouvé.")
            )
            return

        self.stdout.write(f"Traitement de {candidats.count()} candidat(s)...\n")

        updated_count = 0
        unchanged_count = 0

        for candidat in candidats:
            calculated = candidat.xp_duration_calculated

            if calculated is None:
                self.stdout.write(
                    f"  ⚠️  {candidat.prenom} {candidat.nom} (ID: {candidat.id}): "
                    f"Impossible de calculer (xp_duration_start ou created_at manquant)"
                )
                continue

            old_xp = candidat.xp_duration
            diff = calculated - (old_xp or 0)

            if diff == 0:
                unchanged_count += 1
                status = "✓ Pas de changement"
            else:
                updated_count += 1
                status = f"{'→' if not dry_run else '→ DRY-RUN'} {old_xp or 'N/A'} → {calculated}"

            self.stdout.write(
                f"  {status} | {candidat.prenom} {candidat.nom} "
                f"(créé: {candidat.created_at.strftime('%Y-%m-%d')}, "
                f"initial: {candidat.xp_duration_start})"
            )

            if not dry_run and diff != 0:
                candidat.update_xp_duration()

        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS(f"Résumé: {updated_count} mise(s) à jour, {unchanged_count} inchangé(s)"))
        if dry_run:
            self.stdout.write(self.style.WARNING("Mode DRY-RUN: Aucune modification en base de données."))
