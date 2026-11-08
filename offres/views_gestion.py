# ============================================================
# ADMINISTRATION INTÉGRÉE AU SITE (réservée au personnel)
# ============================================================

from functools import wraps

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .models import Candidature, Offre, ProfilEntreprise, ProfilEtudiant

User = get_user_model()

# Caractères sans ambiguïté (pas de 0/O ni de 1/l/I) pour les mots de passe temporaires.
CARACTERES_MOT_DE_PASSE = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def staff_requis(vue):
    """Réserve une vue au personnel : connexion d'abord, puis droit d'accès."""
    @wraps(vue)
    def enveloppe(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, "Connectez-vous pour accéder à l'administration.")
            return redirect("connexion")
        if not (request.user.is_active and request.user.is_staff):
            raise PermissionDenied
        return vue(request, *args, **kwargs)
    return enveloppe


def _retour(request, defaut):
    """Retourne à la page d'origine si l'adresse est sûre, sinon à la page par défaut."""
    suivant = request.POST.get("suivant", "")
    if suivant and url_has_allowed_host_and_scheme(suivant, {request.get_host()}):
        return redirect(suivant)
    return redirect(defaut)


def _role(utilisateur, profils_entreprise, profils_etudiant):
    if utilisateur.is_superuser:
        return "Super-administrateur"
    if utilisateur.is_staff:
        return "Administrateur"
    if utilisateur.pk in profils_entreprise:
        return "Entreprise"
    if utilisateur.pk in profils_etudiant:
        return "Candidat"
    return "Sans profil"


# ------------------------------------------------------------
# Tableau de bord
# ------------------------------------------------------------

@staff_requis
def tableau_bord(request):
    en_attente = Offre.objects.filter(statut="en_attente").order_by("date_creation")

    return render(request, "offres/gestion/tableau_bord.html", {
        "section": "tableau_bord",
        "nb_en_attente": en_attente.count(),
        "nb_publiees": Offre.objects.filter(statut="ouverte").count(),
        "nb_entreprises": ProfilEntreprise.objects.count(),
        "nb_candidats": ProfilEtudiant.objects.count(),
        "nb_candidatures": Candidature.objects.count(),
        "nb_comptes": User.objects.count(),
        "offres_a_valider": en_attente[:5],
    })


# ------------------------------------------------------------
# Offres
# ------------------------------------------------------------

@staff_requis
def offres(request):
    statut = request.GET.get("statut", "")
    recherche = request.GET.get("q", "").strip()

    liste = Offre.objects.select_related("profil_entreprise").annotate(
        nb_candidatures=Count("candidatures")
    ).order_by("-date_creation")

    if statut in dict(Offre.STATUT_CHOIX):
        liste = liste.filter(statut=statut)
    else:
        statut = ""

    if recherche:
        liste = liste.filter(Q(titre__icontains=recherche) | Q(entreprise__icontains=recherche))

    return render(request, "offres/gestion/offres.html", {
        "section": "offres",
        "offres": liste,
        "statut": statut,
        "recherche": recherche,
        "statuts": Offre.STATUT_CHOIX,
        "nb_en_attente": Offre.objects.filter(statut="en_attente").count(),
        "aujourdhui": timezone.localdate(),
    })


@staff_requis
@require_POST
def offre_action(request, offre_id, action):
    offre = get_object_or_404(Offre, pk=offre_id)

    if action == "valider":
        if offre.statut == "en_attente":
            offre.statut = "ouverte"
            offre.save(update_fields=["statut"])
            messages.success(request, f"L'offre « {offre.titre} » est publiée.")
        else:
            messages.info(request, "Cette offre n'est pas en attente de validation.")

    elif action == "cloturer":
        if offre.statut != "fermee":
            offre.statut = "fermee"
            offre.save(update_fields=["statut"])
            messages.success(request, f"L'offre « {offre.titre} » est clôturée.")
        else:
            messages.info(request, "Cette offre est déjà clôturée.")

    elif action == "supprimer":
        titre = offre.titre
        offre.delete()
        messages.success(request, f"L'offre « {titre} » a été supprimée.")

    else:
        raise PermissionDenied

    return _retour(request, reverse("gestion_offres"))


# ------------------------------------------------------------
# Utilisateurs
# ------------------------------------------------------------

@staff_requis
def utilisateurs(request):
    recherche = request.GET.get("q", "").strip()

    liste = User.objects.order_by("-date_joined")
    if recherche:
        liste = liste.filter(
            Q(username__icontains=recherche) | Q(email__icontains=recherche)
        )

    entreprises = dict(ProfilEntreprise.objects.values_list("utilisateur_id", "nom"))
    etudiants = dict(ProfilEtudiant.objects.values_list("utilisateur_id", "nom_complet"))

    comptes = []
    for u in liste:
        comptes.append({
            "utilisateur": u,
            "role": _role(u, entreprises, etudiants),
            "nom": entreprises.get(u.pk) or etudiants.get(u.pk) or "",
            "est_moi": u.pk == request.user.pk,
            "modifiable": request.user.is_superuser or not u.is_staff,
        })

    return render(request, "offres/gestion/utilisateurs.html", {
        "section": "utilisateurs",
        "nb_en_attente": Offre.objects.filter(statut="en_attente").count(),
        "comptes": comptes,
        "recherche": recherche,
    })


def _cible_modifiable(request, utilisateur_id):
    """Un administrateur ne peut agir ni sur lui-même, ni sur le personnel (sauf super-administrateur)."""
    cible = get_object_or_404(User, pk=utilisateur_id)
    if cible.pk == request.user.pk:
        raise PermissionDenied
    if cible.is_staff and not request.user.is_superuser:
        raise PermissionDenied
    return cible


@staff_requis
@require_POST
def utilisateur_activer(request, utilisateur_id):
    cible = _cible_modifiable(request, utilisateur_id)
    cible.is_active = not cible.is_active
    cible.save(update_fields=["is_active"])

    messages.success(
        request,
        f"Le compte « {cible.username} » est maintenant "
        f"{'actif' if cible.is_active else 'désactivé'}."
    )
    return _retour(request, reverse("gestion_utilisateurs"))


@staff_requis
@require_POST
@never_cache
def utilisateur_mot_de_passe(request, utilisateur_id):
    """Génère un mot de passe temporaire, affiché une seule fois."""
    cible = _cible_modifiable(request, utilisateur_id)

    mot_de_passe = get_random_string(12, allowed_chars=CARACTERES_MOT_DE_PASSE)
    cible.set_password(mot_de_passe)
    cible.save(update_fields=["password"])

    return render(request, "offres/gestion/mot_de_passe.html", {
        "section": "utilisateurs",
        "nb_en_attente": Offre.objects.filter(statut="en_attente").count(),
        "cible": cible,
        "mot_de_passe": mot_de_passe,
    })


# ------------------------------------------------------------
# Candidatures (consultation)
# ------------------------------------------------------------

@staff_requis
def candidatures(request):
    statut = request.GET.get("statut", "")

    liste = Candidature.objects.select_related("etudiant", "offre")
    if statut in dict(Candidature.STATUT_CHOIX):
        liste = liste.filter(statut=statut)
    else:
        statut = ""

    return render(request, "offres/gestion/candidatures.html", {
        "section": "candidatures",
        "candidatures": liste,
        "statut": statut,
        "statuts": Candidature.STATUT_CHOIX,
        "nb_en_attente": Offre.objects.filter(statut="en_attente").count(),
    })
