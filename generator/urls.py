from django.urls import path
from . import views
from generator.views import upload_files, map_fields

urlpatterns = [
    path('map-fields/', map_fields, name='map_fields'),
    path('', upload_files, name='upload_files'),
]
