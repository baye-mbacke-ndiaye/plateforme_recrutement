
from django.db import models
from django.conf import settings
from django.utils import timezone


class Offre(models.Model):

    TYPE_CHOIX = [
        ('emploi', 'Emploi'),
        ('stage', 'Stage'),
        ('alternance', 'Alternance'),
    ]

    # ouverte    : publiée immédiatement et visible par les candidats.
    # fermee     : clôturée par l'entreprise ou par l'administration.
    # en_attente : ancien statut conservé pour les données historiques et
    #              une éventuelle modération exceptionnelle uniquement.
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

    # ---- Méthodes métier (règles de gestion d'une offre) ----

    def est_publique(self):
        """Vrai si l'offre est publiée et si sa date limite n'est pas dépassée."""
        return self.statut == 'ouverte' and self.date_limite >= timezone.localdate()

    def publier(self):
        """Publie l'offre. Retourne False si elle l'était déjà."""
        if self.statut == 'ouverte':
            return False
        self.statut = 'ouverte'
        self.save(update_fields=['statut'])
        return True

    def cloturer(self):
        """Clôture l'offre. Retourne False si elle l'était déjà."""
        if self.statut == 'fermee':
            return False
        self.statut = 'fermee'
        self.save(update_fields=['statut'])
        return True


class ProfilBase(models.Model):
    """Classe abstraite : informations communes aux profils étudiant et entreprise.

    Elle n'a pas de table propre. Chaque classe fille (ProfilEtudiant,
    ProfilEntreprise) hérite des champs et redéfinit nom_affiche() :
    c'est le polymorphisme.
    """

    ROLE = ''

    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20, unique=True)

    class Meta:
        abstract = True

    @property
    def role(self):
        return self.ROLE

    def nom_affiche(self):
        raise NotImplementedError("Chaque profil doit définir nom_affiche().")

    def __str__(self):
        return self.nom_affiche()


class ProfilEtudiant(ProfilBase):
    ROLE = 'etudiant'

    utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profil_etudiant'
    )
    nom_complet = models.CharField(max_length=150)

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

    def nom_affiche(self):
        return self.nom_complet

    def a_postule(self, offre):
        """Vrai si l'étudiant a déjà une candidature pour cette offre."""
        return self.candidatures.filter(offre=offre).exists()

    def peut_postuler(self, offre):
        """Une candidature est possible si l'offre est publique et sans doublon."""
        return offre.est_publique() and not self.a_postule(offre)



class ProfilEntreprise(ProfilBase):
    ROLE = 'entreprise'

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


    # Affiche le nom de l'entreprise dans l'administration Django
    def nom_affiche(self):
        return self.nom

    
     

class Candidature(models.Model):

    STATUT_CHOIX = [
        ('en_attente', 'Soumise'),
        ('en_cours', "En cours d'étude"),
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

    def changer_statut(self, nouveau_statut):
        """Change le statut et notifie l'étudiant.

        Retourne True si le statut a changé, False s'il était déjà le même.
        Lève ValueError si le statut n'existe pas.
        """
        libelles = dict(self.STATUT_CHOIX)
        if nouveau_statut not in libelles:
            raise ValueError(f"Statut invalide : {nouveau_statut}")
        if self.statut == nouveau_statut:
            return False
        self.statut = nouveau_statut
        self.save(update_fields=['statut'])
        NotificationCandidature.objects.create(
            etudiant=self.etudiant,
            candidature=self,
            message=(
                f"Votre candidature pour l'offre « {self.offre.titre} » "
                f"est maintenant : {libelles[nouveau_statut]}."
            ),
        )
        return True


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


class NotificationEntreprise(models.Model):
    entreprise = models.ForeignKey(
        ProfilEntreprise,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    candidature = models.ForeignKey(
        Candidature,
        on_delete=models.CASCADE,
        related_name="notifications_entreprise",
    )
    message = models.CharField(max_length=255)
    date_creation = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date_creation"]
        verbose_name = "Notification entreprise"
        verbose_name_plural = "Notifications entreprise"

    def __str__(self):
        return f"{self.entreprise.nom} - {self.message}"