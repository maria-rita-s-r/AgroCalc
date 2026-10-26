from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
import os
import secrets
import hmac
import sqlite3
import math
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
# Importa do seu arquivo bancoDB.py
from bancoDB import conectar_banco, criar_banco_de_dados, is_integrity_error, marcar_solicitacao_atendida
from solo_validacoes import normalizar_unidades_solo, validar_data_laudo, calcular_dose_fertilizante

app = Flask(__name__)
# Em produção, defina AGROCALC_SECRET_KEY como variável de ambiente.
app.secret_key = os.environ.get("AGROCALC_SECRET_KEY") or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=os.environ.get("FLASK_HTTPS_ONLY", "0") == "1")



@app.context_processor
def disponibilizar_csrf():
    """Disponibiliza um token CSRF para os formulários que alteram dados."""
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return {"csrf_token": session["csrf_token"]}

def validar_csrf():
    """Bloqueia POSTs sem token válido, reduzindo risco de CSRF."""
    enviado = request.form.get("csrf_token", "")
    esperado = session.get("csrf_token", "")
    if not esperado or not enviado or not hmac.compare_digest(enviado, esperado):
        abort(400, description="Token de segurança inválido. Atualize a página e tente novamente.")

# Inicializa o banco ao iniciar o aplicativo
criar_banco_de_dados()

# Cria a conta inicial do agrônomo uma única vez. Em produção, configure estas variáveis.
def garantir_conta_agronomo():
    email = os.environ.get("AGROCALC_ADMIN_EMAIL", "admin@agrocalc.local").strip().lower()
    senha = os.environ.get("AGROCALC_ADMIN_PASSWORD", "AgroCalc@123")
    conexao = conectar_banco()
    existe = conexao.execute("SELECT id FROM usuarios WHERE email = ?", (email,)).fetchone()
    if not existe:
        conexao.execute("INSERT INTO usuarios (nome,email,senha_hash,papel) VALUES (?,?,?,'agronomo')",
                         ("Agrônomo responsável", email, generate_password_hash(senha)))
        conexao.commit()
    conexao.close()

garantir_conta_agronomo()

@app.before_request
def proteger_rotas():
    """Aplica autorização por perfil em todas as rotas privadas."""
    endpoint = request.endpoint or ""
    publicas = {"index", "login", "logout", "static"}
    if endpoint in publicas or endpoint.startswith("static"):
        return None
    usuario = session.get("usuario")
    if not usuario:
        return redirect(url_for("index"))

    agronomo_only = {
        "painel_agronomo", "produtores", "novo_produtor", "editar_produtor", "excluir_produtor",
        "propriedades", "nova_propriedade", "editar_propriedade", "excluir_propriedade",
        "talhoes", "novo_talhao", "editar_talhao", "excluir_talhao",
        "culturas", "nova_cultura", "editar_cultura", "excluir_cultura",
        "calcarios", "novo_calcario", "editar_calcario", "excluir_calcario",
        "fertilizantes", "novo_fertilizante", "editar_fertilizante", "excluir_fertilizante",
        "solicitacoes_admin", "iniciar_atendimento_solicitacao", "marcar_novidade_vista",
        "calculadora_solo", "formulario_solo", "calcular_solo", "resultado_solo",
        "recomendacoes_solo", "documento_solo"
    }
    produtor_only = {
        "painel_produtor", "produtor_relatorio_detalhado", "produtor_nova_terra", "produtor_editar_terra",
        "produtor_excluir_terra", "produtor_novo_talhao", "produtor_editar_talhao", "produtor_excluir_talhao",
        "produtor_nova_cultura", "produtor_editar_cultura", "produtor_excluir_cultura",
        "produtor_calcular", "solicitar_relatorio", "produtor_novo_calcario"
    }
    papel = usuario.get("papel")
    if endpoint in agronomo_only and papel != "agronomo":
        abort(403)
    if endpoint in produtor_only and papel != "produtor":
        abort(403)
    return None

@app.context_processor
def contexto_usuario():
    return {"usuario_atual": session.get("usuario")}


@app.route("/")
def index():
    if session.get("usuario"):
        return redirect(url_for("painel_agronomo" if session["usuario"]["papel"] == "agronomo" else "painel_produtor"))
    return render_template("index.html")

@app.route("/entrar/<tipo>", methods=["GET", "POST"])
def login(tipo):
    if tipo not in ("produtor", "admin"):
        abort(404)
    if request.method == "POST":
        validar_csrf()
        email = (request.form.get("email") or "").strip().lower()
        senha = request.form.get("senha") or ""
        conexao = conectar_banco()
        usuario = conexao.execute("SELECT * FROM usuarios WHERE email = ? AND ativo = TRUE", (email,)).fetchone()
        conexao.close()
        papel_esperado = "agronomo" if tipo == "admin" else "produtor"
        if not usuario or usuario["papel"] != papel_esperado or not check_password_hash(usuario["senha_hash"], senha):
            flash("E-mail, senha ou tipo de acesso inválido.", "warning")
            return render_template("auth/login.html", tipo=tipo)
        session.clear()
        session["usuario"] = {"id": usuario["id"], "nome": usuario["nome"], "email": usuario["email"],
                               "papel": usuario["papel"], "produtor_id": usuario["produtor_id"]}
        session["csrf_token"] = secrets.token_urlsafe(32)
        return redirect(url_for("painel_agronomo" if tipo == "admin" else "painel_produtor"))
    return render_template("auth/login.html", tipo=tipo)

@app.route("/sair", methods=["POST"])
def logout():
    validar_csrf()
    session.clear()
    flash("Você saiu da sua conta.", "success")
    return redirect(url_for("index"))

@app.route("/agronomo")
def painel_agronomo():
    if session.get("usuario", {}).get("papel") != "agronomo": abort(403)
    conexao = conectar_banco()
    dados = {
        "produtores": conexao.execute("SELECT COUNT(*) n FROM produtores").fetchone()["n"],
        "terras": conexao.execute("SELECT COUNT(*) n FROM propriedades").fetchone()["n"],
        "talhoes": conexao.execute("SELECT COUNT(*) n FROM talhoes").fetchone()["n"],
        "relatorios": conexao.execute("SELECT COUNT(*) n FROM recomendacoes_solo").fetchone()["n"],
        "produtores_atendidos": conexao.execute("SELECT COUNT(DISTINCT p.produtor_id) n FROM recomendacoes_solo r JOIN talhoes t ON t.id=r.talhao_id JOIN propriedades p ON p.id=t.propriedade_id").fetchone()["n"],
        "solicitacoes_atendidas": conexao.execute("SELECT COUNT(*) n FROM solicitacoes_relatorio WHERE status='Atendida'").fetchone()["n"],
        "solicitacoes_pendentes": conexao.execute("SELECT COUNT(*) n FROM solicitacoes_relatorio WHERE status!='Atendida'").fetchone()["n"]}
    solicitacoes = conexao.execute("SELECT s.*, p.nome AS produtor_nome, p.id AS produtor_codigo FROM solicitacoes_relatorio s JOIN produtores p ON p.id=s.produtor_id ORDER BY CASE s.status WHEN 'Pendente' THEN 0 WHEN 'Em atendimento' THEN 1 ELSE 2 END, s.id DESC LIMIT 30").fetchall()
    novidades = conexao.execute("SELECT n.*, p.nome AS produtor_nome FROM novidades_produtor n JOIN produtores p ON p.id=n.produtor_id ORDER BY n.visto_admin ASC, n.id DESC LIMIT 30").fetchall()
    conexao.close()
    return render_template("painel_agronomo.html", dados=dados, solicitacoes=solicitacoes, novidades=novidades)

@app.route("/produtor")
def painel_produtor():
    usuario = session.get("usuario")
    if not usuario or usuario.get("papel") != "produtor": abort(403)
    conexao = conectar_banco(); pid = usuario["produtor_id"]
    terras = conexao.execute("SELECT * FROM propriedades WHERE produtor_id=? ORDER BY nome_propriedade", (pid,)).fetchall()
    talhoes = conexao.execute("SELECT t.*, p.nome_propriedade FROM talhoes t JOIN propriedades p ON p.id=t.propriedade_id WHERE p.produtor_id=? ORDER BY t.nome_talhao", (pid,)).fetchall()
    culturas = conexao.execute("SELECT c.*, p.nome_propriedade FROM culturas c LEFT JOIN propriedades p ON p.id=c.propriedade_id WHERE c.propriedade_id IN (SELECT id FROM propriedades WHERE produtor_id=?) OR c.propriedade_id IS NULL ORDER BY c.nome_cultura", (pid,)).fetchall()
    relatorios = conexao.execute("SELECT r.*,t.nome_talhao,c.nome_cultura,p.nome_propriedade FROM recomendacoes_solo r JOIN talhoes t ON t.id=r.talhao_id JOIN propriedades p ON p.id=t.propriedade_id JOIN culturas c ON c.id=r.cultura_id WHERE p.produtor_id=? ORDER BY r.id DESC", (pid,)).fetchall()
    solicitacoes = conexao.execute("SELECT * FROM solicitacoes_relatorio WHERE produtor_id=? ORDER BY id DESC", (pid,)).fetchall()
    conexao.close()
    return render_template("painel_produtor.html", terras=terras, talhoes=talhoes, culturas=culturas, relatorios=relatorios, solicitacoes=solicitacoes)

@app.route("/produtor/relatorios/<int:recomendacao_id>")
def produtor_relatorio_detalhado(recomendacao_id):
    """Exibe ao produtor somente relatórios vinculados às próprias terras."""
    usuario = session.get("usuario")
    if not usuario or usuario.get("papel") != "produtor":
        abort(403)
    conexao = conectar_banco()
    relatorio = conexao.execute("""
        SELECT r.*, COALESCE(r.v2_alvo, c.v2_alvo) AS v2_alvo_relatorio, t.nome_talhao, t.area_ha, c.nome_cultura,
               p.nome_propriedade, p.municipio, p.estado,
               prod.nome AS produtor_nome, cc.nome_comercial, cc.tipo_calcario, cc.prnt_porcento AS prnt_porcento
        FROM recomendacoes_solo r
        JOIN talhoes t ON t.id = r.talhao_id
        JOIN propriedades p ON p.id = t.propriedade_id
        JOIN produtores prod ON prod.id = p.produtor_id
        JOIN culturas c ON c.id = r.cultura_id
        LEFT JOIN corretivos_calcario cc ON cc.id = r.calcario_id
        WHERE r.id = ? AND p.produtor_id = ?
    """, (recomendacao_id, usuario["produtor_id"])).fetchone()
    conexao.close()
    if not relatorio:
        abort(404)
    return render_template("auth/relatorio_detalhado.html", relatorio=relatorio)


@app.route("/produtor/terras/nova", methods=["GET", "POST"])
def produtor_nova_terra():
    u=session.get("usuario")
    if not u or u.get("papel") != "produtor": abort(403)
    if request.method == "POST":
        validar_csrf(); nome=(request.form.get("nome_propriedade") or "").strip(); municipio=(request.form.get("municipio") or "").strip(); estado=(request.form.get("estado") or "").strip()
        if not nome: flash("Informe o nome da terra.", "warning")
        else:
            con=conectar_banco(); cur=con.execute("INSERT INTO propriedades (produtor_id,nome_propriedade,municipio,estado) VALUES (?,?,?,?)",(u["produtor_id"],nome,municipio,estado)); con.execute("INSERT INTO novidades_produtor (produtor_id,tipo,entidade_id,descricao) VALUES (?,?,?,?)",(u["produtor_id"],"Terra",cur.lastrowid,f"Nova terra cadastrada: {nome}")); con.commit(); con.close(); flash("Terra cadastrada. O agrônomo foi notificado.","success"); return redirect(url_for("painel_produtor"))
    return render_template("auth/terra_form.html", terra=None)

@app.route("/produtor/terras/<int:id>/editar", methods=["GET", "PUT"])
def produtor_editar_terra(id):
    u=session.get("usuario");
    if not u or u.get("papel") != "produtor": abort(403)
    con=conectar_banco(); terra=con.execute("SELECT * FROM propriedades WHERE id=? AND produtor_id=?",(id,u["produtor_id"])).fetchone()
    if not terra: con.close(); abort(404)
    if request.method == "PUT":
        validar_csrf()
        validar_csrf(); nome=(request.form.get("nome_propriedade") or "").strip()
        if not nome: flash("O nome é obrigatório.","warning")
        else: con.execute("UPDATE propriedades SET nome_propriedade=?, municipio=?, estado=? WHERE id=? AND produtor_id=?",(nome,request.form.get("municipio"),request.form.get("estado"),id,u["produtor_id"])); con.commit(); con.close(); flash("Terra atualizada.","success"); return redirect(url_for("painel_produtor"))
    con.close(); return render_template("auth/terra_form.html",terra=terra)

@app.route("/produtor/terras/<int:id>/excluir", methods=["DELETE"])
def produtor_excluir_terra(id):
    u=session.get("usuario");
    if not u or u.get("papel") != "produtor": abort(403)
    validar_csrf(); con=conectar_banco(); con.execute("DELETE FROM propriedades WHERE id=? AND produtor_id=?",(id,u["produtor_id"])); con.commit(); con.close(); flash("Terra excluída.","success"); return redirect(url_for("painel_produtor"))

@app.route("/produtor/talhoes/novo", methods=["GET", "POST"])
def produtor_novo_talhao():
    u=session.get("usuario");
    if not u or u.get("papel") != "produtor": abort(403)
    con=conectar_banco(); terras=con.execute("SELECT id,nome_propriedade FROM propriedades WHERE produtor_id=? ORDER BY nome_propriedade",(u["produtor_id"],)).fetchall()
    if request.method == "POST":
        validar_csrf()
        try: area=float(request.form.get("area_ha",""))
        except ValueError: area=0
        pid=request.form.get("propriedade_id"); nome=(request.form.get("nome_talhao") or "").strip()
        permitido=con.execute("SELECT id FROM propriedades WHERE id=? AND produtor_id=?",(pid,u["produtor_id"])).fetchone()
        if not permitido or not nome or area<=0: flash("Confira a terra, o nome e a área maior que zero.","warning")
        else:
            cur=con.execute("INSERT INTO talhoes (propriedade_id,nome_talhao,area_ha) VALUES (?,?,?)",(pid,nome,area)); con.execute("INSERT INTO novidades_produtor (produtor_id,tipo,entidade_id,descricao) VALUES (?,?,?,?)",(u["produtor_id"],"Talhão",cur.lastrowid,f"Novo talhão cadastrado: {nome}")); con.commit(); con.close(); flash("Talhão cadastrado. O agrônomo foi notificado.","success"); return redirect(url_for("painel_produtor"))
    con.close(); return render_template("auth/talhao_form.html",talhao=None,terras=terras)

@app.route("/produtor/talhoes/<int:id>/editar", methods=["GET", "PUT"])
def produtor_editar_talhao(id):
    u=session.get("usuario");
    if not u or u.get("papel") != "produtor": abort(403)
    con=conectar_banco(); talhao=con.execute("SELECT t.* FROM talhoes t JOIN propriedades p ON p.id=t.propriedade_id WHERE t.id=? AND p.produtor_id=?",(id,u["produtor_id"])).fetchone(); terras=con.execute("SELECT id,nome_propriedade FROM propriedades WHERE produtor_id=?",(u["produtor_id"],)).fetchall()
    if not talhao: con.close(); abort(404)
    if request.method == "PUT":
        validar_csrf()
        validar_csrf(); nome=(request.form.get("nome_talhao") or "").strip(); pid=request.form.get("propriedade_id")
        try: area=float(request.form.get("area_ha",""))
        except ValueError: area=0
        permitido=con.execute("SELECT id FROM propriedades WHERE id=? AND produtor_id=?",(pid,u["produtor_id"])).fetchone()
        if not permitido or not nome or area<=0: flash("Confira os dados informados.","warning")
        else: con.execute("UPDATE talhoes SET propriedade_id=?,nome_talhao=?,area_ha=? WHERE id=?",(pid,nome,area,id)); con.commit(); con.close(); flash("Talhão atualizado.","success"); return redirect(url_for("painel_produtor"))
    con.close(); return render_template("auth/talhao_form.html",talhao=talhao,terras=terras)

@app.route("/produtor/talhoes/<int:id>/excluir", methods=["DELETE"])
def produtor_excluir_talhao(id):
    u=session.get("usuario");
    if not u or u.get("papel") != "produtor": abort(403)
    validar_csrf(); con=conectar_banco(); con.execute("DELETE FROM talhoes WHERE id IN (SELECT t.id FROM talhoes t JOIN propriedades p ON p.id=t.propriedade_id WHERE t.id=? AND p.produtor_id=?)",(id,u["produtor_id"])); con.commit(); con.close(); flash("Talhão excluído.","success"); return redirect(url_for("painel_produtor"))

@app.route("/produtor/culturas/nova", methods=["GET", "POST"])
def produtor_nova_cultura():
    u=session.get("usuario");
    if not u or u.get("papel") != "produtor": abort(403)
    con=conectar_banco(); terras=con.execute("SELECT id,nome_propriedade FROM propriedades WHERE produtor_id=?",(u["produtor_id"],)).fetchall()
    if request.method == "POST":
        validar_csrf(); nome=(request.form.get("nome_cultura") or "").strip(); pid=request.form.get("propriedade_id")
        try: v2=float(request.form.get("v2_alvo",""))
        except ValueError: v2=-1
        permitido=con.execute("SELECT id FROM propriedades WHERE id=? AND produtor_id=?",(pid,u["produtor_id"])).fetchone()
        if not permitido or not nome or not 0<=v2<=100: flash("Informe uma terra, cultura e V% alvo entre 0 e 100.","warning")
        else:
            cur=con.execute("INSERT INTO culturas (nome_cultura,v2_alvo,propriedade_id) VALUES (?,?,?)",(nome,v2,pid)); con.execute("INSERT INTO novidades_produtor (produtor_id,tipo,entidade_id,descricao) VALUES (?,?,?,?)",(u["produtor_id"],"Cultura",cur.lastrowid,f"Nova cultura cadastrada: {nome}")); con.commit(); con.close(); flash("Cultura cadastrada. O agrônomo foi notificado.","success"); return redirect(url_for("painel_produtor"))
    con.close(); return render_template("auth/cultura_form.html",cultura=None,terras=terras)

@app.route("/produtor/culturas/<int:id>/editar", methods=["GET", "PUT"])
def produtor_editar_cultura(id):
    u=session.get("usuario");
    if not u or u.get("papel") != "produtor": abort(403)
    con=conectar_banco(); cultura=con.execute("SELECT c.* FROM culturas c JOIN propriedades p ON p.id=c.propriedade_id WHERE c.id=? AND p.produtor_id=?",(id,u["produtor_id"])).fetchone(); terras=con.execute("SELECT id,nome_propriedade FROM propriedades WHERE produtor_id=?",(u["produtor_id"],)).fetchall()
    if not cultura: con.close(); abort(404)
    if request.method == "PUT":
        validar_csrf()
        validar_csrf(); nome=(request.form.get("nome_cultura") or "").strip(); pid=request.form.get("propriedade_id")
        try: v2=float(request.form.get("v2_alvo",""))
        except ValueError: v2=-1
        permitido=con.execute("SELECT id FROM propriedades WHERE id=? AND produtor_id=?",(pid,u["produtor_id"])).fetchone()
        if not permitido or not nome or not 0<=v2<=100: flash("Confira os dados da cultura.","warning")
        else: con.execute("UPDATE culturas SET nome_cultura=?,v2_alvo=?,propriedade_id=? WHERE id=?",(nome,v2,pid,id)); con.commit(); con.close(); flash("Cultura atualizada.","success"); return redirect(url_for("painel_produtor"))
    con.close(); return render_template("auth/cultura_form.html",cultura=cultura,terras=terras)

@app.route("/produtor/culturas/<int:id>/excluir", methods=["DELETE"])
def produtor_excluir_cultura(id):
    u=session.get("usuario");
    if not u or u.get("papel") != "produtor": abort(403)
    validar_csrf(); con=conectar_banco(); con.execute("DELETE FROM culturas WHERE id IN (SELECT c.id FROM culturas c JOIN propriedades p ON p.id=c.propriedade_id WHERE c.id=? AND p.produtor_id=?)",(id,u["produtor_id"])); con.commit(); con.close(); flash("Cultura excluída.","success"); return redirect(url_for("painel_produtor"))

@app.route("/produtor/calcular", methods=["GET", "POST"])
def produtor_calcular():
    """O produtor não gera relatórios; este endereço conduz à solicitação administrativa."""
    u = session.get("usuario")
    if not u or u.get("papel") != "produtor":
        abort(403)
    flash("Para obter um relatório atualizado, envie uma solicitação ao administrador.", "info")
    return redirect(url_for("solicitar_relatorio"))

@app.route("/produtor/solicitar-relatorio", methods=["GET", "POST"])
def solicitar_relatorio():
    u = session.get("usuario")
    if not u or u.get("papel") != "produtor":
        abort(403)
    opcoes = ["Novo cadastro de terras", "Novo cadastro de talhões", "Novo cadastro de culturas", "Novo calcário", "Relatório muito antigo (ou com a data expirada)", "Outro"]
    if request.method == "POST":
        validar_csrf()
        motivos = [m for m in opcoes if m in request.form.getlist("motivos")]
        outro = (request.form.get("outro") or "").strip()
        if not motivos:
            flash("Selecione pelo menos um motivo para a solicitação.", "warning")
        elif "Outro" in motivos and not outro:
            flash("Explique o motivo em até 500 caracteres.", "warning")
        elif len(outro) > 500:
            flash("A justificativa deve ter no máximo 500 caracteres.", "warning")
        else:
            con = conectar_banco()
            cur = con.execute("INSERT INTO solicitacoes_relatorio (produtor_id,motivos,outro) VALUES (?,?,?)", (u["produtor_id"], " | ".join(motivos), outro or None))
            con.execute("INSERT INTO auditoria (usuario_id,acao,entidade,entidade_id) VALUES (?,?,?,?)", (u["id"], "solicitacao_relatorio", "solicitacao_relatorio", cur.lastrowid))
            con.commit(); con.close()
            flash("Solicitação enviada ao administrador.", "success")
            return redirect(url_for("painel_produtor"))
    return render_template("auth/solicitar_relatorio.html", opcoes=opcoes)

@app.route("/admin/solicitacoes")
def solicitacoes_admin():
    if session.get("usuario", {}).get("papel") != "agronomo": abort(403)
    con = conectar_banco()
    solicitacoes = con.execute("SELECT s.*, p.nome AS produtor_nome FROM solicitacoes_relatorio s JOIN produtores p ON p.id=s.produtor_id ORDER BY s.id DESC").fetchall()
    con.close()
    return render_template("solicitacoes_admin.html", solicitacoes=solicitacoes)

@app.route("/admin/solicitacoes/<int:solicitacao_id>/atender", methods=["POST"])
def iniciar_atendimento_solicitacao(solicitacao_id):
    if session.get("usuario", {}).get("papel") != "agronomo": abort(403)
    validar_csrf()
    con = conectar_banco()
    sol = con.execute("SELECT * FROM solicitacoes_relatorio WHERE id=?", (solicitacao_id,)).fetchone()
    if not sol:
        con.close(); abort(404)
    if sol["status"] == "Atendida":
        con.close(); flash("Esta solicitação já foi atendida.", "info"); return redirect(url_for("solicitacoes_admin"))
    # Não pré-seleciona talhão nem cultura: o agrônomo deve escolher ambos.
    tem_talhao = con.execute("SELECT 1 FROM talhoes t JOIN propriedades p ON p.id=t.propriedade_id WHERE p.produtor_id=? LIMIT 1", (sol["produtor_id"],)).fetchone()
    # Culturas cadastradas para a propriedade do produtor e culturas gerais do catálogo
    # podem ser escolhidas. Não selecionar nenhuma automaticamente.
    tem_cultura = con.execute("SELECT 1 FROM culturas c LEFT JOIN propriedades p ON p.id=c.propriedade_id WHERE p.produtor_id=? OR c.propriedade_id IS NULL LIMIT 1", (sol["produtor_id"],)).fetchone()
    if not tem_talhao or not tem_cultura:
        con.close()
        flash("Antes de gerar o relatório, cadastre ao menos um talhão e uma cultura para este produtor.", "warning")
        return redirect(url_for("solicitacoes_admin"))
    con.execute("UPDATE solicitacoes_relatorio SET status='Em atendimento' WHERE id=? AND status!='Atendida'", (solicitacao_id,))
    con.commit()
    con.close()
    return redirect(url_for("calculadora_solo", solicitacao_id=solicitacao_id))

@app.route("/admin/novidades/<int:novidade_id>/vista", methods=["POST"])
def marcar_novidade_vista(novidade_id):
    if session.get("usuario", {}).get("papel") != "agronomo": abort(403)
    validar_csrf()
    con=conectar_banco(); con.execute("UPDATE novidades_produtor SET visto_admin=1 WHERE id=?", (novidade_id,)); con.commit(); con.close()
    return redirect(url_for("painel_agronomo"))

@app.route("/produtor/calcarios/novo", methods=["GET", "POST"])
def produtor_novo_calcario():
    u=session.get("usuario")
    if not u or u.get("papel") != "produtor": abort(403)
    if request.method == "POST":
        validar_csrf()
        nome=(request.form.get("nome_comercial") or "").strip()
        tipo=(request.form.get("tipo_calcario") or "").strip()
        try: prnt=float((request.form.get("prnt_porcento") or "").replace(",", "."))
        except ValueError: prnt=0
        if not nome or tipo not in {"calcítico","dolomítico","magnesiano","não informado"} or not 0 < prnt <= 100:
            flash("Informe o nome, o tipo e um PRNT entre 0 e 100%.", "warning")
        else:
            con=conectar_banco(); cur=con.execute("INSERT INTO corretivos_calcario (nome_comercial,prnt_porcento,tipo_calcario) VALUES (?,?,?)",(nome,prnt,tipo)); con.execute("INSERT INTO novidades_produtor (produtor_id,tipo,entidade_id,descricao) VALUES (?,?,?,?)",(u["produtor_id"],"Calcário",cur.lastrowid,f"Novo calcário cadastrado: {nome} (PRNT {prnt:g}%)")); con.commit(); con.close(); flash("Calcário cadastrado e novidade enviada ao agrônomo.","success"); return redirect(url_for("painel_produtor"))
    return render_template("calcario_form.html", nome_comercial="", tipo_calcario="", prnt_porcento="", acao_calcario=url_for("produtor_novo_calcario"), produtor=True)

# --- PRODUTORES ---
@app.route("/produtores")
def produtores():
    busca = (request.args.get("q") or "").strip()
    conexao = conectar_banco()
    if busca:
        if busca.startswith("#"):
            busca_id = busca[1:]
        else:
            busca_id = busca
        if busca_id.isdigit():
            produtores = conexao.execute("SELECT * FROM produtores WHERE id=? OR nome LIKE ? OR telefone LIKE ? ORDER BY nome", (int(busca_id), f"%{busca}%", f"%{busca}%")).fetchall()
        else:
            produtores = conexao.execute("SELECT * FROM produtores WHERE nome LIKE ? OR telefone LIKE ? ORDER BY nome", (f"%{busca}%", f"%{busca}%")).fetchall()
    else:
        produtores = conexao.execute("SELECT * FROM produtores ORDER BY nome").fetchall()
    conexao.close()
    return render_template("produtores.html", produtores=produtores, busca=busca)

@app.route("/produtores/novo", methods=["GET", "POST"])
def novo_produtor():
    if request.method == "POST":
        validar_csrf()
        nome = (request.form.get("nome") or "").strip()
        telefone = (request.form.get("telefone") or "").strip()

        if not nome:
            flash("O nome do produtor é obrigatório.")
            return redirect(url_for("novo_produtor"))

        email = (request.form.get("email") or "").strip().lower()
        senha = request.form.get("senha") or ""
        if not email or len(senha) < 8:
            flash("Para criar o acesso do produtor, informe e-mail e senha com pelo menos 8 caracteres.", "warning")
            return redirect(url_for("novo_produtor"))
        conexao = conectar_banco()
        try:
            cursor = conexao.execute("INSERT INTO produtores (nome, telefone) VALUES (?, ?)", (nome, telefone))
            conexao.execute("INSERT INTO usuarios (nome,email,senha_hash,papel,produtor_id) VALUES (?,?,?,'produtor',?)",
                            (nome, email, generate_password_hash(senha), cursor.lastrowid))
            conexao.commit()
        except Exception as exc:
            if not is_integrity_error(exc):
                conexao.rollback(); conexao.close(); raise
            conexao.rollback(); conexao.close()
            flash("Este e-mail já está cadastrado.", "warning")
            return redirect(url_for("novo_produtor"))
        conexao.close()

        flash("Produtor cadastrado com acesso à conta com sucesso!")
        return redirect(url_for("produtores"))

    return render_template("produtor_form.html")

@app.route("/produtores/editar/<int:id>", methods=["GET", "PUT"])
def editar_produtor(id):
    conexao = conectar_banco()
    produtor = conexao.execute("SELECT * FROM produtores WHERE id = ?", (id,)).fetchone()

    if not produtor:
        conexao.close()
        flash("Produtor não encontrado.")
        return redirect(url_for("produtores"))

    if request.method == "PUT":
        validar_csrf()
        nome = (request.form.get("nome") or "").strip()
        telefone = (request.form.get("telefone") or "").strip()

        if not nome:
            conexao.close()
            flash("O nome do produtor é obrigatório.")
            return redirect(url_for("editar_produtor", id=id))

        conexao.execute("UPDATE produtores SET nome = ?, telefone = ? WHERE id = ?", (nome, telefone, id))
        conexao.commit()
        conexao.close()

        flash("Produtor atualizado com sucesso!")
        return redirect(url_for("produtores"))

    conexao.close()
    return render_template("produtor_form.html", produtor=produtor)

@app.route("/produtores/excluir/<int:id>", methods=["DELETE"])
def excluir_produtor(id):
    validar_csrf()
    conexao = conectar_banco()
    conexao.execute("DELETE FROM produtores WHERE id = ?", (id,))
    conexao.commit()
    conexao.close()
    flash("Produtor excluído com sucesso.")
    return redirect(url_for("produtores"))

# --- PROPRIEDADES ---
@app.route("/propriedades")
def propriedades():
    conexao = conectar_banco()
    propriedades = conexao.execute("""
        SELECT propriedades.*, produtores.nome AS produtor_nome
        FROM propriedades
        INNER JOIN produtores ON propriedades.produtor_id = produtores.id
        ORDER BY propriedades.nome_propriedade
    """).fetchall()
    conexao.close()
    return render_template("propriedades.html", propriedades=propriedades)

@app.route("/propriedades/nova", methods=["GET", "POST"])
def nova_propriedade():
    conexao = conectar_banco()
    produtores = conexao.execute("SELECT * FROM produtores ORDER BY nome").fetchall()

    if request.method == "POST":
        validar_csrf()
        produtor_id = request.form.get("produtor_id")
        nome_propriedade = request.form.get("nome_propriedade")
        municipio = request.form.get("municipio")
        estado = request.form.get("estado")

        if not produtor_id or not nome_propriedade:
            conexao.close()
            flash("Produtor e propriedade são obrigatórios.")
            return redirect(url_for("nova_propriedade"))

        conexao.execute("""
            INSERT INTO propriedades (produtor_id, nome_propriedade, municipio, estado)
            VALUES (?, ?, ?, ?)
        """, (produtor_id, nome_propriedade, municipio, estado))
        conexao.commit()
        conexao.close()

        flash("Propriedade cadastrada com sucesso!")
        return redirect(url_for("propriedades"))

    conexao.close()
    return render_template("propriedade_form.html", produtores=produtores)

@app.route("/propriedades/editar/<int:id>", methods=["GET", "PUT"])
def editar_propriedade(id):
    conexao = conectar_banco()
    propriedade = conexao.execute("SELECT * FROM propriedades WHERE id = ?", (id,)).fetchone()

    if not propriedade:
        conexao.close()
        flash("Propriedade não encontrada.")
        return redirect(url_for("propriedades"))

    if request.method == "PUT":
        validar_csrf()
        produtor_id = request.form.get("produtor_id")
        nome_propriedade = request.form.get("nome_propriedade")
        municipio = request.form.get("municipio")
        estado = request.form.get("estado")

        if not produtor_id or not nome_propriedade:
            conexao.close()
            flash("Produtor e propriedade são obrigatórios.")
            return redirect(url_for("editar_propriedade", id=id))

        conexao.execute("""
            UPDATE propriedades
            SET produtor_id = ?, nome_propriedade = ?, municipio = ?, estado = ?
            WHERE id = ?
        """, (produtor_id, nome_propriedade, municipio, estado, id))
        conexao.commit()
        conexao.close()

        flash("Propriedade atualizada com sucesso!")
        return redirect(url_for("propriedades"))

    produtores = conexao.execute("SELECT * FROM produtores ORDER BY nome").fetchall()
    conexao.close()
    return render_template("propriedade_form.html", propriedade=propriedade, produtores=produtores)

@app.route("/propriedades/excluir/<int:id>", methods=["DELETE"])
def excluir_propriedade(id):
    validar_csrf()
    conexao = conectar_banco()
    vinculada = conexao.execute("SELECT id FROM talhoes WHERE propriedade_id=? LIMIT 1", (id,)).fetchone()
    if vinculada:
        conexao.close()
        flash("Esta propriedade possui talhões vinculados. Remova ou transfira os talhões antes de excluí-la.", "warning")
        return redirect(url_for("propriedades"))
    conexao.execute("DELETE FROM propriedades WHERE id = ?", (id,))
    conexao.commit()
    conexao.close()
    flash("Propriedade excluída com sucesso.")
    return redirect(url_for("propriedades"))

# --- TALHÕES ---
@app.route("/talhoes")
def talhoes():
    """Lista os talhões para o agrônomo, incluindo terra e produtor responsáveis."""
    conexao = conectar_banco()
    lista_talhoes = conexao.execute("""
        SELECT t.id, t.nome_talhao, t.area_ha, t.propriedade_id,
               p.nome_propriedade, pr.nome AS produtor_nome
        FROM talhoes t
        INNER JOIN propriedades p ON t.propriedade_id = p.id
        INNER JOIN produtores pr ON p.produtor_id = pr.id
        ORDER BY pr.nome, p.nome_propriedade, t.nome_talhao
    """).fetchall()
    conexao.close()
    return render_template("talhoes.html", talhoes=lista_talhoes)

@app.route("/talhoes/novo", methods=["GET", "POST"])
def novo_talhao():
    """Permite ao agrônomo cadastrar talhão vinculado à terra de um produtor."""
    conexao = conectar_banco()
    propriedades = conexao.execute("""
        SELECT p.id, p.nome_propriedade, pr.nome AS produtor_nome
        FROM propriedades p
        INNER JOIN produtores pr ON p.produtor_id = pr.id
        ORDER BY pr.nome, p.nome_propriedade
    """).fetchall()

    if request.method == "POST":
        validar_csrf()
        propriedade_id = request.form.get("propriedade_id", type=int)
        nome_talhao = (request.form.get("nome_talhao") or "").strip()
        try:
            area_ha = float(request.form.get("area_ha", ""))
        except (ValueError, TypeError):
            area_ha = 0
        propriedade_valida = conexao.execute(
            "SELECT id FROM propriedades WHERE id = ?", (propriedade_id,)
        ).fetchone() if propriedade_id else None
        if not propriedade_valida or not nome_talhao or area_ha <= 0:
            conexao.close()
            flash("Selecione uma terra, informe o nome e uma área maior que zero.", "warning")
            return redirect(url_for("novo_talhao"))

        conexao.execute(
            "INSERT INTO talhoes (propriedade_id, nome_talhao, area_ha) VALUES (?, ?, ?)",
            (propriedade_id, nome_talhao, area_ha)
        )
        conexao.commit()
        conexao.close()
        flash("Talhão cadastrado com sucesso.", "success")
        return redirect(url_for("talhoes"))

    conexao.close()
    return render_template("auth/talhao_form.html", talhao=None, terras=propriedades, is_agronomo=True)

@app.route("/talhoes/editar/<int:id>", methods=["GET", "PUT"])
def editar_talhao(id):
    """Permite ao agrônomo editar talhão sem quebrar o vínculo com sua terra."""
    conexao = conectar_banco()
    talhao = conexao.execute("SELECT * FROM talhoes WHERE id = ?", (id,)).fetchone()
    if not talhao:
        conexao.close()
        flash("Talhão não encontrado.", "warning")
        return redirect(url_for("talhoes"))

    propriedades = conexao.execute("""
        SELECT p.id, p.nome_propriedade, pr.nome AS produtor_nome
        FROM propriedades p
        INNER JOIN produtores pr ON p.produtor_id = pr.id
        ORDER BY pr.nome, p.nome_propriedade
    """).fetchall()

    if request.method == "PUT":
        validar_csrf()
        propriedade_id = request.form.get("propriedade_id", type=int)
        nome_talhao = (request.form.get("nome_talhao") or "").strip()
        try:
            area_ha = float(request.form.get("area_ha", ""))
        except (ValueError, TypeError):
            area_ha = 0
        propriedade_valida = conexao.execute(
            "SELECT id FROM propriedades WHERE id = ?", (propriedade_id,)
        ).fetchone() if propriedade_id else None
        if not propriedade_valida or not nome_talhao or area_ha <= 0:
            conexao.close()
            flash("Confira a terra, o nome e a área informados.", "warning")
            return redirect(url_for("editar_talhao", id=id))

        conexao.execute(
            "UPDATE talhoes SET propriedade_id = ?, nome_talhao = ?, area_ha = ? WHERE id = ?",
            (propriedade_id, nome_talhao, area_ha, id)
        )
        conexao.commit()
        conexao.close()
        flash("Talhão atualizado com sucesso.", "success")
        return redirect(url_for("talhoes"))

    conexao.close()
    return render_template("auth/talhao_form.html", talhao=talhao, terras=propriedades, is_agronomo=True)

@app.route("/talhoes/excluir/<int:id>", methods=["DELETE"])
def excluir_talhao(id):
    validar_csrf()
    conexao = conectar_banco()
    existe = conexao.execute("SELECT id FROM talhoes WHERE id = ?", (id,)).fetchone()
    if not existe:
        conexao.close()
        flash("Talhão não encontrado.", "warning")
        return redirect(url_for("talhoes"))
    conexao.execute("DELETE FROM talhoes WHERE id = ?", (id,))
    conexao.commit()
    conexao.close()
    flash("Talhão excluído com sucesso.", "success")
    return redirect(url_for("talhoes"))

# --- CULTURAS ---
@app.route("/culturas")
def culturas():
    conexao = conectar_banco()
    culturas = conexao.execute("SELECT culturas.*, propriedades.nome_propriedade FROM culturas LEFT JOIN propriedades ON propriedades.id=culturas.propriedade_id ORDER BY culturas.nome_cultura").fetchall()
    conexao.close()
    return render_template("culturas.html", culturas=culturas)

@app.route("/culturas/nova", methods=["GET", "POST"])
def nova_cultura():
    conexao = conectar_banco()
    propriedades = conexao.execute("SELECT propriedades.id, propriedades.nome_propriedade, produtores.nome AS produtor_nome FROM propriedades JOIN produtores ON produtores.id=propriedades.produtor_id ORDER BY propriedades.nome_propriedade").fetchall()
    if request.method == "POST":
        validar_csrf()
        nome_cultura = (request.form.get("nome_cultura") or "").strip()
        propriedade_id = request.form.get("propriedade_id") or None
        try: v2_alvo = float(request.form.get("v2_alvo"))
        except (ValueError, TypeError): v2_alvo = -1
        if not nome_cultura or not 0 <= v2_alvo <= 100:
            conexao.close(); flash("Informe o nome e um V% alvo entre 0 e 100.", "warning"); return redirect(url_for("nova_cultura"))
        conexao.execute("INSERT INTO culturas (nome_cultura, v2_alvo, propriedade_id) VALUES (?, ?, ?)", (nome_cultura, v2_alvo, propriedade_id))
        conexao.commit(); conexao.close(); flash("Cultura cadastrada.", "success"); return redirect(url_for("culturas"))
    conexao.close(); return render_template("cultura_form.html", cultura=None, propriedades=propriedades)

@app.route("/culturas/editar/<int:id>", methods=["GET", "PUT"])
def editar_cultura(id):
    conexao=conectar_banco(); cultura=conexao.execute("SELECT * FROM culturas WHERE id=?",(id,)).fetchone()
    propriedades=conexao.execute("SELECT id,nome_propriedade FROM propriedades ORDER BY nome_propriedade").fetchall()
    if not cultura: conexao.close(); abort(404)
    if request.method == "PUT":
        validar_csrf()
        validar_csrf(); nome=(request.form.get("nome_cultura") or "").strip()
        try: v2=float(request.form.get("v2_alvo"))
        except (ValueError,TypeError): v2=-1
        pid=request.form.get("propriedade_id") or None
        if not nome or not 0<=v2<=100: flash("Confira o nome e o V% alvo (0 a 100).","warning")
        else: conexao.execute("UPDATE culturas SET nome_cultura=?,v2_alvo=?,propriedade_id=? WHERE id=?",(nome,v2,pid,id)); conexao.commit(); conexao.close(); flash("Cultura atualizada.","success"); return redirect(url_for("culturas"))
    conexao.close(); return render_template("cultura_form.html",cultura=cultura,propriedades=propriedades)

@app.route("/culturas/excluir/<int:id>", methods=["DELETE"])
def excluir_cultura(id):
    validar_csrf(); conexao=conectar_banco()
    usada=conexao.execute("SELECT id FROM recomendacoes_solo WHERE cultura_id=? LIMIT 1",(id,)).fetchone()
    if usada:
        conexao.close(); flash("Esta cultura possui relatórios vinculados e não pode ser excluída.","warning"); return redirect(url_for("culturas"))
    conexao.execute("DELETE FROM culturas WHERE id=?",(id,)); conexao.commit(); conexao.close(); flash("Cultura excluída.","success"); return redirect(url_for("culturas"))

# --- CALCÁRIOS ---
@app.route("/calcarios")
def calcarios():
    """Lista o catálogo compartilhado de corretivos disponível aos usuários."""
    conexao = conectar_banco()
    calcarios = conexao.execute(
        "SELECT * FROM corretivos_calcario ORDER BY nome_comercial"
    ).fetchall()
    conexao.close()
    return render_template("calcarios.html", calcarios=calcarios)

@app.route("/calcarios/novo", methods=["GET", "POST"])
def novo_calcario():
    """Permite ao produtor ou agrônomo cadastrar um corretivo no catálogo compartilhado."""
    if request.method == "POST":
        validar_csrf()
        nome_comercial = (request.form.get("nome_comercial") or "").strip()
        tipo_calcario = (request.form.get("tipo_calcario") or "").strip()
        prnt_bruto = (request.form.get("prnt_porcento") or "").strip().replace(",", ".")
        try:
            prnt = float(prnt_bruto)
        except (ValueError, TypeError):
            flash("Informe um PRNT numérico válido.", "warning")
            return render_template("calcario_form.html", nome_comercial=nome_comercial, tipo_calcario=tipo_calcario, prnt_porcento=prnt_bruto)

        if not nome_comercial:
            flash("Informe o nome comercial do calcário.", "warning")
            return render_template("calcario_form.html", nome_comercial=nome_comercial, tipo_calcario=tipo_calcario, prnt_porcento=prnt_bruto)
        if not 0 < prnt <= 100:
            flash("O PRNT deve ser maior que 0 e menor ou igual a 100%.", "warning")
            return render_template("calcario_form.html", nome_comercial=nome_comercial, tipo_calcario=tipo_calcario, prnt_porcento=prnt_bruto)

        if tipo_calcario not in {"calcítico", "dolomítico", "magnesiano", "não informado"}:
            flash("Selecione o tipo de calcário.", "warning")
            return render_template("calcario_form.html", nome_comercial=nome_comercial, tipo_calcario=tipo_calcario, prnt_porcento=prnt_bruto)

        conexao = conectar_banco()
        conexao.execute(
            "INSERT INTO corretivos_calcario (nome_comercial, prnt_porcento, tipo_calcario) VALUES (?, ?, ?)",
            (nome_comercial, prnt, tipo_calcario),
        )
        conexao.commit()
        conexao.close()
        flash("Calcário cadastrado. A próxima recomendação usará este corretivo.", "success")
        return redirect(url_for("calcarios"))

    return render_template("calcario_form.html", nome_comercial="", tipo_calcario="", prnt_porcento="")

@app.route("/calcarios/editar/<int:id>", methods=["GET", "PUT"])
def editar_calcario(id):
    con = conectar_banco()
    calcario = con.execute("SELECT * FROM corretivos_calcario WHERE id=?", (id,)).fetchone()
    if not calcario:
        con.close(); abort(404)
    if request.method == "PUT":
        validar_csrf()
        nome = (request.form.get("nome_comercial") or "").strip()
        tipo = (request.form.get("tipo_calcario") or "").strip()
        bruto = (request.form.get("prnt_porcento") or "").strip().replace(",", ".")
        try: prnt = float(bruto)
        except ValueError: prnt = 0
        if not nome or tipo not in {"calcítico", "dolomítico", "magnesiano", "não informado"} or not 0 < prnt <= 100:
            con.close(); flash("Confira nome, tipo e PRNT (maior que 0 e até 100%).", "warning")
            return redirect(url_for("editar_calcario", id=id))
        con.execute("UPDATE corretivos_calcario SET nome_comercial=?, tipo_calcario=?, prnt_porcento=? WHERE id=?", (nome, tipo, prnt, id))
        con.commit(); con.close(); flash("Calcário atualizado com sucesso.", "success")
        return redirect(url_for("calcarios"))
    con.close()
    return render_template("calcario_form.html", calcario=calcario, nome_comercial=calcario["nome_comercial"], tipo_calcario=calcario["tipo_calcario"], prnt_porcento=calcario["prnt_porcento"], acao_calcario=url_for("editar_calcario", id=id), produtor=False)

@app.route("/calcarios/excluir/<int:id>", methods=["DELETE"])
def excluir_calcario(id):
    validar_csrf(); con = conectar_banco()
    usado = con.execute("SELECT id FROM recomendacoes_solo WHERE calcario_id=? LIMIT 1", (id,)).fetchone()
    if usado:
        con.close(); flash("Este calcário já está vinculado a relatórios e não pode ser excluído.", "warning")
        return redirect(url_for("calcarios"))
    con.execute("DELETE FROM corretivos_calcario WHERE id=?", (id,)); con.commit(); con.close()
    flash("Calcário excluído com sucesso.", "success")
    return redirect(url_for("calcarios"))

# --- FERTILIZANTES ---
@app.route("/fertilizantes")
def fertilizantes():
    conexao = conectar_banco()
    fertilizantes = conexao.execute("SELECT * FROM fertilizantes ORDER BY nome_comercial").fetchall()
    conexao.close()
    return render_template("fertilizantes.html", fertilizantes=fertilizantes)

@app.route("/fertilizantes/novo", methods=["GET", "POST"])
def novo_fertilizante():
    if request.method == "POST":
        nome_comercial = (request.form.get("nome_comercial") or "").strip()
        try:
            teor_n = float((request.form.get("teor_n") or "0").replace(",", "."))
            teor_p2o5 = float((request.form.get("teor_p2o5") or "0").replace(",", "."))
            teor_k2o = float((request.form.get("teor_k2o") or "0").replace(",", "."))
        except ValueError:
            flash("Informe teores numéricos válidos.", "warning")
            return redirect(url_for("novo_fertilizante"))
        if not nome_comercial or any(not math.isfinite(x) or x < 0 or x > 100 for x in (teor_n, teor_p2o5, teor_k2o)):
            flash("Informe o nome e teores entre 0 e 100%.", "warning")
            return redirect(url_for("novo_fertilizante"))

        conexao = conectar_banco()
        conexao.execute("""
            INSERT INTO fertilizantes (nome_comercial, teor_n, teor_p2o5, teor_k2o)
            VALUES (?, ?, ?, ?)
        """, (nome_comercial, teor_n, teor_p2o5, teor_k2o))
        conexao.commit()
        conexao.close()

        flash("Fertilizante cadastrado com sucesso!")
        return redirect(url_for("fertilizantes"))

    return render_template("fertilizante_form.html")

@app.route("/fertilizantes/editar/<int:id>", methods=["GET", "PUT"])
def editar_fertilizante(id):
    con = conectar_banco(); fertilizante = con.execute("SELECT * FROM fertilizantes WHERE id=?", (id,)).fetchone()
    if not fertilizante:
        con.close(); abort(404)
    if request.method == "PUT":
        validar_csrf()
        nome = (request.form.get("nome_comercial") or "").strip()
        try:
            n = float((request.form.get("teor_n") or "0").replace(",", "."))
            p = float((request.form.get("teor_p2o5") or "0").replace(",", "."))
            k = float((request.form.get("teor_k2o") or "0").replace(",", "."))
        except ValueError:
            con.close(); flash("Informe teores numéricos válidos.", "warning"); return redirect(url_for("editar_fertilizante", id=id))
        if not nome or any(not math.isfinite(x) or x < 0 or x > 100 for x in (n,p,k)):
            con.close(); flash("Informe o nome e teores entre 0 e 100%.", "warning"); return redirect(url_for("editar_fertilizante", id=id))
        con.execute("UPDATE fertilizantes SET nome_comercial=?, teor_n=?, teor_p2o5=?, teor_k2o=? WHERE id=?", (nome,n,p,k,id))
        con.commit(); con.close(); flash("Fertilizante atualizado com sucesso.", "success"); return redirect(url_for("fertilizantes"))
    con.close(); return render_template("fertilizante_form.html", fertilizante=fertilizante, acao=url_for("editar_fertilizante", id=id))

@app.route("/fertilizantes/excluir/<int:id>", methods=["DELETE"])
def excluir_fertilizante(id):
    validar_csrf(); con = conectar_banco()
    con.execute("DELETE FROM fertilizantes WHERE id=?", (id,)); con.commit(); con.close()
    flash("Fertilizante excluído com sucesso.", "success"); return redirect(url_for("fertilizantes"))

# --- MÓDULO DE SOLO ---
@app.route("/solo/calculadora")
def calculadora_solo():
    if session.get("usuario", {}).get("papel") != "agronomo": abort(403)
    solicitacao_id = request.args.get("solicitacao_id", type=int)
    conexao = conectar_banco()
    if solicitacao_id:
        sol = conexao.execute("SELECT produtor_id FROM solicitacoes_relatorio WHERE id=? AND status!='Atendida'", (solicitacao_id,)).fetchone()
        if not sol:
            conexao.close(); abort(404)
        talhoes = conexao.execute("SELECT t.id,t.nome_talhao,t.area_ha,p.nome_propriedade FROM talhoes t JOIN propriedades p ON p.id=t.propriedade_id WHERE p.produtor_id=? ORDER BY t.nome_talhao", (sol["produtor_id"],)).fetchall()
        culturas = conexao.execute("SELECT c.*,p.nome_propriedade FROM culturas c LEFT JOIN propriedades p ON p.id=c.propriedade_id WHERE p.produtor_id=? OR c.propriedade_id IS NULL ORDER BY c.nome_cultura", (sol["produtor_id"],)).fetchall()
    else:
        talhoes = conexao.execute("""SELECT talhoes.id, talhoes.nome_talhao, talhoes.area_ha, propriedades.nome_propriedade FROM talhoes INNER JOIN propriedades ON talhoes.propriedade_id = propriedades.id ORDER BY talhoes.nome_talhao""").fetchall()
        culturas = conexao.execute("SELECT culturas.*, propriedades.nome_propriedade FROM culturas LEFT JOIN propriedades ON propriedades.id=culturas.propriedade_id ORDER BY culturas.nome_cultura").fetchall()
    conexao.close()
    return render_template("solo/calculadora.html", talhoes=talhoes, culturas=culturas, solicitacao_id=solicitacao_id)

@app.route("/solo/formulario")
def formulario_solo():
    if session.get("usuario", {}).get("papel") != "agronomo": abort(403)
    solicitacao_id = request.args.get("solicitacao_id", type=int)
    talhao_id = request.args.get("talhao_id") or request.args.get("talhao id")
    cultura_id = request.args.get("cultura_id") or request.args.get("cultura id")

    if not talhao_id or not cultura_id:
        flash("Selecione o talhão e a cultura.")
        return redirect(url_for("calculadora_solo"))

    conexao = conectar_banco()
    talhao = conexao.execute("""
        SELECT talhoes.*, propriedades.nome_propriedade, produtores.nome AS produtor_nome
        FROM talhoes
        INNER JOIN propriedades ON talhoes.propriedade_id = propriedades.id
        INNER JOIN produtores ON propriedades.produtor_id = produtores.id
        WHERE talhoes.id = ?
    """, (talhao_id,)).fetchone()

    cultura = conexao.execute("SELECT * FROM culturas WHERE id = ?", (cultura_id,)).fetchone()
    conexao.close()

    if not talhao or not cultura:
        flash("Dados não encontrados.")
        return redirect(url_for("calculadora_solo"))
    if solicitacao_id:
        con_check = conectar_banco()
        sol = con_check.execute("SELECT produtor_id FROM solicitacoes_relatorio WHERE id=? AND status!='Atendida'", (solicitacao_id,)).fetchone()
        dono = con_check.execute("SELECT p.produtor_id FROM talhoes t JOIN propriedades p ON p.id=t.propriedade_id WHERE t.id=?", (talhao_id,)).fetchone()
        dono_cultura = con_check.execute("SELECT propriedade_id FROM culturas WHERE id=?", (cultura_id,)).fetchone()
        cultura_ok = False
        if dono_cultura and dono_cultura["propriedade_id"] is None:
            # Cultura geral do catálogo, disponível para qualquer produtor.
            cultura_ok = True
        elif dono_cultura and dono_cultura["propriedade_id"] is not None:
            prop_cultura = con_check.execute("SELECT produtor_id FROM propriedades WHERE id=?", (dono_cultura["propriedade_id"],)).fetchone()
            cultura_ok = bool(prop_cultura and sol and prop_cultura["produtor_id"] == sol["produtor_id"])
        con_check.close()
        if not sol or not dono or sol["produtor_id"] != dono["produtor_id"] or not cultura_ok:
            abort(403)

    conexao = conectar_banco()
    calcarios = conexao.execute("SELECT * FROM corretivos_calcario WHERE prnt_porcento > 0 AND prnt_porcento <= 100 ORDER BY nome_comercial").fetchall()
    fertilizantes = conexao.execute("SELECT * FROM fertilizantes ORDER BY nome_comercial").fetchall()
    conexao.close()
    return render_template("solo/formulario.html", talhao=talhao, cultura=cultura, calcarios=calcarios, fertilizantes=fertilizantes, solicitacao_id=solicitacao_id)

@app.route("/solo/calcular", methods=["POST"])
def calcular_solo():
    if session.get("usuario", {}).get("papel") != "agronomo": abort(403)
    validar_csrf()
    solicitacao_id = request.form.get("solicitacao_id", type=int)
    talhao_id = request.form.get("talhao_id")
    cultura_id = request.form.get("cultura_id")
    data_coleta = request.form.get("data_coleta", "").strip()
    erro_data = validar_data_laudo(data_coleta)
    if erro_data:
        flash(erro_data, "warning")
        return redirect(url_for("formulario_solo", talhao_id=talhao_id, cultura_id=cultura_id, solicitacao_id=solicitacao_id) if solicitacao_id else url_for("formulario_solo", talhao_id=talhao_id, cultura_id=cultura_id))

    campos = ["ph", "v1_atual", "ctc_t", "ca", "mg", "k", "p", "h_al", "argila"]
    valores = {}

    try:
        for campo in campos:
            valor = (request.form.get(campo) or "").strip().replace(",", ".")
            valores[campo] = float(valor) if valor else None
    except ValueError:
        flash("Verifique os valores informados. Utilize apenas números.")
        return redirect(url_for("formulario_solo", talhao_id=talhao_id, cultura_id=cultura_id, solicitacao_id=solicitacao_id) if solicitacao_id else url_for("formulario_solo", talhao_id=talhao_id, cultura_id=cultura_id))

    if valores["ph"] is None or valores["v1_atual"] is None or valores["ctc_t"] is None:
        flash("Os campos pH, V1 atual e CTC T são obrigatórios.")
        return redirect(url_for("formulario_solo", talhao_id=talhao_id, cultura_id=cultura_id, solicitacao_id=solicitacao_id) if solicitacao_id else url_for("formulario_solo", talhao_id=talhao_id, cultura_id=cultura_id))

    if not 3 <= valores["ph"] <= 10 or not 0 <= valores["v1_atual"] <= 100:
        flash("Confira os limites: pH de 3 a 10 (valores fora disso devem ser conferidos no laudo) e V% entre 0 e 100.", "warning")
        return redirect(url_for("formulario_solo", talhao_id=talhao_id, cultura_id=cultura_id, solicitacao_id=solicitacao_id) if solicitacao_id else url_for("formulario_solo", talhao_id=talhao_id, cultura_id=cultura_id))
    if any(v is not None and not math.isfinite(v) for v in valores.values()):
        flash("Informe valores numéricos finitos no laudo.", "warning")
        return redirect(url_for("formulario_solo", talhao_id=talhao_id, cultura_id=cultura_id, solicitacao_id=solicitacao_id) if solicitacao_id else url_for("formulario_solo", talhao_id=talhao_id, cultura_id=cultura_id))
    # Preserve K exactly as entered; valores[campo] será normalizado para uso interno.
    k_original = valores.get("k")
    unidade_k_original = request.form.get("unidade_k", "mg/dm3")
    unidades = {campo: request.form.get("unidade_" + campo, padrao) for campo, padrao in {
        "ph": "ph", "v1_atual": "%", "ctc_t": "cmolc/dm3", "ca": "cmolc/dm3",
        "mg": "cmolc/dm3", "k": "mg/dm3", "p": "mg/dm3", "h_al": "cmolc/dm3", "argila": "%"
    }.items()}
    try:
        conversoes = normalizar_unidades_solo(valores, unidades)
    except ValueError:
        flash("Selecione unidades válidas para os parâmetros da análise.", "warning")
        return redirect(url_for("formulario_solo", talhao_id=talhao_id, cultura_id=cultura_id, solicitacao_id=solicitacao_id) if solicitacao_id else url_for("formulario_solo", talhao_id=talhao_id, cultura_id=cultura_id))
    # Os limites são conferidos DEPOIS de converter para as unidades internas.
    if valores["ctc_t"] is None or not 0 < valores["ctc_t"] <= 100:
        flash(f"CTC inválida após conversão: {valores['ctc_t']!r} cmolc/dm³. Informe a CTC a pH 7 e confira a unidade selecionada.", "warning")
        return redirect(url_for("formulario_solo", talhao_id=talhao_id, cultura_id=cultura_id, solicitacao_id=solicitacao_id) if solicitacao_id else url_for("formulario_solo", talhao_id=talhao_id, cultura_id=cultura_id))
    limites = {"ca": 100, "mg": 100, "k": 100, "p": 1000, "h_al": 100}
    if any(valores[c] is not None and not 0 <= valores[c] <= limite for c, limite in limites.items()) or (valores["argila"] is not None and not 0 <= valores["argila"] <= 100):
        flash("Confira os limites: Ca, Mg, K e H + Al de 0 a 100; P de 0 a 1000 mg/dm³; argila de 0 a 100%.", "warning")
        return redirect(url_for("formulario_solo", talhao_id=talhao_id, cultura_id=cultura_id, solicitacao_id=solicitacao_id) if solicitacao_id else url_for("formulario_solo", talhao_id=talhao_id, cultura_id=cultura_id))

    conexao = conectar_banco()
    cultura = conexao.execute("SELECT * FROM culturas WHERE id = ?", (cultura_id,)).fetchone()
    talhao = conexao.execute("""
        SELECT t.*, p.municipio AS municipio_propriedade, p.estado AS estado_propriedade
        FROM talhoes t JOIN propriedades p ON p.id = t.propriedade_id
        WHERE t.id = ?
    """, (talhao_id,)).fetchone()
    calcario_id_form = request.form.get("calcario_id", type=int)
    calcario = conexao.execute("SELECT * FROM corretivos_calcario WHERE id = ?", (calcario_id_form,)).fetchone() if calcario_id_form else None

    if solicitacao_id:
        solicitacao_validacao = conexao.execute(
            "SELECT produtor_id, status FROM solicitacoes_relatorio WHERE id=?", (solicitacao_id,)
        ).fetchone()
        dono_talhao_validacao = conexao.execute(
            "SELECT p.produtor_id FROM talhoes t JOIN propriedades p ON p.id=t.propriedade_id WHERE t.id=?",
            (talhao_id,)
        ).fetchone()
        if (not solicitacao_validacao or solicitacao_validacao["status"] == "Atendida" or
                not dono_talhao_validacao or solicitacao_validacao["produtor_id"] != dono_talhao_validacao["produtor_id"]):
            conexao.close()
            abort(403, description="A solicitação não corresponde ao produtor do talhão selecionado.")

    if not cultura or not talhao:
        conexao.close()
        flash("Talhão ou cultura não encontrados. Selecione novamente os dois campos.", "warning")
        return redirect(url_for("calculadora_solo", solicitacao_id=solicitacao_id) if solicitacao_id else url_for("calculadora_solo"))

    # Se a cultura pertence a uma propriedade específica, ela precisa corresponder
    # ao produtor dono do talhão. Culturas globais (propriedade_id NULL) são permitidas.
    cultura_prop_id = cultura["propriedade_id"] if "propriedade_id" in cultura.keys() else None
    if cultura_prop_id is not None:
        dono_cultura = conexao.execute("SELECT produtor_id FROM propriedades WHERE id=?", (cultura_prop_id,)).fetchone()
        dono_talhao = conexao.execute("SELECT produtor_id FROM propriedades WHERE id=?", (talhao["propriedade_id"],)).fetchone()
        if not dono_cultura or not dono_talhao or dono_cultura["produtor_id"] != dono_talhao["produtor_id"]:
            conexao.close()
            flash("A cultura selecionada não pertence ao produtor do talhão. Escolha novamente.", "warning")
            return redirect(url_for("calculadora_solo", solicitacao_id=solicitacao_id) if solicitacao_id else url_for("calculadora_solo"))

    # Todas as culturas usam o V% alvo cadastrado para aquela cultura.
    # O valor não é universal: deve ser definido conforme cultura, região,
    # solo e sistema de manejo, com base técnica local ou orientação profissional.
    v2_alvo = float(cultura["v2_alvo"]) if cultura["v2_alvo"] is not None else None

    v1_atual = valores["v1_atual"]
    ctc = valores["ctc_t"]
    if v2_alvo is None or not 0 < float(v2_alvo) <= 100:
        conexao.close()
        flash("O V% alvo da cultura está ausente ou inválido. Corrija o cadastro da cultura.")
        return redirect(url_for("calculadora_solo"))

    # A inconsistência não bloqueia o relatório: registra os valores e mostra um alerta.
    # O resultado numérico é apenas demonstrativo quando os parâmetros não fecham.
    problemas = []
    quimicos = {"Ca": valores["ca"], "Mg": valores["mg"], "K": valores["k"], "H + Al": valores["h_al"]}
    preenchidos = [nome for nome, valor in quimicos.items() if valor is not None]
    if preenchidos and len(preenchidos) != len(quimicos):
        faltantes = [nome for nome, valor in quimicos.items() if valor is None]
        problemas.append("Conferência química incompleta; faltam: " + ", ".join(faltantes))
    if all(v is not None for v in quimicos.values()):
        soma_bases = valores["ca"] + valores["mg"] + valores["k"]
        soma_ctc = soma_bases + valores["h_al"]
        tolerancia_ctc = max(0.5, ctc * 0.20)
        v1_calculado = 100.0 * soma_bases / ctc
        if soma_bases > ctc:
            problemas.append(f"Ca + Mg + K = {soma_bases:.2f} cmolc/dm³, acima da CTC de {ctc:.2f}")
        diferenca_ctc = soma_ctc - ctc
        if abs(diferenca_ctc) > tolerancia_ctc:
            problemas.append(f"Ca + Mg + K + H + Al = {soma_ctc:.2f} cmolc/dm³, mas a CTC informada é {ctc:.2f} (diferença {diferenca_ctc:+.2f})")
        if v1_calculado > 100:
            problemas.append(f"V% estimado por Ca + Mg + K = {v1_calculado:.1f}%, acima de 100%")
        elif abs(v1_calculado - v1_atual) > 10:
            problemas.append(f"V1 informado = {v1_atual:.1f}%, mas o V% estimado por Ca + Mg + K e CTC = {v1_calculado:.1f}%")
    consistencia_status = "INCONSISTENTE" if problemas else "CONSISTENTE"
    consistencia_detalhes = "; ".join(problemas) if problemas else None
    if not calcario or not 0 < float(calcario["prnt_porcento"]) <= 100:
        conexao.close()
        flash("Cadastre um calcário com PRNT válido antes de calcular.")
        return redirect(url_for("calculadora_solo"))
    prnt = float(calcario["prnt_porcento"])
    calcario_id = calcario["id"]
    if conversoes:
        flash("Unidades convertidas para o cálculo: " + "; ".join(conversoes) + ".", "info")
    area_ha = talhao["area_ha"]

    # Conversão de metas técnicas de nutrientes em doses de fertilizantes.
    # As metas são informadas pelo agrônomo; não são inferidas automaticamente do laudo.
    plano_adubacao = []
    try:
        metas = [("N", "alvo_n_kg_ha", "fertilizante_n_id", "teor_n"),
                 ("P2O5", "alvo_p2o5_kg_ha", "fertilizante_p_id", "teor_p2o5"),
                 ("K2O", "alvo_k2o_kg_ha", "fertilizante_k_id", "teor_k2o")]
        for nutriente, campo_alvo, campo_produto, campo_teor in metas:
            texto = (request.form.get(campo_alvo) or "").strip().replace(",", ".")
            alvo = float(texto) if texto else 0.0
            if not math.isfinite(alvo) or not 0 <= alvo <= 1000:
                raise ValueError(f"A meta de {nutriente} deve estar entre 0 e 1000 kg/ha.")
            produto_id = request.form.get(campo_produto, type=int)
            if alvo == 0:
                continue
            if not produto_id:
                raise ValueError(f"Selecione um fertilizante para a meta de {nutriente}.")
            produto = conexao.execute("SELECT * FROM fertilizantes WHERE id=?", (produto_id,)).fetchone()
            if not produto:
                raise ValueError(f"O fertilizante selecionado para {nutriente} não existe.")
            dose, total = calcular_dose_fertilizante(alvo, produto[campo_teor], float(area_ha))
            plano_adubacao.append({"nutriente": nutriente, "fertilizante_id": produto_id,
                                   "nome": produto["nome_comercial"], "alvo_kg_ha": alvo,
                                   "dose_kg_ha": dose, "total_kg": total})
    except (ValueError, TypeError) as exc:
        conexao.close()
        flash(str(exc) or "Confira as metas e os fertilizantes selecionados.", "warning")
        return redirect(url_for("formulario_solo", talhao_id=talhao_id, cultura_id=cultura_id, solicitacao_id=solicitacao_id) if solicitacao_id else url_for("formulario_solo", talhao_id=talhao_id, cultura_id=cultura_id))

    # Método da saturação por bases, camada de referência 0–20 cm:
    # NC base (t/ha, PRNT 100%) = CTC × (V2 − V1) / 100.
    # Dose comercial (t/ha) = NC base × 100 / PRNT.
    # A necessidade não pode ser negativa; quando V1 >= V2, o resultado é zero.
    nc_ha = max(0.0, ctc * (float(v2_alvo) - v1_atual) / 100.0)
    dose_calcario_ha = nc_ha * (100.0 / prnt)
    total_talhao = dose_calcario_ha * float(area_ha)

    cursor = conexao.execute("""
        INSERT INTO recomendacoes_solo (
            talhao_id, cultura_id, calcario_id, data_coleta,
            ph, v1_atual, v2_alvo, ctc_t, ca, mg, k, p, h_al, argila,
            nc_ha, dose_calcario_ha, total_calcario_talhao, k_original, unidade_k,
            consistencia_status, consistencia_detalhes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        talhao_id, cultura_id, calcario_id, data_coleta,
        valores["ph"], valores["v1_atual"], v2_alvo, valores["ctc_t"],
        valores["ca"], valores["mg"], valores["k"], valores["p"],
        valores["h_al"], valores["argila"],
        nc_ha, dose_calcario_ha, total_talhao, k_original, unidade_k_original,
        consistencia_status, consistencia_detalhes
    ))

    recomendacao_id = cursor.lastrowid
    for item in plano_adubacao:
        conexao.execute("""INSERT INTO recomendacao_adubacao_itens
            (recomendacao_id, nutriente, fertilizante_id, alvo_kg_ha, dose_kg_ha, total_kg)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (recomendacao_id, item["nutriente"], item["fertilizante_id"], item["alvo_kg_ha"], item["dose_kg_ha"], item["total_kg"]))
    if solicitacao_id:
        solicitacao = conexao.execute("SELECT produtor_id,status FROM solicitacoes_relatorio WHERE id=?", (solicitacao_id,)).fetchone()
        dono = conexao.execute("SELECT p.produtor_id FROM talhoes t JOIN propriedades p ON p.id=t.propriedade_id WHERE t.id=?", (talhao_id,)).fetchone()
        if solicitacao and dono and solicitacao["produtor_id"] == dono["produtor_id"] and solicitacao["status"] != "Atendida":
            marcar_solicitacao_atendida(conexao, solicitacao_id, recomendacao_id)
    conexao.commit()
    conexao.close()

    return redirect(url_for("resultado_solo", recomendacao_id=recomendacao_id))

@app.route("/solo/resultado/<int:recomendacao_id>")
def resultado_solo(recomendacao_id):
    conexao = conectar_banco()
    recomendacao = conexao.execute("""
        SELECT r.*, t.nome_talhao, t.area_ha, c.nome_cultura, p.nome_propriedade, 
               prod.nome AS produtor_nome, cc.nome_comercial, cc.tipo_calcario, cc.prnt_porcento AS prnt_porcento
        FROM recomendacoes_solo r
        JOIN talhoes t ON r.talhao_id = t.id
        JOIN propriedades p ON t.propriedade_id = p.id
        JOIN produtores prod ON p.produtor_id = prod.id
        JOIN culturas c ON r.cultura_id = c.id
        LEFT JOIN corretivos_calcario cc ON r.calcario_id = cc.id
        WHERE r.id = ?
    """, (recomendacao_id,)).fetchone()
    itens_adubacao = conexao.execute("""SELECT i.*, f.nome_comercial FROM recomendacao_adubacao_itens i
        JOIN fertilizantes f ON f.id=i.fertilizante_id WHERE i.recomendacao_id=? ORDER BY i.id""", (recomendacao_id,)).fetchall() if recomendacao else []
    conexao.close()

    if not recomendacao:
        flash("Recomendação não encontrada.")
        return redirect(url_for("calculadora_solo"))

    return render_template("solo/resultado.html", recomendacao=recomendacao, itens_adubacao=itens_adubacao)

@app.route("/solo/recomendacoes")
def recomendacoes_solo():
    conexao = conectar_banco()
    recomendacoes = conexao.execute("""
        SELECT r.*, t.nome_talhao, c.nome_cultura, p.nome_propriedade, 
               prod.nome AS produtor_nome, cc.nome_comercial, cc.tipo_calcario, cc.prnt_porcento AS prnt_porcento
        FROM recomendacoes_solo r
        JOIN talhoes t ON r.talhao_id = t.id
        JOIN propriedades p ON t.propriedade_id = p.id
        JOIN produtores prod ON p.produtor_id = prod.id
        JOIN culturas c ON r.cultura_id = c.id
        LEFT JOIN corretivos_calcario cc ON r.calcario_id = cc.id
        ORDER BY r.id DESC
    """).fetchall()
    conexao.close()
    return render_template("solo/recomendacaos.html", recomendacoes=recomendacoes)

@app.route("/solo/documento/<int:recomendacao_id>")
def documento_solo(recomendacao_id):
    conexao = conectar_banco()
    documento = conexao.execute("""
        SELECT r.*, t.nome_talhao, t.area_ha, c.nome_cultura, p.nome_propriedade, 
               p.municipio, p.estado, prod.nome AS produtor_nome, prod.telefone,
               cc.nome_comercial, cc.tipo_calcario, cc.prnt_porcento AS prnt_porcento
        FROM recomendacoes_solo r
        JOIN talhoes t ON r.talhao_id = t.id
        JOIN propriedades p ON t.propriedade_id = p.id
        JOIN produtores prod ON p.produtor_id = prod.id
        JOIN culturas c ON r.cultura_id = c.id
        LEFT JOIN corretivos_calcario cc ON r.calcario_id = cc.id
        WHERE r.id = ?
    """, (recomendacao_id,)).fetchone()
    itens_adubacao = conexao.execute("""SELECT i.*, f.nome_comercial FROM recomendacao_adubacao_itens i
        JOIN fertilizantes f ON f.id=i.fertilizante_id WHERE i.recomendacao_id=? ORDER BY i.id""", (recomendacao_id,)).fetchall() if documento else []
    conexao.close()

    if not documento:
        flash("Documento não encontrado.")
        return redirect(url_for("recomendacoes_solo"))

    return render_template("solo/documentacao.html", documento=documento, itens_adubacao=itens_adubacao)

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")