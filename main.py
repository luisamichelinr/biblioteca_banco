from flask import Flask, render_template, flash, redirect, url_for, request, session, send_from_directory, send_file
from flask_bcrypt import generate_password_hash, check_password_hash
import fdb
from fpdf import FPDF




app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'

# Mostrar para o python onde está e como acessar o banco
host = 'localhost'
database = r'C:\Users\Aluno\Documents\GitHub\biblioteca_banco\LIVRO.FDB'
user = 'sysdba'
password = 'sysdba'
con = fdb.connect(host=host, database=database, user=user, password=password)

@app.route('/')
def index():
    cursor = con.cursor()
    cursor.execute("select id_livro, titulo, autor, ano_publicacao from livro")
    livros = cursor.fetchall()
    cursor.close()

    return render_template('livros.html', livros=livros)



@app.route('/novo')
def novo():
    if "id_usuario" not in session:
        flash('Você precisa estar logado para acessar essa página', 'error')
        return redirect(url_for('login'))
    return render_template('novo.html', titulo='Novo livro')

@app.route('/criar', methods=['POST'])
def criar():
    titulo = request.form['titulo']
    autor = request.form['autor']
    ano_publicacao = request.form['ano_publicacao']

    cursor = con.cursor()
    try:
        cursor.execute('select 1 from livro where livro.titulo = ?', (titulo,))
        if cursor.fetchone():
            flash('Esse livro já está cadastrado', 'error')
            return redirect(url_for('novo'))
        cursor.execute(
            "insert into livro(titulo, autor, ano_publicacao) VALUES (?, ?, ?) RETURNING id_livro",
            (titulo, autor, ano_publicacao)
        )
        id_livro = cursor.fetchone()[0]
        con.commit()
        arquivo = request.files['arquivo']
        arquivo.save(f'uploads/capa{id_livro}.jpg')

        con.commit()
    finally:
        cursor.close()
    flash('O livro foi cadastrado com sucesso', 'success')
    return redirect(url_for('index'))

@app.route('/atualizar')
def atualizar():
    if "id_usuario" not in session:
        flash('Você precisa estar logado para acessar essa página', 'error')
        return redirect(url_for('login'))
    return render_template('editar.html', titulo='Editar Livro')

@app.route('/uploads/<nome_arquivo>')
def imagem(nome_arquivo):
    return send_from_directory('uploads', nome_arquivo)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    if "id_usuario" not in session:
        flash('Você precisa estar logado para acessar essa página', 'error')
        return redirect(url_for('login'))
    cursor = con.cursor()
    cursor.execute("select id_livro, titulo, autor, ano_publicacao from livro where id_livro = ?", (id,))
    livro = cursor.fetchone()

    if not livro:
        cursor.close()
        flash('Livro não foi encontrado', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        titulo = request.form['titulo']
        autor = request.form['autor']
        ano_publicacao = request.form['ano_publicacao']

        cursor.execute("update livro set titulo = ?, autor = ?, ano_publicacao = ? where id_livro = ?",
                       (titulo, autor, ano_publicacao, id))
        con.commit()
        cursor.close()  # Fecha o cursor ao final da função, se não for uma requisição POST
        flash('Livro atualizado com sucesso', 'success')
        return redirect(url_for('index'))

    cursor.close()
    return render_template('editar.html', livro=livro, titulo='Editar Livro')  # Renderiza a página de edição

@app.route('/deletar/<int:id>', methods=('POST',))
def deletar(id):
    cursor = con.cursor()  # Abre o cursor
    try:
        if "id_usuario" not in session:
            flash('Você precisa estar logado para acessar essa página', 'error')
            return redirect(url_for('login'))
        cursor.execute('DELETE FROM livro WHERE id_livro = ?', (id,))
        con.commit()  # Salva as alterações no banco de dados
        flash('Livro excluído com sucesso!', 'success')  # Mensagem de sucesso
    except Exception as e:
        con.rollback()  # Reverte as alterações em caso de erro
        flash('Erro ao excluir o livro.', 'error')  # Mensagem de erro
    finally:
        cursor.close()  # Fecha o cursor independentemente do resultado

    return redirect(url_for('index'))  # Redireciona para a página principal

@app.route('/usuarios')
def usuarios():
    if "id_usuario" not in session:
        flash('Você precisa estar logado para acessar essa página', 'error')
        return redirect(url_for('login'))
    cursor = con.cursor()
    cursor.execute("select id_usuario, nome, email, senha from usuario")
    usuarios = cursor.fetchall()
    cursor.close()

    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/novo_usuario')
def novo_usuario():
    return render_template('novo_usuario.html', titulo='Novo usuário')

@app.route('/criar_usuario', methods=['POST'])
def criar_usuario():
    nome = request.form['nome']
    email = request.form['email']
    senha = request.form['senha']
    senha_cripto = generate_password_hash(senha).decode('utf-8')

    cursor = con.cursor()
    try:
        cursor.execute('select 1 from usuario where usuario.email = ?', (email,))
        if cursor.fetchone():
            flash('Esse email já foi cadastrado', 'error')
            return redirect(url_for('novo_usuario'))
        cursor.execute('insert into usuario(nome, email, senha) values(?, ?, ?)',
                       (nome, email, senha_cripto))

        con.commit()
    finally:
        cursor.close()
    flash('O usuário foi cadastrado com sucesso', 'success')
    return redirect(url_for('usuarios'))

@app.route('/atualizar_usuario')
def atualizar_usuario():
        if "id_usuario" not in session:
            flash('Você precisa estar logado para acessar essa página', 'error')
            return redirect(url_for('login'))
        return render_template('editar_usuario.html', titulo='Editar Usuário')

@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
def editar_usuario(id):
    cursor = con.cursor()
    cursor.execute("select id_usuario, nome, email, senha from usuario where id_usuario = ?", (id,))
    usuario = cursor.fetchone()
    senha_cripto = usuario[3]


    if not usuario:
        cursor.close()
        flash('Usuário não foi encontrado', 'error')
        return redirect(url_for('usuarios'))

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        nova_senha = request.form['senha']

        cursor.execute('select 1 from usuario where usuario.email = ? and usuario.id_usuario != ?', (email, id,))
        if cursor.fetchone():
            flash('Esse email já foi cadastrado', 'error')
            return redirect(url_for('editar_usuario', id=usuario[0]))

        if not nova_senha:
            nova_senha_cripto = senha_cripto
        else:
            nova_senha_cripto = generate_password_hash(nova_senha)

        cursor.execute("update usuario set nome = ?, email = ?, senha = ? where id_usuario = ?",
                       (nome, email, nova_senha_cripto, id))
        con.commit()
        cursor.close()  # Fecha o cursor ao final da função, se não for uma requisição POST
        flash('Usuário atualizado com sucesso', 'success')
        return redirect(url_for('usuarios'))

    cursor.close()
    return render_template('editar_usuario.html', usuario=usuario, titulo='Editar Usuário')  # Renderiza a página de edição

@app.route('/deletar_usuario/<int:id>', methods=('POST',))
def deletar_usuario(id):
    cursor = con.cursor()
    try:
        if "id_usuario" not in session:
            flash('Você precisa estar logado para acessar essa página', 'error')
            return redirect(url_for('login'))
        cursor.execute('DELETE FROM usuario WHERE id_usuario = ?', (id,))
        con.commit()  # Salva as alterações no banco de dados
        flash('Usuário excluído com sucesso!', 'success')  # Mensagem de sucesso
    except Exception as e:
        con.rollback()  # Reverte as alterações em caso de erro
        flash('Erro ao excluir o usuário.', 'error')  # Mensagem de erro
    finally:
        cursor.close()  # Fecha o cursor independentemente do resultado

    return redirect(url_for('usuarios'))  # Redireciona para a página principal

@app.route('/login', methods=['GET', 'POST'])
def login():
    cursor = con.cursor()
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        cursor.execute("select id_usuario, email, senha from usuario where email = ?", (email,))
        usuario = cursor.fetchone()
        if not usuario:
            cursor.close()
            flash('Usuário não foi encontrado', 'error')
            return redirect(url_for('login'))
        senha_hash = usuario[2]
        if check_password_hash(senha_hash, senha):
            cursor.close()  # Fecha o cursor ao final da função, se não for uma requisição POST
            session["id_usuario"] = usuario[0]
            flash('Usuário logado com sucesso', 'success')
            return redirect(url_for('index'))
    cursor.close()
    return render_template('login.html', titulo='Login')  # Renderiza a página de edição

@app.route('/logout')
def logout():
    session.pop('id_usuario', None)
    return redirect(url_for('index'))

@app.route('/relatorio', methods=['GET'])
def relatorio():
    cursor = con.cursor()
    cursor.execute("SELECT id_livro, titulo, autor, ano_publicacao FROM livro")
    livros = cursor.fetchall()
    cursor.close()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, "Relatorio de Livros", ln=True, align='C')
    pdf.ln(5)  # Espaço entre o título e a linha
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())  # Linha abaixo do título
    pdf.ln(5)  # Espaço após a linha
    pdf.set_font("Arial", size=12)
    for livro in livros:
        pdf.cell(200, 10, f"ID: {livro[0]} - {livro[1]} - {livro[2]} - {livro[3]}", ln=True)
    contador_livros = len(livros)
    pdf.ln(10)  # Espaço antes do contador
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, f"Total de livros cadastrados: {contador_livros}", ln=True, align='C')
    pdf_path = "relatorio_livros.pdf"
    pdf.output(pdf_path)
    return send_file(pdf_path, as_attachment=True, mimetype='application/pdf')


if __name__ == '__main__':
    app.run(debug=True)
