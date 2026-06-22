from django.contrib import admin

from .models import Candidat


@admin.register(Candidat)
class CandidatAdmin(admin.ModelAdmin):
    list_display = ["nom", "prenom", "email", "created_at", "updated_at"]
    list_filter = ["created_at"]
    search_fields = ["nom", "prenom", "email"]
    readonly_fields = ["id", "created_at", "updated_at"]
