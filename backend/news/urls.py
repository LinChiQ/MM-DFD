# backend/news/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('api/verify/', views.NewsVerificationView.as_view(), name='verify_news'),
]
