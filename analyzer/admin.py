from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User  # Utiliser cela si vous n'avez pas de modèle utilisateur personnalisé

# Enregistrez uniquement si personnalisé
# from .models import User # Si vous avez un modèle utilisateur personnalisé

# admin.site.unregister(User)  # Supprimez cette ligne si elle cause des erreurs

admin.site.register(User, UserAdmin)  # Enregistrez-le seulement s'il est personnalisé