from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

# --- Modelos Existentes ---

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.CharField(max_length=180, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Perfil de {self.user.username}'

class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f'{self.follower.username} → {self.following.username}'

class Tweet(models.Model):
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    is_retweet = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.CharField(max_length=280)
    image = models.ImageField(upload_to='tweets/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username}: {self.content[:30]}'

    def get_absolute_url(self):
        return reverse('tweet_detail', args=[self.pk])

    @property
    def like_count(self) -> int:
        return self.likes.count()

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'tweet')

    def __str__(self):
        return f'{self.user.username} ♥ {self.tweet_id}'

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE, related_name='comments')
    content = models.CharField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Coment de {self.user.username} en {self.tweet_id}'


class Notification(models.Model):
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications_sent')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    verb = models.CharField(max_length=80)
    tweet = models.ForeignKey(Tweet, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.actor} -> {self.recipient}: {self.verb}'


# --- NUEVOS MODELOS PARA LA TAREA DE LISTAS (FEAT/LISTAS) ---

class Lista(models.Model):
    """Define una lista de usuarios."""
    nombre = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    # Lista pública o privada
    es_privada = models.BooleanField(default=False) 
    
    # El creador de la lista
    creador = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='listas_creadas'
    )
    
    # Los usuarios que pertenecen a esta lista (relación Many-to-Many usando MiembroDeLista)
    miembros = models.ManyToManyField(
        User,
        related_name='listas_a_las_que_pertenece',
        through='MiembroDeLista'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Listas"

    def __str__(self):
        return self.nombre


class MiembroDeLista(models.Model):
    """Tabla intermedia para la relación de pertenencia."""
    lista = models.ForeignKey(Lista, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Esto previene que un usuario sea agregado dos veces a la misma lista.
        unique_together = ('lista', 'usuario') 
        verbose_name = "Miembro de Lista"
        verbose_name_plural = "Miembros de Lista"
        
    def __str__(self):
        return f"{self.usuario.username} en {self.lista.nombre}"
    
#modelo coleccion
class Coleccion(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='colecciones')
    tweets = models.ManyToManyField('Tweet', blank=True, related_name='colecciones')
    creada_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} - {self.usuario.username}"
    #fin modelo coleccion