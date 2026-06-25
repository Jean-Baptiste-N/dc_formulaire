"""
Migration des descriptions dans xp_pro du format string vers le format structuré {title, description}.
"""
from django.core.management.base import BaseCommand
from formulaire.models import Candidat


class Command(BaseCommand):
    help = "Convertit les descriptions dans xp_pro du format string vers le format {title, description}"

    def handle(self, *args, **options):
        updated_count = 0

        for candidat in Candidat.objects.all():
            dossier = candidat.dossier or {}
            xp_pro = dossier.get("xp_pro", [])
            
            if not xp_pro:
                continue

            modified = False
            for exp in xp_pro:
                description = exp.get("description", "")
                
                # Check if description is a string (old format)
                if isinstance(description, str) and description:
                    # Convert string to structured list
                    # Split by bullet points if they exist
                    lines = [line.strip() for line in description.split('\n') if line.strip()]
                    
                    if len(lines) > 1:
                        # Multiple items - create one per line
                        new_description = [
                            {"title": line, "description": []}
                            for line in lines
                        ]
                    else:
                        # Single item
                        new_description = [
                            {"title": description, "description": []}
                        ]
                    
                    exp["description"] = new_description
                    modified = True
                elif isinstance(description, str) and not description:
                    # Empty string becomes empty list
                    exp["description"] = []
                    modified = True

            if modified:
                candidat.dossier = dossier
                candidat.save(update_fields=["dossier"])
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ {candidat.nom} {candidat.prenom} - description converties"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Migration complete: {updated_count} candidat(s) updated"
            )
        )
