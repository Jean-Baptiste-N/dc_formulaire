"""
Management command to migrate existing skills from dict format to simple string format.
Converts: [{"title": "Python", "description": []}, ...] 
to: ["Python", "SQL", "Git"]
"""
from django.core.management.base import BaseCommand
from formulaire.models import Candidat


class Command(BaseCommand):
    help = 'Migrate existing skills from dict format to simple string format'

    def handle(self, *args, **options):
        count = 0
        for candidat in Candidat.objects.all():
            dossier = candidat.dossier or {}
            
            # Check if main_skills.bullet exists and needs conversion
            if "main_skills" in dossier and "bullet" in dossier["main_skills"]:
                bullet = dossier["main_skills"]["bullet"]
                
                # If items are dicts, convert to strings
                if bullet and isinstance(bullet[0], dict):
                    new_bullet = [
                        item.get("title", str(item))
                        for item in bullet
                        if item
                    ]
                    dossier["main_skills"]["bullet"] = new_bullet
                    candidat.dossier = dossier
                    candidat.save(update_fields=["dossier"])
                    count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ {candidat} - {len(new_bullet)} competences'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Migration complete: {count} candidats updated')
        )
