# Corrections apportées à Kaay Job

## Fonctionnement et sécurité

- Maintien de la publication immédiate des offres créées par une entreprise.
- Clarification du statut historique `en_attente` : il n'est plus présenté comme une étape normale.
- Blocage de l'accès public direct aux offres non publiées, clôturées ou expirées ; l'entreprise propriétaire et le personnel conservent l'accès.
- Ajout d'un téléchargement contrôlé des CV de candidature : candidat concerné, entreprise propriétaire ou personnel uniquement.
- Suppression de la mise à disposition publique directe du dossier `media/`.
- Vérification de la signature `%PDF-` en plus de l'extension et de la limite de 5 Mo.
- Protection par POST des actions de déconnexion, de changement de statut et de lecture des notifications.
- Paramètres de sécurité et de déploiement configurables par variables d'environnement.
- Enregistrement des profils entreprise et des notifications dans l'administration Django.

## Documentation et livrables

- README réécrit avec installation, rôles, règles métier, tests et préparation de la production.
- Ajout de l'analyse des besoins et du diagramme UML.
- Ajout d'un plan de tests fonctionnels et d'une liste des captures d'écran à produire.

## Vérifications réalisées

- `python manage.py check` : réussi.
- `python manage.py test offres` : 49 tests réussis.
- `python manage.py migrate` : migration `0012_statut_en_cours_d_etude` appliquée à la copie de la base incluse dans l'archive.
- `python manage.py check --deploy` reste à effectuer avec les variables d'environnement et le domaine de l'hébergeur.
