from flask import Flask, render_template, request, redirect, url_for, session, flash
from dao import dao
from functools import wraps

app = Flask(__name__)
app.secret_key = 'testedechave'

# Decorador para exigir login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'login_user' not in session:
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def home():
    return render_template('index2.html')


@app.route('/cadastrar_usuario', methods=['GET', 'POST'])
def cadastrar_usuario():
    if request.method == 'POST':
        login = request.form.get('login')
        senha = request.form.get('senha')
        tipo = request.form.get('tipo')

        conn = dao.conectardb()
        if dao.cadastrar_usuario(login, senha, tipo, conn):
            session['login_user'] = login
            return redirect(url_for('dashboard'))
        else:
            msg = 'Erro ao cadastrar usuário. Verifique se o login já existe.'
            return render_template('cadastrar_usuario.html', texto=msg)

    return render_template('cadastrar_usuario.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('home.html', user=session['login_user'])


@app.route('/fazer_login', methods=['POST'])
def fazer_login():
    login = request.form.get('login')
    senha = request.form.get('senha')

    conn = dao.conectardb()
    if dao.verificar_login(login, senha, conn):
        session['login_user'] = login
        return redirect(url_for('dashboard'))
    else:
        msg = 'Login ou senha incorretos'
        return render_template('index2.html', texto=msg)


@app.route('/cadastrar_produto', methods=['GET', 'POST'])
@login_required
def cadastrar_produto():
    """Página de cadastro de produto."""
    if request.method == 'POST':
        nome = request.form.get('nome')
        qtde = int(request.form.get('qtde'))
        preco = float(request.form.get('preco'))

        conn = dao.conectardb()
        cur = None
        try:
            cur = conn.cursor()

            tipo_usuario = dao.verificar_tipo_usuario(session['login_user'], conn)
            cur.execute("SELECT COUNT(*) FROM produtos WHERE loginUser = %s", (session['login_user'],))
            product_count = cur.fetchone()[0]

            if tipo_usuario == 'normal' and product_count >= 3:
                flash('Usuários normais podem cadastrar no máximo 3 produtos.')
                return redirect(url_for('cadastrar_produto'))

            dao.cadastrar_produto(session['login_user'], nome, qtde, preco, conn)

            conn.commit()
            flash('Produto cadastrado com sucesso!')
            return redirect(url_for('cadastrar_produto'))

        except Exception as e:
            if conn and not conn.closed:
                conn.rollback()
            flash(f"Erro ao cadastrar produto: {e}")
            print(e)
        finally:
            if cur:
                cur.close()
            if conn and not conn.closed:
                conn.close()

    return render_template('cadastrar-produto.html')


@app.route('/produtos')
@login_required
def listar_produtos():
    """Lista todos os produtos cadastrados."""
    conn = dao.conectardb()
    cur = conn.cursor()
    cur.execute("SELECT nome, qtde, preco FROM produtos WHERE loginUser = %s", (session['login_user'],))
    produtos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('lista_produtos.html', produtos=produtos)


@app.route('/logout')
def logout():
    """Faz logout do usuário."""
    session.pop('login_user', None)
    return redirect(url_for('home'))


@app.route('/comentario/inserir', methods=['POST'])
def inserirmsgdatabase():
    coment = request.form.get('mensagem')
    print(coment + " - " + session['login_user'])
    if dao.insert_comentario(session['login_user'], coment, dao.conectardb()):
        return 'inseriu com sucesso!'
    else:
        return render_template(home.html, user=session['login_user'])

if __name__ == '__main__':
    app.run(debug=True)

if __name__ == '__main__':
    app.run(debug=True)
