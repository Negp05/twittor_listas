from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Tweet, Comment, UserProfile, Lista, Coleccion

# --- Configuración base para estilos con Tailwind ---
BASE_INPUT = {'class': 'input'}
BASE_AREA = {'class': 'input min-h-[100px]'}
BASE_FILE = {'class': 'file-input'}

# --- Formulario de Tweets ---
class TweetForm(forms.ModelForm):
    class Meta:
        model = Tweet
        fields = ['content', 'image']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': '¿Qué está pasando? (280 máx.)', **BASE_AREA}),
            'image': forms.ClearableFileInput(attrs={**BASE_FILE})
        }

# --- Formulario de Comentarios ---
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Escribe una respuesta…', **BASE_AREA}),
        }

# --- Formulario de Registro de Usuario ---
class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'tucorreo@ejemplo.com', **BASE_INPUT}))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget = forms.TextInput(attrs={'placeholder': 'usuario', **BASE_INPUT})
        self.fields['password1'].widget = forms.PasswordInput(attrs={'placeholder': 'Contraseña', **BASE_INPUT})
        self.fields['password2'].widget = forms.PasswordInput(attrs={'placeholder': 'Confirmar contraseña', **BASE_INPUT})

# --- Formulario de Perfil ---
class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('bio', 'avatar')
        widgets = {
            'bio': forms.TextInput(attrs={'placeholder': 'Cuéntanos algo sobre ti', **BASE_INPUT}),
            'avatar': forms.ClearableFileInput(attrs={**BASE_FILE})
        }

# --- Formulario de Listas ---
class ListaForm(forms.ModelForm):
    """Formulario para crear y editar una Lista."""
    class Meta:
        model = Lista
        fields = ['nombre', 'descripcion', 'es_privada']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Nombre de la lista', **BASE_INPUT}),
            'descripcion': forms.Textarea(attrs={'placeholder': 'Descripción de la lista (opcional)', 'rows': 3, **BASE_AREA}),
            'es_privada': forms.CheckboxInput(),
        }

# --- Formulario de Colecciones ---
class ColeccionForm(forms.ModelForm):
    class Meta:
        model = Coleccion
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Nombre de la colección', **BASE_INPUT}),
            'descripcion': forms.Textarea(attrs={'placeholder': 'Descripción (opcional)', 'rows': 3, **BASE_AREA}),
        }
