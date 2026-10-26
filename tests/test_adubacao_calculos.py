import unittest
from solo_validacoes import calcular_dose_fertilizante

class TestCalculoDoseFertilizante(unittest.TestCase):
    def test_converte_alvo_em_dose_e_total(self):
        dose, total = calcular_dose_fertilizante(60, 20, 2.5)
        self.assertAlmostEqual(dose, 300.0)
        self.assertAlmostEqual(total, 750.0)

    def test_meta_zero_nao_exige_teor(self):
        self.assertEqual(calcular_dose_fertilizante(0, 0, 3), (0.0, 0.0))

    def test_rejeita_nutriente_ausente_no_produto(self):
        with self.assertRaises(ValueError):
            calcular_dose_fertilizante(20, 0, 1)

    def test_rejeita_valores_invalidos(self):
        for args in [(-1, 20, 1), (10, 101, 1), (10, 20, 0)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                calcular_dose_fertilizante(*args)

if __name__ == '__main__':
    unittest.main()
