from django.urls import path

from apps.core import views

urlpatterns = [
    path("", views.BaseView.as_view(), name="core-base"),
    path("welcome", views.WelcomePartialView.as_view(), name="core-welcome"),
]
