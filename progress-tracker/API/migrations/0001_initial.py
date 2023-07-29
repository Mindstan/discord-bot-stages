# Generated by Django 2.2.4 on 2020-07-15 12:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Candidat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('prenom', models.CharField(max_length=256)),
                ('nom', models.CharField(max_length=256)),
                ('classe', models.CharField(max_length=256)),
                ('login', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='Parcours',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='Sujet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=256)),
                ('ordre', models.IntegerField()),
                ('lien', models.CharField(max_length=1024)),
                ('explications', models.TextField()),
                ('parcours', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='API.Parcours')),
            ],
        ),
        migrations.CreateModel(
            name='Stage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=256)),
                ('date', models.DateField()),
                ('statut', models.CharField(max_length=256)),
                ('candidats', models.ManyToManyField(to='API.Candidat')),
            ],
        ),
        migrations.CreateModel(
            name='Recherche',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('premiere_lecture', models.DateField()),
                ('demarrage_officiel', models.DateField()),
                ('validation', models.DateField()),
                ('commentaires', models.TextField()),
                ('candidat', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='API.Candidat')),
                ('sujet', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='API.Sujet')),
            ],
        ),
        migrations.AddField(
            model_name='candidat',
            name='sujet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='API.Sujet'),
        ),
    ]
