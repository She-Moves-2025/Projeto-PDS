from datetime import datetime
from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify, current_app 
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db, Profissional, Perfil, Login, Regiao, Modalidade, Cliente, RecuperarSenha, Notificacao, Avaliacao, Agendamento, Pagamento, Chat
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import requests

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

# Cria as tabelas no banco
with app.app_context():
    db.create_all()

# ========== ROTA: Home =============
@app.route('/')
def home():
    return render_template('login.html')


# ========== ROTA: Cadastro-escolha =============
@app.route('/cadastro', methods=['GET'])
def cadastro():
    return render_template('cadastro-escolha.html')


# ========== ROTA: Cadastro Cliente ===========
@app.route('/cadastro-cliente', methods=['GET', 'POST'])
def cadastro_cliente():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        cpf = request.form['cpf']
        nascimento = request.form['nascimento']
        senha = generate_password_hash(request.form['senha'])

        # Verifica se já existe um login com esse e-mail
        if Login.query.filter_by(email=email).first():
            flash('E-mail já cadastrado.', 'error')
            return render_template('cadastro-cliente.html')

        # Verifica se já existe cliente com esse CPF
        if Cliente.query.filter_by(cpf=cpf).first():
            flash('CPF já cadastrado.', 'error')
            return render_template('cadastro-cliente.html')

        # Cria cliente
        cliente = Cliente(nome=nome, cpf=cpf, data_nascimento=nascimento, validado=False)
        db.session.add(cliente)
        db.session.commit()  

        # Cria perfil com id_cliente vinculado
        perfil = Perfil(id_cliente=cliente.id, criacao=datetime.now())
        db.session.add(perfil)
        db.session.commit()  

        login = Login(id_perfil=perfil.id, email=email, senha=senha)
        db.session.add(login)
        db.session.commit()

        session['tipo'] = 'cliente'
        session['id'] = cliente.id

        return redirect('/envio-documentos')

    return render_template('cadastro-cliente.html')

# ========== ROTA: Cadastro Profissional ===========
@app.route('/cadastro-profissional', methods=['GET', 'POST'])
def cadastro_profissional():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        cpf = request.form['cpf']
        nascimento = request.form['nascimento']
        cref = request.form['cref']
        senha = generate_password_hash(request.form['senha'])

        # Verifica se já existe um login com esse e-mail
        if Login.query.filter_by(email=email).first():
            flash('E-mail já cadastrado.', 'error')
            return render_template('cadastro-profissional.html')

        # Verifica se já existe cliente com esse CPF
        if Profissional.query.filter_by(cpf=cpf).first():
            flash('CPF já cadastrado.', 'error')
            return render_template('cadastro-profissional.html')

        # Cria cliente
        profissional = Profissional(nome=nome, cpf=cpf, data_nascimento=nascimento, validado=False, cref=cref)
        db.session.add(profissional)
        db.session.commit()  

        # Cria perfil com id_cliente vinculado
        perfil = Perfil(id_profissional=profissional.id, criacao=datetime.now())
        db.session.add(perfil)
        db.session.commit()  

        login = Login(id_perfil=perfil.id, email=email, senha=senha)
        db.session.add(login)
        db.session.commit()

        session['tipo'] = 'profissional'
        session['id'] = profissional.id

        return redirect('/envio-documentos')

    return render_template('cadastro-profissional.html')

# ========== ROTA: Envio de Documentos ===========
from werkzeug.utils import secure_filename
import os

@app.route('/envio-documentos', methods=['GET', 'POST'])
def envio_documentos():
    if 'id' not in session:
        return redirect('/')

    if request.method == 'POST':
        documento = request.files['documento']
        selfie = request.files['selfie']

        tipo = session['tipo']
        id_usuaria = session['id']

        # Pasta dentro de static/uploads/
        pasta_destino = os.path.join(app.config['UPLOAD_FOLDER'], f'{tipo}_{id_usuaria}')
        os.makedirs(pasta_destino, exist_ok=True)

        # Caminhos dos arquivos (salvos como .png fixos)
        documento_filename = secure_filename('documento.png')
        selfie_filename = secure_filename('selfie.png')

        documento_path = os.path.join(pasta_destino, documento_filename)
        selfie_path = os.path.join(pasta_destino, selfie_filename)

        documento.save(documento_path)
        selfie.save(selfie_path)

        # Caminhos relativos para salvar no banco (usados em HTML depois)
        documento_rel = os.path.relpath(documento_path, 'static')
        selfie_rel = os.path.relpath(selfie_path, 'static')

        # Atualiza os campos no banco
        if tipo == 'cliente':
            usuaria = Cliente.query.get(id_usuaria)
        else:
            usuaria = Profissional.query.get(id_usuaria)

        usuaria.documento = documento_rel
        usuaria.selfie = selfie_rel
        db.session.commit()

        flash('Documentos enviados com sucesso! Aguarde aprovação.')
        return redirect('/aguardando-aprovacao')

    return render_template('envio-documentos.html')


# ========== ROTA: Tela de Aguardando Aprovação ===========
@app.route('/aguardando-aprovacao')
def aguardando_aprovacao():
    return render_template('aguardando.html')

# ========== ROTA: Login ===========
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    senha = request.form['senha']

    if email == 'admin@master' and senha == '010203':
        session['master'] = True
        return redirect('/painel-master')

    login_user = Login.query.filter_by(email=email).first()

    if not login_user:
        flash('Usuária não encontrada.')
        return redirect('/')
    
    if not check_password_hash(login_user.senha, senha):
        flash('Senha incorreta.')
        return redirect('/')

    perfil = Perfil.query.get(login_user.id_perfil)

    if perfil.id_cliente:
        cliente = Cliente.query.get(perfil.id_cliente)
        if not cliente.validado:
            return redirect('/aguardando-aprovacao')

        session['id'] = cliente.id
        session['tipo'] = 'cliente'
        return redirect('/agenda')

    elif perfil.id_profissional:
          profissional = Profissional.query.get(perfil.id_profissional)
          if not profissional.validado:
              return redirect('/aguardando-aprovacao')

          session['id'] = profissional.id
          session['tipo'] = 'profissional'

          tem_regioes = Regiao.query.filter_by(id_profissional=profissional.id).first()
          tem_modalidades = Modalidade.query.filter_by(id_profissional=profissional.id).first()
          if not tem_regioes or not tem_modalidades:
              return redirect('/modalidade-local')
          return redirect('/agenda')

# ========== ROTA: Painel após login ===========
@app.route('/agenda')
def agenda():
    if 'id' not in session:
        return redirect('/')
    
    # if request.method == 'POST':

    #     tipo = session['tipo']
    #     id_usuaria = session['id']

    #     # Atualiza os campos no banco
    #     if tipo == 'cliente':
    #         usuaria = Cliente.query.get(id_usuaria)
    #     else:
    #         usuaria = Profissional.query.get(id_usuaria)
    #     return render_template('agenda.html')

    return render_template('agenda.html')

# ========== ROTA: Painel MASTER ===========
@app.route('/painel-master')
def painel_master():
    if not session.get('master'):
        return redirect('/')
    
    profissionais = Profissional.query.filter_by(validado=False).all()
    clientes = Cliente.query.filter_by(validado=False).all()
    return render_template('painel-master.html', profissionais=profissionais, clientes=clientes)

# ========== ROTA: Aprovar usuária ===========
@app.route('/aprovar/<tipo>/<int:id_usuaria>', methods=['POST'])
def aprovar_usuaria(tipo, id_usuaria):
    if not session.get('master'):
        return redirect('/')

    if tipo == 'cliente':
        user = Cliente.query.get(id_usuaria)
    else:
        user = Profissional.query.get(id_usuaria)

    user.validado = True
    db.session.commit()
    return redirect('/painel-master')

# ========== ROTA: Recusar usuária ===========
@app.route('/recusar/<tipo>/<int:id_usuaria>', methods=['POST'])
def recusar_usuaria(tipo, id_usuaria):
    if not session.get('master'):
        return redirect('/')

    if tipo == 'cliente':
        user = Cliente.query.get(id_usuaria)
    else:
        user = Profissional.query.get(id_usuaria)

    db.session.delete(user)
    db.session.commit()

    return redirect('/painel-master')

# ========== ROTA: Adicionar modalidade e local de profissional ===========
@app.route('/api/estados')
def api_estados():
    resp = requests.get('https://servicodados.ibge.gov.br/api/v1/localidades/estados?orderBy=nome')
    data = resp.json()
    return jsonify([{'id': e['id'], 'sigla': e['sigla'], 'nome': e['nome']} for e in data])

@app.route('/api/cidades/<int:id_estado>')
def api_cidades(id_estado):
    resp = requests.get(f'https://servicodados.ibge.gov.br/api/v1/localidades/estados/{id_estado}/municipios')
    data = resp.json()
    return jsonify([{'id': c['id'], 'nome': c['nome']} for c in data])

@app.route('/api/bairros/<int:id_cidade>')
def api_bairros(id_cidade):
    # Tente pegar do current_app.config primeiro
    api_key = current_app.config.get('BRASIL_ABERTO_API_KEY') or os.getenv('BRASIL_ABERTO_API_KEY')
    print(f"TOKEN: {api_key}")
    if not api_key:
        return jsonify({'result': []}), 500
    headers = {'Authorization': f'Bearer {api_key}'}
    url = f'https://api.brasilaberto.com/v1/districts-by-ibge-code/{id_cidade}'
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        return jsonify(data.get('result', []))
    return jsonify({'result': []}), resp.status_code

# --- TELA DE CONFIGURAÇÃO INICIAL ---
@app.route('/modalidade-local', methods=['GET', 'POST'])
def modalidade_local():
    if 'id' not in session or session.get('tipo') != 'profissional':
        return redirect('/')

    profissional_id = session['id']

    modalidades = [
        'Pilates', 
        'Musculação',
        'Yoga',
        'Fit Dance',
        'Boxe',
        'Alongamento',
        'Crossfit',
        'Dança',
        'Treinamento Funcional',
        'Natação'
    ]

    if request.method == 'POST':
        # Salva locais de atendimento
        locais = request.form.getlist('locais[]')
        Regiao.query.filter_by(id_profissional=profissional_id).delete()
        locais_salvos = 0
        for local in locais:
            estado, cidade, bairro = local.split('|')
            regiao = Regiao(estado=estado, cidade=cidade, bairro=bairro, id_profissional=profissional_id)
            db.session.add(regiao)
            locais_salvos += 1

        # Salva modalidades
        modalidades_selecionadas = request.form.getlist('modalidades[]')
        Modalidade.query.filter_by(id_profissional=profissional_id).delete()
        for nome in modalidades_selecionadas:
            modalidade = Modalidade(nome=nome, id_profissional=profissional_id)
            db.session.add(modalidade)

        db.session.commit()

        if locais_salvos > 0:
            flash('Configuração salva com sucesso!', 'sucess')
            return redirect('/agenda')  # Redireciona para a página inicial
        else:
            flash('Adicione ao menos um local de atendimento.', 'error')
            # Não redireciona, apenas recarrega a página mostrando a mensagem

    # Carrega dados já cadastrados
    regioes = Regiao.query.filter_by(id_profissional=profissional_id).all()
    regioes_list = [
        {'estado': r.estado, 'cidade': r.cidade, 'bairro': r.bairro}
        for r in regioes
    ]
    modalidades_salvas = [m.nome for m in Modalidade.query.filter_by(id_profissional=profissional_id).all()]

    return render_template(
        'modalidade-local.html',
        modalidades=modalidades,
        regioes=regioes_list,
        modalidades_salvas=modalidades_salvas
    )
# ========== ROTA: Esqueceu a senha  ===========
@app.route('/esqueceu-senha', methods=['GET', 'POST'])
def esqueceu_senha():
    if request.method == 'POST':
        email = request.form['email']
        
        flash('Se este e-mail estiver cadastrado, você receberá instruções para redefinir sua senha.')
        return redirect('/esqueceu-senha')
    return render_template('esqueceu-senha.html')

# ========== Perfil ===========
@app.route('/perfil')
def perfil():
    return render_template('perfil.html')

# ========== Meu Perfil ===========
@app.route('/meu-perfil')
def meuperfil():
    return render_template('meu-perfil.html')

# ========== Busca ===========
@app.route('/busca')
def busca():
    return render_template('busca.html')

# ========== Lista Chat===========
@app.route('/lista-chat')
def listachat():
    return render_template('lista-chat.html')

# ========== Notificações ===========
@app.route('/notifiçações')
def notificacoes():
    return render_template('notificações.html')


# ========== Rodar servidor ===========
if __name__ == '__main__':
    app.run(debug=True)
