import os
import tempfile
import unittest
import sqlite3
import bancoDB

class DatabaseTriggerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_database = bancoDB.DATABASE
        bancoDB.DATABASE = os.path.join(self.tmp.name, 'test.db')
        bancoDB.criar_banco_de_dados()

    def tearDown(self):
        bancoDB.DATABASE = self.old_database
        self.tmp.cleanup()

    def test_insert_recommendation_writes_audit_trigger(self):
        con = bancoDB.conectar_banco()
        producer = con.execute("INSERT INTO produtores(nome) VALUES ('Produtor teste')").lastrowid
        prop = con.execute("INSERT INTO propriedades(produtor_id,nome_propriedade) VALUES (?,?)", (producer, 'Terra teste')).lastrowid
        talhao = con.execute("INSERT INTO talhoes(propriedade_id,nome_talhao,area_ha) VALUES (?,?,?)", (prop, 'Talhão teste', 1.0)).lastrowid
        cultura = con.execute("INSERT INTO culturas(nome_cultura,v2_alvo) VALUES (?,?)", ('Soja', 60)).lastrowid
        rec = con.execute("INSERT INTO recomendacoes_solo(talhao_id,cultura_id) VALUES (?,?)", (talhao, cultura)).lastrowid
        con.commit()
        audit = con.execute("SELECT acao,entidade,entidade_id FROM auditoria WHERE entidade='recomendacoes_solo' ORDER BY id DESC LIMIT 1").fetchone()
        con.close()
        self.assertEqual(tuple(audit), ('INSERT_TRIGGER', 'recomendacoes_solo', rec))

if __name__ == '__main__':
    unittest.main()
