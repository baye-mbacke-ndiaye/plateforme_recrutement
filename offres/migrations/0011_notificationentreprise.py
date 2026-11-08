from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("offres", "0010_alter_profilentreprise_secteur"),
    ]

    operations = [
        migrations.CreateModel(
            name="NotificationEntreprise",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("message", models.CharField(max_length=255)),
                ("date_creation", models.DateTimeField(auto_now_add=True)),
                ("lu", models.BooleanField(default=False)),
                (
                    "candidature",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications_entreprise",
                        to="offres.candidature",
                    ),
                ),
                (
                    "entreprise",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to="offres.profilentreprise",
                    ),
                ),
            ],
            options={
                "verbose_name": "Notification entreprise",
                "verbose_name_plural": "Notifications entreprise",
                "ordering": ["-date_creation"],
            },
        ),
    ]
