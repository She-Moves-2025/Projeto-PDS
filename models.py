from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


db = SQLAlchemy()


class Regiao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    estado = db.Column(db.String(50))
    cidade = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    id_profissional = db.Column(db.Integer, db.ForeignKey('profissional.id'))

class Modalidade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    id_profissional = db.Column(db.Integer, db.ForeignKey('profissional.id'))

class Profissional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    data_nascimento = db.Column(db.Date)
    cpf = db.Column(db.String(11))
    cref = db.Column(db.String(11))
    validado = db.Column(db.Boolean, default=False)
    documento = db.Column(db.String)
    selfie = db.Column(db.String)

    regioes = db.relationship('Regiao', backref='profissional', lazy=True)
    modalidades = db.relationship('Modalidade', backref='profissional', lazy=True)
    perfil = db.relationship('Perfil', backref='profissional', uselist=False)

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100))
    data_nascimento = db.Column(db.Date)
    cpf = db.Column(db.String(11))
    validado = db.Column(db.Boolean, default=False)
    documento = db.Column(db.String)
    selfie = db.Column(db.String)

    perfil = db.relationship('Perfil', backref='cliente', uselist=False)

class Perfil(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('cliente.id'))
    id_profissional = db.Column(db.Integer, db.ForeignKey('profissional.id'))
    criacao = db.Column(db.Date, default=datetime)
    celular = db.Column(db.String(15))
    biografia = db.Column(db.String(500))
    imagem_perfil = db.Column(db.String)

class Login(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_perfil = db.Column(db.Integer, db.ForeignKey('perfil.id'))
    email = db.Column(db.String(200), unique=True)
    senha = db.Column(db.String)

class RecuperarSenha(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    perfil_id = db.Column(db.Integer, db.ForeignKey('perfil.id'))
    nova_senha = db.Column(db.String)
    redefinido = db.Column(db.Boolean, default=False)
    redefinicao = db.Column(db.DateTime)
    codigo_verificacao = db.Column(db.String)

class Notificacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    perfil_id = db.Column(db.Integer, db.ForeignKey('perfil.id'))
    mensagem = db.Column(db.String(255))
    tipo = db.Column(db.String(50))
    lida = db.Column(db.Boolean, default=False)
    data_envio = db.Column(db.DateTime, default=datetime)

class Avaliacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissional.id'))
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'))
    comentario = db.Column(db.String(500))
    nota = db.Column(db.String(2))
    data = db.Column(db.DateTime, default=datetime)

class Agendamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(15))
    id_cliente = db.Column(db.Integer, db.ForeignKey('cliente.id'))
    id_profissional = db.Column(db.Integer, db.ForeignKey('profissional.id'))
    data = db.Column(db.Date)
    horario = db.Column(db.Time)
    local = db.Column(db.String(300))
    valor = db.Column(db.Numeric(10, 2))

class Pagamento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    agendamento_id = db.Column(db.Integer, db.ForeignKey('agendamento.id'))
    status = db.Column(db.String(15))
    metodo = db.Column(db.String(15))
    valor = db.Column(db.Integer)
    data_pagamento = db.Column(db.DateTime)

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    remetente_id = db.Column(db.Integer)
    destinatario_id = db.Column(db.Integer)
    mensagem = db.Column(db.Text)
    lida = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime)
