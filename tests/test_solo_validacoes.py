import unittest
from datetime import date, timedelta

from solo_validacoes import normalizar_unidades_solo, validar_data_laudo


class TestConversoesSolo(unittest.TestCase):
    def test_potassio_mg_dm3_para_cmolc_dm3(self):
        valores = {"k": 18.0}
        normalizar_unidades_solo(valores, {"k": "mg/dm3"})
        self.assertAlmostEqual(valores["k"], 18.0 / 391.0, places=10)
        self.assertAlmostEqual(valores["k"], 0.0460358056, places=9)

    def test_potassio_ja_em_cmolc_nao_e_convertido(self):
        valores = {"k": 0.0468}
        normalizar_unidades_solo(valores, {"k": "cmolc/dm3"})
        self.assertAlmostEqual(valores["k"], 0.0468)


class TestDataLaudo(unittest.TestCase):
    def test_data_ausente_rejeitada(self):
        self.assertIn("Informe a data", validar_data_laudo("", hoje=date(2026, 10, 26)))

    def test_data_futura_rejeitada(self):
        self.assertIn("futuro", validar_data_laudo("2026-10-27", hoje=date(2026, 10, 26)))

    def test_laudo_com_mais_de_dois_anos_rejeitado(self):
        antiga = (date(2026, 10, 26) - timedelta(days=731)).isoformat()
        self.assertIn("mais de dois anos", validar_data_laudo(antiga, hoje=date(2026, 10, 26)))

    def test_laudo_recente_aceito(self):
        recente = (date(2026, 10, 26) - timedelta(days=30)).isoformat()
        self.assertIsNone(validar_data_laudo(recente, hoje=date(2026, 10, 26)))


if __name__ == "__main__":
    unittest.main()
