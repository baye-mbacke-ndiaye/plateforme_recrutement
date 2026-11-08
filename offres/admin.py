
from django.contrib import admin
from .models import Offre, ProfilEtudiant, ProfilEntreprise, Candidature
from django.utils.html import format_html

@admin.register(Offre)
class OffreAdmin(admin.ModelAdmin):
    list_display = (
        'titre',
        'entreprise',
        'type_contrat',
        'localisation',
        'date_limite',
        'statut',
    )
    list_filter = ('statut', 'type_contrat')
    search_fields = ('titre', 'entreprise')
    ordering = ('-date_creation',)
    actions = ('valider_offres', 'cloturer_offres')

    @admin.action(description="Valider et publier les offres sélectionnées")
    def valider_offres(self, request, queryset):
        nombre = queryset.filter(statut='en_attente').update(statut='ouverte')
        self.message_user(request, f"{nombre} offre(s) validée(s) et publiée(s).")

    @admin.action(description="Clôturer les offres sélectionnées")
    def cloturer_offres(self, request, queryset):
        nombre = queryset.exclude(statut='fermee').update(statut='fermee')
        self.message_user(request, f"{nombre} offre(s) clôturée(s).")


@admin.register(ProfilEtudiant)
class ProfilEtudiantAdmin(admin.ModelAdmin):
    list_display = (
        'nom_complet',
        'email',
        'telephone',
        'niveau_etudes',
        'filiere',
    )
    search_fields = ('nom_complet', 'email', 'telephone')



@admin.register(Candidature)
class CandidatureAdmin(admin.ModelAdmin):

    list_display = (
        'etudiant',
        'offre',
        'entreprise',
        'statut',
        'voir_cv',
        'date_candidature',
    )

    list_editable = ('statut',)

    list_filter = (
        'statut',
        'offre',
        'date_candidature',
    )

    search_fields = (
        'etudiant__nom_complet',
        'etudiant__email',
        'offre__titre',
        'offre__entreprise',
    )

    ordering = ('-date_candidature',)

    list_per_page = 20

    @admin.display(description="Entreprise")
    def entreprise(self, obj):
        return obj.offre.entreprise

    @admin.display(description="CV du candidat")
    def voir_cv(self, obj):
        if obj.cv:
            return format_html(
                '<a href="{}" target="_blank" rel="noopener noreferrer">Voir le CV</a>',
                obj.cv.url
            )
        return "Aucun CV"