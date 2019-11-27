from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('students/', include('students.urls')),
    Search Results
    #path('admin/', admin.site.urls),
]