from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('offres', '0008_profiletudiant_competences_profiletudiant_cv'),
    ]

    operations = [
        migrations.AlterField(
            model_name='offre',
            name='statut',
            field=models.CharField(
                choices=[
                    ('en_attente', 'En attente de validation'),
                    ('ouverte', 'Publiée'),
                    ('fermee', 'Clôturée'),
                ],
                default='ouverte',
                max_length=10,
            ),
        ),
    ]
