import os
import sqlite3
import unittest
from fastapi.testclient import TestClient
from main import app, get_db

TEST_DATABASE = "lunita_test.db"

# Sobrescribir la dependencia get_db para apuntar a la base de datos de pruebas
def get_test_db():
    conn = sqlite3.connect(TEST_DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

app.dependency_overrides[get_db] = get_test_db

class TestLunitaAPI(unittest.TestCase):
    def setUp(self):
        # Crear base de datos de prueba
        conn = sqlite3.connect(TEST_DATABASE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS registros_diarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT UNIQUE NOT NULL,
                dia_del_ciclo INTEGER NOT NULL,
                flujo TEXT NOT NULL,
                animo TEXT NOT NULL,
                sintomas TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
        self.client = TestClient(app)

    def tearDown(self):
        # Eliminar base de datos de prueba
        if os.path.exists(TEST_DATABASE):
            try:
                os.remove(TEST_DATABASE)
            except PermissionError:
                pass  # Ignorar si hay conexiones pendientes que se cierran un poco después

    def test_raiz(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("¡Te damos la bienvenida a Lunita API!", data["mensaje"])
        self.assertIn("registros", data["endpoints"])

    def test_crear_registro(self):
        payload = {
            "fecha": "2026-06-16",
            "dia_del_ciclo": 3,
            "flujo": "Moderado",
            "animo": "Tranquila",
            "sintomas": "Leve dolor abdominal"
        }
        response = self.client.post("/api/registros", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIsNotNone(data["id"])
        self.assertEqual(data["fecha"], "2026-06-16")
        self.assertEqual(data["dia_del_ciclo"], 3)
        self.assertEqual(data["flujo"], "Moderado")

        # Intentar crear duplicado (debe fallar con 400)
        response_dup = self.client.post("/api/registros", json=payload)
        self.assertEqual(response_dup.status_code, 400)
        self.assertIn("Ya existe un registro", response_dup.json()["detail"])

    def test_obtener_y_listar_registros(self):
        payload = {
            "fecha": "2026-06-15",
            "dia_del_ciclo": 2,
            "flujo": "Abundante",
            "animo": "Cansada",
            "sintomas": "Cólicos"
        }
        self.client.post("/api/registros", json=payload)

        # Listar registros
        response = self.client.get("/api/registros")
        self.assertEqual(response.status_code, 200)
        registros = response.json()
        self.assertTrue(len(registros) >= 1)
        self.assertEqual(registros[0]["fecha"], "2026-06-15")

        # Obtener por ID
        reg_id = registros[0]["id"]
        response_get = self.client.get(f"/api/registros/{reg_id}")
        self.assertEqual(response_get.status_code, 200)
        self.assertEqual(response_get.json()["animo"], "Cansada")

        # Obtener ID inexistente (debe dar 404)
        response_get_404 = self.client.get("/api/registros/999")
        self.assertEqual(response_get_404.status_code, 404)

    def test_actualizar_registro(self):
        payload = {
            "fecha": "2026-06-14",
            "dia_del_ciclo": 1,
            "flujo": "Ligero",
            "animo": "Feliz",
            "sintomas": "Ninguno"
        }
        create_resp = self.client.post("/api/registros", json=payload)
        reg_id = create_resp.json()["id"]

        # Actualizar
        update_payload = {
            "flujo": "Moderado",
            "animo": "Radiante"
        }
        response_put = self.client.put(f"/api/registros/{reg_id}", json=update_payload)
        self.assertEqual(response_put.status_code, 200)
        data = response_put.json()
        self.assertEqual(data["flujo"], "Moderado")
        self.assertEqual(data["animo"], "Radiante")
        self.assertEqual(data["fecha"], "2026-06-14")

    def test_eliminar_registro(self):
        payload = {
            "fecha": "2026-06-13",
            "dia_del_ciclo": 28,
            "flujo": "Ninguno",
            "animo": "Tranquila",
            "sintomas": "Sensibilidad"
        }
        create_resp = self.client.post("/api/registros", json=payload)
        reg_id = create_resp.json()["id"]

        # Eliminar
        response_delete = self.client.delete(f"/api/registros/{reg_id}")
        self.assertEqual(response_delete.status_code, 200)
        self.assertIn("eliminado exitosamente", response_delete.json()["mensaje"])

        # Intentar eliminar de nuevo (404)
        response_delete_404 = self.client.delete(f"/api/registros/{reg_id}")
        self.assertEqual(response_delete_404.status_code, 404)

    def test_endpoint_consejos(self):
        # Menstrual (1-5)
        resp = self.client.get("/api/consejos/3")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["fase"], "Menstrual")
        self.assertIn("alimentacion", data["consejos"])
        self.assertIn("ejercicio", data["consejos"])

        # Folicular (6-13)
        resp = self.client.get("/api/consejos/8")
        data = resp.json()
        self.assertEqual(data["fase"], "Folicular")

        # Ovulación (14-16)
        resp = self.client.get("/api/consejos/15")
        data = resp.json()
        self.assertEqual(data["fase"], "Ovulación")

        # Lútea (17-28+)
        resp = self.client.get("/api/consejos/22")
        data = resp.json()
        self.assertEqual(data["fase"], "Lútea")

        # Día inválido (menor a 1)
        resp = self.client.get("/api/consejos/0")
        self.assertEqual(resp.status_code, 400)

if __name__ == "__main__":
    unittest.main()
