from django.urls import path
from core import views

urlpatterns = [
    path('', views.home, name="home"),
    path('login/', views.login, name="login"),
    path('callback/', views.callback, name="callback"),
    path('organize/', views.organize, name="organize"),
    path('playlist_info/', views.playlist_info, name='playlist_info'),
]