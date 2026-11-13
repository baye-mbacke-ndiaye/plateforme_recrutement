# Plan de soutenance — Kaay Job (10 à 15 minutes)

## 1. Introduction et contexte — 1 minute
Présenter le problème : les étudiants ont besoin de trouver des stages et des emplois, tandis que les entreprises ont besoin de diffuser leurs offres et de suivre les candidatures.

## 2. Objectifs et acteurs — 1 minute
Présenter les trois rôles principaux : étudiant, entreprise et administrateur. Expliquer l'objectif de mise en relation.

## 3. Analyse et conception UML — 2 minutes
Présenter les entités `User`, `ProfilBase`, `ProfilEtudiant`, `ProfilEntreprise`, `Offre`, `Candidature` et les notifications. Justifier l'héritage, les relations et la règle empêchant les candidatures multiples.

## 4. Technologies et architecture — 1 minute
Présenter Python, Django, l'ORM, SQLite, les templates HTML, CSS et JavaScript. Expliquer brièvement la séparation modèles, formulaires, vues et templates.

## 5. Démonstration fonctionnelle — 4 à 6 minutes
1. Afficher la recherche publique et les filtres.
2. Se connecter en tant qu'entreprise.
3. Publier une offre et montrer qu'elle apparaît immédiatement côté public.
4. Se connecter en tant qu'étudiant.
5. Déposer une candidature.
6. Revenir dans l'espace entreprise pour consulter la candidature et télécharger le CV.
7. Modifier le statut et montrer la notification côté étudiant.
8. Montrer brièvement le tableau de bord administrateur et la modération.

## 6. Tests, sécurité et limites — 1 à 2 minutes
Indiquer les tests automatisés exécutés, les permissions par rôle, la protection des CV et les contrôles de candidature. Préciser que le déploiement nécessite les variables d'environnement et un hébergement configuré.

## 7. Conclusion — 1 minute
Résumer la valeur de Kaay Job et les évolutions possibles : PostgreSQL, hébergement, notifications par e-mail, export PDF et filtres avancés.

## Conseils
- Utiliser des comptes et des données de démonstration.
- Préparer les comptes avant la soutenance pour éviter les temps d'attente.
- Ne pas montrer de vrais CV ou des informations personnelles.
- Faire une démonstration courte et expliquer les règles métier importantes.
