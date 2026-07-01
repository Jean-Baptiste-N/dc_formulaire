from django.urls import path

from . import views

app_name = "formulaire"

urlpatterns = [
    # ========================================================================
    # 1. HEADERS & INFOS DU CANDIDAT - List, Create, Edit, Detail
    # ========================================================================
    path("", views.candidat_list, name="candidat_list"),
    path("candidat/nouveau/", views.candidat_create, name="candidat_create"),
    path("candidat/<uuid:pk>/", views.candidat_detail, name="candidat_detail"),
    path("candidat/<uuid:pk>/modifier/", views.candidat_edit, name="candidat_edit"),
    path("candidat/<uuid:pk>/export/", views.candidat_export_docx, name="candidat_export"),

    # ========================================================================
    # 2. POSTES CIBLES - Add, Delete, Activate, Update
    # ========================================================================
    path("candidat/<uuid:pk>/poste-cible/ajouter/", views.poste_cible_add, name="poste_cible_add"),
    path("candidat/<uuid:pk>/poste-cible/<str:poste_cible_id>/supprimer/", views.poste_cible_delete, name="poste_cible_delete"),
    path("candidat/<uuid:pk>/poste-cible/<str:poste_cible_id>/activer/", views.poste_cible_activate, name="poste_cible_activate"),
    path("candidat/<uuid:pk>/poste-cible/<str:poste_cible_id>/mettre-a-jour/", views.poste_cible_update, name="poste_cible_update"),
    path("candidat/<uuid:pk>/poste-cible/bulk-update/", views.poste_cible_bulk_update, name="poste_cible_bulk_update"),

    # ========================================================================
    # 3. MAIN-SKILLS DOMAINES DE COMPÉTENCES - Bullet Section
    # 4. MAIN-SKILLS OUTILS & LANGAGES - Table Section
    # ========================================================================
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
    path(
        "candidat/<uuid:pk>/main_skills/<str:section>/bulk-update/",
        views.main_skills_hierarchy_bulk_update,
        name="main_skills_hierarchy_bulk_update",
    ),

    # ========================================================================
    # 5. FORMATIONS - Add, Remove
    # ========================================================================
    path("candidat/<uuid:pk>/formation/ajouter/", views.formation_add, name="formation_add"),
    path("candidat/<uuid:pk>/formation/<int:index>/supprimer/", views.formation_remove, name="formation_remove"),

    # ========================================================================
    # 6. CERTIFICATIONS - Add, Remove
    # ========================================================================
    path("candidat/<uuid:pk>/certification/ajouter/", views.certification_add, name="certification_add"),
    path("candidat/<uuid:pk>/certification/<int:index>/supprimer/", views.certification_remove, name="certification_remove"),

    # ========================================================================
    # 7. LANGUES - Add, Remove
    # ========================================================================
    path("candidat/<uuid:pk>/langue/ajouter/", views.langue_add, name="langue_add"),
    path("candidat/<uuid:pk>/langue/<int:index>/supprimer/", views.langue_remove, name="langue_remove"),

    # ========================================================================
    # 8. XP_PRO BLOCS - 1ère étape du workflow (Add, Remove)
    # ========================================================================
    path("candidat/<uuid:pk>/experience/ajouter/", views.experience_add, name="experience_add"),
    path("candidat/<uuid:pk>/experience/<int:index>/supprimer/", views.experience_remove, name="experience_remove"),

    # ========================================================================
    # 9. XP_PRO BULLETS - 2e étape du workflow (Add, Update, Delete)
    # ========================================================================
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
    path(
        "candidat/<uuid:pk>/experience/<int:exp_index>/realization/bulk-update/",
        views.xp_pro_realization_bulk_update,
        name="xp_pro_realization_bulk_update",
    ),
    path(
        "candidat/<uuid:pk>/experience/<int:exp_index>/contexte/mettre-a-jour/",
        views.xp_pro_context_update,
        name="xp_pro_context_update",
    ),
]

