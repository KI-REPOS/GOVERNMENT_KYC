# backend/kyc_app/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('generate_token/', views.generate_token, name='generate_token'),
    path('verify/', views.verify_kyc, name='verify_kyc'),
    path('user/<int:user_id>/', views.get_user, name='get_user'),
    path('csrf/', views.get_csrf_token, name='get_csrf_token'),
    path('test/', views.test_view, name='test'),
    path("register_page/", views.register_page, name="register_page"),
    path("profile/", views.profile_view, name="profile_page"),
    path('test-mongo/', views.test_mongo, name='test_mongo'),
]