from datetime import datetime, date, timedelta
from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify, current_app 
from flask_sqlalchemy import SQLAlchemy
from config import Config
from models import db, Profissional, Perfil, Login, Regiao, Modalidade, Cliente, RecuperarSenha, Notificacao, Avaliacao, Agendamento, Pagamento, Chat, VerificacaoEmail
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import func, or_, and_
from sqlalchemy.orm import joinedload
from flask_babel import Babel
from flask_mail import Mail, Message
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from flask_socketio import SocketIO, emit, join_room
import eventlet
import base64
import os
import requests
import random, string
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from sib_api_v3_sdk.models import SendSmtpEmail
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config.from_object(Config)

# app.config['MAIL_SERVER'] = "smtp.gmail.com"
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = "shemoves.sistema@gmail.com"
# app.config['MAIL_PASSWORD'] = "nyla upss ebcv semv"
# mail = Mail(app)

configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = os.getenv("SENDINBLUE_API_KEY")

api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
    sib_api_v3_sdk.ApiClient(configuration)
)

socketio = SocketIO(app, async_mode='eventlet')

def get_locale():
    return session.get('lang', 'pt')

def gerar_codigo():
    return ''.join(random.choices(string.digits, k=6))


babel = Babel(app, locale_selector=get_locale)

# Configuração de idiomas
app.config['BABEL_DEFAULT_LOCALE'] = 'pt'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

db.init_app(app)

# Cria as tabelas no banco
with app.app_context():
    db.create_all()

@app.route('/change_lang/<lang>')
def change_lang(lang):
    session['lang'] = lang
    return redirect(request.referrer or url_for('home'))

def calcular_idade(data_nascimento):
    hoje = date.today()
    return hoje.year - data_nascimento.year - ((hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))

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
        data_nascimento_str = request.form.get('nascimento')
        data_nascimento = datetime.strptime(data_nascimento_str, '%Y-%m-%d').date()
        idade = calcular_idade(data_nascimento)
        senha = generate_password_hash(request.form['senha'])

        cpf = ''.join(filter(str.isdigit, cpf))

        # Valida CPF
        if not validar_cpf(cpf):
            flash(('CPF inválido.'), 'error')
            return render_template('cadastro-cliente.html')

        # Verifica se já existe um login com esse e-mail
        if Login.query.filter_by(email=email).first():
            flash(('E-mail já cadastrado.'), 'error')
            return render_template('cadastro-cliente.html')

        # Verifica se já existe cliente com esse CPF
        if Cliente.query.filter_by(cpf=cpf).first():
            flash(('CPF já cadastrado.'), 'error')
            return render_template('cadastro-cliente.html')

        if idade < 13:
            flash(('Você precisa ter pelo menos 13 anos para se cadastrar.'), 'error')
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

        # Gerar código e salvar no Login
        codigo = gerar_codigo()
        login.codigo_verificacao = codigo
        login.expira_em = datetime.utcnow() + timedelta(minutes=5)
        db.session.commit()

        # Enviar e-mail
        # msg = Message("Verificação de E-mail - SheMoves",
        #             sender=app.config['MAIL_USERNAME'],
        #             recipients=[login.email])
        # msg.body = f"Seu código de verificação é: {codigo}\nEle expira em 5 minutos."
        # mail.send(msg)

        send_smtp_email = SendSmtpEmail(
            to=[{"email": login.email}],
            sender={"name": "SheMoves", "email": "shemoves.sistema@gmail.com"},
            subject="Verificação de E-mail - SheMoves",
            html_content=f"<p>Seu código de verificação é: <b>{codigo}</b><br>Ele expira em 5 minutos.</p>"
        )
        try:
            api_instance.send_transac_email(send_smtp_email)
        except ApiException as e:
            print("Erro ao enviar e-mail:", e)

        flash(('Código de verificação enviado para seu e-mail.'), 'info')

        session['tipo'] = 'cliente'
        session['id'] = cliente.id

        return redirect(url_for('verificar_email', email=login.email))

    return render_template('cadastro-cliente.html')

# ========== ROTA: Cadastro Profissional ===========
@app.route('/cadastro-profissional', methods=['GET', 'POST'])
def cadastro_profissional():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        cpf = request.form['cpf']
        nascimento = request.form['nascimento']
        data_nascimento_str = request.form.get('nascimento')
        data_nascimento = datetime.strptime(data_nascimento_str, '%Y-%m-%d').date()
        idade = calcular_idade(data_nascimento)
        cref = request.form['cref']
        senha = generate_password_hash(request.form['senha'])

        cpf = ''.join(filter(str.isdigit, cpf))

        # Valida CPF
        if not validar_cpf(cpf):
            flash(('CPF inválido.'), 'error')
            return render_template('cadastro-profissional.html')

        # Verifica se já existe um login com esse e-mail
        if Login.query.filter_by(email=email).first():
            flash(('E-mail já cadastrado.'), 'error')
            return render_template('cadastro-profissional.html')

        # Verifica se já existe cliente com esse CPF
        if Profissional.query.filter_by(cpf=cpf).first():
            flash(('CPF já cadastrado.'), 'error')
            return render_template('cadastro-profissional.html')
        
        if idade < 18:
            flash(('Você precisa ter pelo menos 18 anos para se cadastrar.'), 'error')
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
        
        # Gerar código e salvar no Login
        codigo = gerar_codigo()
        login.codigo_verificacao = codigo
        login.expira_em = datetime.utcnow() + timedelta(minutes=5)
        db.session.commit()

        # Enviar e-mail
        # msg = Message("Verificação de E-mail - SheMoves",
        #             sender=app.config['MAIL_USERNAME'],
        #             recipients=[login.email])
        # msg.body = f"Seu código de verificação é: {codigo}\nEle expira em 5 minutos."
        # mail.send(msg)

        send_smtp_email = SendSmtpEmail(
            to=[{"email": login.email}],
            sender={"name": "SheMoves", "email": "shemoves.sistema@gmail.com"},
            subject="Verificação de E-mail - SheMoves",
            html_content=f"<p>Seu código de verificação é: <b>{codigo}</b><br>Ele expira em 5 minutos.</p>"
        )
        try:
            api_instance.send_transac_email(send_smtp_email)
        except ApiException as e:
            print("Erro ao enviar e-mail:", e)


        flash(('Código de verificação enviado para seu e-mail.'), 'info')

        session['tipo'] = 'profissional'
        session['id'] = profissional.id

        return redirect(url_for('verificar_email', email=login.email))

    return render_template('cadastro-profissional.html')

# ========== ROTA: Verificação de e-mail ==========

@app.route('/verificar-email', methods=['GET', 'POST'])
def verificar_email():
    email = request.args.get("email")
    login = Login.query.filter_by(email=email).first()

    if not login:
        flash(("Usuária não encontrada."), "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        codigo = request.form.get("codigo")

        if login.codigo_verificacao != codigo:
            flash(("Código inválido."), "error")
            return redirect(url_for("verificar_email", email=email))

        if login.expira_em < datetime.utcnow():
            flash(("Código expirado, solicite novamente."), "error")
            return redirect(url_for("verificar_email", email=email))

        login.email_verificado = True
        login.codigo_verificacao = None  # opcional: limpar
        db.session.commit()

        flash(("E-mail verificado com sucesso!"), "success")
        
        return redirect("/envio-documentos")
    
    return render_template("verificar-email.html", email=email)

# ========== ROTA: Envio de Documentos ==========

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

        flash(('Documentos enviados com sucesso! Aguarde aprovação.'))
        return redirect('/aguardando-aprovacao')

    return render_template('envio-documentos.html')


# ========== ROTA: Tela de Aguardando Aprovação ===========
@app.route('/aguardando-aprovacao')
def aguardando_aprovacao():
    return render_template('aguardando.html')

# ========== ROTA: Login ===========
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        if email == 'admin@master' and senha == '010203':
            session['master'] = True
            return redirect('/painel-master')

        login_user = Login.query.filter_by(email=email).first()

        if not login_user:
            flash(('Usuária não encontrada.'))
            return redirect('/')
        
        if not check_password_hash(login_user.senha, senha):
            flash(('Senha incorreta.'))
            return redirect('/')
        
        if not getattr(login_user, "email_verificado", False):
            flash(("Confirme seu e-mail antes de continuar."), "warning")
            return redirect(url_for("verificar_email", email=login_user.email))

        perfil = Perfil.query.get(login_user.id_perfil)
        session['id_perfil'] = perfil.id 


        if perfil.id_cliente:
            cliente = Cliente.query.get(perfil.id_cliente)
            if not cliente.validado:
                return redirect('/aguardando-aprovacao')

            session['id'] = cliente.id
            session['tipo'] = 'cliente'
            session['user_name'] = cliente.nome
            return redirect('/agenda')

        elif perfil.id_profissional:
            profissional = Profissional.query.get(perfil.id_profissional)
            if not profissional.validado:
                return redirect('/aguardando-aprovacao')

            session['id'] = profissional.id
            session['tipo'] = 'profissional'
            session['user_name'] = profissional.nome

            tem_regioes = Regiao.query.filter_by(id_profissional=profissional.id).first()
            tem_modalidades = Modalidade.query.filter_by(id_profissional=profissional.id).first()
            if not tem_regioes or not tem_modalidades:
                return redirect('/modalidade-local')
            return redirect('/agenda')

    return render_template('login.html')  # GET mostra a tela
# ========== ROTA: Painel após login ===========
@app.route('/agenda')
def agenda():
    if 'id' not in session:
        return redirect('/')
    
    tipo = session.get('tipo')
    id_perfil = session.get('id')

    if tipo == 'profissional':
        agendamentos = Agendamento.query.filter_by(id_profissional=id_perfil).all()
    else:
        agendamentos = Agendamento.query.filter_by(id_cliente=id_perfil).all()

    return render_template(
        'agenda.html',
        user_name=session.get('user_name'),
        agendamentos=agendamentos
    )


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
        bairros = data.get('result', [])

        # Se cada bairro é um dicionário com chave "name"
        bairros_ordenados = sorted(bairros, key=lambda b: b.get("name", "").lower())

    return jsonify(bairros_ordenados), resp.status_code

@app.route('/api/cidades-sugestao')
def api_cidades_sugestao():
    termo = request.args.get('q', '').strip()
    if not termo:
        return jsonify([])

    resultados = (
    db.session.query(Regiao.cidade, Regiao.estado)
    .filter(func.lower(Regiao.cidade).like(f"%{termo.lower()}%"))
    .distinct()
    .limit(10)
    .all()
    )

    return jsonify([{'cidade': c, 'estado': e} for c, e in resultados])


# --- TELA DE CADASTRO DE REGIÃO E MODALIDADE ---

@app.route('/modalidade-local', methods=['GET', 'POST'])
def modalidade_local():
    if 'id' not in session:
        return redirect('/')

    if session.get('tipo') == 'cliente':
        return redirect('/busca')

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
            flash(('Configuração salva com sucesso!'), 'sucess')
            return redirect('/agenda')  # Redireciona para a página inicial
        else:
            flash(('Adicione ao menos um local de atendimento.'), 'error')
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
        login = Login.query.filter_by(email=email).first()

        if not login:
            flash(('E-mail não encontrado.'), 'error')
            return redirect(url_for('esqueceu_senha'))

        codigo = ''.join(random.choices(string.digits, k=6))
        login.codigo_verificacao = codigo
        login.expira_em = datetime.utcnow() + timedelta(minutes=5)
        db.session.commit()

        # msg = Message(_("Recuperação de senha"), sender=app.config['MAIL_USERNAME'], recipients=[email])
        # msg.body = _(f"Seu código de recuperação é: {codigo}. Ele expira em 5 minutos.")
        # mail.send(msg)

        send_smtp_email = SendSmtpEmail(
            to=[{"email": email}],
            sender={"name": "SheMoves", "email": "shemoves.sistema@gmail.com"},
            subject="Recuperação de Senha",
            html_content=f"<p>Seu código de recuperação é: <b>{codigo}</b><br>Ele expira em 5 minutos.</p>"
        )
        try:
            api_instance.send_transac_email(send_smtp_email)
        except ApiException as e:
            print("Erro ao enviar e-mail:", e)


        flash(('Enviamos um código de recuperação para seu e-mail.'), 'sucess')
        return redirect(url_for('confirmar_codigo', email=email))

    return render_template('esqueceu-senha.html')

# ========== ROTA: Confirmar código ===========
@app.route('/confirmar-codigo/<email>', methods=['GET', 'POST'])
def confirmar_codigo(email):
    login = Login.query.filter_by(email=email).first()
    if not login:
        flash(('Usuária não encontrada.'), 'error')
        return redirect(url_for('esqueceu_senha'))

    if request.method == 'POST':
        codigo = request.form['codigo']

        if login.codigo_verificacao != codigo:
            flash(('Código inválido.'), 'error')
            return redirect(url_for('confirmar_codigo', email=email))

        if login.expira_em < datetime.utcnow():
            flash(('O código expirou, solicite um novo.'), 'error')
            return redirect(url_for('esqueceu_senha'))

        # Código confirmado
        session['reset_email'] = email
        return redirect(url_for('nova_senha'))

    return render_template('confirmar-codigo.html', email=email)

# ========== ROTA: Nova senha ===========
@app.route('/nova-senha', methods=['GET', 'POST'])
def nova_senha():
    email = session.get('reset_email')
    if not email:
        flash(('Sessão expirada, solicite novamente.'), 'error')
        return redirect(url_for('esqueceu_senha'))

    login = Login.query.filter_by(email=email).first()

    if request.method == 'POST':
        senha = request.form['senha']
        login.senha = generate_password_hash(senha)
        login.codigo_verificacao = None
        login.expira_em = None
        db.session.commit()

        session.pop('reset_email', None)
        flash(('Senha alterada com sucesso. Faça login novamente.'), 'success')
        return redirect(url_for('login'))

    return render_template('nova-senha.html')

# ========== Perfil ===========
@app.route('/perfil')
def perfil():
    return render_template('perfil.html')

# ========== Meu Perfil ===========

@app.route('/meu-perfil', methods=['GET', 'POST'])
def meu_perfil():
    if 'id' not in session or session.get('tipo') != 'profissional':
        return redirect('/')

    profissional_id = session['id']
    perfil = Perfil.query.filter_by(id_profissional=profissional_id).first()
    profissional = Profissional.query.get(profissional_id)
    login = Login.query.filter_by(id_perfil=perfil.id).first()  # ou ajuste conforme seu relacionamento

    if request.method == 'POST':
        celular = request.form.get('celular')
        biografia = request.form.get('biografia')[:500]
        email = request.form.get('email')

        # Atualiza perfil
        perfil.celular = celular
        perfil.biografia = biografia

        # Atualiza e-mail
        if login and email:
            login.email = email

        # Atualiza imagem (igual ao exemplo anterior)
        file = request.files.get('imagem_perfil')
        if file and file.filename:
            filename = secure_filename(file.filename)
            upload_path = os.path.join('static', 'uploads', filename)
            file.save(upload_path)
            perfil.imagem_perfil = upload_path

        db.session.commit()
        flash(('Perfil atualizado com sucesso!'), 'success')
        return redirect(url_for('meu_perfil'))

    return render_template('meu-perfil.html', perfil=perfil, email=login.email if login else '')

# ========== ROTA: Pesquisa de Profissionas  ===========

@app.route('/busca', methods=['GET', 'POST'])
def buscar():
    if 'id' not in session:
        return redirect('/')
    
    if session.get('tipo') == 'profissional':
        return redirect('/modalidade-local')

    modalidades_disponiveis = [
        'Pilates', 'Musculação', 'Yoga', 'Fit Dance', 'Boxe',
        'Alongamento', 'Crossfit', 'Dança', 'Treinamento Funcional', 'Natação'
    ]

    if request.method == 'POST':
        estado = request.form.get('estado')
        cidade = request.form.get('cidade') 
        cidade_digitada = request.form.get('cidade_digitada')
        bairro = request.form.get('bairro')
        modalidade = request.form.get('modalidade')

        if cidade_digitada and not cidade:
           partes = cidade_digitada.split('-')
           cidade = partes[0].strip()
           if len(partes) > 1:
              estado = partes[1].strip()

        return redirect(url_for(
            'resultados_busca',
            estado=estado or '',
            cidade=cidade or '',
            bairro=bairro or '',
            modalidade=modalidade or ''
        ))

    return render_template('busca.html', modalidades=modalidades_disponiveis)

@app.route('/resultados')
def resultados_busca():
    if 'id' not in session:
        return redirect('/')

    if session.get('tipo') == 'profissional':
        return redirect('/modalidade-local')
    
    estado = request.args.get('estado', '').strip()
    cidade = request.args.get('cidade', '').strip()
    bairro = request.args.get('bairro', '').strip().lower()
    modalidade = request.args.get('modalidade', '').strip().lower()

    query = Profissional.query.join(Regiao).join(Modalidade).filter(Profissional.validado == True)

    if cidade:
        query = query.filter(func.lower(Regiao.cidade) == cidade.lower())

    if bairro:
        query = query.filter(func.lower(Regiao.bairro) == bairro)

    if modalidade:
        query = query.filter(func.lower(Modalidade.nome) == modalidade)

    profissionais = query.options(joinedload(Profissional.perfil)).all()

    # Gera texto dinâmico para exibir na página
    if cidade and not bairro and not modalidade:
        descricao_busca = f"{cidade}"
    elif cidade and bairro and not modalidade:
        descricao_busca = f"{bairro}, {cidade}"
    elif cidade and modalidade and not bairro:
        descricao_busca = f"{modalidade.title()} em {cidade}"
    elif cidade and bairro and modalidade:
        descricao_busca = f"{modalidade.title()} em {bairro}, {cidade}"
    else:
        descricao_busca = "Resultados da busca"

    return render_template(
        'resultados.html',
        profissionais=profissionais,
        busca_info={
            'estado': estado,
            'cidade': cidade,
            'bairro': bairro,
            'modalidade': modalidade,
            'descricao': descricao_busca
        }
    )


# ========== Lista Chat===========
@app.route('/lista-chat')
def listachat():
    if 'id_perfil' not in session:
        return redirect('/')

    id_perfil = session['id_perfil']

    # Pega todos os chats onde o perfil aparece
    chats = Chat.query.filter(
        (Chat.remetente_id == id_perfil) | (Chat.destinatario_id == id_perfil)
    ).all()

    ids = set()
    for c in chats:
        if c.remetente_id != id_perfil:
            ids.add(c.remetente_id)
        elif c.destinatario_id != id_perfil:
            ids.add(c.destinatario_id)

    # Carregar perfis das pessoas que conversaram
    pessoas = Perfil.query.filter(Perfil.id.in_(ids)).all()

    return render_template('lista-chat.html', pessoas=pessoas)


@app.route('/chat/<int:id_destino>')
def chat(id_destino):
    if 'id_perfil' not in session:
        return redirect('/')

    id_perfil = session['id_perfil']

    # Monta uma "sala" única entre dois perfis
    sala = f"perfil_{min(id_perfil, id_destino)}_{max(id_perfil, id_destino)}"

    outra_pessoa = Perfil.query.get(id_destino)

    historico = Chat.query.filter(
        ((Chat.remetente_id == id_perfil) & (Chat.destinatario_id == id_destino)) |
        ((Chat.remetente_id == id_destino) & (Chat.destinatario_id == id_perfil))
    ).order_by(Chat.timestamp).all()

    return render_template(
        'chat.html',
        sala=sala,
        outra_pessoa=outra_pessoa,
        historico=historico
    )


@socketio.on('entrar')
def entrar(data):
    join_room(data['sala'])


@socketio.on('mensagem')
def handle_mensagem(data):
    remetente_id = session.get('id_perfil')
    sala = data['sala']
    tipo_msg = data['tipo']

    # Determinar o ID do destinatário pela sala
    partes = sala.replace("perfil_", "").split("_")
    ids = list(map(int, partes))
    destinatario_id = ids[0] if ids[1] == remetente_id else ids[1]

    if tipo_msg == 'texto':
        msg = data.get('msg')
        nova_msg = Chat(
            remetente_id=remetente_id,
            destinatario_id=destinatario_id,
            mensagem=msg
        )
        db.session.add(nova_msg)
        db.session.commit()

        emit('mensagem', {
            'msg': msg,
            'remetente_id': remetente_id,
            'tipo': 'texto'
        }, to=sala)

        emit('nova_mensagem', {
            'remetente_id': remetente_id,
            'destinatario_id': destinatario_id,
            'msg': msg
        }, broadcast=True)

    elif tipo_msg == 'audio':
        base64_audio = data.get('audio')
        nova_msg = Chat(
            remetente_id=remetente_id,
            destinatario_id=destinatario_id,
            mensagem=base64_audio
        )
        db.session.add(nova_msg)
        db.session.commit()

        emit('mensagem', {
            'audio': base64_audio,
            'remetente_id': remetente_id,
            'tipo': 'audio'
        }, to=sala)

        emit('nova_mensagem', {
            'remetente_id': remetente_id,
            'destinatario_id': destinatario_id,
            'msg': '[áudio]'
        }, broadcast=True)

# ========== Cadastrar agendamento ===========
@app.route('/cadastrar-agendamento/<int:id_perfil_cliente>/<int:id_perfil_profissional>', methods=['GET', 'POST'])
def cadastrar_agendamento(id_perfil_cliente, id_perfil_profissional):
    if 'id' not in session or session.get('tipo') != 'profissional':
        return redirect('/')

    # Buscar o perfil da cliente
    perfil_cliente = Perfil.query.get(id_perfil_cliente)
    if not perfil_cliente or not perfil_cliente.id_cliente:
        flash("Perfil de cliente não encontrado.", "danger")
        return redirect('/')

    # Buscar o perfil da profissional
    perfil_profissional = Perfil.query.get(id_perfil_profissional)
    if not perfil_profissional or not perfil_profissional.id_profissional:
        flash("Perfil de profissional não encontrado.", "danger")
        return redirect('/')

    # Extrair os IDs reais
    id_cliente = perfil_cliente.id_cliente
    id_profissional = perfil_profissional.id_profissional

    if request.method == 'POST':
        data = request.form['data']
        horario = request.form['horario']
        local = request.form['local']
        valor = request.form['valor']
        atividade = request.form['atividade']

        agendamento = Agendamento(
            status='pendente',
            id_cliente=id_cliente,
            id_profissional=id_profissional,
            data=datetime.strptime(data, '%Y-%m-%d').date(),
            horario=datetime.strptime(horario, '%H:%M').time(),
            local=local,
            valor=valor,
            atividade=atividade
        )
        db.session.add(agendamento)
        db.session.commit()
        flash('Agendamento criado com sucesso!', 'success')

        # Redireciona para o chat com o perfil da cliente
        return redirect(url_for('chat', id_destino=id_perfil_cliente))

    return render_template(
        'cadastrar-agendamento.html',
        id_perfil_cliente=id_perfil_cliente,
        id_perfil_profissional=id_perfil_profissional
    )

# ========== Pagamento ===========
@app.route('/pagamento/<int:agendamento_id>')
def tela_pagamento(agendamento_id):
    # Aqui você pode buscar os dados do agendamento no banco
    agendamento = Agendamento.query.get_or_404(agendamento_id)

    return render_template(
        'tela-pagamento.html',
        agendamento=agendamento
    )


# ========== Notificações ===========
@app.route('/notifiçações')
def notificacoes():
    return render_template('notificações.html')

# ========== Validações ===========
def validar_cpf(cpf: str) -> bool:
    cpf = ''.join(filter(str.isdigit, cpf))

    if len(cpf) != 11:
        return False

    if cpf == cpf[0] * 11:
        return False

    # Calcula o 1º dígito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito1 = (soma * 10 % 11) % 10

    if digito1 != int(cpf[9]):
        return False

    # Calcula o 2º dígito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito2 = (soma * 10 % 11) % 10

    if digito2 != int(cpf[10]):
        return False

    return True

# ========== Rodar servidor ===========
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)

