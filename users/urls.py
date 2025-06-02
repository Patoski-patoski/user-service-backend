from django.urls import path
from .views import RegisterView, ActivateView


urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('activate/<uuid:token>/', ActivateView.as_view(), name='activate'),
]
