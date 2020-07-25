from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'parcours', views.ParcoursViewSet)
router.register(r'sujet', views.SujetViewSet)
router.register(r'candidat', views.CandidatViewSet)
router.register(r'recherche', views.RechercheViewSet)
router.register(r'stage', views.StageViewSet)

urlpatterns = [
   path('', views.index, name='index'),
   path('api/', include(router.urls)),
   path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
