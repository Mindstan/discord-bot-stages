import base64
import os

import django_filters.rest_framework
from django.http import HttpResponse
from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Candidat, Parcours, Recherche, Stage, Sujet
from .serializers import (CandidatSerializer, ParcoursSerializer,
                          RechercheSerializer, StageSerializer,
                          SujetSerializer)


def index(request):
    API_TOKEN = os.getenv("API_TOKEN", "")
    INDEX_USERPASS = os.getenv("INDEX_USERPASS", None)

    if not INDEX_USERPASS:
        return render(request, "index.html", {"api_token": API_TOKEN})

    if "HTTP_AUTHORIZATION" in request.META:
        auth = request.META["HTTP_AUTHORIZATION"].split()
        if len(auth) == 2 and auth[0].lower() == "basic":
            userpass = base64.b64decode(auth[1].encode("utf-8")).decode("utf-8")
            if userpass == INDEX_USERPASS:
                return render(request, "index.html", {"api_token": API_TOKEN})

    # Either they did not provide an authorization header or
    # something in the authorization attempt failed. Send a 401
    # back to them to ask them to authenticate.
    response = HttpResponse()
    response.status_code = 401
    response["WWW-Authenticate"] = 'Basic realm="Please enter your credentials"'
    return response


class ParcoursViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = Parcours.objects.all().order_by("nom")
    serializer_class = ParcoursSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]


class SujetViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = Sujet.objects.all().order_by("ordre")
    serializer_class = SujetSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    # filterset_fields = ["parcours"]


class CandidatViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = Candidat.objects.all().order_by("prenom")
    serializer_class = CandidatSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]


class RechercheViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = Recherche.objects.all()
    serializer_class = RechercheSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_fields = ["candidat", "sujet"]


class StageViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = Stage.objects.all().order_by("date")
    serializer_class = StageSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
