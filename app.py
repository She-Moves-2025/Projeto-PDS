from datetime import datetime
from flask import Flask, render_template, request, redirect, session, url_for, flash 
from config import Config
from models import db, Profissional, Perfil, Login, Regiao, Modalidade, Cliente, RecuperarSenha, Notificacao, Avaliacao, Agendamento, Pagamento, Chat
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

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
        return redirect('/agenda')

    else:
        flash('Perfil inválido.')
        return redirect('/')

# ========== ROTA: Painel após login ===========
@app.route('/agenda')
def painel():
    if 'id' not in session:
        return redirect('/')
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

# ========== Rodar servidor ===========
if __name__ == '__main__':
    app.run(debug=True)