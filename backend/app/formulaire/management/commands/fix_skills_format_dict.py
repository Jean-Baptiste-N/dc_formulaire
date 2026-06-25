"""
Migration des competences du format string vers le format dict {title, description}.
Utilise apres la modification du code qui attend des dicts pour les skills.
"""
from django.core.management.base import BaseCommand
from formulaire.models import Candidat


class Command(BaseCommand):
    help = "Convertit les competences du format string vers le format dict {title, description}"

    def handle(self, *args, **options):
        updated_count = 0

        for candidat in Candidat.objects.all():
            dossier = candidat.dossier or {}
            if "main_skills" not in dossier:
                continue

            if "bullet" not in dossier["main_skills"]:
                continue

            bullet = dossier["main_skills"]["bullet"]
            if not bullet:
                continue

            # Check if first item is string (old format)
            if isinstance(bullet[0], str):
                # Convert strings to dicts
                new_bullet = [
                    {"title": skill, "description": []}
                    for skill in bullet
                ]
                dossier["main_skills"]["bullet"] = new_bullet
                candidat.dossier = dossier
                candidat.save(update_fields=["dossier"])
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ {candidat.nom} {candidat.prenom} - {len(new_bullet)} competences converties"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Migration complete: {updated_count} candidat(s) updated"
            )
        )
