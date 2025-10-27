import re
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Q
from django.template.loader import render_to_string
# --- IMPORTACIONES ACTUALIZADAS ---
from .models import Tweet, Like, Comment, Follow, UserProfile, Lista, MiembroDeLista
from .forms import TweetForm, CommentForm, SignUpForm, ProfileForm, ListForm
from .models import Coleccion, Tweet
from .forms import ColeccionForm
# -----------------------------------

HASHTAG_RE = re.compile(r"(#\w+)")

def _create_notification(actor, recipient, verb, tweet=None):
    if actor == recipient:
        return
    from .models import Notification
    Notification.objects.create(actor=actor, recipient=recipient, verb=verb, tweet=tweet)


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('timeline')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('timeline')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
def timeline(request):
    # Users to show: me + I'm following
    following_ids = list(Follow.objects.filter(follower=request.user).values_list('following_id', flat=True))
    qs = Tweet.objects.filter(user_id__in=[request.user.id, *following_ids]).select_related('user', 'user__userprofile')
    if request.method == 'POST':
        form = TweetForm(request.POST, request.FILES)
        if form.is_valid():
            tw = form.save(commit=False)
            tw.user = request.user
            tw.save()
            return redirect('timeline')
    else:
        form = TweetForm()
    return render(request, 'core/timeline.html', {'tweets': qs, 'form': form})

@login_required
def explore(request):
    qs = Tweet.objects.select_related('user', 'user__userprofile').all()[:100]
    return render(request, 'core/timeline.html', {'tweets': qs, 'form': TweetForm()})

# NOTA: La vista like_toggle duplicada ha sido eliminada. Se mantiene la versión HTMX al final.

@login_required
def tweet_detail(request, pk):
    tw = get_object_or_404(Tweet.objects.select_related('user', 'user__userprofile'), pk=pk)
    if request.method == 'POST':
        cform = CommentForm(request.POST)
        if cform.is_valid():
            c = cform.save(commit=False)
            c.user = request.user
            c.tweet = tw
            c.save()
            return redirect(tw.get_absolute_url())
    else:
        cform = CommentForm()
    return render(request, 'core/tweet_detail.html', {'tweet': tw, 'cform': cform})

@login_required
def profile(request, username):
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(UserProfile, user=user)
    is_me = request.user == user
    is_following = Follow.objects.filter(follower=request.user, following=user).exists()
    tweets = Tweet.objects.filter(user=user)
    if request.method == 'POST':
        # follow/unfollow or edit profile
        action = request.POST.get('action')
        if action == 'follow':
            if request.user != user:
                Follow.objects.get_or_create(follower=request.user, following=user)
        elif action == 'unfollow':
            Follow.objects.filter(follower=request.user, following=user).delete()
        elif action == 'edit' and is_me:
            form = ProfileForm(request.POST, request.FILES, instance=profile)
            if form.is_valid():
                form.save()
        return redirect('profile', username=username)

    form = ProfileForm(instance=profile) if is_me else None
    ctx = {'profile_user': user, 'profile': profile, 'is_me': is_me, 'is_following': is_following, 'tweets': tweets, 'form': form}
    return render(request, 'core/profile.html', ctx)

@login_required
def search(request):
    q = request.GET.get('q', '').strip()
    tweets = Tweet.objects.none()
    users = User.objects.none()
    if q:
        tweets = Tweet.objects.filter(Q(content__icontains=q) | Q(user__username__icontains=q)).select_related('user')[:100]
        users = User.objects.select_related('userprofile').filter(username__icontains=q)[:50]
    return render(request, 'core/search.html', {'q': q, 'tweets': tweets, 'users': users})

@login_required
def tag(request, tag):
    tag_lower = tag.lower()
    tweets = Tweet.objects.filter(content__iregex=rf'(^|\s)#({tag_lower})\b').select_related('user')
    return render(request, 'core/tag.html', {'tag': tag, 'tweets': tweets})

@login_required
def notifications(request):
    from .models import Notification
    notifs = Notification.objects.filter(recipient=request.user).select_related('actor', 'actor__userprofile', 'tweet').order_by('-created_at')[:50]
    # mark as read
    Notification.objects.filter(recipient=request.user, read=False).update(read=True)
    return render(request, 'core/notifications.html', {'notifs': notifs})

@login_required
def retweet(request, pk):
    if request.method != 'POST':
        return HttpResponseForbidden('Solo POST')
    tw = get_object_or_404(Tweet.objects.select_related('user', 'user__userprofile'), pk=pk)
    # Avoid duplicate pure-retweets by same user
    exists = Tweet.objects.filter(user=request.user, parent=tw, is_retweet=True).exists()
    if not exists:
        new_tw = Tweet.objects.create(user=request.user, content='', parent=tw, is_retweet=True)
        _create_notification(request.user, tw.user, 'retwitteó tu publicación', tweet=tw)
    return redirect(request.META.get('HTTP_REFERER', 'timeline'))

@login_required
def quote(request, pk):
    tw = get_object_or_404(Tweet.objects.select_related('user', 'user__userprofile'), pk=pk)
    if request.method == 'POST':
        form = TweetForm(request.POST, request.FILES)
        if form.is_valid():
            quote_tw = form.save(commit=False)
            quote_tw.user = request.user
            quote_tw.parent = tw
            quote_tw.is_retweet = False
            quote_tw.save()
            _create_notification(request.user, tw.user, 'citó tu publicación', tweet=tw)
            return redirect('timeline')
    else:
        form = TweetForm()
    return render(request, 'core/quote.html', {'original': tw, 'form': form})

# --- VISTAS PARA LISTAS DE USUARIOS (NUEVAS FUNCIONALIDADES) ---

@login_required
def list_create(request):
    """Permite al usuario crear una nueva lista."""
    if request.method == 'POST':
        form = ListForm(request.POST)
        if form.is_valid():
            lista = form.save(commit=False)
            lista.creador = request.user
            lista.save()
            return redirect('my_lists') 
    else:
        form = ListForm()
        
    return render(request, 'core/list_create.html', {'form': form, 'title': 'Crear Nueva Lista'})


@login_required
def my_lists(request):
    """Muestra todas las listas creadas por el usuario."""
    listas = Lista.objects.filter(creador=request.user).order_by('-fecha_creacion')
    return render(request, 'core/my_lists.html', {'listas': listas})


@login_required
def list_feed(request, list_pk):
    """Muestra el timeline filtrado por los miembros de una lista."""
    lista = get_object_or_404(Lista, pk=list_pk)
    
    # Restricción de acceso a listas privadas
    if lista.es_privada and lista.creador != request.user:
        return HttpResponseForbidden("No tienes permiso para ver esta lista privada.")

    # 1. Obtener IDs de los miembros de la lista
    member_ids = list(MiembroDeLista.objects.filter(lista=lista).values_list('usuario_id', flat=True))

    # 2. Obtener tweets de esos miembros
    tweets = Tweet.objects.filter(user_id__in=member_ids).select_related('user', 'user__userprofile').order_by('-created_at')

    form = TweetForm() 
    
    ctx = {
        'lista': lista,
        'tweets': tweets,
        'form': form,
        'title': f'Lista: {lista.nombre}'
    }
    return render(request, 'core/list_feed.html', ctx)


@login_required
def list_members(request, list_pk):
    """Muestra y permite gestionar a los miembros de una lista."""
    lista = get_object_or_404(Lista, pk=list_pk)
    
    # Solo el creador puede gestionar miembros
    if lista.creador != request.user:
        return HttpResponseForbidden("Solo el creador puede gestionar los miembros.")

    # Miembros actuales
    miembros_actuales = lista.miembros.all()
    
    # Lógica para añadir/eliminar miembros (generalmente manejado por POST/AJAX)
    if request.method == 'POST':
        user_id_to_manage = request.POST.get('user_id')
        action = request.POST.get('action')
        
        try:
            user_to_manage = User.objects.get(pk=user_id_to_manage)
            
            if action == 'add':
                # Crear la relación MiembroDeLista
                MiembroDeLista.objects.get_or_create(lista=lista, usuario=user_to_manage)
            elif action == 'remove':
                # Eliminar la relación
                MiembroDeLista.objects.filter(lista=lista, usuario=user_to_manage).delete()
        except User.DoesNotExist:
            pass # Ignorar si el usuario no existe

        # Usar redirect para prevenir doble envío
        return redirect('list_members', list_pk=list_pk)

    # Puedes añadir la lista de todos los usuarios para la búsqueda aquí si es necesario
    return render(request, 'core/list_members.html', {'lista': lista, 'miembros': miembros_actuales})

# --- FIN DE VISTAS DE LISTAS ---

@login_required
def like_toggle(request, pk):
    # Enhanced: if HTMX request, return partial
    if request.method != 'POST':
        return HttpResponseForbidden('Solo POST')
    tweet = get_object_or_404(Tweet, pk=pk)
    like, created = Like.objects.get_or_create(user=request.user, tweet=tweet)
    if not created:
        like.delete()
    else:
        _create_notification(request.user, tweet.user, 'le gustó tu publicación', tweet=tweet)

    if request.headers.get('Hx-Request'):
        html = render_to_string('components/like_button.html', {'t': tweet, 'user': request.user})
        return JsonResponse({'html': html})
    return redirect(request.META.get('HTTP_REFERER', tweet.get_absolute_url()))

#vistas CRUD basico
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
    tweets = coleccion.tweets.all()
    return render(request, 'core/coleccion_detalle.html', {'coleccion': coleccion, 'tweets': tweets})

@login_required
def eliminar_coleccion(request, pk):
    coleccion = get_object_or_404(Coleccion, pk=pk, usuario=request.user)
    if request.method == 'POST':
        coleccion.delete()
        return redirect('lista_colecciones')
    return render(request, 'core/coleccion_confirm_delete.html', {'coleccion': coleccion})


#vista para agregar tweets a colecciones
@login_required
def agregar_a_coleccion(request, tweet_id):
    tweet = get_object_or_404(Tweet, id=tweet_id)
    colecciones = Coleccion.objects.filter(usuario=request.user)

    if request.method == 'POST':
        coleccion_id = request.POST.get('coleccion_id')
        coleccion = get_object_or_404(Coleccion, id=coleccion_id, usuario=request.user)
        coleccion.tweets.add(tweet)
        return redirect('feed')  # Cambia 'feed' por el nombre de tu vista principal si se llama distinto

    return render(request, 'core/agregar_a_coleccion.html', {
        'tweet': tweet,
        'colecciones': colecciones
    })
#fin de vista agregar tweets a colecciones

#vista ajax para agregar tweets a colecciones
@login_required
def agregar_a_coleccion_ajax(request):
    if request.method == 'POST':
        tweet_id = request.POST.get('tweet_id')
        coleccion_id = request.POST.get('coleccion_id')

        tweet = get_object_or_404(Tweet, id=tweet_id)
        coleccion = get_object_or_404(Coleccion, id=coleccion_id, usuario=request.user)

        coleccion.tweets.add(tweet)
        return JsonResponse({'success': True, 'message': 'Tweet agregado correctamente.'})

    elif request.method == 'GET':
        colecciones = list(Coleccion.objects.filter(usuario=request.user).values('id', 'nombre'))
        return JsonResponse({'colecciones': colecciones})

    return JsonResponse({'success': False, 'message': 'Método no permitido.'}, status=400)
#fin de vista ajax para agregar tweets a colecciones