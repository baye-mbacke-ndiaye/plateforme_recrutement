# ============================================================
# IMPORTATION DES OUTILS
# ============================================================

from pathlib import Path

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, FileResponse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

# Importer les formulaires utilisés dans les vues.
from .forms import (
    InscriptionEtudiantForm,
    InscriptionEntrepriseForm,
    CandidatureForm,
    OffreForm,
    ProfilEtudiantForm,
)

# Importer les modèles utilisés dans les vues.
from .models import (
    Offre,
    Candidature,
    ProfilEtudiant,
    ProfilEntreprise,
    NotificationCandidature,
    NotificationEntreprise,
)


# ============================================================
# PARTIE 1 : RECHERCHE D'EMPLOI ET DE STAGE
# ============================================================

def rechercher_offres(request):

    mot_cle = request.GET.get('q', '').strip()
    type_contrat = request.GET.get('type', '').strip()
    localisation = request.GET.get('lieu', '').strip()
    secteur = request.GET.get('secteur', '').strip()
    avant = request.GET.get('avant', '').strip()
    voir_tout = request.GET.get('tous') == '1'

    # Offres publiées (ouvertes) et non expirées : ce sont les seules visibles.
    offres_publiques = Offre.objects.filter(
        statut='ouverte',
        date_limite__gte=timezone.localdate(),
    )

    offres = offres_publiques

    # Rechercher dans le titre, l'entreprise, la description et le lieu.
    if mot_cle:
     offres = offres.filter(
        Q(titre__icontains=mot_cle)
        | Q(entreprise__icontains=mot_cle)
        | Q(description__icontains=mot_cle)
        | Q(localisation__icontains=mot_cle)
    )

    # Filtrer par type de contrat (emploi, stage, alternance).
    types_valides = dict(Offre.TYPE_CHOIX)
    if type_contrat not in types_valides:
        type_contrat = ''
    if type_contrat:
        offres = offres.filter(type_contrat=type_contrat)

    # Filtrer par localisation.
    if localisation:
        offres = offres.filter(localisation__iexact=localisation)

    # Filtrer par secteur d'activité de l'entreprise.
    secteurs_valides = dict(ProfilEntreprise.SECTEURS_ACTIVITE)
    if secteur not in secteurs_valides:
        secteur = ''
    if secteur:
        offres = offres.filter(profil_entreprise__secteur=secteur)

    # Filtrer par date limite : offres qui se terminent au plus tard à cette date.
    date_avant = parse_date(avant) if avant else None
    if date_avant:
        offres = offres.filter(date_limite__lte=date_avant)
    else:
        avant = ''

    filtre_actif = bool(mot_cle or type_contrat or localisation or secteur or avant)

    offres = offres.order_by('-date_creation')
    total_offres = offres.count()

    # Sans filtre, on montre les offres les plus récentes (liste complète sur demande).
    limite = 8
    liste_reduite = not filtre_actif and not voir_tout and total_offres > limite
    if liste_reduite:
        offres = offres[:limite]

    localisations = (
        offres_publiques
        .exclude(localisation='')
        .order_by('localisation')
        .values_list('localisation', flat=True)
        .distinct()
    )

    return render(
        request,
        'offres/recherche.html',
        {
            'offres': offres,
            'mot_cle': mot_cle,
            'type_contrat': type_contrat,
            'localisation': localisation,
            'secteur': secteur,
            'secteurs': ProfilEntreprise.SECTEURS_ACTIVITE,
            'avant': avant,
            'types_contrat': Offre.TYPE_CHOIX,
            'localisations': localisations,
            'filtre_actif': filtre_actif,
            'liste_reduite': liste_reduite,
            'total_offres': total_offres,
            # Chiffres réels de la plateforme affichés dans l'accueil.
            'stat_offres': offres_publiques.count(),
            'stat_entreprises': ProfilEntreprise.objects.count(),
            'stat_candidats': ProfilEtudiant.objects.count(),
        }
    )


# ============================================================
# PARTIE 2 : DÉTAILS D'UNE OFFRE
# ============================================================

def detail_offre(request, offre_id):

    # Une offre non publiée ne doit pas être accessible par son URL publique.
    # Son entreprise propriétaire et le personnel peuvent toutefois la consulter.
    offre = get_object_or_404(Offre, id=offre_id)
    est_proprietaire = (
        request.user.is_authenticated
        and offre.profil_entreprise_id is not None
        and hasattr(request.user, "profil_entreprise")
        and request.user.profil_entreprise.pk == offre.profil_entreprise_id
    )
    if not offre.est_publique() and not (request.user.is_staff or est_proprietaire):
        raise Http404("Cette offre n'est pas disponible.")

    # Vérifier si l'offre est encore disponible.
    offre_active = (
        offre.statut == 'ouverte'
        and offre.date_limite >= timezone.localdate()
    )

    profil_etudiant = None
    deja_postule = False

    # Vérifier si l'utilisateur est connecté.
    if request.user.is_authenticated:

        try:
            profil_etudiant = request.user.profil_etudiant

        except ProfilEtudiant.DoesNotExist:
            pass

        # Vérifier si l'étudiant a déjà postulé.
        if profil_etudiant:
            deja_postule = Candidature.objects.filter(
                etudiant=profil_etudiant,
                offre=offre,
            ).exists()

    return render(
        request,
        'offres/detail_offre.html',
        {
            'offre': offre,
            'offre_active': offre_active,
            'deja_postule': deja_postule,
            'peut_postuler': (
                offre_active
                and profil_etudiant is not None
                and not deja_postule
            ),
        }
    )


# ============================================================
# PARTIE 3 : INSCRIPTION DES ÉTUDIANTS
# ============================================================

def inscription(request):

    # Traiter les informations lorsque le formulaire est envoyé.
    if request.method == 'POST':

        form = InscriptionEtudiantForm(request.POST)

        if form.is_valid():

            # Créer le compte étudiant.
            utilisateur = form.save()

            messages.success(
                request,
                "Votre compte étudiant a été créé avec succès."
            )

            # Connecter automatiquement l'étudiant.
            login(request, utilisateur)

            return redirect('rechercher_offres')

    else:
        # Afficher un formulaire vide.
        form = InscriptionEtudiantForm()

    return render(
        request,
        'offres/inscription.html',
        {'form': form}
    )


# ============================================================
# PARTIE 4 : MODIFICATION DU PROFIL ÉTUDIANT
# ============================================================

@login_required
def modifier_profil_etudiant(request):

    # Récupérer le profil de l'étudiant connecté.
    try:
        profil = request.user.profil_etudiant

    except ProfilEtudiant.DoesNotExist:

        messages.error(
            request,
            "Cette page est réservée aux étudiants."
        )

        return redirect("rechercher_offres")

    # Traiter les informations envoyées par le formulaire.
    if request.method == "POST":

        form = ProfilEtudiantForm(
            request.POST,
            request.FILES,
            instance=profil
        )

        # Vérifier les données avant l'enregistrement.
        if form.is_valid():

            # Enregistrer les modifications du profil.
            profil = form.save()

            # Synchroniser l'adresse e-mail du compte utilisateur.
            utilisateur = request.user
            utilisateur.email = profil.email
            utilisateur.save(update_fields=["email"])

            messages.success(
                request,
                "Votre profil a été modifié avec succès."
            )

            return redirect("modifier_profil_etudiant")

    else:
        # Afficher le formulaire avec les informations actuelles.
        form = ProfilEtudiantForm(instance=profil)

    # Afficher la page de modification du profil.
    return render(
        request,
        "offres/profil_etudiant.html",
        {
            "form": form,
            "profil": profil,
        }
    )


# ============================================================
# PARTIE 5 : INSCRIPTION DES ENTREPRISES
# ============================================================

def inscription_entreprise(request):

    # Traiter les données lorsque le formulaire est envoyé.
    if request.method == 'POST':

        form = InscriptionEntrepriseForm(request.POST)

        if form.is_valid():

            # Créer le compte utilisateur et le profil entreprise.
            utilisateur = form.save()

            # Connecter automatiquement l'entreprise.
            login(request, utilisateur)

            messages.success(
                request,
                "Votre compte entreprise a été créé avec succès."
            )

            return redirect('tableau_bord_entreprise')

    else:
        # Afficher un formulaire vide.
        form = InscriptionEntrepriseForm()

    return render(
        request,
        'offres/inscription_entreprise.html',
        {'form': form}
    )


# ============================================================
# PARTIE 6 : CONNEXION DES UTILISATEURS
# ============================================================

def connexion(request):

    # Traiter les informations lorsque le formulaire est envoyé.
    if request.method == 'POST':

        form = AuthenticationForm(
            request,
            data=request.POST
        )

        if form.is_valid():

            # Récupérer et connecter l'utilisateur.
            utilisateur = form.get_user()
            login(request, utilisateur)

            # Rediriger les entreprises vers leur tableau de bord.
            if hasattr(utilisateur, 'profil_entreprise'):

                messages.success(
                    request,
                    "Connexion réussie. Bienvenue dans votre espace entreprise."
                )

                return redirect('tableau_bord_entreprise')

            # Rediriger les étudiants vers la recherche des offres.
            if hasattr(utilisateur, 'profil_etudiant'):

                messages.success(
                    request,
                    "Connexion réussie. Bienvenue sur votre espace candidat."
                )

                return redirect('rechercher_offres')

            # Rediriger le personnel vers l'administration du site.
            if utilisateur.is_staff:

                messages.success(
                    request,
                    "Connexion réussie. Bienvenue dans l'administration."
                )

                return redirect('gestion_tableau_bord')

            messages.warning(
                request,
                "Aucun profil KayJoop n'est associé à ce compte."
            )

            return redirect('rechercher_offres')

    else:
        form = AuthenticationForm(request)

    return render(
        request,
        'offres/connexion.html',
        {'form': form}
    )


# ============================================================
# PARTIE 7 : DÉCONNEXION
# ============================================================

@require_POST
def deconnexion(request):

    # Autoriser la déconnexion uniquement par une requête POST.
    if request.method == 'POST':

        logout(request)

        messages.success(
            request,
            "Vous avez été déconnecté de votre compte en toute sécurité."
        )

        return redirect('connexion')

    return redirect('rechercher_offres')


# ============================================================
# PARTIE 8 : CANDIDATURE DES ÉTUDIANTS
# ============================================================

@login_required
def postuler(request, offre_id):

    # Récupérer une offre ouverte et non expirée.
    offre = get_object_or_404(
        Offre,
        id=offre_id,
        statut='ouverte',
        date_limite__gte=timezone.localdate(),
    )

    # Récupérer le profil étudiant.
    try:
        profil = request.user.profil_etudiant

    except ProfilEtudiant.DoesNotExist:

        messages.error(
            request,
            "Aucun profil étudiant n'est associé à ce compte."
        )

        return redirect('detail_offre', offre_id=offre.id)

    # Empêcher les candidatures en double.
    deja_postule = profil.a_postule(offre)

    if deja_postule:

        messages.warning(
            request,
            "Vous avez déjà postulé à cette offre. Une seule candidature est autorisée par offre."
        )

        return redirect('detail_offre', offre_id=offre.id)

    # Traiter le formulaire et le fichier CV.
    if request.method == 'POST':

        form = CandidatureForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            # Préparer la candidature avant son enregistrement.
            candidature = form.save(commit=False)

            # Associer la candidature à l'étudiant et à l'offre.
            candidature.etudiant = profil
            candidature.offre = offre

            # Enregistrer la candidature.
            candidature.save()

            if offre.profil_entreprise_id:
                NotificationEntreprise.objects.create(
                    entreprise=offre.profil_entreprise,
                    candidature=candidature,
                    message=(
                        f"{profil.nom_complet} a postulé à l'offre "
                        f"« {offre.titre} »."
                    ),
                )

            messages.success(
                request,
                "Votre candidature a été envoyée avec succès !"
            )

            return redirect('detail_offre', offre_id=offre.id)

    else:
        form = CandidatureForm()

    return render(
        request,
        'offres/postuler.html',
        {
            'form': form,
            'offre': offre,
        }
    )


# ============================================================
# PARTIE 9 : MES CANDIDATURES
# ============================================================

@login_required
def mes_candidatures(request):

    # Récupérer le profil de l'étudiant connecté.
    try:
        profil = request.user.profil_etudiant

    except ProfilEtudiant.DoesNotExist:

        messages.error(
            request,
            "Aucun profil étudiant n'est associé à ce compte."
        )

        return redirect('rechercher_offres')

    # Récupérer toutes les candidatures de l'étudiant.
    candidatures = Candidature.objects.filter(
        etudiant=profil
    ).select_related('offre').order_by('-date_candidature')

    # Récupérer les notifications de l'étudiant.
    notifications = NotificationCandidature.objects.filter(
        etudiant=profil
    ).select_related('candidature', 'candidature__offre')

    # Compter les notifications non lues.
    notifications_non_lues = notifications.filter(lu=False).count()

    # Calculer les statistiques des candidatures.
    total_candidatures = candidatures.count()

    # Candidatures encore sans décision : soumises ou en cours d'étude.
    candidatures_attente = candidatures.filter(
        statut__in=['en_attente', 'en_cours']
    ).count()

    candidatures_acceptees = candidatures.filter(
        statut='acceptee'
    ).count()

    candidatures_refusees = candidatures.filter(
        statut='refusee'
    ).count()

    return render(
        request,
        'offres/mes_candidatures.html',
        {
            'candidatures': candidatures,
            'notifications': notifications,
            'notifications_non_lues': notifications_non_lues,
            'total_candidatures': total_candidatures,
            'candidatures_attente': candidatures_attente,
            'candidatures_acceptees': candidatures_acceptees,
            'candidatures_refusees': candidatures_refusees,
        }
    )


# ============================================================
# PARTIE 10 : PUBLICATION D'UNE OFFRE
# ============================================================

@login_required
def publier_offre(request):

    # Vérifier que l'utilisateur connecté possède un profil entreprise.
    try:
        profil = request.user.profil_entreprise

    except ProfilEntreprise.DoesNotExist:

        messages.error(
            request,
            "Cette fonctionnalité est réservée aux comptes entreprise."
        )

        return redirect("rechercher_offres")

    # Traiter le formulaire lorsque l'entreprise l'envoie.
    if request.method == "POST":

        form = OffreForm(request.POST)

        if form.is_valid():

            # Préparer l'offre sans l'enregistrer immédiatement.
            offre = form.save(commit=False)

            # Enregistrer le nom de l'entreprise.
            offre.entreprise = profil.nom

            # Relier l'offre au profil de l'entreprise connectée.
            offre.profil_entreprise = profil

            # Publier immédiatement l'offre sur la plateforme.
            offre.statut = "ouverte"

            # Enregistrer l'offre dans la base de données.
            offre.save()

            messages.success(
                request,
                "Votre offre a été publiée avec succès."
            )

            return redirect("tableau_bord_entreprise")

    else:
        form = OffreForm()

    return render(
        request,
        "offres/publier_offre.html",
        {"form": form}
    )


# ============================================================
# PARTIE 11 : TABLEAU DE BORD ENTREPRISE
# ============================================================

@login_required
def tableau_bord_entreprise(request):

    # Récupérer le profil de l'entreprise connectée.
    try:
        profil = request.user.profil_entreprise

    except ProfilEntreprise.DoesNotExist:

        messages.error(
            request,
            "Cet espace est réservé aux comptes entreprise."
        )

        return redirect("rechercher_offres")

    # Récupérer uniquement les offres liées à cette entreprise.
    offres = Offre.objects.filter(
        profil_entreprise=profil
    ).annotate(
        nombre_candidatures=Count("candidatures")
    ).order_by("-date_creation")

    # Compter toutes les candidatures reçues par cette entreprise.
    nombre_candidatures = Candidature.objects.filter(
        offre__profil_entreprise=profil
    ).count()
    notifications = NotificationEntreprise.objects.filter(
        entreprise=profil
    ).select_related(
        "candidature",
        "candidature__offre",
        "candidature__etudiant",
    )

    # Afficher le tableau de bord.
    return render(
        request,
        "offres/tableau_bord_entreprise.html",
        {
            "profil": profil,
            "offres": offres,
            "nombre_candidatures": nombre_candidatures,
            "notifications": notifications,
            "notifications_non_lues": notifications.filter(lu=False).count(),
            "date_aujourdhui": timezone.localdate(),
        }
    )


# ============================================================
# PARTIE 11 BIS : MODIFIER OU CLÔTURER UNE OFFRE
# ============================================================

def _profil_entreprise_ou_redirection(request):
    """Retourne le profil entreprise de l'utilisateur, ou None s'il n'en a pas."""
    try:
        return request.user.profil_entreprise
    except ProfilEntreprise.DoesNotExist:
        messages.error(
            request,
            "Cet espace est réservé aux comptes entreprise."
        )
        return None


@login_required
def modifier_offre(request, offre_id):

    profil = _profil_entreprise_ou_redirection(request)
    if profil is None:
        return redirect("rechercher_offres")

    # Une entreprise ne peut modifier que ses propres offres.
    offre = get_object_or_404(
        Offre,
        id=offre_id,
        profil_entreprise=profil
    )

    if request.method == "POST":

        form = OffreForm(request.POST, instance=offre)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "L'offre a été modifiée avec succès."
            )

            return redirect("tableau_bord_entreprise")

    else:
        form = OffreForm(instance=offre)

    return render(
        request,
        "offres/publier_offre.html",
        {
            "form": form,
            "offre": offre,
            "mode_edition": True,
        }
    )


@login_required
def cloturer_offre(request, offre_id):

    profil = _profil_entreprise_ou_redirection(request)
    if profil is None:
        return redirect("rechercher_offres")

    offre = get_object_or_404(
        Offre,
        id=offre_id,
        profil_entreprise=profil
    )

    # La clôture se fait uniquement par un formulaire POST.
    if request.method == "POST":

        if not offre.cloturer():
            messages.info(request, "Cette offre est déjà clôturée.")
        else:
            messages.success(
                request,
                f"L'offre « {offre.titre} » a été clôturée."
            )

    return redirect("tableau_bord_entreprise")


# ============================================================
# PARTIE 12 : CANDIDATURES REÇUES PAR UNE ENTREPRISE
# ============================================================

@login_required
def candidatures_offre(request, offre_id):

    # Vérifier que l'utilisateur possède un profil entreprise.
    try:
        profil = request.user.profil_entreprise

    except ProfilEntreprise.DoesNotExist:

        messages.error(
            request,
            "Accès réservé aux entreprises."
        )

        return redirect("rechercher_offres")

    # Récupérer uniquement une offre appartenant à cette entreprise.
    offre = get_object_or_404(
        Offre,
        id=offre_id,
        profil_entreprise=profil
    )

    # Récupérer les candidatures reçues pour cette offre.
    candidatures = Candidature.objects.filter(
        offre=offre
    ).select_related("etudiant")

    return render(
        request,
        "offres/candidatures_offre.html",
        {
            "profil": profil,
            "offre": offre,
            "candidatures": candidatures,
            "statuts": Candidature.STATUT_CHOIX,
        }
    )


# ============================================================
# PARTIE 13 : MODIFICATION DU STATUT D'UNE CANDIDATURE
# ============================================================

@login_required
@require_POST
def modifier_statut_candidature(request, candidature_id):

    # Vérifier que l'utilisateur possède un profil entreprise.
    try:
        profil = request.user.profil_entreprise

    except ProfilEntreprise.DoesNotExist:

        messages.error(
            request,
            "Accès réservé aux entreprises."
        )

        return redirect("rechercher_offres")

    # Vérifier que la candidature concerne une offre de cette entreprise.
    candidature = get_object_or_404(
        Candidature,
        id=candidature_id,
        offre__profil_entreprise=profil
    )

    # Autoriser uniquement les modifications envoyées par formulaire POST.
    if request.method == "POST":

        nouveau_statut = request.POST.get("statut")
        statuts_valides = dict(Candidature.STATUT_CHOIX)

        if nouveau_statut not in statuts_valides:

            messages.error(
                request,
                "Statut invalide."
            )

            return redirect(
                "candidatures_offre",
                offre_id=candidature.offre.id
            )

        # La méthode du modèle change le statut et notifie l'étudiant.
        if candidature.changer_statut(nouveau_statut):

            messages.success(
                request,
                "Le statut a été modifié et l'étudiant a été notifié."
            )

        else:

            messages.info(
                request,
                "Le statut n'a pas changé."
            )

    return redirect(
        "candidatures_offre",
        offre_id=candidature.offre.id
    )


# ============================================================
# PARTIE 14 : MARQUER UNE NOTIFICATION COMME LUE
# ============================================================

@login_required
@require_POST
def marquer_notification_lue(request, notification_id):

    # Vérifier que l'utilisateur possède un profil étudiant.
    try:
        profil = request.user.profil_etudiant

    except ProfilEtudiant.DoesNotExist:

        messages.error(
            request,
            "Accès réservé aux étudiants."
        )

        return redirect("rechercher_offres")

    # Récupérer uniquement une notification appartenant à cet étudiant.
    notification = get_object_or_404(
        NotificationCandidature,
        id=notification_id,
        etudiant=profil
    )

    # Marquer la notification comme lue.
    notification.lu = True
    notification.save(update_fields=["lu"])

    messages.success(
        request,
        "Notification marquée comme lue."
    )

    return redirect("mes_candidatures")


@login_required
@require_POST
def marquer_notification_entreprise_lue(request, notification_id):
    try:
        profil = request.user.profil_entreprise
    except ProfilEntreprise.DoesNotExist:
        messages.error(request, "Accès réservé aux entreprises.")
        return redirect("rechercher_offres")

    notification = get_object_or_404(
        NotificationEntreprise,
        id=notification_id,
        entreprise=profil,
    )
    notification.lu = True
    notification.save(update_fields=["lu"])

    return redirect("tableau_bord_entreprise")

# ============================================================
# TÉLÉCHARGEMENT SÉCURISÉ DES CV
# ============================================================

@login_required
def telecharger_cv_candidature(request, candidature_id):
    # Le CV est réservé au candidat concerné, à son entreprise et au personnel.
    candidature = get_object_or_404(
        Candidature.objects.select_related(
            "etudiant", "offre", "offre__profil_entreprise"
        ),
        pk=candidature_id,
    )

    autorise = request.user.is_staff

    try:
        profil_etudiant = request.user.profil_etudiant
    except ProfilEtudiant.DoesNotExist:
        profil_etudiant = None

    try:
        profil_entreprise = request.user.profil_entreprise
    except ProfilEntreprise.DoesNotExist:
        profil_entreprise = None

    if profil_etudiant and candidature.etudiant_id == profil_etudiant.pk:
        autorise = True

    if profil_entreprise and candidature.offre.profil_entreprise_id == profil_entreprise.pk:
        autorise = True

    if not autorise:
        raise Http404("Ce document n'est pas accessible avec ce compte.")

    if not candidature.cv:
        raise Http404("Aucun CV n'est associé à cette candidature.")

    nom_fichier = Path(candidature.cv.name).name
    return FileResponse(
        candidature.cv.open("rb"),
        as_attachment=True,
        filename=nom_fichier,
        content_type="application/pdf",
    )

