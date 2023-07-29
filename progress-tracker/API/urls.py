from django.urls import include, path
from rest_framework import routers
from rest_framework.authtoken import views as authtoken_views

from . import views

router = routers.DefaultRouter()
router.register(r"parcours", views.ParcoursViewSet)
router.register(r"sujet", views.SujetViewSet)
router.register(r"candidat", views.CandidatViewSet)
router.register(r"recherche", views.RechercheViewSet)
router.register(r"stage", views.StageViewSet)

urlpatterns = [
    path("", views.index, name="index"),
    path("login", authtoken_views.obtain_auth_token),
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
