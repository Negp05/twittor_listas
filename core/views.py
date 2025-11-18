import re
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Q
from django.template.loader import render_to_string
from .models import Tweet, Like, Comment, Follow, UserProfile, Lista, MiembroDeLista, Coleccion
from .forms import TweetForm, CommentForm, SignUpForm, ProfileForm, ListaForm, ColeccionForm

HASHTAG_RE = re.compile(r"(#\w+)")

# --- Función auxiliar ---
def _create_notification(actor, recipient, verb, tweet=None):
    if actor == recipient:
        return
    from .models import Notification
    Notification.objects.create(actor=actor, recipient=recipient, verb=verb, tweet=tweet)

# --- Registro de usuario ---
def signup_view(request):
    if request.user.is_authenticated:
        return redirect('timeline')
    form = SignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('timeline')
    return render(request, 'registration/signup.html', {'form': form})

# --- Timeline principal ---
@login_required
def timeline(request):
    following_ids = list(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))
    qs = Tweet.objects.filter(user_id__in=[request.user.id, *following_ids]).select_related('user', 'user__userprofile')
    form = TweetForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        tw = form.save(commit=False)
        tw.user = request.user
        tw.save()
        return redirect('timeline')
    return render(request, 'core/timeline.html', {'tweets': qs, 'form': form})

# --- Explorar ---
@login_required
def explore(request):
    qs = Tweet.objects.select_related('user', 'user__userprofile').all()[:100]
    return render(request, 'core/timeline.html', {'tweets': qs, 'form': TweetForm()})

# --- BUSCADOR GLOBAL ---
@login_required
def search(request):
    query = request.GET.get('q', '').strip()
    tweets = []
    users = []

    if query:
        tweets = Tweet.objects.filter(
            Q(content__icontains=query) | Q(user__username__icontains=query)
        ).select_related('user', 'user__userprofile')[:50]

        users = User.objects.filter(username__icontains=query)[:30]

    return render(request, 'core/search.html', {
        'query': query,
        'tweets': tweets,
        'users': users
    })

# --- Detalle de tweet ---
@login_required
def tweet_detail(request, pk):
    tw = get_object_or_404(Tweet.objects.select_related('user', 'user__userprofile'), pk=pk)
    cform = CommentForm(request.POST or None)
    if request.method == 'POST' and cform.is_valid():
        c = cform.save(commit=False)
        c.user = request.user
        c.tweet = tw
        c.save()
        return redirect(tw.get_absolute_url())
    return render(request, 'core/tweet_detail.html', {'tweet': tw, 'cform': cform})

# --- Perfil de usuario ---
@login_required
def profile(request, username):
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(UserProfile, user=user)
    is_me = request.user == user
    is_following = Follow.objects.filter(follower=request.user, following=user).exists()
    tweets = Tweet.objects.filter(user=user)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'follow':
            Follow.objects.get_or_create(follower=request.user, following=user)
        elif action == 'unfollow':
            Follow.objects.filter(follower=request.user, following=user).delete()
        elif action == 'edit' and is_me:
            form = ProfileForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                form.save()
        return redirect('profile', username=username)
    form = ProfileForm(instance=profile) if is_me else None
    return render(request, 'core/profile.html', {
        'profile_user': user,
        'profile': profile,
        'is_me': is_me,
        'is_following': is_following,
        'tweets': tweets,
        'form': form
    })


# --- NOTIFICACIONES ---
@login_required
def notifications(request):
    """Muestra las notificaciones recibidas por el usuario."""
    from .models import Notification
    notificaciones = Notification.objects.filter(recipient=request.user).select_related('actor', 'tweet')
    return render(request, 'core/notifications.html', {'notificaciones': notificaciones})


# --- VISTAS DE LISTAS ---
@login_required
def list_create(request):
    if request.method == 'POST':
        form = ListaForm(request.POST)
        if form.is_valid():
            lista = form.save(commit=False)
            lista.creador = request.user
            lista.save()
            return redirect('my_lists')
    else:
        form = ListaForm()
    return render(request, 'core/list_create.html', {'form': form})

@login_required
def my_lists(request):
    listas = Lista.objects.filter(creador=request.user).order_by('-fecha_creacion')
    return render(request, 'core/my_lists.html', {'listas': listas})

@login_required
def list_feed(request, list_pk):
    lista = get_object_or_404(Lista, pk=list_pk)
    if lista.es_privada and lista.creador != request.user:
        return HttpResponseForbidden("No tienes permiso para ver esta lista privada.")
    miembros = MiembroDeLista.objects.filter(lista=lista).values_list('usuario_id', flat=True)
    tweets = Tweet.objects.filter(user_id__in=miembros).select_related('user', 'user__userprofile')
    return render(request, 'core/list_feed.html', {'lista': lista, 'tweets': tweets})

@login_required
def list_members(request, list_pk):
    lista = get_object_or_404(Lista, pk=list_pk)
    if lista.creador != request.user:
        return HttpResponseForbidden("Solo el creador puede modificar los miembros.")
    miembros = lista.miembros.all()
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        try:
            usuario = User.objects.get(pk=user_id)
            if action == 'add':
                MiembroDeLista.objects.get_or_create(lista=lista, usuario=usuario)
            elif action == 'remove':
                MiembroDeLista.objects.filter(lista=lista, usuario=usuario).delete()
        except User.DoesNotExist:
            pass
        return redirect('list_members', list_pk=lista.id)
    return render(request, 'core/list_members.html', {'lista': lista, 'miembros': miembros})

@login_required
def list_remove_member(request, list_pk, user_pk):
    """
    Vista para eliminar un usuario específico de una lista.
    Solo el creador de la lista puede ejecutar esta acción.
    """
    if request.method == 'POST':
        # 1. Obtener la Lista y verificar que el dueño sea el usuario actual
        lista = get_object_or_404(Lista, pk=list_pk)
        
        # Seguridad: Solo el dueño/creador de la lista puede eliminar miembros
        if lista.creador != request.user:
            return HttpResponseForbidden("No tienes permiso para modificar esta lista.")

        # 2. Obtener el usuario que se intenta eliminar
        user_to_remove = get_object_or_404(User, pk=user_pk)
        
        # 3. Eliminar la relación de MiembroDeLista
        try:
            # Usamos 'usuario' para el campo del modelo, coincidiendo con la vista 'list_members'
            MiembroDeLista.objects.filter(
                lista=lista, 
                usuario=user_to_remove
            ).delete()
            # Opcional: añadir un mensaje de éxito con django.contrib.messages
        except:
            # Si la relación no existe, simplemente ignoramos el error
            pass

        # 4. Redirigir de vuelta a la página de gestión de miembros
        return redirect('list_members', list_pk=list_pk)
    
    # Si alguien intenta acceder por GET, lo redirigimos
    return redirect('list_members', list_pk=list_pk)

# --- VISTAS DE COLECCIONES ---
@login_required
def lista_colecciones(request):
    colecciones = Coleccion.objects.filter(usuario=request.user)
    return render(request, 'core/colecciones_list.html', {'colecciones': colecciones})

@login_required
def crear_coleccion(request):
    if request.method == 'POST':
        form = ColeccionForm(request.POST)
        if form.is_valid():
            coleccion = form.save(commit=False)
            coleccion.usuario = request.user
            coleccion.save()
            return redirect('lista_colecciones')
    else:
        form = ColeccionForm()
    return render(request, 'core/coleccion_form.html', {'form': form})

@login_required
def detalle_coleccion(request, pk):
    coleccion = get_object_or_404(Coleccion, pk=pk, usuario=request.user)
    tweets = coleccion.tweets.select_related('user', 'user__userprofile')
    return render(request, 'core/coleccion_detalle.html', {'coleccion': coleccion, 'tweets': tweets})

@login_required
def eliminar_coleccion(request, pk):
    coleccion = get_object_or_404(Coleccion, pk=pk, usuario=request.user)
    if request.method == 'POST':
        coleccion.delete()
        return redirect('lista_colecciones')
    return render(request, 'core/coleccion_confirm_delete.html', {'coleccion': coleccion})

# --- VISTA DE HASHTAGS ---
@login_required
def tag(request, tag):
    """Muestra todos los tweets que contienen un hashtag específico."""
    hashtag = f"#{tag}"
    tweets = Tweet.objects.filter(content__icontains=hashtag).select_related('user', 'user__userprofile')
    return render(request, 'core/tag.html', {'tag': hashtag, 'tweets': tweets})

# --- LIKE / UNLIKE ---
@login_required
def like_toggle(request, pk):
    """Activa o desactiva un 'Me gusta' en un tweet."""
    tweet = get_object_or_404(Tweet, pk=pk)
    like, created = Like.objects.get_or_create(user=request.user, tweet=tweet)

    # Si ya existía el "like", lo elimina (toggle off)
    if not created:
        like.delete()

    # Si la solicitud viene de HTMX, renderiza solo el botón actualizado
    if request.headers.get("HX-Request"):
        return render(request, "components/like_button.html", {"t": tweet, "user": request.user})

    # Si no, recarga la página anterior
    return redirect(request.META.get("HTTP_REFERER", "timeline"))

# --- RETWEET ---
@login_required
def retweet(request, pk):
    """Permite retuitear un tweet existente."""
    tweet_original = get_object_or_404(Tweet, pk=pk)

    # Evita que el usuario se retuitee a sí mismo varias veces
    ya_retweeteado = Tweet.objects.filter(user=request.user, content=tweet_original.content).exists()
    if not ya_retweeteado:
        Tweet.objects.create(
            user=request.user,
            content=tweet_original.content,
            parent=tweet_original  # opcional, si tu modelo Tweet tiene un campo 'parent'
        )

    return redirect('timeline')

# --- QUOTE TWEET ---
@login_required
def quote(request, pk):
    """Permite citar un tweet (retweet con comentario)."""
    original = get_object_or_404(Tweet, pk=pk)

    if request.method == "POST":
        form = TweetForm(request.POST, request.FILES)
        if form.is_valid():
            nuevo_tweet = form.save(commit=False)
            nuevo_tweet.user = request.user
            nuevo_tweet.content = f"RT @{original.user.username}: {original.content}\n\n{nuevo_tweet.content}"
            nuevo_tweet.save()
            return redirect('timeline')
    else:
        form = TweetForm()

    return render(request, 'core/quote.html', {
        'form': form,
        'original': original
    })

# --- AGREGAR TWEET A UNA COLECCIÓN ---
@login_required
def agregar_a_coleccion(request, tweet_id):
    """Permite agregar un tweet a una colección existente del usuario."""
    tweet = get_object_or_404(Tweet, id=tweet_id)
    colecciones = Coleccion.objects.filter(usuario=request.user)

    if request.method == "POST":
        coleccion_id = request.POST.get("coleccion_id")
        coleccion = get_object_or_404(Coleccion, id=coleccion_id, usuario=request.user)
        coleccion.tweets.add(tweet)
        return redirect("detalle_coleccion", pk=coleccion.id)

    return render(request, "core/agregar_a_coleccion.html", {
        "tweet": tweet,
        "colecciones": colecciones
    })

@login_required
def agregar_a_coleccion_ajax(request):
    """Agrega un tweet a una colección existente mediante HTMX/AJAX."""
    tweet_id = request.POST.get("tweet_id")
    coleccion_id = request.POST.get("coleccion_id")

    if not (tweet_id and coleccion_id):
        return JsonResponse({"error": "Faltan datos"}, status=400)

    tweet = get_object_or_404(Tweet, id=tweet_id)
    coleccion = get_object_or_404(Coleccion, id=coleccion_id, usuario=request.user)

    coleccion.tweets.add(tweet)
    return JsonResponse({"success": True, "coleccion": coleccion.nombre})