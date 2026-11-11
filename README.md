# KayJoop — Plateforme de gestion des stages et des offres d’emploi

KayJoop met en relation les étudiants et les entreprises pour la publication d’offres d’emploi, de stage et d’alternance, le dépôt de candidatures et le suivi de leur traitement.

## 1. Technologies

- Python 3
- Django 5.2
- SQLite en configuration locale
- HTML, CSS, JavaScript et templates Django
- Authentification et permissions Django

## 2. Installation sous Windows (PowerShell)

Ouvrir le terminal dans le dossier qui contient `manage.py` :

```powershell
cd plateforme_recrutement

# Créer l'environnement virtuel une seule fois
python -m venv .venv

# Activer l'environnement virtuel
.venv\Scripts\Activate.ps1

# Installer les dépendances
pip install -r requirements.txt

# Préparer la base de données
python manage.py migrate

# Créer le compte administrateur
python manage.py createsuperuser

# Vérifier le projet et lancer les tests
python manage.py check
python manage.py test offres

# Lancer le serveur local
python manage.py runserver
```

Ouvrir http://127.0.0.1:8000/

## 3. Rôles et fonctionnalités

| Rôle | Fonctionnalités |
|---|---|
| Étudiant | Inscription, connexion, profil, CV, recherche et filtres, candidature, suivi des statuts et notifications |
| Entreprise | Inscription, profil, publication immédiate, modification et clôture de ses offres, consultation des candidatures, changement de statut et notifications |
| Administrateur | Tableau de bord, statistiques, gestion des offres, des comptes et consultation des candidatures |

Les pages et actions privées vérifient le rôle et la propriété des données. Une entreprise ne peut gérer que ses propres offres et candidatures.

## 4. Règles de gestion principales

### Offres

1. Une entreprise connectée publie une offre : son statut devient `ouverte` et elle est immédiatement visible dans la recherche publique.
2. L'offre comporte un titre, une description, un type de contrat, une localisation et une date limite.
3. L'entreprise peut modifier ou clôturer ses propres offres.
4. Une offre clôturée ou dont la date limite est dépassée n'accepte plus de candidatures et n'est plus affichée dans la recherche publique.
5. L'administrateur peut modérer une offre publiée, la clôturer ou la supprimer.
6. Le statut historique `en_attente` est conservé pour compatibilité avec d'anciennes données et une modération exceptionnelle. Il ne fait pas partie du parcours normal de publication.

### Candidatures

1. Seul un étudiant connecté peut déposer une candidature.
2. Une candidature concerne une offre publiée et non expirée.
3. Un étudiant ne peut pas candidater deux fois à la même offre : la règle est aussi protégée au niveau de la base de données.
4. Le CV est obligatoire au dépôt, au format PDF, avec une limite de 5 Mo.
5. L'entreprise concernée reçoit une notification lorsqu'une candidature est déposée.
6. L'entreprise peut faire évoluer le statut : `en_attente` (Soumise), `en_cours` (En cours d'étude), `acceptee` ou `refusee`.
7. Chaque changement réel de statut crée une notification destinée à l'étudiant.

## 5. Administration

- Administration intégrée : `/gestion/`
- Administration Django : `/admin/`
- Création d'un super-administrateur : `python manage.py createsuperuser`
- Changement d'un mot de passe depuis le terminal : `python manage.py changepassword nom_utilisateur`

Les mots de passe ne sont jamais affichés en clair. L'administration intégrée peut générer un mot de passe temporaire pour un compte autorisé ; celui-ci est affiché une seule fois.

## 6. Documentation du projet

Le dossier `docs/` contient :
- `ANALYSE_ET_UML.md` : acteurs, règles de gestion, associations et diagramme UML ;
- `PLAN_DE_TEST.md` : scénarios de vérification avant la démonstration.

Les captures d'écran réelles doivent être ajoutées après exécution et vérification de l'application. Ne pas utiliser de captures fictives.

## 7. Tests

Depuis le dossier contenant `manage.py` :

```powershell
python manage.py check
python manage.py test offres
```

Les tests automatisés couvrent notamment la publication immédiate, les droits d'accès, la clôture, les candidatures, les notifications et l'administration. Le résultat doit être vérifié sur l'environnement local après installation des dépendances.

## 8. Configuration de production

Ne jamais déployer avec `DEBUG=True` ni avec la clé secrète de développement.

Définir les variables d'environnement suivantes sur l'hébergeur :

- `DJANGO_SECRET_KEY` : une clé secrète longue et aléatoire ;
- `DJANGO_DEBUG=False` ;
- `DJANGO_ALLOWED_HOSTS` : les noms de domaine autorisés, séparés par des virgules ;
- `DJANGO_CSRF_TRUSTED_ORIGINS` : les origines HTTPS autorisées, séparées par des virgules, par exemple `https://kayjoop.example.com`.

Avant la mise en ligne :

```powershell
python manage.py check --deploy
python manage.py migrate
python manage.py collectstatic
```

La base SQLite convient au développement et à une démonstration simple. Pour un service en production, privilégier PostgreSQL et un stockage persistant et privé pour les CV. Les fichiers déposés dans `media/` contiennent des documents utilisateurs : ne pas les exposer publiquement sans contrôle d'accès.

## 9. Organisation

```text
config/                         Réglages et URLs Django
offres/
  models.py                     Profils, offres, candidatures et notifications
  forms.py                      Formulaires et validations
  views.py                      Pages publiques, étudiant et entreprise
  views_gestion.py              Administration intégrée
  admin.py                      Administration Django
  tests.py                      Tests automatisés
  templates/offres/             Pages et composants HTML
  static/offres/                CSS et JavaScript
docs/                           Analyse, UML et plan de test
media/                          Fichiers téléversés (CV)
manage.py                       Commande de gestion Django
requirements.txt                Dépendances Python
```

## 10. Conception orientée objet

- **Héritage** : `ProfilEtudiant` et `ProfilEntreprise` héritent de `ProfilBase`.
- **Polymorphisme** : les profils définissent chacun leur méthode `nom_affiche()`.
- **Encapsulation** : les règles métier sont regroupées dans les modèles, par exemple `Offre.est_publique()`, `Offre.publier()`, `Offre.cloturer()`, `ProfilEtudiant.peut_postuler()` et `Candidature.changer_statut()`.
- **Associations** : un compte possède un profil, une entreprise possède plusieurs offres, un étudiant possède plusieurs candidatures et une offre reçoit plusieurs candidatures.
