
# Importe path pour définir les adresses des pages.
from django.urls import path

# Importe les fonctions de l'application.
from . import views


# Déclare les adresses des pages de TalentConnect.
urlpatterns = [
    # Recherche des offres.
    path('', views.rechercher_offres, name='rechercher_offres'),

    # Inscription et connexion des étudiants.
    path('inscription/', views.inscription, name='inscription'),
    path('connexion/', views.connexion, name='connexion'),

    # Déconnexion.
    path('deconnexion/', views.deconnexion, name='deconnexion'),

    # Détails d'une offre.
    path(
        'offre/<int:offre_id>/',
        views.detail_offre,
        name='detail_offre'
    ),

    # Candidature à une offre.
    path(
        'offre/<int:offre_id>/postuler/',
        views.postuler,
        name='postuler'
    ),

    # Liste des candidatures de l'étudiant.
    path(
        'mes-candidatures/',
        views.mes_candidatures,
        name='mes_candidatures'
    ),

    # Inscription des entreprises.
    path(
        'inscription-entreprise/',
        views.inscription_entreprise,
        name='inscription_entreprise'
    ),
    
        # Permet aux entreprises connectées d'accéder à la publication d'une offre.
    path(
        'publier-offre/',
        views.publier_offre,
        name='publier_offre'
    ),
    
    path(
    "tableau-bord-entreprise/",
    views.tableau_bord_entreprise,
    name="tableau_bord_entreprise"
),
    
    
path(
    "entreprise/candidatures/<int:offre_id>/",
    views.candidatures_offre,
    name="candidatures_offre"
),

path(
    "entreprise/candidature/<int:candidature_id>/modifier/",
    views.modifier_statut_candidature,
    name="modifier_statut_candidature"
),


path(
    "notification/<int:notification_id>/lue/",
    views.marquer_notification_lue,
    name="marquer_notification_lue"
),

path(
    "mon-profil/modifier/",
    views.modifier_profil_etudiant,
    name="modifier_profil_etudiant"
),

]
