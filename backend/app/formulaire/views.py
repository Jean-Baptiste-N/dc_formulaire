import logging
import uuid
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from .forms import CandidatInfoForm
from .models import Candidat

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _new_id():
    return str(uuid.uuid4())


def _ensure_realization_ids(description):
    """Ajoute des IDs aux réalisations qui n'en ont pas (migration)."""
    if not isinstance(description, list):
        return description

    for item in description:
        if "id" not in item:
            item["id"] = _new_id()
        if "description" in item and isinstance(item["description"], list):
            _ensure_realization_ids(item["description"])

    return description



def _empty_dossier():
    """Initialise la structure du dossier de competences."""
    return {
        "header": {},
        "main_skills": {
            "bullet": []
        },
        "formations": [],
        "certifications": [],
        "xp_pro": [],
        "sections": []  # Pour compatibilité avec l'ancien système
    }


# ---------------------------------------------------------------------------
# Candidat list / create
# ---------------------------------------------------------------------------

def candidat_list(request):
    candidats = Candidat.objects.all()
    return render(request, "formulaire/candidat_list.html", {"candidats": candidats})


def candidat_create(request):
    if request.method == "POST":
        form = CandidatInfoForm(request.POST)
        if form.is_valid():
            candidat = form.save(commit=False)
            candidat.dossier = _empty_dossier()
            candidat.save()
            return redirect("formulaire:candidat_edit", pk=candidat.pk)
    else:
        form = CandidatInfoForm()
    return render(request, "formulaire/candidat_create.html", {"form": form})


# ---------------------------------------------------------------------------
# Candidat edit (main form)
# ---------------------------------------------------------------------------

def candidat_edit(request, pk):
    candidat = get_object_or_404(Candidat, pk=pk)

    # Enrichir les réalisations avec des IDs si nécessaire et sauvegarder
    ids_added = False
    if candidat.dossier and "xp_pro" in candidat.dossier:
        for exp in candidat.dossier["xp_pro"]:
            if "description" in exp:
                _ensure_realization_ids(exp["description"])
                ids_added = True

    # Sauvegarder si des IDs ont été ajoutés (migration data)
    if ids_added:
        candidat.save(update_fields=["dossier"])

    if request.method == "POST":
        form = CandidatInfoForm(request.POST, instance=candidat)
        if form.is_valid():
            form.save()

            # Synchroniser les infos dans le dossier['header']
            dossier = candidat.dossier or _empty_dossier()
            dossier['header'] = {
                'nom': candidat.nom,
                'prenom': candidat.prenom,
                'email': candidat.email,
                'trigramme': candidat.trigramme,
                'poste': candidat.poste,
                'xp_duration': candidat.xp_duration,
            }
            candidat.dossier = dossier
            candidat.save(update_fields=['dossier'])
    else:
        form = CandidatInfoForm(instance=candidat)
    return render(
        request,
        "formulaire/candidat_edit.html",
        {"candidat": candidat, "form": form},
    )


def candidat_detail(request, pk):
    candidat = get_object_or_404(Candidat, pk=pk)
    return render(request, "formulaire/candidat_detail.html", {"candidat": candidat})


# ---------------------------------------------------------------------------
# Compétences (Skills)
# ---------------------------------------------------------------------------

@require_POST
def skills_add(request, pk):
    """Ajoute les competences du candidat dans main_skills.bullet."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    skills_input = request.POST.get("skills", "").strip()
    if skills_input:
        # Parse les competences separees par des virgules
        new_skills = [s.strip() for s in skills_input.split(",") if s.strip()]

        # Initialiser main_skills si necessaire
        if "main_skills" not in dossier:
            dossier["main_skills"] = {"bullet": []}
        if "bullet" not in dossier["main_skills"]:
            dossier["main_skills"]["bullet"] = []

        # Recuperer les skills existants
        existing_skills = {item["title"] for item in dossier["main_skills"]["bullet"]}

        # Ajoute les nouvelles competences (evite les doublons)
        for skill in new_skills:
            if skill not in existing_skills:
                dossier["main_skills"]["bullet"].append({
                    "title": skill,
                    "description": []
                })

        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

    return redirect("formulaire:candidat_edit", pk=pk)


@require_POST
def skill_remove(request, pk, skill):
    """Supprime une competence de main_skills.bullet."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    if "main_skills" in dossier and "bullet" in dossier["main_skills"]:
        # Supprimer la competence avec le titre correspondant
        dossier["main_skills"]["bullet"] = [
            item for item in dossier["main_skills"]["bullet"] if item.get("title") != skill
        ]
        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

    return redirect("formulaire:candidat_edit", pk=pk)


# ---------------------------------------------------------------------------
# Formations
# ---------------------------------------------------------------------------

@require_POST
def formation_add(request, pk):
    """Ajoute une formation."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    formation = {
        "title": request.POST.get("title", "").strip(),
        "school": request.POST.get("school", "").strip(),
        "date": request.POST.get("date", "").strip(),
        "description": request.POST.get("description", "").strip(),
    }

    if formation["title"] and formation["school"]:
        if "formations" not in dossier:
            dossier["formations"] = []
        dossier["formations"].append(formation)
        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

    return redirect("formulaire:candidat_edit", pk=pk)


@require_POST
def formation_remove(request, pk, index):
    """Supprime une formation."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    try:
        index = int(index)
        if "formations" in dossier and 0 <= index < len(dossier["formations"]):
            dossier["formations"].pop(index)
            candidat.dossier = dossier
            candidat.save(update_fields=["dossier"])
    except (ValueError, IndexError):
        pass

    return redirect("formulaire:candidat_edit", pk=pk)


# ---------------------------------------------------------------------------
# Certifications
# ---------------------------------------------------------------------------

@require_POST
def certification_add(request, pk):
    """Ajoute une certification."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    certification = {
        "title": request.POST.get("title", "").strip(),
        "date": request.POST.get("date", "").strip(),
        "description": request.POST.get("description", "").strip(),
    }

    if certification["title"]:
        if "certifications" not in dossier:
            dossier["certifications"] = []
        dossier["certifications"].append(certification)
        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

    return redirect("formulaire:candidat_edit", pk=pk)


@require_POST
def certification_remove(request, pk, index):
    """Supprime une certification."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    try:
        index = int(index)
        if "certifications" in dossier and 0 <= index < len(dossier["certifications"]):
            dossier["certifications"].pop(index)
            candidat.dossier = dossier
            candidat.save(update_fields=["dossier"])
    except (ValueError, IndexError):
        pass

    return redirect("formulaire:candidat_edit", pk=pk)


# ---------------------------------------------------------------------------
# Expériences professionnelles
# ---------------------------------------------------------------------------

@require_POST
def experience_add(request, pk):
    """Ajoute une expérience professionnelle."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    technologies = request.POST.get("technologies", "").strip()
    tech_list = [t.strip() for t in technologies.split(",") if t.strip()] if technologies else []

    # Pré-remplir avec un premier item vide (scaffolding UX)
    # L'utilisateur ajoutera les réalisations hiérarchiquement après création
    description_array = [{
        "id": _new_id(),
        "title": "",
        "description": []
    }]

    experience = {
        "company": request.POST.get("company", "").strip(),
        "poste": request.POST.get("poste", "").strip(),
        "date": request.POST.get("date", "").strip(),
        "context": request.POST.get("context", "").strip(),
        "description": description_array,  # Array de réalisations, pas texte
        "env_tech": tech_list,
    }

    if experience["company"] and experience["poste"]:
        if "xp_pro" not in dossier:
            dossier["xp_pro"] = []
        dossier["xp_pro"].append(experience)
        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

    return redirect("formulaire:candidat_edit", pk=pk)


@require_POST
def experience_remove(request, pk, index):
    """Supprime une expérience."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    try:
        index = int(index)
        if "xp_pro" in dossier and 0 <= index < len(dossier["xp_pro"]):
            dossier["xp_pro"].pop(index)
            candidat.dossier = dossier
            candidat.save(update_fields=["dossier"])
    except (ValueError, IndexError):
        pass

    return redirect("formulaire:candidat_edit", pk=pk)


# ---------------------------------------------------------------------------
# Section CRUD (Ancien système - compatibilité)
# ---------------------------------------------------------------------------

@require_POST
def section_add(request, pk):
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()
    new_section = {"id": _new_id(), "titre": "", "postes": []}
    if "sections" not in dossier:
        dossier["sections"] = []
    dossier["sections"].append(new_section)
    candidat.dossier = dossier
    candidat.save(update_fields=["dossier"])
    return render(
        request,
        "formulaire/partials/section_item.html",
        {"section": new_section, "candidat": candidat},
    )


@require_POST
def section_save(request, pk, section_id):
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()
    titre = request.POST.get("titre", "").strip()
    if "sections" not in dossier:
        dossier["sections"] = []
    for section in dossier["sections"]:
        if section["id"] == section_id:
            section["titre"] = titre
            break
    candidat.dossier = dossier
    candidat.save(update_fields=["dossier"])
    return render(
        request,
        "formulaire/partials/section_item.html",
        {"section": next(s for s in dossier["sections"] if s["id"] == section_id), "candidat": candidat},
    )


@require_POST
def section_delete(request, pk, section_id):
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()
    if "sections" not in dossier:
        dossier["sections"] = []
    dossier["sections"] = [s for s in dossier["sections"] if s["id"] != section_id]
    candidat.dossier = dossier
    candidat.save(update_fields=["dossier"])
    return HttpResponse("")


# ---------------------------------------------------------------------------
# Item CRUD (Ancien système - compatibilité)
# ---------------------------------------------------------------------------

@require_POST
def poste_add(request, pk, section_id):
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()
    new_poste = {"id": _new_id(), "texte": "", "sous_postes": []}
    if "sections" not in dossier:
        dossier["sections"] = []
    for section in dossier["sections"]:
        if section["id"] == section_id:
            section["postes"].append(new_poste)
            break
    candidat.dossier = dossier
    candidat.save(update_fields=["dossier"])
    return render(
        request,
        "formulaire/partials/poste_row.html",
        {"poste": new_poste, "section_id": section_id, "candidat": candidat},
    )


@require_POST
def poste_save(request, pk, section_id, poste_id):
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()
    texte = request.POST.get("texte", "").strip()
    if "sections" not in dossier:
        dossier["sections"] = []
    for section in dossier["sections"]:
        if section["id"] == section_id:
            for poste in section["postes"]:
                if poste["id"] == poste_id:
                    poste["texte"] = texte
                    break
            break
    candidat.dossier = dossier
    candidat.save(update_fields=["dossier"])
    for section in dossier["sections"]:
        if section["id"] == section_id:
            for poste in section["postes"]:
                if poste["id"] == poste_id:
                    return render(
                        request,
                        "formulaire/partials/poste_row.html",
                        {"poste": poste, "section_id": section_id, "candidat": candidat},
                    )
    return HttpResponse("")


@require_POST
def poste_delete(request, pk, section_id, poste_id):
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()
    if "sections" not in dossier:
        dossier["sections"] = []
    for section in dossier["sections"]:
        if section["id"] == section_id:
            section["postes"] = [p for p in section["postes"] if p["id"] != poste_id]
            break
    candidat.dossier = dossier
    candidat.save(update_fields=["dossier"])
    return HttpResponse("")


# ---------------------------------------------------------------------------
# Sous-item CRUD (Ancien système - compatibilité)
# ---------------------------------------------------------------------------

@require_POST
def sous_poste_add(request, pk, section_id, poste_id):
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()
    new_sous_poste = {"id": _new_id(), "texte": ""}
    if "sections" not in dossier:
        dossier["sections"] = []
    for section in dossier["sections"]:
        if section["id"] == section_id:
            for poste in section["postes"]:
                if poste["id"] == poste_id:
                    poste["sous_postes"].append(new_sous_poste)
                    break
            break
    candidat.dossier = dossier
    candidat.save(update_fields=["dossier"])
    return render(
        request,
        "formulaire/partials/sous_poste_row.html",
        {
            "sous_poste": new_sous_poste,
            "poste_id": poste_id,
            "section_id": section_id,
            "candidat": candidat,
        },
    )


@require_POST
def sous_poste_save(request, pk, section_id, poste_id, sous_poste_id):
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()
    texte = request.POST.get("texte", "").strip()
    if "sections" not in dossier:
        dossier["sections"] = []
    for section in dossier["sections"]:
        if section["id"] == section_id:
            for poste in section["postes"]:
                if poste["id"] == poste_id:
                    for sous_poste in poste["sous_postes"]:
                        if sous_poste["id"] == sous_poste_id:
                            sous_poste["texte"] = texte
                            break
                    break
            break
    candidat.dossier = dossier
    candidat.save(update_fields=["dossier"])
    for section in dossier["sections"]:
        if section["id"] == section_id:
            for poste in section["postes"]:
                if poste["id"] == poste_id:
                    for sous_poste in poste["sous_postes"]:
                        if sous_poste["id"] == sous_poste_id:
                            return render(
                                request,
                                "formulaire/partials/sous_poste_row.html",
                                {
                                    "sous_poste": sous_poste,
                                    "poste_id": poste_id,
                                    "section_id": section_id,
                                    "candidat": candidat,
                                },
                            )
    return HttpResponse("")


@require_POST
def sous_poste_delete(request, pk, section_id, poste_id, sous_poste_id):
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()
    if "sections" not in dossier:
        dossier["sections"] = []
    for section in dossier["sections"]:
        if section["id"] == section_id:
            for poste in section["postes"]:
                if poste["id"] == poste_id:
                    poste["sous_postes"] = [
                        sp for sp in poste["sous_postes"] if sp["id"] != sous_poste_id
                    ]
                    break
            break
    candidat.dossier = dossier
    candidat.save(update_fields=["dossier"])
    return HttpResponse("")


# ---------------------------------------------------------------------------
# Réalisations (Hiérarchie dans expériences)
# ---------------------------------------------------------------------------

def _calculate_depth(items, item_id, current_depth=0):
    """Calcule la profondeur d'un item dans la hiérarchie (pour validation)."""
    for item in items:
        if item.get("id") == item_id:
            return current_depth
        if "description" in item and isinstance(item["description"], list):
            result = _calculate_depth(item["description"], item_id, current_depth + 1)
            if result is not None:
                return result
    return None


def _find_realization_recursive(items, item_id):
    """Cherche un item par son ID dans la structure récursive (description)."""
    for item in items:
        if item.get("id") == item_id:
            return item
        if "description" in item and isinstance(item["description"], list):
            found = _find_realization_recursive(item["description"], item_id)
            if found:
                return found
    return None


def _find_parent_and_index(items, item_id):
    """Cherche le parent et l'index d'un item dans la structure récursive."""
    for i, item in enumerate(items):
        if item.get("id") == item_id:
            return items, i
        if "description" in item and isinstance(item["description"], list):
            parent, idx = _find_parent_and_index(item["description"], item_id)
            if parent is not None:
                return parent, idx
    return None, None


@require_POST
def realization_add(request, pk, exp_index):
    """Ajoute une réalisation ou un sous-item à une réalisation."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    try:
        exp_index = int(exp_index)
        if "xp_pro" not in dossier or exp_index >= len(dossier["xp_pro"]):
            return HttpResponse("Expérience introuvable", status=404)

        experience = dossier["xp_pro"][exp_index]

        # Initialiser description si nécessaire
        if "description" not in experience:
            experience["description"] = []
        elif not isinstance(experience["description"], list):
            experience["description"] = []

        new_item = {
            "id": _new_id(),
            "title": "",
            "description": []
        }

        # Vérifier si c'est un sous-item (a un parent_id)
        parent_id = request.POST.get("parent_id")
        requested_depth = request.POST.get("depth")

        # Limiter à 3 niveaux de détails (depth max = 3)
        if requested_depth:
            requested_depth = int(requested_depth)
            if requested_depth > 3:
                return HttpResponse("Limite de profondeur atteinte (3 niveaux de détails maximum)", status=400)

        if parent_id:
            logger.info(f"Cherche parent_id={parent_id} dans exp {exp_index}")
            logger.info(f"Items en base avec IDs: {[item.get('id') for item in experience['description']]}")
            parent = _find_realization_recursive(experience["description"], parent_id)
            if parent:
                if "description" not in parent:
                    parent["description"] = []
                parent["description"].append(new_item)
                logger.info(f"Parent trouvé! Nouvel item ajouté sous {parent.get('id')}")
            else:
                logger.error(f"❌ Parent {parent_id} non trouvé!")
                logger.error(f"   Tous les IDs disponibles: {[item.get('id') for item in experience['description']]}")
                logger.error(f"   Cherchait dans: {experience['description']}")
                return HttpResponse(f"Parent introuvable (cherchait {parent_id[:8]}...)", status=404)
        else:
            # C'est un item racine
            experience["description"].append(new_item)

        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

        # Retourner le HTML du nouvel item avec la profondeur correcte
        current_depth = requested_depth if requested_depth else 0
        html = render_to_string(
            "formulaire/partials/realization_item.html",
            {
                "item": new_item,
                "exp_index": exp_index,
                "depth": current_depth,
            }
        )
        return HttpResponse(html)

    except (ValueError, IndexError) as e:
        logger.error(f"Erreur realization_add: {e}")
        return HttpResponse(f"Erreur: {e}", status=400)


@require_POST
def realization_update(request, pk, exp_index, item_id):
    """Met à jour le titre d'une réalisation."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    try:
        exp_index = int(exp_index)
        if "xp_pro" not in dossier or exp_index >= len(dossier["xp_pro"]):
            return HttpResponse("Expérience introuvable", status=404)

        experience = dossier["xp_pro"][exp_index]
        if "description" not in experience or not isinstance(experience["description"], list):
            return HttpResponse("Description introuvable", status=404)

        item = _find_realization_recursive(experience["description"], item_id)
        if not item:
            return HttpResponse("Item introuvable", status=404)

        # Mettre à jour le titre
        item["title"] = request.POST.get("title", "").strip()

        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

        return HttpResponse("OK")

    except (ValueError, IndexError) as e:
        logger.error(f"Erreur realization_update: {e}")
        return HttpResponse(f"Erreur: {e}", status=400)


@require_POST
def realization_delete(request, pk, exp_index, item_id):
    """Supprime une réalisation et ses enfants."""
    candidat = get_object_or_404(Candidat, pk=pk)
    dossier = candidat.dossier or _empty_dossier()

    try:
        exp_index = int(exp_index)
        if "xp_pro" not in dossier or exp_index >= len(dossier["xp_pro"]):
            return HttpResponse("Expérience introuvable", status=404)

        experience = dossier["xp_pro"][exp_index]
        if "description" not in experience or not isinstance(experience["description"], list):
            return HttpResponse("Description introuvable", status=404)

        parent, idx = _find_parent_and_index(experience["description"], item_id)
        if parent is None or idx is None:
            return HttpResponse("Item introuvable", status=404)

        # Supprimer l'item
        parent.pop(idx)

        candidat.dossier = dossier
        candidat.save(update_fields=["dossier"])

        return HttpResponse("OK")

    except (ValueError, IndexError) as e:
        logger.error(f"Erreur realization_delete: {e}")
        return HttpResponse(f"Erreur: {e}", status=400)


# ---------------------------------------------------------------------------
# DOCX export
# ---------------------------------------------------------------------------

def candidat_export_docx(request, pk):
    candidat = get_object_or_404(Candidat, pk=pk)
    template_path = Path(settings.DOCX_TEMPLATE_PATH)

    if not template_path.exists():
        return HttpResponse(
            "Le template DOCX est introuvable. Veuillez le placer dans templates_docx/template_jinja.docx.",
            status=404,
            content_type="text/plain; charset=utf-8",
        )

    try:
        from docxtpl import DocxTemplate

        tpl = DocxTemplate(template_path)
        # Extraire les données du dossier JSON
        dossier_data = candidat.dossier or {}

        # Enrichir le header avec les infos du candidat
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
            "sections": candidat.get_sections(),
            "dossier": candidat.dossier,
            # Passer les clés du dossier directement au contexte
            "header": header_data,
            "main_skills": dossier_data.get("main_skills", {"bullet": []}),
            "xp_pro": dossier_data.get("xp_pro", []),
            "formations": dossier_data.get("formations", []),
            "certifications": dossier_data.get("certifications", []),
        }
        tpl.render(context)

        import io

        buffer = io.BytesIO()
        tpl.save(buffer)
        buffer.seek(0)

        filename = f"DC_{candidat.trigramme}_{candidat.poste}.docx".replace(" ", "_")
        response = HttpResponse(
            buffer.read(),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        logger.exception("Erreur lors de la génération du DOCX pour le candidat %s: %s", pk, str(e))
        return HttpResponse(
            f"Une erreur est survenue lors de la génération du document:\n{str(e)}",
            status=500,
            content_type="text/plain; charset=utf-8",
        )
