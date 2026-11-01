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
            (
                f'<form method="post" action="{reverse("deconnexion")}">'
            ),
            html=False,
        )

    def test_un_etudiant_ne_peut_pas_acceder_a_la_publication(self):
        self.client.force_login(self.etudiant_user)

        response = self.client.get(reverse("publier_offre"))

        self.assertRedirects(response, reverse("rechercher_offres"))
