# Generated by Django 3.0.8 on 2020-07-15 14:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('API', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidat',
            name='sujet',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='API.Sujet'),
        ),
        migrations.AlterField(
            model_name='recherche',
            name='candidat',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='API.Candidat'),
        ),
        migrations.AlterField(
            model_name='recherche',
            name='sujet',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='API.Sujet'),
        ),
        migrations.AlterField(
            model_name='sujet',
            name='parcours',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='API.Parcours'),
        ),
    ]