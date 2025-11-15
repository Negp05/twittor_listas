from django.contrib import admin
from .models import (
    Tweet, Like, Comment, UserProfile, Follow,
    Lista, MiembroDeLista, Coleccion
)

# --- Modelos base ---

@admin.register(Tweet)
class TweetAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'content', 'created_at')
    search_fields = ('content', 'user__username')
    list_filter = ('created_at',)
    ordering = ('-created_at',)


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'tweet', 'created_at')
    search_fields = ('user__username',)
    list_filter = ('created_at',)
    ordering = ('-created_at',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'tweet', 'created_at')
    search_fields = ('content', 'user__username')
    list_filter = ('created_at',)
    ordering = ('-created_at',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at')
    search_fields = ('user__username',)
    ordering = ('-created_at',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'follower', 'following', 'created_at')
    search_fields = ('follower__username', 'following__username')
    list_filter = ('created_at',)
    ordering = ('-created_at',)

# --- Nuevos modelos (rama feat/listas) ---

@admin.register(Lista)
class ListaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'creador', 'es_privada', 'fecha_creacion')
    list_filter = ('es_privada', 'fecha_creacion')
    search_fields = ('nombre', 'creador__username')
    ordering = ('-fecha_creacion',)


@admin.register(MiembroDeLista)
class MiembroDeListaAdmin(admin.ModelAdmin):
    list_display = ('id', 'lista', 'usuario', 'fecha_agregado')
    list_filter = ('fecha_agregado',)
    search_fields = ('lista__nombre', 'usuario__username')
    ordering = ('-fecha_agregado',)


@admin.register(Coleccion)
class ColeccionAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'usuario', 'creada_en')
    search_fields = ('nombre', 'usuario__username')
    list_filter = ('creada_en',)
    ordering = ('-creada_en',)
