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

    # Langues
    path("candidat/<uuid:pk>/langue/ajouter/", views.langue_add, name="langue_add"),
    path("candidat/<uuid:pk>/langue/<int:index>/supprimer/", views.langue_remove, name="langue_remove"),

    # Postes cibles (variantes)
    path("candidat/<uuid:pk>/poste-cible/ajouter/", views.poste_cible_add, name="poste_cible_add"),
    path("candidat/<uuid:pk>/poste-cible/<str:poste_cible_id>/supprimer/", views.poste_cible_delete, name="poste_cible_delete"),
    path("candidat/<uuid:pk>/poste-cible/<str:poste_cible_id>/activer/", views.poste_cible_activate, name="poste_cible_activate"),
    path("candidat/<uuid:pk>/poste-cible/<str:poste_cible_id>/mettre-a-jour/", views.poste_cible_update, name="poste_cible_update"),

    # Expériences professionnelles
    path("candidat/<uuid:pk>/experience/ajouter/", views.experience_add, name="experience_add"),
    path("candidat/<uuid:pk>/experience/<int:index>/supprimer/", views.experience_remove, name="experience_remove"),

    # Réalisations XP_PRO (HTMX)
    path(
        "candidat/<uuid:pk>/experience/<int:exp_index>/realization/ajouter/",
        views.xp_pro_realization_add,
        name="xp_pro_realization_add",
    ),
    path(
        "candidat/<uuid:pk>/experience/<int:exp_index>/realization/<str:item_id>/mettre-a-jour/",
        views.xp_pro_realization_update,
        name="xp_pro_realization_update",
    ),
    path(
        "candidat/<uuid:pk>/experience/<int:exp_index>/realization/<str:item_id>/supprimer/",
        views.xp_pro_realization_delete,
        name="xp_pro_realization_delete",
    ),

    # Main Skills - Hierarchy Items (HTMX)
    path(
        "candidat/<uuid:pk>/main_skills/<str:section>/item/ajouter/",
        views.main_skills_hierarchy_add,
        name="main_skills_hierarchy_add",
    ),
    path(
        "candidat/<uuid:pk>/main_skills/<str:section>/item/ajouter_enfant/",
        views.main_skills_hierarchy_add_child,
        name="main_skills_hierarchy_add_child",
    ),
    path(
        "candidat/<uuid:pk>/main_skills/<str:section>/item/<str:item_id>/mettre-a-jour/",
        views.main_skills_hierarchy_update,
        name="main_skills_hierarchy_update",
    ),
    path(
        "candidat/<uuid:pk>/main_skills/<str:section>/item/<str:item_id>/supprimer/",
        views.main_skills_hierarchy_delete,
        name="main_skills_hierarchy_delete",
    ),

]

