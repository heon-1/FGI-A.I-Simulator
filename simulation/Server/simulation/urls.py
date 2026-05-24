"""
Simulation app URL configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'projects', views.ProjectViewSet)


urlpatterns = [
    # Persona endpoints
    path('persona/validate/', views.validate_persona, name='validate-persona'),
    path('persona/generate/', views.generate_persona, name='generate-persona'),
    
    # Questionnaire endpoints
    path('questionnaire/validate/', views.validate_questionnaire, name='validate-questionnaire'),
    path('questionnaire/generate/', views.generate_questionnaire, name='generate-questionnaire'),
    
    # Individual interview endpoints
    path('individual/run/', views.run_individual_interview, name='run-individual'),
    path('individual/stream/', views.run_individual_interview_stream, name='run-individual-stream'),
    
    # FGI endpoints
    path('fgi/run/', views.run_fgi, name='run-fgi'),
    path('fgi/stream/', views.run_fgi_stream, name='run-fgi-stream'),
    
    # Journey map endpoints
    path('journey/generate/', views.generate_journey_map, name='generate-journey'),
    path('journey/stream/', views.generate_journey_map_stream, name='generate-journey-stream'),
    path('journey/csv/', views.journey_to_csv, name='journey-to-csv'),
    
    # ViewSets
    path('', include(router.urls)),
]
