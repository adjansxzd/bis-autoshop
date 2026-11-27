from django.urls import path

from . import views

urlpatterns = [path("analytics/summary/", views.summary)]
