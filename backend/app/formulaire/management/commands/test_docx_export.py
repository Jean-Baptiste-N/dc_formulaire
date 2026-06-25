"""
Test DOCX export to identify template rendering issues.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
from docxtpl import DocxTemplate
from formulaire.models import Candidat
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test DOCX export for a specific candidat'

    def add_arguments(self, parser):
        parser.add_argument('candidat_id', type=str, help='UUID of the candidat')

    def handle(self, *args, **options):
        candidat_id = options['candidat_id']
        
        try:
            candidat = Candidat.objects.get(pk=candidat_id)
        except Candidat.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Candidat {candidat_id} not found'))
            return

        template_path = Path(settings.DOCX_TEMPLATE_PATH)
        
        if not template_path.exists():
            self.stdout.write(self.style.ERROR(f'Template not found: {template_path}'))
            return

        try:
            tpl = DocxTemplate(template_path)
            dossier_data = candidat.dossier or {}

            header_data = dossier_data.get("header", {})
            header_data.update({
                "trigramme": candidat.trigramme,
                "poste": candidat.poste,
                "skills": [],
                "xp_duration": candidat.xp_duration,
            })

            context = {
                "candidat": candidat,
                "nom": candidat.nom,
                "prenom": candidat.prenom,
                "email": candidat.email,
                "trigramme": candidat.trigramme,
                "poste": candidat.poste,
                "xp_duration": candidat.xp_duration,
                "sections": candidat.get_sections() if hasattr(candidat, 'get_sections') else [],
                "dossier": candidat.dossier,
                "header": header_data,
                "main_skills": dossier_data.get("main_skills", {"bullet": []}),
                "xp_pro": dossier_data.get("xp_pro", []),
                "formations": dossier_data.get("formations", []),
                "certifications": dossier_data.get("certifications", []),
            }

            self.stdout.write(self.style.SUCCESS('=== Context Data ==='))
            for key, value in context.items():
                if isinstance(value, list):
                    self.stdout.write(f'{key}: list({len(value)} items)')
                    if value and key in ['main_skills', 'xp_pro', 'formations', 'certifications', 'sections']:
                        self.stdout.write(f'  First item: {repr(value[0])[:200]}')
                elif isinstance(value, dict):
                    self.stdout.write(f'{key}: dict({len(value)} keys)')
                    if key in ['main_skills', 'header']:
                        self.stdout.write(f'  Content: {repr(value)[:200]}')
                else:
                    self.stdout.write(f'{key}: {type(value).__name__} = {repr(value)[:100]}')

            self.stdout.write(self.style.SUCCESS('\n=== Rendering Template ==='))
            tpl.render(context)
            
            self.stdout.write(self.style.SUCCESS('✅ Template rendered successfully!'))
            
            # Try to save to a test file
            import io
            buffer = io.BytesIO()
            tpl.save(buffer)
            buffer.seek(0)
            
            test_path = Path(settings.DOCX_TEMPLATE_PATH).parent / "test_export.docx"
            with open(test_path, 'wb') as f:
                f.write(buffer.read())
            
            self.stdout.write(self.style.SUCCESS(f'✅ Saved test file: {test_path}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
