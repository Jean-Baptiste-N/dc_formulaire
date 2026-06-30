from django.urls import path

from . import views

app_name = "formulaire"

urlpatterns = [
    # Candidat list & create
    path("", views.candidat_list, name="candidat_list"),
    path("candidat/nouveau/", views.candidat_create, name="candidat_create"),
    path("candidat/<uuid:pk>/", views.candidat_detail, name="candidat_detail"),
    path("candidat/<uuid:pk>/modifier/", views.candidat_edit, name="candidat_edit"),
    path("candidat/<uuid:pk>/export/", views.candidat_export_docx, name="candidat_export"),

    # Compétences
    path("candidat/<uuid:pk>/competences/ajouter/", views.skills_add, name="skills_add"),
    path("candidat/<uuid:pk>/competence/<str:skill>/supprimer/", views.skill_remove, name="skill_remove"),

    # Formations
    path("candidat/<uuid:pk>/formation/ajouter/", views.formation_add, name="formation_add"),
    path("candidat/<uuid:pk>/formation/<int:index>/supprimer/", views.formation_remove, name="formation_remove"),

    # Certifications
    path("candidat/<uuid:pk>/certification/ajouter/", views.certification_add, name="certification_add"),
    path("candidat/<uuid:pk>/certification/<int:index>/supprimer/", views.certification_remove, name="certification_remove"),

    # Expériences professionnelles
    path("candidat/<uuid:pk>/experience/ajouter/", views.experience_add, name="experience_add"),
    path("candidat/<uuid:pk>/experience/<int:index>/supprimer/", views.experience_remove, name="experience_remove"),

    # Sections (HTMX)
    path("candidat/<uuid:pk>/section/ajouter/", views.section_add, name="section_add"),
    path(
        "candidat/<uuid:pk>/section/<str:section_id>/sauvegarder/",
        views.section_save,
        name="section_save",
    ),
    path(
        "candidat/<uuid:pk>/section/<str:section_id>/supprimer/",
        views.section_delete,
        name="section_delete",
    ),

    # Postes (HTMX)
    path(
        "candidat/<uuid:pk>/section/<str:section_id>/poste/ajouter/",
        views.poste_add,
        name="poste_add",
    ),
    path(
        "candidat/<uuid:pk>/section/<str:section_id>/poste/<str:poste_id>/sauvegarder/",
        views.poste_save,
        name="poste_save",
    ),
    path(
        "candidat/<uuid:pk>/section/<str:section_id>/poste/<str:poste_id>/supprimer/",
        views.poste_delete,
        name="poste_delete",
    ),

    # Sous-postes (HTMX)
    path(
        "candidat/<uuid:pk>/section/<str:section_id>/poste/<str:poste_id>/sous-poste/ajouter/",
        views.sous_poste_add,
        name="sous_poste_add",
    ),
    path(
        "candidat/<uuid:pk>/section/<str:section_id>/poste/<str:poste_id>/sous-poste/<str:sous_poste_id>/sauvegarder/",
        views.sous_poste_save,
        name="sous_poste_save",
    ),
    path(
        "candidat/<uuid:pk>/section/<str:section_id>/poste/<str:poste_id>/sous-poste/<str:sous_poste_id>/supprimer/",
        views.sous_poste_delete,
        name="sous_poste_delete",
    ),

    # Réalisations (HTMX)
    path(
        "candidat/<uuid:pk>/experience/<int:exp_index>/realization/ajouter/",
        views.realization_add,
        name="realization_add",
    ),
    path(
        "candidat/<uuid:pk>/experience/<int:exp_index>/realization/<str:item_id>/mettre-a-jour/",
        views.realization_update,
        name="realization_update",
    ),
    path(
        "candidat/<uuid:pk>/experience/<int:exp_index>/realization/<str:item_id>/supprimer/",
        views.realization_delete,
        name="realization_delete",
    ),

    # Main Skills - Hierarchy Items (HTMX)
    path(
        "candidat/<uuid:pk>/main_skills/<str:section>/item/ajouter/",
        views.main_skills_item_add,
        name="main_skills_item_add",
    ),
    path(
        "candidat/<uuid:pk>/main_skills/<str:section>/item/ajouter_enfant/",
        views.main_skills_item_add_child,
        name="main_skills_item_add_child",
    ),
    path(
        "candidat/<uuid:pk>/main_skills/<str:section>/item/<str:item_id>/mettre-a-jour/",
        views.main_skills_item_update,
        name="main_skills_item_update",
    ),
    path(
        "candidat/<uuid:pk>/main_skills/<str:section>/item/<str:item_id>/supprimer/",
        views.main_skills_item_delete,
        name="main_skills_item_delete",
    ),

]

