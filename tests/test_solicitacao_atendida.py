import os
import tempfile
import unittest
import bancoDB

class SolicitacaoAtendidaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.original = bancoDB.DATABASE
        bancoDB.DATABASE = os.path.join(self.tmp.name, "agrocalc_test.db")
        bancoDB.criar_banco_de_dados()

    def tearDown(self):
        bancoDB.DATABASE = self.original
        self.tmp.cleanup()

    def test_mensagem_e_status_sao_atualizados(self):
        con = bancoDB.conectar_banco()
        produtor_id = con.execute("INSERT INTO produtores(nome) VALUES (?)", ("Produtor teste",)).lastrowid
        solic_id = con.execute("INSERT INTO solicitacoes_relatorio(produtor_id,motivos) VALUES (?,?)", (produtor_id,"Relatório muito antigo")).lastrowid
        # A função aceita o ID de recomendação já criado; a FK exige um relatório válido.
        prop_id = con.execute("INSERT INTO propriedades(produtor_id,nome_propriedade) VALUES (?,?)", (produtor_id,"Terra")).lastrowid
        talhao_id = con.execute("INSERT INTO talhoes(propriedade_id,nome_talhao,area_ha) VALUES (?,?,?)", (prop_id,"Talhão",1)).lastrowid
        cultura_id = con.execute("INSERT INTO culturas(nome_cultura,v2_alvo) VALUES (?,?)", ("Soja",60)).lastrowid
        rec_id = con.execute("INSERT INTO recomendacoes_solo(talhao_id,cultura_id) VALUES (?,?)", (talhao_id,cultura_id)).lastrowid
        bancoDB.marcar_solicitacao_atendida(con, solic_id, rec_id)
        con.commit()
        s = con.execute("SELECT status, mensagem_produtor, recomendacao_id FROM solicitacoes_relatorio WHERE id=?", (solic_id,)).fetchone()
        con.close()
        self.assertEqual(s["status"], "Atendida")
        self.assertEqual(s["mensagem_produtor"], "Solicitação atendida: Relatório atualizado com sucesso!")
        self.assertEqual(s["recomendacao_id"], rec_id)

if __name__ == "__main__": unittest.main()
