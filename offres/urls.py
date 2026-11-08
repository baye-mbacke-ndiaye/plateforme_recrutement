
# Importe path pour définir les adresses des pages.
from django.urls import path

# Importe les fonctions de l'application.
from . import views, views_gestion


# Déclare les adresses des pages de KayJoop.
urlpatterns = [
    # Administration intégrée au site (réservée au personnel).
    path('gestion/', views_gestion.tableau_bord, name='gestion_tableau_bord'),
    path('gestion/offres/', views_gestion.offres, name='gestion_offres'),
    path('gestion/offres/<int:offre_id>/<str:action>/', views_gestion.offre_action, name='gestion_offre_action'),
    path('gestion/utilisateurs/', views_gestion.utilisateurs, name='gestion_utilisateurs'),
    path('gestion/utilisateurs/<int:utilisateur_id>/activer/', views_gestion.utilisateur_activer, name='gestion_utilisateur_activer'),
    path('gestion/utilisateurs/<int:utilisateur_id>/mot-de-passe/', views_gestion.utilisateur_mot_de_passe, name='gestion_utilisateur_mot_de_passe'),
    path('gestion/candidatures/', views_gestion.candidatures, name='gestion_candidatures'),

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
    "entreprise/offre/<int:offre_id>/modifier/",
    views.modifier_offre,
    name="modifier_offre"
),

path(
    "entreprise/offre/<int:offre_id>/cloturer/",
    views.cloturer_offre,
    name="cloturer_offre"
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
