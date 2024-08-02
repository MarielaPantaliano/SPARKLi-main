from django.contrib import admin
from WebApp import views
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include("WebApp.urls")),
]
