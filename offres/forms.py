
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.utils import timezone
from .models import ProfilEtudiant, ProfilEntreprise, Candidature, Offre

User = get_user_model()


class InscriptionEtudiantForm(UserCreationForm):
    # Informations personnelles de l'étudiant.
    nom_complet = forms.CharField(
        max_length=150,
        label="Nom complet"
    )
    email = forms.EmailField(
        label="Adresse e-mail"
    )
    telephone = forms.CharField(
        max_length=20,
        label="Numéro de téléphone"
    )

    # Informations sur la formation suivie.
    niveau_etudes = forms.ChoiceField(
        choices=ProfilEtudiant.NIVEAU_CHOIX,
        initial="licence",
        label="Niveau d'études"
    )
    filiere = forms.CharField(
        max_length=150,
        initial="Informatique de gestion",
        label="Filière"
    )
    annee_etudes = forms.ChoiceField(
        choices=ProfilEtudiant.ANNEE_CHOIX,
        initial="2e",
        label="Année d'études"
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "nom_complet",
            "email",
            "telephone",
            "niveau_etudes",
            "filiere",
            "annee_etudes",
        )

    
    
    # Refuse une adresse e-mail déjà utilisée.
    def clean_email(self):
        # Vérifie uniquement l'adresse e-mail.
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Cette adresse e-mail possède déjà un compte."
            )

        if ProfilEtudiant.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Cette adresse e-mail est déjà enregistrée."
            )

        return email


    def clean_telephone(self):
        # Vérifie uniquement le numéro de téléphone.
        telephone = self.cleaned_data["telephone"].strip()

        if ProfilEtudiant.objects.filter(telephone=telephone).exists():
            raise forms.ValidationError(
                "Ce numéro de téléphone est déjà utilisé."
            )

        return telephone

    # Crée le compte et son profil dans une même transaction.
    @transaction.atomic
    def save(self, commit=True):
        utilisateur = super().save(commit=False)
        utilisateur.email = self.cleaned_data["email"]

        if commit:
            utilisateur.save()

            ProfilEtudiant.objects.create(
                utilisateur=utilisateur,
                nom_complet=self.cleaned_data["nom_complet"],
                email=self.cleaned_data["email"],
                telephone=self.cleaned_data["telephone"],
                niveau_etudes=self.cleaned_data["niveau_etudes"],
                filiere=self.cleaned_data["filiere"],
                annee_etudes=self.cleaned_data["annee_etudes"],
            )

        return utilisateur
    
    
class ProfilEtudiantForm(forms.ModelForm):
    # Formulaire permettant à l'étudiant de modifier son profil.

    class Meta:
        # Modèle associé au formulaire.
        model = ProfilEtudiant

        # Champs modifiables par l'étudiant.
        fields = [
            "nom_complet",
            "email",
            "telephone",
            "niveau_etudes",
            "filiere",
            "annee_etudes",
            "competences",
            "cv",
        ]

        # Étiquettes affichées dans la page HTML.
        labels = {
            "nom_complet": "Nom complet",
            "email": "Adresse e-mail",
            "telephone": "Téléphone",
            "niveau_etudes": "Niveau d'études",
            "filiere": "Filière",
            "annee_etudes": "Année d'études",
            "competences": "Mes compétences",
            "cv": "Mon CV",
        }

        # Personnalisation du champ compétences.
        widgets = {
            "competences": forms.Textarea(attrs={
                "rows": 5,
                "placeholder": "Python, Django, HTML, CSS..."
            }),
        }

    # Vérifie que l'e-mail n'appartient pas à un autre compte.
    def clean_email(self):
        # Récupérer l'adresse e-mail et la normaliser.
        email = self.cleaned_data["email"].strip().lower()

        # Vérifier que l'adresse n'appartient pas à un autre compte utilisateur.
        if User.objects.filter(
            email__iexact=email
        ).exclude(pk=self.instance.utilisateur_id).exists():
            raise forms.ValidationError(
                "Cette adresse e-mail est déjà utilisée par un autre compte."
            )

        # Vérifier que l'adresse n'appartient pas à un autre profil étudiant.
        doublon = ProfilEtudiant.objects.filter(
            email__iexact=email
        ).exclude(pk=self.instance.pk).exists()

        if doublon:
            raise forms.ValidationError(
                "Cette adresse e-mail est déjà utilisée par un autre étudiant."
            )

        # Retourner l'adresse si toutes les vérifications sont correctes.
        return email

    # Vérifie que le téléphone n'appartient pas à un autre étudiant.
    def clean_telephone(self):
        telephone = self.cleaned_data["telephone"].strip()

        doublon = ProfilEtudiant.objects.filter(
            telephone=telephone
        ).exclude(pk=self.instance.pk).exists()

        if doublon:
            raise forms.ValidationError(
                "Ce numéro de téléphone est déjà utilisé."
            )

        return telephone

    # Vérifie le format et la taille du fichier CV.
    def clean_cv(self):
        fichier = self.cleaned_data.get("cv")

        if fichier:
            if not fichier.name.lower().endswith(".pdf"):
                raise forms.ValidationError(
                    "Le CV doit être au format PDF."
                )

            if fichier.size > 5 * 1024 * 1024:
                raise forms.ValidationError(
                    "Le CV ne doit pas dépasser 5 Mo."
                )

        return fichier


class CandidatureForm(forms.ModelForm):
    cv = forms.FileField(
        required=True,
        label="CV (PDF, 5 Mo maximum)",
        help_text="Déposez votre CV au format PDF."
    )

    class Meta:
        model = Candidature
        fields = ['cv', 'lettre_motivation']
        labels = {
            'lettre_motivation': 'Lettre de motivation (facultative)',
        }
        widgets = {
            'lettre_motivation': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': (
                    "Présentez brièvement votre motivation "
                    "pour ce poste..."
                ),
            }),
        }

    def clean_cv(self):
        fichier = self.cleaned_data.get('cv')

        if fichier:
            if not fichier.name.lower().endswith('.pdf'):
                raise forms.ValidationError(
                    "Le CV doit être au format PDF."
                )

            if fichier.size > 5 * 1024 * 1024:
                raise forms.ValidationError(
                    "Le CV ne doit pas dépasser 5 Mo."
                )

        return fichier
    
    
    


class InscriptionEntrepriseForm(UserCreationForm):

    # Informations principales de l'entreprise.
    nom = forms.CharField(
        max_length=150,
        label="Nom de l'entreprise"
    )

    # Liste déroulante contenant les 20 secteurs du modèle.
    secteur = forms.ChoiceField(
        choices=ProfilEntreprise.SECTEURS_ACTIVITE,
        label="Secteur d'activité"
    )

    # Présentation de l'entreprise.
    description = forms.CharField(
        required=False,
        label="Présentation de l'entreprise",
        widget=forms.Textarea(attrs={
            'rows': 4,
            'placeholder': "Présentez les activités de votre entreprise..."
        })
    )

    # Coordonnées professionnelles.
    email = forms.EmailField(
        label="Adresse e-mail professionnelle"
    )

    telephone = forms.CharField(
        max_length=20,
        label="Numéro de téléphone"
    )

    # Configuration du formulaire d'inscription.
    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "nom",
            "secteur",
            "description",
            "email",
            "telephone",
        )

    # Vérifie que l'adresse e-mail n'est pas déjà utilisée.
    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Cette adresse e-mail possède déjà un compte."
            )

        if ProfilEntreprise.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Cette adresse e-mail est déjà enregistrée."
            )

        return email

    # Vérifie que le numéro de téléphone est disponible.
    def clean_telephone(self):
        telephone = self.cleaned_data["telephone"].strip()

        if ProfilEntreprise.objects.filter(
            telephone=telephone
        ).exists():
            raise forms.ValidationError(
                "Ce numéro de téléphone est déjà utilisé."
            )

        return telephone

    # Enregistre le compte utilisateur et le profil entreprise
    # dans une seule transaction pour éviter les enregistrements incomplets.
    @transaction.atomic
    def save(self, commit=True):

        # Prépare le compte utilisateur sans l'enregistrer immédiatement.
        utilisateur = super().save(commit=False)

        # Associe l'adresse e-mail au compte utilisateur.
        utilisateur.email = self.cleaned_data["email"]

        if commit:
            # Enregistre le compte utilisateur.
            utilisateur.save()

            # Crée le profil professionnel associé à ce compte.
            ProfilEntreprise.objects.create(
                utilisateur=utilisateur,
                nom=self.cleaned_data["nom"],
                secteur=self.cleaned_data["secteur"],
                description=self.cleaned_data["description"],
                email=self.cleaned_data["email"],
                telephone=self.cleaned_data["telephone"],
            )

        return utilisateur

class OffreForm(forms.ModelForm):
    # Permet à l'entreprise de choisir une date limite dans un calendrier.
    date_limite = forms.DateField(
        label="Date limite de candidature",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
    )

    class Meta:
        model = Offre
        fields = [
            "titre",
            "description",
            "type_contrat",
            "localisation",
            "date_limite",
        ]
        labels = {
            "titre": "Titre de l'offre",
            "description": "Description de l'offre",
            "type_contrat": "Type de contrat",
            "localisation": "Lieu de travail",
        }
        widgets = {
            "description": forms.Textarea(attrs={
                "rows": 6,
                "placeholder": "Décrivez le poste, les missions et les compétences recherchées..."
            }),
        }

    def clean_date_limite(self):
        date_limite = self.cleaned_data["date_limite"]
        if date_limite < timezone.localdate():
            raise forms.ValidationError(
                "La date limite doit être aujourd'hui ou une date future."
            )
        return date_limite