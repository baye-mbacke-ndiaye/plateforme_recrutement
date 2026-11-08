from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import OffreForm
from .models import Candidature, Offre, ProfilEntreprise, ProfilEtudiant


User = get_user_model()


class OffrePagesTests(TestCase):
    def setUp(self):
        self.entreprise_user = User.objects.create_user(
            username="entreprise",
            password="motdepasse-securise",
        )
        self.entreprise = ProfilEntreprise.objects.create(
            utilisateur=self.entreprise_user,
            nom="Entreprise A",
            secteur="Informatique",
            email="contact@entreprise-a.test",
            telephone="770000001",
        )
        self.etudiant_user = User.objects.create_user(
            username="etudiant",
            password="motdepasse-securise",
        )
        self.etudiant = ProfilEtudiant.objects.create(
            utilisateur=self.etudiant_user,
            nom_complet="Étudiant Test",
            email="etudiant@test.example",
            telephone="770000002",
        )
        self.offre_active = self.creer_offre(
            "Offre active",
            date_limite=timezone.localdate(),
        )
        self.offre_expiree = self.creer_offre(
            "Offre expirée",
            date_limite=timezone.localdate() - timedelta(days=1),
        )
        self.offre_fermee = self.creer_offre(
            "Offre fermée",
            statut="fermee",
        )

    def creer_offre(self, titre, date_limite=None, statut="ouverte"):
        return Offre.objects.create(
            titre=titre,
            entreprise=self.entreprise.nom,
            profil_entreprise=self.entreprise,
            description="Description de test",
            type_contrat="emploi",
            localisation="Dakar",
            date_limite=date_limite or timezone.localdate() + timedelta(days=7),
            statut=statut,
        )

    def test_recherche_ne_montre_que_les_offres_ouvertes_non_expirees(self):
        response = self.client.get(reverse("rechercher_offres"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["offres"]),
            [self.offre_active],
        )

    def test_detail_reste_accessible_pour_une_offre_fermee(self):
        response = self.client.get(
            reverse("detail_offre", args=[self.offre_fermee.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["offre_active"])
        self.assertFalse(response.context["peut_postuler"])

    def test_candidature_impossible_pour_une_offre_expiree(self):
        self.client.force_login(self.etudiant_user)

        response = self.client.get(
            reverse("postuler", args=[self.offre_expiree.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_formulaire_de_candidature_active_saffiche(self):
        self.client.force_login(self.etudiant_user)

        response = self.client.get(
            reverse("postuler", args=[self.offre_active.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Déposer ma candidature")
        self.assertNotContains(response, ">\\")

    def test_formulaire_candidature_permet_d_annuler_le_choix_du_cv(self):
        self.client.force_login(self.etudiant_user)

        response = self.client.get(
            reverse("postuler", args=[self.offre_active.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'type="file"')
        self.assertContains(response, "data-clear-file")

    def test_profil_etudiant_permet_d_annuler_le_choix_du_cv(self):
        self.client.force_login(self.etudiant_user)

        response = self.client.get(reverse("modifier_profil_etudiant"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'type="file"')
        self.assertContains(response, "data-clear-file")

    def test_detail_indique_une_candidature_deja_envoyee(self):
        Candidature.objects.create(
            etudiant=self.etudiant,
            offre=self.offre_active,
        )
        self.client.force_login(self.etudiant_user)

        response = self.client.get(
            reverse("detail_offre", args=[self.offre_active.pk])
        )

        self.assertTrue(response.context["deja_postule"])
        self.assertFalse(response.context["peut_postuler"])

    def test_tableau_entreprise_compte_seulement_ses_candidatures(self):
        Candidature.objects.create(
            etudiant=self.etudiant,
            offre=self.offre_active,
        )
        self.client.force_login(self.entreprise_user)

        response = self.client.get(reverse("tableau_bord_entreprise"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["nombre_candidatures"], 1)
        self.assertEqual(
            response.context["offres"].get(
                pk=self.offre_active.pk
            ).nombre_candidatures,
            1,
        )

    def test_page_entreprise_anonyme_redirige_vers_la_connexion_du_site(self):
        response = self.client.get(reverse("tableau_bord_entreprise"))

        self.assertRedirects(
            response,
            f"{reverse('connexion')}?next={reverse('tableau_bord_entreprise')}",
        )

    def test_date_limite_passee_refusee_a_la_publication(self):
        form = OffreForm(
            data={
                "titre": "Offre passée",
                "description": "Description de test",
                "type_contrat": "emploi",
                "localisation": "Dakar",
                "date_limite": (
                    timezone.localdate() - timedelta(days=1)
                ).isoformat(),
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("date_limite", form.errors)

    def test_page_publication_affiche_la_navigation_entreprise(self):
        self.client.force_login(self.entreprise_user)

        response = self.client.get(reverse("publier_offre"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("tableau_bord_entreprise"))
        self.assertContains(response, reverse("rechercher_offres"))
        self.assertContains(response, reverse("deconnexion"))
        self.assertContains(response, 'aria-current="page"')
        self.assertContains(
            response,
            f'action="{reverse("deconnexion")}"',
        )

    def test_un_etudiant_ne_peut_pas_acceder_a_la_publication(self):
        self.client.force_login(self.etudiant_user)

        response = self.client.get(reverse("publier_offre"))

        self.assertRedirects(response, reverse("rechercher_offres"))


class GestionOffresEntrepriseTests(TestCase):
    """Publication en attente, modification et clôture des offres."""

    def setUp(self):
        def creer_entreprise(nom, suffixe):
            user = User.objects.create_user(
                username=f"ent{suffixe}", password="motdepasse-securise"
            )
            profil = ProfilEntreprise.objects.create(
                utilisateur=user, nom=nom, secteur="IT",
                email=f"c{suffixe}@test.example", telephone=f"77000010{suffixe}",
            )
            return user, profil

        self.user_a, self.profil_a = creer_entreprise("Entreprise A", 1)
        self.user_b, self.profil_b = creer_entreprise("Entreprise B", 2)
        self.offre = Offre.objects.create(
            titre="Offre A", entreprise="Entreprise A",
            profil_entreprise=self.profil_a, description="Desc",
            type_contrat="stage", localisation="Dakar",
            date_limite=timezone.localdate() + timedelta(days=5),
        )

    def donnees_offre(self, titre="Nouvelle offre"):
        return {
            "titre": titre, "description": "Description",
            "type_contrat": "emploi", "localisation": "Dakar",
            "date_limite": (timezone.localdate() + timedelta(days=10)).isoformat(),
        }

    def test_nouvelle_offre_est_en_attente_et_invisible(self):
        self.client.force_login(self.user_a)
        self.client.post(reverse("publier_offre"), self.donnees_offre())

        nouvelle = Offre.objects.get(titre="Nouvelle offre")
        self.assertEqual(nouvelle.statut, "en_attente")

        reponse = self.client.get(reverse("rechercher_offres"))
        self.assertNotIn(nouvelle, list(reponse.context["offres"]))

    def test_modifier_offre(self):
        self.client.force_login(self.user_a)
        reponse = self.client.post(
            reverse("modifier_offre", args=[self.offre.pk]),
            self.donnees_offre("Titre modifié"),
        )
        self.assertRedirects(reponse, reverse("tableau_bord_entreprise"))
        self.offre.refresh_from_db()
        self.assertEqual(self.offre.titre, "Titre modifié")
        self.assertEqual(self.offre.statut, "ouverte")

    def test_cloturer_offre_par_post_uniquement(self):
        self.client.force_login(self.user_a)
        self.client.get(reverse("cloturer_offre", args=[self.offre.pk]))
        self.offre.refresh_from_db()
        self.assertEqual(self.offre.statut, "ouverte")

        self.client.post(reverse("cloturer_offre", args=[self.offre.pk]))
        self.offre.refresh_from_db()
        self.assertEqual(self.offre.statut, "fermee")

    def test_une_autre_entreprise_ne_peut_ni_modifier_ni_cloturer(self):
        self.client.force_login(self.user_b)
        self.assertEqual(
            self.client.get(reverse("modifier_offre", args=[self.offre.pk])).status_code, 404
        )
        self.assertEqual(
            self.client.post(reverse("cloturer_offre", args=[self.offre.pk])).status_code, 404
        )

    def test_tableau_affiche_etat_et_actions(self):
        self.client.force_login(self.user_a)
        reponse = self.client.get(reverse("tableau_bord_entreprise"))
        self.assertContains(reponse, "Publiée")
        self.assertContains(reponse, "Modifier")
        self.assertContains(reponse, "Clôturer")

    def test_filtre_par_type_sur_l_accueil(self):
        reponse = self.client.get(reverse("rechercher_offres"), {"type": "emploi"})
        self.assertEqual(list(reponse.context["offres"]), [])
        reponse = self.client.get(reverse("rechercher_offres"), {"type": "stage"})
        self.assertEqual(list(reponse.context["offres"]), [self.offre])


class AdministrationIntegreeTests(TestCase):
    """Administration du site réservée au personnel."""

    def setUp(self):
        self.admin = User.objects.create_user(
            username="gestionnaire", password="motdepasse-securise", is_staff=True
        )
        self.super = User.objects.create_user(
            username="chef", password="motdepasse-securise",
            is_staff=True, is_superuser=True,
        )
        self.membre = User.objects.create_user(
            username="membre", password="ancien-mot-de-passe"
        )
        self.offre = Offre.objects.create(
            titre="À valider", entreprise="Société", description="Desc",
            type_contrat="emploi", localisation="Dakar", statut="en_attente",
            date_limite=timezone.localdate() + timedelta(days=5),
        )

    def test_visiteur_redirige_vers_la_connexion(self):
        reponse = self.client.get(reverse("gestion_tableau_bord"))
        self.assertRedirects(reponse, reverse("connexion"))

    def test_compte_non_staff_refuse(self):
        self.client.force_login(self.membre)
        for nom in ("gestion_tableau_bord", "gestion_offres",
                    "gestion_utilisateurs", "gestion_candidatures"):
            self.assertEqual(self.client.get(reverse(nom)).status_code, 403)

    def test_pages_accessibles_au_personnel(self):
        self.client.force_login(self.admin)
        for nom in ("gestion_tableau_bord", "gestion_offres",
                    "gestion_utilisateurs", "gestion_candidatures"):
            self.assertEqual(self.client.get(reverse(nom)).status_code, 200)

    def test_valider_une_offre(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("gestion_offre_action", args=[self.offre.pk, "valider"]))
        self.offre.refresh_from_db()
        self.assertEqual(self.offre.statut, "ouverte")

    def test_action_refusee_en_get_et_non_staff(self):
        self.client.force_login(self.admin)
        reponse = self.client.get(reverse("gestion_offre_action", args=[self.offre.pk, "valider"]))
        self.assertEqual(reponse.status_code, 405)

        self.client.force_login(self.membre)
        self.client.post(reverse("gestion_offre_action", args=[self.offre.pk, "supprimer"]))
        self.assertTrue(Offre.objects.filter(pk=self.offre.pk).exists())

    def test_supprimer_une_offre(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("gestion_offre_action", args=[self.offre.pk, "supprimer"]))
        self.assertFalse(Offre.objects.filter(pk=self.offre.pk).exists())

    def test_nouveau_mot_de_passe_temporaire(self):
        self.client.force_login(self.admin)
        reponse = self.client.post(
            reverse("gestion_utilisateur_mot_de_passe", args=[self.membre.pk])
        )
        temporaire = reponse.context["mot_de_passe"]
        self.assertContains(reponse, temporaire)
        self.membre.refresh_from_db()
        self.assertTrue(self.membre.check_password(temporaire))
        self.assertFalse(self.membre.check_password("ancien-mot-de-passe"))

    def test_pas_d_action_sur_soi_ni_sur_le_personnel(self):
        self.client.force_login(self.admin)
        self.assertEqual(
            self.client.post(reverse("gestion_utilisateur_mot_de_passe", args=[self.admin.pk])).status_code, 403
        )
        self.assertEqual(
            self.client.post(reverse("gestion_utilisateur_mot_de_passe", args=[self.super.pk])).status_code, 403
        )
        self.client.force_login(self.super)
        self.assertEqual(
            self.client.post(reverse("gestion_utilisateur_mot_de_passe", args=[self.admin.pk])).status_code, 200
        )

    def test_desactiver_un_compte(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("gestion_utilisateur_activer", args=[self.membre.pk]))
        self.membre.refresh_from_db()
        self.assertFalse(self.membre.is_active)

    def test_connexion_du_personnel_vers_l_administration(self):
        reponse = self.client.post(
            reverse("connexion"),
            {"username": "gestionnaire", "password": "motdepasse-securise"},
        )
        self.assertRedirects(reponse, reverse("gestion_tableau_bord"))
