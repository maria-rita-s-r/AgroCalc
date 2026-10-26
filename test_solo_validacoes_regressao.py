import unittest
from solo_validacoes import normalizar_unidades_solo

class TestConversaoPotassio(unittest.TestCase):
    def test_k_18_mg_dm3(self):
        valores = {"k": 18.0}
        normalizar_unidades_solo(valores, {"k": "mg/dm3"})
        self.assertAlmostEqual(valores["k"], 18 / 391, places=8)
        self.assertAlmostEqual(valores["k"], 0.0460358, places=6)

    def test_k_ja_em_cmolc_nao_converte(self):
        valores = {"k": 0.046}
        normalizar_unidades_solo(valores, {"k": "cmolc/dm3"})
        self.assertEqual(valores["k"], 0.046)

if __name__ == "__main__":
    unittest.main()
