from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Rol, UsuarioXRol


class UsuarioXRolInline(admin.TabularInline):
    model = UsuarioXRol
    extra = 0


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    inlines = [UsuarioXRolInline]


@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion")
    search_fields = ("nombre",)
