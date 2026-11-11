# Plan de test et vérification — KayJoop

À exécuter sur une base de test avec des comptes fictifs. Ne pas utiliser de vrais CV dans les captures de démonstration.

| N° | Acteur | Scénario | Résultat attendu |
|---|---|---|---|
| 1 | Visiteur | Consulter la page des offres | Seules les offres ouvertes et non expirées sont visibles |
| 2 | Visiteur | Ouvrir directement une offre clôturée ou en attente | Page non accessible publiquement |
| 3 | Étudiant | Créer un compte avec un e-mail déjà utilisé | Inscription refusée avec un message explicite |
| 4 | Étudiant | Se connecter | Redirection vers l'espace de recherche |
| 5 | Étudiant | Consulter le formulaire de candidature | Le CV PDF est obligatoire |
| 6 | Étudiant | Envoyer un fichier non PDF renommé en `.pdf` | Fichier refusé |
| 7 | Étudiant | Déposer deux fois une candidature à la même offre | Deuxième candidature refusée |
| 8 | Étudiant | Consulter ses candidatures | Statuts et notifications visibles |
| 9 | Entreprise | Publier une offre | Offre immédiatement visible dans la recherche publique |
| 10 | Entreprise A | Modifier ou clôturer une offre de l'entreprise B | Accès refusé |
| 11 | Entreprise | Consulter les candidatures de son offre | Seulement ses candidatures sont visibles |
| 12 | Entreprise | Modifier le statut d'une candidature | Le statut est enregistré et l'étudiant reçoit une notification |
| 13 | Entreprise | Consulter les notifications | Nouvelle candidature signalée |
| 14 | Administrateur | Accéder à `/gestion/` | Tableau de bord et statistiques accessibles |
| 15 | Visiteur/étudiant | Accéder à `/gestion/` | Accès refusé ou redirection vers la connexion |
| 16 | Administrateur | Clôturer ou supprimer une offre | Action enregistrée et offre non publique |
| 17 | Tous | Envoyer une requête GET à une action réservée au POST | Action non exécutée |
| 18 | Administrateur | Consulter comptes, offres et candidatures | Listes filtrables et actions réservées au personnel |

## Commandes de vérification

```powershell
python manage.py check
python manage.py test offres
python manage.py check --deploy
```

`check --deploy` signale les réglages à compléter pour l'hébergement. Les variables de production doivent être définies avant ce contrôle.

## Captures d'écran à préparer pour le rapport

1. Page d'accueil et recherche des offres.
2. Formulaire d'inscription étudiant.
3. Profil étudiant.
4. Détail d'une offre et formulaire de candidature.
5. Suivi des candidatures et notifications.
6. Inscription entreprise et tableau de bord.
7. Publication immédiate d'une offre.
8. Consultation des candidatures par l'entreprise.
9. Tableau de bord d'administration.
10. Gestion des offres et des comptes.

Les captures doivent être prises sur la version réellement exécutée et testée.
