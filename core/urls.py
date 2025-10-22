from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.search, name='search'),
    path('tag/<str:tag>/', views.tag, name='tag'),
    path('n/', views.notifications, name='notifications'),

    path('', views.timeline, name='timeline'),
    path('explore/', views.explore, name='explore'),
    path('signup/', views.signup_view, name='signup'),
    path('t/<int:pk>/', views.tweet_detail, name='tweet_detail'),
    path('t/<int:pk>/like/', views.like_toggle, name='like_toggle'),
    path('t/<int:pk>/retweet/', views.retweet, name='retweet'),
    path('t/<int:pk>/quote/', views.quote, name='quote'),
    path('u/<str:username>/', views.profile, name='profile'),
    path('listas/crear/', views.list_create, name='list_create'),
    path('listas/yo/', views.my_lists, name='my_lists'),
    path('listas/<int:list_pk>/feed/', views.list_feed, name='list_feed'),
    path('listas/<int:list_pk>/miembros/', views.list_members, name='list_members'),
]
