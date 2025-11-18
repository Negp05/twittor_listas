from django.urls import path
from . import views

urlpatterns = [
    # --- Búsqueda, etiquetas y notificaciones ---
    path('search/', views.search, name='search'),
    path('tag/<str:tag>/', views.tag, name='tag'),
    path('n/', views.notifications, name='notifications'),

    # --- Feed principal ---
    path('', views.timeline, name='timeline'),
    path('explore/', views.explore, name='explore'),

    # --- Autenticación / Perfil ---
    path('signup/', views.signup_view, name='signup'),
    path('u/<str:username>/', views.profile, name='profile'),

    # --- Tweets ---
    path('t/<int:pk>/', views.tweet_detail, name='tweet_detail'),
    path('t/<int:pk>/like/', views.like_toggle, name='like_toggle'),
    path('t/<int:pk>/retweet/', views.retweet, name='retweet'),
    path('t/<int:pk>/quote/', views.quote, name='quote'),

    # --- Listas ---
    path('listas/yo/', views.my_lists, name='my_lists'),
    path('listas/crear/', views.list_create, name='list_create'),
    path('listas/<int:list_pk>/feed/', views.list_feed, name='list_feed'),
    path('listas/<int:list_pk>/miembros/', views.list_members, name='list_members'),
    path('listas/<int:list_pk>/miembros/<int:user_pk>/eliminar/', views.list_remove_member, name='list_remove_member'),
    

    # --- Colecciones ---
    path('colecciones/', views.lista_colecciones, name='lista_colecciones'),
    path('colecciones/nueva/', views.crear_coleccion, name='crear_coleccion'),
    path('colecciones/<int:pk>/', views.detalle_coleccion, name='detalle_coleccion'),
    path('colecciones/<int:pk>/eliminar/', views.eliminar_coleccion, name='eliminar_coleccion'),

    # --- Agregar tweets a colecciones ---
    path('tweets/<int:tweet_id>/agregar-a-coleccion/', views.agregar_a_coleccion, name='agregar_a_coleccion'),
    path('ajax/agregar-a-coleccion/', views.agregar_a_coleccion_ajax, name='agregar_a_coleccion_ajax'),
]
