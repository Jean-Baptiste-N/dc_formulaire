import io
import logging
import uuid
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CandidatInfoForm
from .models import Candidat

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _new_id():
    return str(uuid.uuid4())


def _empty_parcours():
    return {"sections": []}


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
            candidat.parcours = _empty_parcours()
            candidat.save()
            return redirect("formulaire:candidat_edit", pk=candidat.pk)
    else:
        form = CandidatInfoForm()
    return render(request, "formulaire/candidat_create.html", {"form": form})


# ---------------------------------------------------------------------------
# Candidat edit (main form with HTMX)
# ---------------------------------------------------------------------------

def candidat_edit(request, pk):
    candidat = get_object_or_404(Candidat, pk=pk)
    if request.method == "POST":
        form = CandidatInfoForm(request.POST, instance=candidat)
        if form.is_valid():
            form.save()
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
# Section CRUD (HTMX)
# ---------------------------------------------------------------------------

@require_POST
def section_add(request, pk):
    candidat = get_object_or_404(Candidat, pk=pk)
    parcours = candidat.parcours or _empty_parcours()
    new_section = {"id": _new_id(), "titre": "", "postes": []}
    parcours["sections"].append(new_section)
    candidat.parcours = parcours
    candidat.save(update_fields=["parcours"])
    return render(
        request,
        "formulaire/partials/section_item.html",
        {"section": new_section, "candidat": candidat},
    )


@require_POST
def section_save(request, pk, section_id):
    candidat = get_object_or_404(Candidat, pk=pk)
    parcours = candidat.parcours or _empty_parcours()
    titre = request.POST.get("titre", "").strip()
    for section in parcours["sections"]:
        if section["id"] == section_id:
            section["titre"] = titre
            break
    candidat.parcours = parcours
    candidat.save(update_fields=["parcours"])
    return render(
        request,
        "formulaire/partials/section_item.html",
        {"section": next(s for s in parcours["sections"] if s["id"] == section_id), "candidat": candidat},
    )


@require_POST
def section_delete(request, pk, section_id):
    candidat = get_object_or_404(Candidat, pk=pk)
    parcours = candidat.parcours or _empty_parcours()
    parcours["sections"] = [s for s in parcours["sections"] if s["id"] != section_id]
    candidat.parcours = parcours
    candidat.save(update_fields=["parcours"])
    return HttpResponse("")


# ---------------------------------------------------------------------------
# Item CRUD (HTMX)
# ---------------------------------------------------------------------------

@require_POST
def poste_add(request, pk, section_id):
    candidat = get_object_or_404(Candidat, pk=pk)
    parcours = candidat.parcours or _empty_parcours()
    new_poste = {"id": _new_id(), "texte": "", "sous_postes": []}
    for section in parcours["sections"]:
        if section["id"] == section_id:
            section["postes"].append(new_poste)
            break
    candidat.parcours = parcours
    candidat.save(update_fields=["parcours"])
    return render(
        request,
        "formulaire/partials/poste_row.html",
        {"poste": new_poste, "section_id": section_id, "candidat": candidat},
    )


@require_POST
def poste_save(request, pk, section_id, poste_id):
    candidat = get_object_or_404(Candidat, pk=pk)
    parcours = candidat.parcours or _empty_parcours()
    texte = request.POST.get("texte", "").strip()
    for section in parcours["sections"]:
        if section["id"] == section_id:
            for poste in section["postes"]:
                if poste["id"] == poste_id:
                    poste["texte"] = texte
                    break
            break
    candidat.parcours = parcours
    candidat.save(update_fields=["parcours"])
    for section in parcours["sections"]:
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
    parcours = candidat.parcours or _empty_parcours()
    for section in parcours["sections"]:
        if section["id"] == section_id:
            section["postes"] = [p for p in section["postes"] if p["id"] != poste_id]
            break
    candidat.parcours = parcours
    candidat.save(update_fields=["parcours"])
    return HttpResponse("")


# ---------------------------------------------------------------------------
# Sous-item CRUD (HTMX)
# ---------------------------------------------------------------------------

@require_POST
def sous_poste_add(request, pk, section_id, poste_id):
    candidat = get_object_or_404(Candidat, pk=pk)
    parcours = candidat.parcours or _empty_parcours()
    new_sous_poste = {"id": _new_id(), "texte": ""}
    for section in parcours["sections"]:
        if section["id"] == section_id:
            for poste in section["postes"]:
                if poste["id"] == poste_id:
                    poste["sous_postes"].append(new_sous_poste)
                    break
            break
    candidat.parcours = parcours
    candidat.save(update_fields=["parcours"])
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
    parcours = candidat.parcours or _empty_parcours()
    texte = request.POST.get("texte", "").strip()
    for section in parcours["sections"]:
        if section["id"] == section_id:
            for poste in section["postes"]:
                if poste["id"] == poste_id:
                    for sous_poste in poste["sous_postes"]:
                        if sous_poste["id"] == sous_poste_id:
                            sous_poste["texte"] = texte
                            break
                    break
            break
    candidat.parcours = parcours
    candidat.save(update_fields=["parcours"])
    for section in parcours["sections"]:
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
    parcours = candidat.parcours or _empty_parcours()
    for section in parcours["sections"]:
        if section["id"] == section_id:
            for poste in section["postes"]:
                if poste["id"] == poste_id:
                    poste["sous_postes"] = [
                        sp for sp in poste["sous_postes"] if sp["id"] != sous_poste_id
                    ]
                    break
            break
    candidat.parcours = parcours
    candidat.save(update_fields=["parcours"])
    return HttpResponse("")


# ---------------------------------------------------------------------------
# DOCX export
# ---------------------------------------------------------------------------

def candidat_export_docx(request, pk):
    candidat = get_object_or_404(Candidat, pk=pk)
    template_path = Path(settings.DOCX_TEMPLATE_PATH)

    if not template_path.exists():
        return HttpResponse(
            "Le template DOCX est introuvable. Veuillez le placer dans templates_docx/dc_template.docx.",
            status=404,
            content_type="text/plain",
        )

    try:
        from docxtpl import DocxTemplate

        tpl = DocxTemplate(template_path)
        context = {
            "candidat": candidat,
            "nom": candidat.nom,
            "prenom": candidat.prenom,
            "email": candidat.email,
            "sections": candidat.get_sections(),
        }
        tpl.render(context)

        import io

        buffer = io.BytesIO()
        tpl.save(buffer)
        buffer.seek(0)

        filename = f"dc_{candidat.nom}_{candidat.prenom}.docx".replace(" ", "_")
        response = HttpResponse(
            buffer.read(),
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    except Exception:
        logger.exception("Erreur lors de la génération du DOCX pour le candidat %s", pk)
        return HttpResponse(
            "Une erreur est survenue lors de la génération du document. "
            "Vérifiez que votre template DOCX est valide.",
            status=500,
            content_type="text/plain",
        )
