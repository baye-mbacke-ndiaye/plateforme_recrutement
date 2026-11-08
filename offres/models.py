
from django.db import models
from django.conf import settings


class Offre(models.Model):

    TYPE_CHOIX = [
        ('emploi', 'Emploi'),
        ('stage', 'Stage'),
        ('alternance', 'Alternance'),
    ]

    # en_attente : envoyée par l'entreprise, à valider par l'administrateur.
    # ouverte    : publiée et visible par les candidats.
    # fermee     : clôturée par l'entreprise.
    STATUT_CHOIX = [
        ('en_attente', 'En attente de validation'),
        ('ouverte', 'Publiée'),
        ('fermee', 'Clôturée'),
    ]

    titre = models.CharField(max_length=200)
    entreprise = models.CharField(max_length=150)
        # Relie chaque offre au compte de l'entreprise qui l'a publiée.
    # null=True permet de conserver les anciennes offres pendant la migration.
    profil_entreprise = models.ForeignKey(
        'ProfilEntreprise',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='offres'
    )
    description = models.TextField()

    type_contrat = models.CharField(
        max_length=20,
        choices=TYPE_CHOIX,
        default='emploi'
    )

    localisation = models.CharField(max_length=150)
    date_limite = models.DateField()

    statut = models.CharField(
        max_length=10,
        choices=STATUT_CHOIX,
        default='ouverte'
    )

    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titre


class ProfilEtudiant(models.Model):
    utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profil_etudiant'
    )
    nom_complet = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20, unique=True)

    NIVEAU_CHOIX = [
        ('bac', 'Baccalauréat'),
        ('bts', 'BTS / DUT'),
        ('licence', 'Licence'),
        ('master', 'Master'),
        ('doctorat', 'Doctorat'),
        ('autre', 'Autre'),
    ]

    ANNEE_CHOIX = [
        ('1re', '1re année'),
        ('2e', '2e année'),
        ('3e', '3e année'),
        ('4e_plus', '4e année ou plus'),
        ('diplome', 'Déjà diplômé'),
    ]

    niveau_etudes = models.CharField(
        max_length=20,
        choices=NIVEAU_CHOIX,
        default='licence'
    )
    filiere = models.CharField(
        max_length=150,
        default='Informatique de gestion'
    )
    annee_etudes = models.CharField(
        max_length=20,
        choices=ANNEE_CHOIX,
        default='2e'
    )
    competences = models.TextField(
        blank=True,
        verbose_name="Compétences"
    )   

    cv = models.FileField(
        upload_to='cv_etudiants/',
        blank=True,
        null=True,
        verbose_name="CV"
    )

    def __str__(self):
        return f"Profil de {self.nom_complet}"



class ProfilEntreprise(models.Model):
    # Liste des 20 secteurs d'activité proposés aux entreprises
    SECTEURS_ACTIVITE = [
        ('informatique', 'Informatique et nouvelles technologies'),
        ('banque', 'Banque et finance'),
        ('assurance', 'Assurance'),
        ('communication', 'Communication et marketing'),
        ('audiovisuel', 'Graphisme et audiovisuel'),
        ('btp', 'Bâtiment et travaux publics'),
        ('logistique', 'Transport et logistique'),
        ('sante', 'Santé et secteur médical'),
        ('agriculture', 'Agriculture et agroalimentaire'),
        ('education', 'Éducation et formation'),
        ('commerce', 'Commerce et distribution'),
        ('telecommunications', 'Télécommunications'),
        ('tourisme', 'Tourisme et hôtellerie'),
        ('industrie', 'Industrie et production'),
        ('energie', 'Énergie et environnement'),
        ('immobilier', 'Immobilier'),
        ('administration', 'Administration et services publics'),
        ('rh', 'Ressources humaines et recrutement'),
        ('juridique', 'Droit et juridique'),
        ('ong', 'ONG et développement'),
    ]

    # Relie chaque profil entreprise à un seul compte utilisateur Django
    utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profil_entreprise'
    )

    # Nom officiel de l'entreprise
    nom = models.CharField(max_length=150)

    # Secteur d'activité choisi dans la liste ci-dessus
    secteur = models.CharField(
        max_length=150,
        choices=SECTEURS_ACTIVITE
    )

    # Présentation et description des activités de l'entreprise
    description = models.TextField(blank=True)

    # Adresse e-mail professionnelle, obligatoirement unique
    email = models.EmailField(unique=True)

    # Numéro de téléphone de l'entreprise
    telephone = models.CharField(max_length=20, unique=True)

    # Affiche le nom de l'entreprise dans l'administration Django
    def __str__(self):
        return self.nom

    
     

class Candidature(models.Model):

    STATUT_CHOIX = [
        ('en_attente', 'En attente'),
        ('acceptee', 'Acceptée'),
        ('refusee', 'Refusée'),
    ]

    etudiant = models.ForeignKey(
        ProfilEtudiant,
        on_delete=models.CASCADE,
        related_name='candidatures'
    )

    offre = models.ForeignKey(
        Offre,
        on_delete=models.CASCADE,
        related_name='candidatures'
    )
    
    cv = models.FileField(
        upload_to='cv/',
        blank=True,
        verbose_name="CV du candidat"
    )


    lettre_motivation = models.TextField(
        blank=True,
        verbose_name="Lettre de motivation"
    )

    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOIX,
        default='en_attente'
    )

    date_candidature = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ('etudiant', 'offre')
        ordering = ['-date_candidature']

    def __str__(self):
        return f"{self.etudiant.nom_complet} - {self.offre.titre}"


class NotificationCandidature(models.Model):

    etudiant = models.ForeignKey(
        ProfilEtudiant,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    candidature = models.ForeignKey(
        Candidature,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    message = models.CharField(max_length=255)

    date_creation = models.DateTimeField(auto_now_add=True)

    lu = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"{self.etudiant.nom_complet} - {self.message}"