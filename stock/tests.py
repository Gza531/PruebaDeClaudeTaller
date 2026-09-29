from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from catalogo.models import Categoria, Marca, Producto
from seguridad.models import Usuario
from .models import Stock, MovimientoStock
from .services import registrar_movimiento, transferir


class StockTestMixin:

    def setUp(self):
        self.usuario = Usuario.objects.create_user("stock", password="clave-segura-123")
        self.producto = Producto.objects.create(
            nombre="Kaiak Clásico EDT",
            marca=Marca.objects.create(nombre="Natura"),
            categoria=Categoria.objects.create(nombre="Perfumes"),
            origen=Producto.OrigenProducto.IMPORTADO,
            precio_venta=38500,
        )
        self.deposito = Stock.objects.create(
            producto=self.producto,
            ubicacion=Stock.Ubicacion.DEPOSITO,
            stock_minimo=5,
        )


class RegistrarMovimientoTests(StockTestMixin, TestCase):

    def test_entrada_suma_y_salida_resta(self):
        registrar_movimiento(self.deposito, "entrada", 10, self.usuario)
        registrar_movimiento(self.deposito, "salida", 3, self.usuario)

        self.deposito.refresh_from_db()
        self.assertEqual(self.deposito.cantidad_actual, 7)
        self.assertEqual(self.deposito.movimientos.count(), 2)

    def test_ajuste_resta(self):
        registrar_movimiento(self.deposito, "entrada", 4, self.usuario)
        registrar_movimiento(self.deposito, "ajuste", 1, self.usuario, motivo="Unidad dañada")

        self.deposito.refresh_from_db()
        self.assertEqual(self.deposito.cantidad_actual, 3)

    def test_no_permite_stock_negativo(self):
        registrar_movimiento(self.deposito, "entrada", 2, self.usuario)

        with self.assertRaises(ValidationError):
            registrar_movimiento(self.deposito, "salida", 3, self.usuario)

        self.deposito.refresh_from_db()
        self.assertEqual(self.deposito.cantidad_actual, 2)
        self.assertEqual(self.deposito.movimientos.count(), 1)

    def test_cantidad_debe_ser_positiva(self):
        with self.assertRaises(ValidationError):
            registrar_movimiento(self.deposito, "entrada", 0, self.usuario)

    def test_bajo_minimo(self):
        registrar_movimiento(self.deposito, "entrada", 5, self.usuario)
        self.deposito.refresh_from_db()
        self.assertTrue(self.deposito.bajo_minimo)

        registrar_movimiento(self.deposito, "entrada", 1, self.usuario)
        self.deposito.refresh_from_db()
        self.assertFalse(self.deposito.bajo_minimo)


class TransferirTests(StockTestMixin, TestCase):

    def test_transferir_de_deposito_a_sucursal(self):
        registrar_movimiento(self.deposito, "entrada", 10, self.usuario)

        salida, reposicion = transferir(
            self.producto, Stock.Ubicacion.DEPOSITO, Stock.Ubicacion.SUCURSAL,
            4, self.usuario, referencia="REP-0001"
        )

        self.deposito.refresh_from_db()
        sucursal = Stock.objects.get(producto=self.producto, ubicacion=Stock.Ubicacion.SUCURSAL)
        self.assertEqual(self.deposito.cantidad_actual, 6)
        self.assertEqual(sucursal.cantidad_actual, 4)
        self.assertEqual(salida.tipo_movimiento, "salida")
        self.assertEqual(reposicion.tipo_movimiento, "reposicion")
        self.assertEqual(reposicion.referencia, "REP-0001")

    def test_transferencia_sin_stock_no_deja_movimientos(self):
        with self.assertRaises(ValidationError):
            transferir(
                self.producto, Stock.Ubicacion.DEPOSITO, Stock.Ubicacion.SUCURSAL,
                1, self.usuario
            )
        self.assertFalse(MovimientoStock.objects.exists())


class StockAPITests(StockTestMixin, TestCase):

    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def test_listar_stock(self):
        respuesta = self.client.get("/api/stock/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data["results"][0]["producto_nombre"], "Kaiak Clásico EDT")

    def test_no_se_puede_editar_la_cantidad_directamente(self):
        respuesta = self.client.patch(
            f"/api/stock/{self.deposito.pk}/", {"cantidad_actual": 99}, format="json"
        )
        self.assertEqual(respuesta.status_code, 200)
        self.deposito.refresh_from_db()
        self.assertEqual(self.deposito.cantidad_actual, 0)

    def test_crear_movimiento_requiere_login(self):
        respuesta = self.client.post("/api/movimientos-stock/", {
            "stock": self.deposito.pk, "tipo_movimiento": "entrada", "cantidad": 5,
        }, format="json")
        self.assertIn(respuesta.status_code, (401, 403))

    def test_crear_movimiento_actualiza_stock(self):
        self.client.force_authenticate(self.usuario)
        respuesta = self.client.post("/api/movimientos-stock/", {
            "stock": self.deposito.pk, "tipo_movimiento": "entrada", "cantidad": 5,
            "motivo": "Ingreso por compra",
        }, format="json")

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.data["usuario"], self.usuario.pk)
        self.deposito.refresh_from_db()
        self.assertEqual(self.deposito.cantidad_actual, 5)

    def test_movimiento_sin_stock_suficiente_devuelve_400(self):
        self.client.force_authenticate(self.usuario)
        respuesta = self.client.post("/api/movimientos-stock/", {
            "stock": self.deposito.pk, "tipo_movimiento": "salida", "cantidad": 1,
        }, format="json")
        self.assertEqual(respuesta.status_code, 400)

    def test_bajo_minimo_y_transferir(self):
        self.client.force_authenticate(self.usuario)
        registrar_movimiento(self.deposito, "entrada", 8, self.usuario)

        respuesta = self.client.post("/api/stock/transferir/", {
            "producto": self.producto.pk, "desde": "Depósito", "hacia": "Sucursal", "cantidad": 4,
        }, format="json")
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(len(respuesta.data), 2)

        respuesta = self.client.get("/api/stock/bajo-minimo/")
        ids = [fila["id_stock"] for fila in respuesta.data["results"]]
        self.assertIn(self.deposito.pk, ids)  # quedaron 4 con mínimo 5
