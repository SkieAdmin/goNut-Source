from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/password/', views.change_password_view, name='change_password'),
    path('favorites/', views.favorites_view, name='favorites'),

    # Public user profiles
    path('u/<str:username>/', views.public_profile_view, name='public_profile'),
    path('u/<str:username>/list/', views.public_list_view, name='public_list'),
]
