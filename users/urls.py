from django.urls import path
from django.urls.resolvers import URLPattern
from .views import RegisterView, ActivateView, LoginView, ProfileView


urlpatterns: list[URLPattern] = [
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/<uuid:token>/', ActivateView.as_view(), name='activate'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
]
