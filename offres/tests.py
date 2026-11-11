from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .forms import OffreForm, REGIONS_SENEGAL
from .models import (
    Candidature,
    NotificationEntreprise,
    Offre,
    ProfilEntreprise,
    ProfilEtudiant,
)


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

    def test_detail_public_refuse_une_offre_fermee(self):
        response = self.client.get(
            reverse("detail_offre", args=[self.offre_fermee.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_entreprise_proprietaire_peut_consulter_son_offre_fermee(self):
        self.client.force_login(self.entreprise_user)
        response = self.client.get(
            reverse("detail_offre", args=[self.offre_fermee.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["offre_active"])
        self.assertFalse(response.context["peut_postuler"])

    def test_detail_public_refuse_une_offre_en_attente(self):
        offre = self.creer_offre("Offre en attente", statut="en_attente")
        response = self.client.get(reverse("detail_offre", args=[offre.pk]))
        self.assertEqual(response.status_code, 404)

    def test_candidature_impossible_pour_une_offre_expiree(self):
        self.client.force_login(self.etudiant_user)

        response = self.client.get(
            reverse("postuler", args=[self.offre_expiree.pk])
        )

        self.assertEqual(response.status_code, 404)

    def test_entreprise_est_notifiee_quand_un_etudiant_postule(self):
        self.client.force_login(self.etudiant_user)

        response = self.client.post(
            reverse("postuler", args=[self.offre_active.pk]),
            {
                "cv": SimpleUploadedFile(
                    "cv-etudiant.pdf",
                    b"%PDF-1.4 test",
                    content_type="application/pdf",
                ),
                "lettre_motivation": "Ma motivation",
            },
        )

        self.assertRedirects(
            response,
            reverse("detail_offre", args=[self.offre_active.pk]),
        )
        candidature = Candidature.objects.get(
            etudiant=self.etudiant,
            offre=self.offre_active,
        )
        notification = NotificationEntreprise.objects.get(
            entreprise=self.entreprise,
            candidature=candidature,
        )
        self.assertFalse(notification.lu)
        self.assertIn(self.etudiant.nom_complet, notification.message)
        self.assertIn(self.offre_active.titre, notification.message)

        self.client.force_login(self.entreprise_user)
        dashboard = self.client.get(reverse("tableau_bord_entreprise"))
        self.assertContains(dashboard, "Nouvelles candidatures")
        self.assertContains(dashboard, self.etudiant.nom_complet)
        self.assertContains(dashboard, self.offre_active.titre)
        self.assertEqual(dashboard.context["notifications_non_lues"], 1)

        self.client.post(
            reverse(
                "marquer_notification_entreprise_lue",
                args=[notification.pk],
            )
        )
        notification.refresh_from_db()
        self.assertTrue(notification.lu)

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
                "region": "Dakar",
                "date_limite": (
                    timezone.localdate() - timedelta(days=1)
                ).isoformat(),
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("date_limite", form.errors)

    def test_page_publication_affiche_region_et_saisie_de_commune(self):
        self.client.force_login(self.entreprise_user)

        response = self.client.get(reverse("publier_offre"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("tableau_bord_entreprise"))
        self.assertContains(response, reverse("rechercher_offres"))
        self.assertContains(response, reverse("deconnexion"))
        self.assertContains(response, 'aria-current="page"')
        self.assertContains(response, "Ville, commune ou sous-région")
        self.assertContains(
            response,
            f'action="{reverse("deconnexion")}"',
        )
        for region in REGIONS_SENEGAL:
            self.assertContains(response, f'<option value="{region}">')

    def test_formulaire_offre_enregistre_region_et_commune(self):
        offre = self.creer_offre("Offre à Dakar")
        form = OffreForm(
            data={
                "titre": offre.titre,
                "description": "Description de test",
                "type_contrat": "emploi",
                "region": "Thiès",
                "commune": "Mbour",
                "date_limite": (
                    timezone.localdate() + timedelta(days=1)
                ).isoformat(),
            },
            instance=offre,
        )

        self.assertTrue(form.is_valid(), form.errors)
        offre = form.save()
        self.assertEqual(offre.localisation, "Thiès — Mbour")

    def test_formulaire_offre_accepte_une_commune_sans_region(self):
        form = OffreForm(
            data={
                "titre": "Offre à Mbour",
                "description": "Description de test",
                "type_contrat": "emploi",
                "region": "",
                "commune": "Mbour",
                "date_limite": (
                    timezone.localdate() + timedelta(days=1)
                ).isoformat(),
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["localisation"], "Mbour")

    def test_un_etudiant_ne_peut_pas_acceder_a_la_publication(self):
        self.client.force_login(self.etudiant_user)

        response = self.client.get(reverse("publier_offre"))

        self.assertRedirects(response, reverse("rechercher_offres"))


class GestionOffresEntrepriseTests(TestCase):
    """Publication immédiate, modification et clôture des offres."""

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
            "type_contrat": "emploi", "region": "Dakar",
            "commune": "",
            "date_limite": (timezone.localdate() + timedelta(days=10)).isoformat(),
        }

    def test_nouvelle_offre_est_publiee_et_visible(self):
        self.client.force_login(self.user_a)
        self.client.post(reverse("publier_offre"), self.donnees_offre())

        nouvelle = Offre.objects.get(titre="Nouvelle offre")
        self.assertEqual(nouvelle.statut, "ouverte")

        reponse = self.client.get(reverse("rechercher_offres"))
        self.assertIn(nouvelle, list(reponse.context["offres"]))

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


class HeritageEtMethodesMetierTests(TestCase):
    """Teste la POO : héritage, polymorphisme et méthodes des modèles."""

    def setUp(self):
        self.user_e = User.objects.create_user("ent", password="motdepasse-securise")
        self.user_s = User.objects.create_user("etu", password="motdepasse-securise")
        self.entreprise = ProfilEntreprise.objects.create(
            utilisateur=self.user_e, nom="Baobab SA", secteur="informatique",
            email="contact@baobab.test", telephone="771000001",
        )
        self.etudiant = ProfilEtudiant.objects.create(
            utilisateur=self.user_s, nom_complet="Awa Diop",
            email="awa@test.example", telephone="771000002",
        )
        self.offre = Offre.objects.create(
            titre="Stage Python", entreprise="Baobab SA",
            profil_entreprise=self.entreprise, description="Stage",
            type_contrat="stage", localisation="Dakar",
            date_limite=timezone.localdate() + timedelta(days=5),
            statut="en_attente",
        )

    def test_heritage_des_profils(self):
        from .models import ProfilBase

        self.assertTrue(ProfilBase._meta.abstract)
        self.assertTrue(issubclass(ProfilEtudiant, ProfilBase))
        self.assertTrue(issubclass(ProfilEntreprise, ProfilBase))
        # Les champs communs viennent de la classe de base.
        self.assertTrue(hasattr(ProfilEtudiant, "email"))
        self.assertTrue(hasattr(ProfilEntreprise, "telephone"))

    def test_polymorphisme_role_et_nom_affiche(self):
        for profil, role, nom in [
            (self.etudiant, "etudiant", "Awa Diop"),
            (self.entreprise, "entreprise", "Baobab SA"),
        ]:
            self.assertEqual(profil.role, role)
            self.assertEqual(profil.nom_affiche(), nom)
            self.assertEqual(str(profil), nom)

    def test_offre_publier_et_cloturer(self):
        self.assertFalse(self.offre.est_publique())
        self.assertTrue(self.offre.publier())
        self.assertTrue(self.offre.est_publique())
        self.assertFalse(self.offre.publier())  # déjà publiée
        self.assertTrue(self.offre.cloturer())
        self.assertFalse(self.offre.est_publique())
        self.assertFalse(self.offre.cloturer())  # déjà clôturée
        self.offre.refresh_from_db()
        self.assertEqual(self.offre.statut, "fermee")

    def test_offre_expiree_n_est_pas_publique(self):
        self.offre.statut = "ouverte"
        self.offre.date_limite = timezone.localdate() - timedelta(days=1)
        self.assertFalse(self.offre.est_publique())

    def test_peut_postuler_une_seule_fois(self):
        self.offre.publier()
        self.assertTrue(self.etudiant.peut_postuler(self.offre))
        Candidature.objects.create(etudiant=self.etudiant, offre=self.offre)
        self.assertTrue(self.etudiant.a_postule(self.offre))
        self.assertFalse(self.etudiant.peut_postuler(self.offre))

    def test_quatre_statuts_de_candidature(self):
        statuts = [valeur for valeur, _ in Candidature.STATUT_CHOIX]
        self.assertEqual(statuts, ["en_attente", "en_cours", "acceptee", "refusee"])
        self.assertEqual(dict(Candidature.STATUT_CHOIX)["en_cours"], "En cours d'étude")

    def test_changer_statut_notifie_l_etudiant(self):
        from .models import NotificationCandidature

        c = Candidature.objects.create(etudiant=self.etudiant, offre=self.offre)
        self.assertTrue(c.changer_statut("en_cours"))
        self.assertFalse(c.changer_statut("en_cours"))  # inchangé : pas de doublon
        self.assertTrue(c.changer_statut("acceptee"))
        self.assertEqual(NotificationCandidature.objects.filter(candidature=c).count(), 2)
        self.assertIn("Acceptée", NotificationCandidature.objects.first().message)
        with self.assertRaises(ValueError):
            c.changer_statut("inconnu")

    def test_entreprise_met_une_candidature_en_cours_d_etude(self):
        c = Candidature.objects.create(etudiant=self.etudiant, offre=self.offre)
        self.client.force_login(self.user_e)
        self.client.post(
            reverse("modifier_statut_candidature", args=[c.id]), {"statut": "en_cours"}
        )
        c.refresh_from_db()
        self.assertEqual(c.statut, "en_cours")


class RechercheSecteurEtDateTests(TestCase):
    def setUp(self):
        def entreprise(nom, secteur, i):
            u = User.objects.create_user(f"u{i}", password="motdepasse-securise")
            return ProfilEntreprise.objects.create(
                utilisateur=u, nom=nom, secteur=secteur,
                email=f"{nom.lower()}@test.example", telephone=f"77200000{i}",
            )

        self.it = entreprise("Techno", "informatique", 1)
        self.banque = entreprise("Banco", "banque", 2)
        aujourdhui = timezone.localdate()
        self.o_it = self.offre("Dev web", self.it, aujourdhui + timedelta(days=3))
        self.o_banque = self.offre("Analyste", self.banque, aujourdhui + timedelta(days=20))

    def offre(self, titre, profil, date_limite):
        return Offre.objects.create(
            titre=titre, entreprise=profil.nom, profil_entreprise=profil,
            description="Description", type_contrat="emploi", localisation="Dakar",
            date_limite=date_limite, statut="ouverte",
        )

    def test_filtre_par_secteur(self):
        r = self.client.get(reverse("rechercher_offres"), {"secteur": "banque"})
        offres = list(r.context["offres"])
        self.assertEqual(offres, [self.o_banque])

    def test_secteur_invalide_est_ignore(self):
        r = self.client.get(reverse("rechercher_offres"), {"secteur": "nimporte"})
        self.assertEqual(len(r.context["offres"]), 2)

    def test_filtre_par_date_limite(self):
        limite = (timezone.localdate() + timedelta(days=10)).isoformat()
        r = self.client.get(reverse("rechercher_offres"), {"avant": limite})
        self.assertEqual(list(r.context["offres"]), [self.o_it])

    def test_date_invalide_est_ignoree(self):
        r = self.client.get(reverse("rechercher_offres"), {"avant": "pas-une-date"})
        self.assertEqual(len(r.context["offres"]), 2)

    def test_la_page_affiche_les_nouveaux_filtres(self):
        r = self.client.get(reverse("rechercher_offres"))
        self.assertContains(r, 'name="secteur"')
        self.assertContains(r, 'name="avant"')


class TelechargementCvPriveTests(TestCase):
    """Les CV de candidature ne sont accessibles qu'aux personnes autorisées."""

    def setUp(self):
        self.entreprise_user = User.objects.create_user(
            username="recruteur_cv", password="motdepasse-securise"
        )
        self.entreprise = ProfilEntreprise.objects.create(
            utilisateur=self.entreprise_user,
            nom="Entreprise CV",
            secteur="informatique",
            email="cv-entreprise@test.example",
            telephone="770000101",
        )
        self.etudiant_user = User.objects.create_user(
            username="candidat_cv", password="motdepasse-securise"
        )
        self.etudiant = ProfilEtudiant.objects.create(
            utilisateur=self.etudiant_user,
            nom_complet="Candidat CV",
            email="cv-etudiant@test.example",
            telephone="770000102",
        )
        self.autre_user = User.objects.create_user(
            username="autre_cv", password="motdepasse-securise"
        )
        self.offre = Offre.objects.create(
            titre="Stage de test",
            entreprise=self.entreprise.nom,
            profil_entreprise=self.entreprise,
            description="Description",
            type_contrat="stage",
            localisation="Dakar",
            date_limite=timezone.localdate() + timedelta(days=10),
        )
        self.candidature = Candidature.objects.create(
            etudiant=self.etudiant,
            offre=self.offre,
            cv=SimpleUploadedFile(
                "cv-candidat.pdf",
                b"%PDF-1.4 document de test",
                content_type="application/pdf",
            ),
        )

    def test_un_autre_compte_ne_peut_pas_telecharger_le_cv(self):
        self.client.force_login(self.autre_user)
        response = self.client.get(
            reverse("telecharger_cv_candidature", args=[self.candidature.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_l_entreprise_concernee_peut_telecharger_le_cv(self):
        self.client.force_login(self.entreprise_user)
        response = self.client.get(
            reverse("telecharger_cv_candidature", args=[self.candidature.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_l_etudiant_peut_telecharger_son_propre_cv_de_candidature(self):
        self.client.force_login(self.etudiant_user)
        response = self.client.get(
            reverse("telecharger_cv_candidature", args=[self.candidature.pk])
        )
        self.assertEqual(response.status_code, 200)
