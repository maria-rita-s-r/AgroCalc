"""Verificações estáticas dos contratos HTTP (não substituem teste no navegador)."""
import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class CrudContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tree = ast.parse((ROOT / "app.py").read_text(encoding="utf-8"))
        cls.routes = {}
        for node in ast.walk(cls.tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr == "route":
                    path = ast.literal_eval(dec.args[0]) if dec.args else ""
                    methods = {"GET"}
                    for kw in dec.keywords:
                        if kw.arg == "methods":
                            methods = set(ast.literal_eval(kw.value))
                    cls.routes[node.name] = (path, methods)

    def test_edicoes_usam_put(self):
        for endpoint in ("editar_produtor", "editar_propriedade", "editar_talhao", "editar_cultura", "editar_calcario", "editar_fertilizante", "produtor_editar_terra", "produtor_editar_talhao", "produtor_editar_cultura"):
            with self.subTest(endpoint=endpoint):
                self.assertIn("PUT", self.routes[endpoint][1])

    def test_exclusoes_usam_delete(self):
        for endpoint in ("excluir_produtor", "excluir_propriedade", "excluir_talhao", "excluir_cultura", "excluir_calcario", "excluir_fertilizante", "produtor_excluir_terra", "produtor_excluir_talhao", "produtor_excluir_cultura"):
            with self.subTest(endpoint=endpoint):
                self.assertEqual(self.routes[endpoint][1], {"DELETE"})

    def test_criacao_usa_post_e_listagem_get(self):
        for endpoint in ("novo_produtor", "nova_propriedade", "novo_talhao", "nova_cultura", "novo_calcario", "novo_fertilizante"):
            with self.subTest(endpoint=endpoint):
                self.assertIn("POST", self.routes[endpoint][1])
        for endpoint in ("produtores", "propriedades", "talhoes", "culturas", "calcarios", "fertilizantes"):
            with self.subTest(endpoint=endpoint):
                self.assertIn("GET", self.routes[endpoint][1])

if __name__ == "__main__":
    unittest.main()
