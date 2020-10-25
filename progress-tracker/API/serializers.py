from rest_framework import serializers
from .models import *


class ParcoursSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Parcours
        fields = ["id", "nom", "code", "sujet_set", "url"]


class SujetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Sujet
        fields = ["id", "nom", "parcours", "ordre",
                  "lien", "correction", "explications", "url"]


class CandidatSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Candidat
        fields = ["id", "prenom", "nom", "annee_bac",
                  "login", "discord_name", "sujet_id", "sujet", "url"]


class RechercheSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Recherche
        fields = ["id", "candidat", "sujet", "premiere_lecture",
                  "demarrage_officiel", "validation", "commentaires", "url", "debut_pause", "faux_debut"]


class StageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Stage
        fields = ["id", "nom", "date", "statut", "candidats", "url"]
