"""
Operaciones sobre el stock.

La cantidad de un registro de Stock nunca se edita a mano: siempre se cambia
registrando un MovimientoStock con estas funciones, así queda el historial de
quién movió qué y por qué.
"""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import Stock, MovimientoStock


@transaction.atomic
def registrar_movimiento(stock, tipo_movimiento, cantidad, usuario,
                         motivo=None, referencia=None, compra=None):
    """
    Registra un movimiento y actualiza la cantidad del stock.

    - entrada / reposicion: suman unidades.
    - salida / ajuste: restan unidades (ej: unidad dañada, faltante).

    Lanza ValidationError si la cantidad no es positiva o si el movimiento
    dejaría el stock en negativo.
    """
    if tipo_movimiento not in MovimientoStock.TipoMovimiento.values:
        raise ValidationError(f"Tipo de movimiento inválido: {tipo_movimiento}.")

    if cantidad is None or cantidad <= 0:
        raise ValidationError("La cantidad debe ser mayor a cero.")

    # Bloqueamos la fila para que dos movimientos simultáneos no se pisen.
    stock = Stock.objects.select_for_update().get(pk=stock.pk)

    es_ingreso = tipo_movimiento in MovimientoStock.TIPOS_INGRESO
    variacion = cantidad if es_ingreso else -cantidad

    if stock.cantidad_actual + variacion < 0:
        raise ValidationError(
            f"Stock insuficiente de {stock.producto} en {stock.ubicacion}: "
            f"hay {stock.cantidad_actual} y se quieren descontar {cantidad}."
        )

    Stock.objects.filter(pk=stock.pk).update(
        cantidad_actual=F("cantidad_actual") + variacion,
        ultima_actualizacion=timezone.now(),
    )

    return MovimientoStock.objects.create(
        stock=stock,
        tipo_movimiento=tipo_movimiento,
        cantidad=cantidad,
        usuario=usuario,
        motivo=motivo,
        referencia=referencia,
        compra=compra,
    )


@transaction.atomic
def transferir(producto, desde, hacia, cantidad, usuario,
               motivo="Reposición", referencia=None):
    """
    Pasa unidades de una ubicación a otra (ej: de Depósito a Sucursal).

    Genera una "salida" en el origen y una "reposicion" en el destino, con la
    misma referencia. Si el destino todavía no tiene registro de stock, se crea.
    """
    if desde == hacia:
        raise ValidationError("El origen y el destino deben ser distintos.")

    try:
        origen = Stock.objects.get(producto=producto, ubicacion=desde)
    except Stock.DoesNotExist:
        raise ValidationError(f"{producto} no tiene stock en {desde}.")

    destino, _ = Stock.objects.get_or_create(producto=producto, ubicacion=hacia)

    salida = registrar_movimiento(
        origen, MovimientoStock.TipoMovimiento.SALIDA, cantidad, usuario,
        motivo=motivo, referencia=referencia
    )
    reposicion = registrar_movimiento(
        destino, MovimientoStock.TipoMovimiento.REPOSICION, cantidad, usuario,
        motivo=motivo, referencia=referencia
    )
    return salida, reposicion
