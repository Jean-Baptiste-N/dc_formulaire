from django import forms
from django.forms import ModelForm
import json

from .models import Candidat


class CandidatInfoForm(ModelForm):
    """Formulaire pour les informations de base du candidat."""

    class Meta:
        model = Candidat
        fields = ["nom", "prenom", "email", "trigramme", "poste", "xp_duration"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control", "placeholder": "Dupont"}),
            "prenom": forms.TextInput(attrs={"class": "form-control", "placeholder": "Jean"}),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "jean.dupont@example.com"}
            ),
            "trigramme": forms.TextInput(attrs={"class": "form-control", "placeholder": "JDU", "maxlength": "3"}),
            "poste": forms.TextInput(attrs={"class": "form-control", "placeholder": "ex: Développeur Python"}),
            "xp_duration": forms.NumberInput(attrs={"class": "form-control", "placeholder": "3", "min": "0"}),
        }
        labels = {
            "nom": "Nom",
            "prenom": "Prénom",
            "email": "Email",
            "trigramme": "Trigramme",
            "poste": "Poste",
            "xp_duration": "Années d'expérience",
        }


class SkillsForm(forms.Form):
    """Formulaire pour ajouter les compétences clés."""

    skills = forms.CharField(
        label="Compétences principales",
        help_text="Entrez les compétences séparées par des virgules (ex: Python, SQL, Git)",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": "Python, SQL, Git"
        })
    )


class FormationForm(forms.Form):
    """Formulaire pour ajouter une formation."""

    title = forms.CharField(
        label="Titre",
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Master en Informatique"})
    )
    school = forms.CharField(
        label="École/Université",
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Université de Technologie"})
    )
    description = forms.CharField(
        label="Description",
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 2,
            "placeholder": "Spécialisation, détails..."
        })
    )
    date = forms.CharField(
        label="Période",
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "2018-2020"})
    )


class CertificationForm(forms.Form):
    """Formulaire pour ajouter une certification."""

    title = forms.CharField(
        label="Titre",
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Certification Python"})
    )
    description = forms.CharField(
        label="Description",
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 2,
            "placeholder": "Détails de la certification..."
        })
    )
    date = forms.CharField(
        label="Date",
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "2021"})
    )


class ExperienceForm(forms.Form):
    """Formulaire pour ajouter une expérience professionnelle."""

    company = forms.CharField(
        label="Entreprise",
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Tech Solutions"})
    )
    poste = forms.CharField(
        label="Poste",
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Développeur Python"})
    )
    date = forms.CharField(
        label="Période",
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "2020-2023"})
    )
    context = forms.CharField(
        label="Contexte",
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 2,
            "placeholder": "Contexte du rôle..."
        })
    )
    description = forms.CharField(
        label="Responsabilités/Réalisations",
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": "Décrivez vos responsabilités et réalisations principales"
        })
    )
    technologies = forms.CharField(
        label="Technologies utilisées",
        required=False,
        help_text="Séparées par des virgules",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Django, Flask, FastAPI, PostgreSQL"
        })
    )

