# Generated migration for adding xp_duration_start field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('formulaire', '0003_alter_candidat_updated_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='candidat',
            name='xp_duration_start',
            field=models.IntegerField(
                blank=True,
                null=True,
                verbose_name='Durée d\'expérience initiale (années)',
                help_text='Valeur initiale saisie au moment de la création'
            ),
        ),
    ]
