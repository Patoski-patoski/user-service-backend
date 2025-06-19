from django.urls import path
from django.urls.resolvers import URLPattern
from .views import RegisterView, ActivateView


urlpatterns: list[URLPattern] = [
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/<uuid:token>/', ActivateView.as_view(), name='activate'),
]
