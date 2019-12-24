from django.urls import path,include
from . import views

urlpatterns = [
    path('',views.index,name='index'),
    path('uploadcsv/',views.upload_csv,name='upload_csv'),
    path('exportcsv/',views.export_csv,name='export_csv'),
]
