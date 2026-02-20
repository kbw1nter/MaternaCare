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
    
    # total de bebês
    cursor.execute("SELECT COUNT(*) as total FROM Bebe WHERE status = 'Ativo'")
    total_bebes = cursor.fetchone()['total']
    
    # dados de leitos 
    cursor.execute("SELECT COUNT(*) as total FROM Leito")
    total_leitos = cursor.fetchone()['total']
    
    #conta leitos ocupados 
    cursor.execute("SELECT COUNT(*) as ocupados FROM Bebe WHERE id_leito IS NOT NULL AND status = 'Ativo'")
    leitos_ocupados = cursor.fetchone()['ocupados']
    
    #cálculos dos leitos
    leitos_disponiveis = total_leitos - leitos_ocupados
    
    #cálculo da taxa de ocupação
    taxa_ocupacao = 0
    if total_leitos > 0:
        taxa_ocupacao = int((leitos_ocupados / total_leitos) * 100)
    
    #bebês recentes (ativos, sem contar os que já tiveram alta, ordenados por nascimento)
    cursor.execute("""
        SELECT b.*, l.numero_quarto 
        FROM Bebe b 
        LEFT JOIN Leito l ON b.id_leito = l.id_leito 
        WHERE b.status = 'Ativo'
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
    
    # O WHERE b.status = 'Ativo' esconde quem já teve alta
    cursor.execute("""
        SELECT b.*, l.numero_quarto, l.numero_berco
        FROM Bebe b 
        LEFT JOIN Leito l ON b.id_leito = l.id_leito 
        WHERE b.status = 'Ativo'
        ORDER BY b.nome
    """)
    bebes = cursor.fetchall()
    conn.close()
    return render_template('lista_bebes.html', bebes=bebes)

@app.route('/bebes/novo', methods=('GET', 'POST'))
def novo_bebe():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        #pega os dados do bebê
        nome = request.form['nome']
        peso = request.form['peso']
        altura = request.form['altura']
        id_leito = request.form.get('id_leito')
        
        #pga os dados do responsável 
        id_responsavel = request.form.get('id_responsavel')
        parentesco = request.form.get('parentesco')
        
        #insere o bebê
        cursor.execute("""
            INSERT INTO Bebe (nome, data_nascimento, peso_nascimento, altura_nascimento, id_leito, status) 
            VALUES (%s, NOW(), %s, %s, %s, 'Ativo')
        """, (nome, peso, altura, id_leito if id_leito else None))
        
        #pega o ID do bebê que acabou de nascer e salva o vínculo com a mãe
        id_bebe_novo = cursor.lastrowid
        if id_responsavel and parentesco:
            cursor.execute("INSERT INTO Responsavel_Bebe (id_responsavel, id_bebe, parentesco) VALUES (%s, %s, %s)", 
                           (id_responsavel, id_bebe_novo, parentesco))
            
        conn.commit()
        conn.close()
        return redirect(url_for('lista_bebes'))
    
    cursor.execute("SELECT * FROM Leito WHERE id_leito NOT IN (SELECT id_leito FROM Bebe WHERE id_leito IS NOT NULL)")
    leitos_livres = cursor.fetchall()
    
    cursor.execute("SELECT id_responsavel, nome, cpf FROM Responsavel WHERE status = 'Ativo'")
    responsaveis_lista = cursor.fetchall()
    
    conn.close()
    
    # envia essa lista para o HTML
    return render_template('form_bebe.html', leitos=leitos_livres, responsaveis=responsaveis_lista)

#rota de lista de responsáveis
@app.route('/responsaveis')
def lista_responsaveis():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # O WHERE r.status = 'Ativo' esconde quem já teve alta
    cursor.execute("""
        SELECT r.*, b.nome as nome_bebe, rb.parentesco
        FROM Responsavel r
        LEFT JOIN Responsavel_Bebe rb ON r.id_responsavel = rb.id_responsavel
        LEFT JOIN Bebe b ON rb.id_bebe = b.id_bebe
        WHERE r.status = 'Ativo'
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
        #id_funcionario = 1 fixo por enquanto, pois não temos login
        
        conn.commit()
        conn.close()
        return redirect(url_for('lista_registros'))
    
    # busca bebês para preencher o select
    cursor.execute("SELECT b.id_bebe, b.nome, l.numero_quarto FROM Bebe b LEFT JOIN Leito l ON b.id_leito = l.id_leito")
    bebes = cursor.fetchall()
    conn.close()
    return render_template('form_registro.html', bebes=bebes)

# rota de novo responsável
@app.route('/responsaveis/novo', methods=('GET', 'POST'))
def novo_responsavel():
    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        telefone = request.form['telefone']
        endereco = request.form['endereco']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO Responsavel (nome, cpf, telefone, endereco, status) 
            VALUES (%s, %s, %s, %s, 'Ativo')
        """, (nome, cpf, telefone, endereco))
        
        conn.commit()
        
        # dispara a notificação
        criar_notificacao(f"Novo responsável cadastrado: {nome}")
        
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

#rota para dar alta ou excluir 
@app.route('/bebes/acao/<int:id_bebe>/<acao>')
def acao_bebe(id_bebe, acao):
    conn = get_db_connection()
    cursor = conn.cursor()
    # muda o status do bebê para alta, tira do leito e marca a data
    cursor.execute("UPDATE Bebe SET status = %s, id_leito = NULL, data_saida = NOW() WHERE id_bebe = %s", (acao.capitalize(), id_bebe))
    conn.commit()
    criar_notificacao(f"Bebê marcado como: {acao}")
    conn.close()
    return redirect('/bebes')

@app.route('/responsaveis/acao/<int:id_responsavel>/<acao>')
def acao_responsavel(id_responsavel, acao):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    #da alta para o responsável
    cursor.execute("UPDATE Responsavel SET status = %s, data_saida = NOW() WHERE id_responsavel = %s", (acao.capitalize(), id_responsavel))
    
    #da alta para os bebês vinculados a ele e libera os berços
    cursor.execute("""
        UPDATE Bebe 
        SET status = %s, id_leito = NULL, data_saida = NOW() 
        WHERE id_bebe IN (SELECT id_bebe FROM Responsavel_Bebe WHERE id_responsavel = %s)
    """, (acao.capitalize(), id_responsavel))
    
    conn.commit()
    criar_notificacao(f"Responsável e seus bebês marcados como: {acao}")
    conn.close()
    return redirect('/responsaveis')

#pagina de historico 
@app.route('/historico')
def historico():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    #busca os bebês que tiveram alta
    cursor.execute("""
        SELECT b.*, rb.parentesco, r.nome as nome_responsavel
        FROM Bebe b
        LEFT JOIN Responsavel_Bebe rb ON b.id_bebe = rb.id_bebe
        LEFT JOIN Responsavel r ON rb.id_responsavel = r.id_responsavel
        WHERE b.status IN ('Alta', 'Excluido')
        ORDER BY b.data_saida DESC
    """)
    bebes_hist = cursor.fetchall()
    
    #busca os responsáveis que tiveram alta
    cursor.execute("""
        SELECT r.*, rb.parentesco, b.nome as nome_bebe
        FROM Responsavel r
        LEFT JOIN Responsavel_Bebe rb ON r.id_responsavel = rb.id_responsavel
        LEFT JOIN Bebe b ON rb.id_bebe = b.id_bebe
        WHERE r.status IN ('Alta', 'Excluido')
        ORDER BY r.data_saida DESC
    """)
    resp_hist = cursor.fetchall()
    
    conn.close()
    return render_template('historico.html', bebes=bebes_hist, responsaveis=resp_hist)

if __name__ == '__main__':
    app.run(debug=True)