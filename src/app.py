from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from db_config import db_config

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(**db_config)

# função para criar uma notificação
def criar_notificacao(mensagem):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Notificacao (mensagem) VALUES (%s)", (mensagem,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erro ao criar notificação: {e}")

# carregar notificações para o topo da página
@app.context_processor
def inject_notifications():
    # isso roda antes de carregar qualquer página pra buscar as notificações
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # pega as 5 últimas notificações
    cursor.execute("SELECT * FROM Notificacao ORDER BY data_hora DESC LIMIT 5")
    notificacoes_topo = cursor.fetchall()
    
    # conta quantas não foram lidas
    cursor.execute("SELECT COUNT(*) as qtd FROM Notificacao WHERE lida = 0")
    qtd_nao_lidas = cursor.fetchone()['qtd']
    
    conn.close()
    
    # disponibiliza essas variáveis pro HTML base.html
    return dict(notificacoes_topo=notificacoes_topo, qtd_nao_lidas=qtd_nao_lidas)

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 1. total de bebês
    cursor.execute("SELECT COUNT(*) as total FROM Bebe")
    total_bebes = cursor.fetchone()['total']
    
    # 2. dados de leitos 
    cursor.execute("SELECT COUNT(*) as total FROM Leito")
    total_leitos = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as ocupados FROM Bebe WHERE id_leito IS NOT NULL")
    leitos_ocupados = cursor.fetchone()['ocupados']
    
    # 3. cálculos finais
    leitos_disponiveis = total_leitos - leitos_ocupados
    
    # cálculo da taxa de ocupação
    taxa_ocupacao = 0
    if total_leitos > 0:
        taxa_ocupacao = int((leitos_ocupados / total_leitos) * 100)
    
    # 4. bebês recentes
    cursor.execute("""
        SELECT b.*, l.numero_quarto 
        FROM Bebe b 
        LEFT JOIN Leito l ON b.id_leito = l.id_leito 
        ORDER BY b.data_nascimento DESC 
        LIMIT 5
    """)
    recentes = cursor.fetchall()
    
    conn.close()
    
    return render_template('index.html', 
                         total_bebes=total_bebes, 
                         leitos_disponiveis=leitos_disponiveis, 
                         taxa_ocupacao=taxa_ocupacao,
                         recentes=recentes)

# rota pra listar bebês
@app.route('/bebes')
def lista_bebes():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT b.*, l.numero_quarto, l.numero_berco 
        FROM Bebe b 
        LEFT JOIN Leito l ON b.id_leito = l.id_leito
    """)
    bebes = cursor.fetchall()
    conn.close()
    return render_template('lista_bebes.html', bebes=bebes)

@app.route('/bebes/novo', methods=('GET', 'POST'))
def novo_bebe():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        nome = request.form['nome']
        peso = request.form['peso']
        altura = request.form['altura']
        id_leito = request.form.get('id_leito')
        cursor.execute("INSERT INTO Bebe (nome, data_nascimento, peso_nascimento, altura_nascimento, id_leito) VALUES (%s, NOW(), %s, %s, %s)", (nome, peso, altura, id_leito if id_leito else None))
        conn.commit()
        conn.close()
        return redirect(url_for('lista_bebes'))
    
    cursor.execute("SELECT * FROM Leito WHERE id_leito NOT IN (SELECT id_leito FROM Bebe WHERE id_leito IS NOT NULL)")
    leitos_livres = cursor.fetchall()
    conn.close()
    return render_template('form_bebe.html', leitos=leitos_livres)

# rota pra listar responsáveis
@app.route('/responsaveis')
def lista_responsaveis():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # mudamos de JOIN pra LEFT JOIN pra trazer quem não tem bebê ainda
    cursor.execute("""
        SELECT r.*, b.nome as nome_bebe, rb.parentesco
        FROM Responsavel r
        LEFT JOIN Responsavel_Bebe rb ON r.id_responsavel = rb.id_responsavel
        LEFT JOIN Bebe b ON rb.id_bebe = b.id_bebe
    """)
    responsaveis = cursor.fetchall()
    conn.close()
    return render_template('responsaveis.html', responsaveis=responsaveis)

# rota pra listar leitos e ocupação
@app.route('/leitos')
def lista_leitos():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # buscamos os leitos e quem está neles
    cursor.execute("""
        SELECT l.*, b.nome as nome_bebe, b.data_nascimento, r.nome as nome_mae
        FROM Leito l
        LEFT JOIN Bebe b ON l.id_leito = b.id_leito
        LEFT JOIN Responsavel_Bebe rb ON b.id_bebe = rb.id_bebe AND rb.parentesco = 'Mãe'
        LEFT JOIN Responsavel r ON rb.id_responsavel = r.id_responsavel
    """)
    leitos = cursor.fetchall()
    conn.close()

    # conta quantos leitos têm um bebê
    total_ocupados = sum(1 for leito in leitos if leito['nome_bebe'])
    
    # O restante é disponível
    total_disponiveis = len(leitos) - total_ocupados

    return render_template('bercario.html', 
                           leitos=leitos, 
                           total_ocupados=total_ocupados, 
                           total_disponiveis=total_disponiveis)

# rota pra listar registros de evolução clínica
@app.route('/registros')
def lista_registros():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # verifica se veio um ID de bebê na URL
    id_bebe_filtro = request.args.get('id_bebe')
    
    # começamos a consulta básica
    sql = """
        SELECT e.*, b.nome as nome_bebe 
        FROM Evolucao_Clinica e 
        JOIN Bebe b ON e.id_bebe = b.id_bebe 
    """
    
    # se tiver filtro, adicionamos a cláusula WHERE
    params = []
    if id_bebe_filtro:
        sql += " WHERE b.id_bebe = %s "
        params.append(id_bebe_filtro)
    
    sql += " ORDER BY e.data_hora DESC"
    
    cursor.execute(sql, params)
    registros = cursor.fetchall()
    conn.close()
    
    return render_template('registros.html', registros=registros)

@app.route('/registros/novo', methods=('GET', 'POST'))
def novo_registro():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        id_bebe = request.form['id_bebe']
        descricao = request.form['descricao']
        peso_atual = request.form.get('peso_atual')
        
        if not peso_atual:
            peso_atual = None
            
        cursor.execute("""
            INSERT INTO Evolucao_Clinica (id_bebe, data_hora, descricao, peso_atual, id_funcionario) 
            VALUES (%s, NOW(), %s, %s, 1)
        """, (id_bebe, descricao, peso_atual))
        # nota: id_funcionario = 1 fixo por enquanto, pois não temos login
        
        conn.commit()
        conn.close()
        return redirect(url_for('lista_registros'))
    
    # busca bebês para preencher o select
    cursor.execute("SELECT b.id_bebe, b.nome, l.numero_quarto FROM Bebe b LEFT JOIN Leito l ON b.id_leito = l.id_leito")
    bebes = cursor.fetchall()
    conn.close()
    return render_template('form_registro.html', bebes=bebes)

# rota pra criar novo responsável
@app.route('/responsaveis/novo', methods=('GET', 'POST'))
def novo_responsavel():
    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        telefone = request.form['telefone']
        endereco = request.form['endereco']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Responsavel (nome, cpf, telefone, endereco) VALUES (%s, %s, %s, %s)", 
                       (nome, cpf, telefone, endereco))
        conn.commit()
        conn.close()
        return redirect(url_for('lista_responsaveis'))
    
    return render_template('form_responsavel.html')

# rota pra vincular responsável a bebê
@app.route('/responsaveis/vincular/<int:id_responsavel>', methods=['GET', 'POST'])
def vincular_responsavel(id_responsavel):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        id_bebe = request.form['id_bebe']
        parentesco = request.form['parentesco']
        
        # cria o vínculo na tabela de associação
        cursor.execute("INSERT INTO Responsavel_Bebe (id_responsavel, id_bebe, parentesco) VALUES (%s, %s, %s)", 
                       (id_responsavel, id_bebe, parentesco))
        conn.commit()
        conn.close()
        return redirect('/responsaveis')

    # se for GET buscamos os dados para preencher o formulário
    cursor.execute("SELECT * FROM Responsavel WHERE id_responsavel = %s", (id_responsavel,))
    responsavel = cursor.fetchone()
    
    cursor.execute("SELECT * FROM Bebe")
    bebes = cursor.fetchall()
    
    conn.close()
    return render_template('form_vinculo.html', responsavel=responsavel, bebes=bebes)

# rota pra excluir responsável
@app.route('/responsaveis/excluir/<int:id_responsavel>')
def excluir_responsavel(id_responsavel):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # primeiro removemos os vínculos desse responsável
    cursor.execute("DELETE FROM Responsavel_Bebe WHERE id_responsavel = %s", (id_responsavel,))
    
    # depois removemos a pessoa
    cursor.execute("DELETE FROM Responsavel WHERE id_responsavel = %s", (id_responsavel,))
    
    conn.commit()
    conn.close()
    return redirect('/responsaveis')

if __name__ == '__main__':
    app.run(debug=True)