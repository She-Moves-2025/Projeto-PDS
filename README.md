# SheMoves - Plataforma para Conectar Profissionais e Alunas da Área de Educação Física

Este repositório contém o **backend (Flask + PostgreSQL)** e o **frontend (HTML/CSS/JS)** da plataforma SheMoves, com deploy voltado para o Render.

---

## 🚀 Tecnologias

- Python 3.10+
- Flask
- SQLAlchemy
- PostgreSQL
- HTML/CSS/JavaScript 
- Render 

---

## ⚙️ Instalação e Execução Local

### 🔧 Pré-requisitos

- Python 3.10 ou superior
- Git
- PostgreSQL instalado e rodando
- Editor de código-fonte
- Navegador moderno

---

### 📦 Passos para rodar localmente

1. **Clone o repositório:**
git clone https://github.com/She-Moves-2025/Projeto-PDS.git
cd Projeto-PDS

2. **Crie o ambiente virtual:**
**Linux/MacOS:
- python3 -m venv venv
- source venv/bin/activate

**Windows:
- python -m venv venv
- venv\Scripts\activate

3. **Instale as dependências:**
pip install -r requirements.txt

4. **Configure a conexão com o banco de dados PostgreSQL:**
No arquivo config.py, atualize a URI do banco:
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://usuario:senha@localhost:5432/nome_do_banco'

5. **Crie as tabelas no banco:**
no terminal rode:
- flask shell
- >>> from app import db
- >>> db.create_all()
- >>> exit()

6. **Execute a aplicação:**
flask run





