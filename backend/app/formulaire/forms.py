from django import forms
from django.forms import ModelForm

from .models import Candidat


class CandidatInfoForm(ModelForm):
    """Formulaire pour les informations de base du candidat."""

    class Meta:
        model = Candidat
        fields = ["nom", "prenom", "email", "trigramme", "poste", "xp_duration"]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-control", "placeholder": "DUPONT"}),
            "prenom": forms.TextInput(attrs={"class": "form-control", "placeholder": "Jean"}),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "jean.dupont@example.com"}
            ),
            "trigramme": forms.TextInput(attrs={"class": "form-control", "placeholder": "ex: JDT", "maxlength": "3"}),
            "poste": forms.TextInput(attrs={"class": "form-control", "placeholder": "ex: Développeur Python"}),
            "xp_duration": forms.NumberInput(attrs={"class": "form-control", "placeholder": "ex: 3", "min": "0"}),
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
        help_text="Nom du diplôme ou de la formation",
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "ex: Master en Informatique"})
    )
    school = forms.CharField(
        label="École/Université",
        help_text="Nom de l'établissement",
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "ex: Université de Technologie"})
    )
    description = forms.CharField(
        label="Description",
        help_text="Détails sur les contenus de la formation",
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 2,
            "placeholder": "Spécialisation, détails..."
        })
    )
    date = forms.CharField(
        label="Période",
        help_text="Format: YYYY-YYYY ou YYYY, MM/YYYY-MM/YYYY ou MM/YYYY",
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "ex: 2015-2020"})
    )


class CertificationForm(forms.Form):
    """Formulaire pour ajouter une certification."""

    title = forms.CharField(
        label="Titre",
        help_text="Titre de la certification",
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "ex: Certification Python"})
    )
    description = forms.CharField(
        label="Description",
        help_text="Détails sur les contenus de la certification",
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 2,
            "placeholder": "Détails de la certification..."
        })
    )
    date = forms.CharField(
        label="Date",
        help_text="Format: YYYY ou YYYY-MM",
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "ex: 2021"})
    )


class ExperienceForm(forms.Form):
    """Formulaire pour ajouter une expérience professionnelle."""

    company = forms.CharField(
        label="Entreprise",
        help_text="Nom de l'entreprise ou de l'organisation",
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "ex: Tech Solutions"})
    )
    poste = forms.CharField(
        label="Poste",
        help_text="Titre du poste occupé",
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "ex: Développeur Junior"})
    )
    date = forms.CharField(
        label="Période",
        help_text="Format: YYYY-YYYY ou YYYY, MM/YYYY-MM/YYYY ou MM/YYYY",
        max_length=50,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "ex: 2020-2023"})
    )
    context = forms.CharField(
        label="Contexte",
        required=False,
        help_text="Décrivez le contexte de votre rôle dans cette expérience",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 2,
            "placeholder": "Contexte du rôle..."
        })
    )
    technologies = forms.CharField(
        label="Technologies utilisées",
        required=False,
        help_text="Séparées par des virgules",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "ex: Python, Django, PostgreSQL..."
        })
    )

