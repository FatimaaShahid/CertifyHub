from django.urls import path
from . import views
from generator.views import upload_files, map_fields,generate_certificates,choose_font

urlpatterns = [
    path('map-fields/', map_fields, name='map_fields'),
    path('', upload_files, name='upload_files'),
    path('generate-certificates/', generate_certificates, name='generate_certificates'),
    path('choose-font/', choose_font, name='choose_font'),
    path('download/', views.download_certificates, name='download_certificates'),

]
