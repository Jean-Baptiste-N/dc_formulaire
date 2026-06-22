from django import forms

from .models import Candidat


class CandidatInfoForm(forms.ModelForm):
    """Formulaire pour les informations de base du candidat."""

    class Meta:
        model = Candidat
        fields = ["nom", "prenom", "email"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control", "placeholder": "Dupont"}),
            "prenom": forms.TextInput(attrs={"class": "form-control", "placeholder": "Jean"}),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "jean.dupont@example.com"}
            ),
        }
