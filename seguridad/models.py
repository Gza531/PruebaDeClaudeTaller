from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils import timezone


class Usuario(AbstractUser):
    """
    Usuario del sistema (tabla "usuarios").

    Hereda de AbstractUser para seguir usando el login y el admin de Django,
    pero sus columnas principales se llaman como en la base de datos:
    username -> nombre_usuario, password -> contrasena_hash,
    is_active -> estado, date_joined -> fecha_alta.
    """

    id_usuario = models.AutoField(primary_key=True)

    username = models.CharField(
        "nombre de usuario",
        max_length=30,
        unique=True,
        db_column="nombre_usuario",
        validators=[UnicodeUsernameValidator()],
        error_messages={"unique": "Ya existe un usuario con ese nombre."},
    )

    password = models.CharField(
        "contraseña",
        max_length=255,
        db_column="contrasena_hash"
    )

    is_active = models.BooleanField(
        "activo",
        default=True,
        db_column="estado"
    )

    date_joined = models.DateTimeField(
        "fecha de alta",
        default=timezone.now,
        db_column="fecha_alta"
    )

    class Meta:
        db_table = "usuarios"

    def __str__(self):
        return self.username


class Rol(models.Model):
    id_rol = models.AutoField(primary_key=True)

    nombre = models.CharField(
        max_length=50,
        unique=True
    )

    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    # Lista de permisos del rol, ej: ["stock", "movimientos_stock", "productos.ver"]
    permisos = models.JSONField(default=list)

    usuarios = models.ManyToManyField(
        Usuario,
        through="UsuarioXRol",
        related_name="roles"
    )

    class Meta:
        db_table = "roles"
        verbose_name_plural = "roles"

    def __str__(self):
        return self.nombre


class UsuarioXRol(models.Model):
    id_usuarioxrol = models.AutoField(primary_key=True)

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column="id_usuario"
    )

    rol = models.ForeignKey(
        Rol,
        on_delete=models.PROTECT,
        db_column="id_rol"
    )

    fecha_asignacion = models.DateField(default=timezone.localdate)

    estado = models.BooleanField(default=True)

    class Meta:
        db_table = "usuarios_x_roles"
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "rol"],
                name="uq_usuario_rol"
            ),
        ]

    def __str__(self):
        return f"{self.usuario} - {self.rol}"
