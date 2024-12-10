import pandas as pd
import plotly.express as px
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from dao import dao

app = Flask(__name__)
app.secret_key = 'testedechave'

def verificar_sessao():
    if 'login_user' not in session:
        flash("Você precisa estar logado para acessar essa página.")
        return False
    return True


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

@app.route('/dashboard')
def dashboard():
    if not verificar_sessao():
        return redirect(url_for('home'))
    return render_template('dashboard.html')

@app.route('/cadastrar_produto', methods=['GET', 'POST'])
def cadastrar_produto():
    if not verificar_sessao():
        return redirect(url_for('home'))

    if request.method == 'POST':
        produto = request.form.get('Produto')
        qtde = int(request.form.get('qtde'))
        preco = float(request.form.get('preco'))

        conn = dao.conectardb()
        cur = None
        try:
            tipo_usuario = dao.verificar_tipo_usuario(session['login_user'], conn)
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM produtos WHERE loginUser = %s", (session['login_user'],))
            product_count = cur.fetchone()[0]

            if tipo_usuario == 'normal' and product_count >= 3:
                flash('Usuários normais podem cadastrar no máximo 3 produtos.')
                return redirect(url_for('cadastrar_produto'))

            cur.execute("INSERT INTO produtos (Produto, loginUser, qtde, preco) VALUES (%s, %s, %s, %s)",
                        (produto, session['login_user'], qtde, preco))
            conn.commit()

            return redirect(url_for('lista_produtos'))

        except Exception as e:
            if conn and not conn.closed:
                conn.rollback()
            flash(f"Erro ao cadastrar produto: {e}")
        finally:
            if cur:
                cur.close()
            if conn and not conn.closed:
                conn.close()

    return render_template('cadastrar-produto.html')

@app.route('/lista_produtos')
def lista_produtos():
    global cur
    if not verificar_sessao():
        return redirect(url_for('home'))

    conn = dao.conectardb()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, Produto, qtde, preco FROM produtos WHERE loginUser = %s", (session['login_user'],))
        produtos = cur.fetchall()

        return render_template('lista-produtos.html', produtos=produtos)

    except Exception as e:
        flash(f"Erro ao carregar os produtos: {e}", "error")
        return render_template('lista-produtos.html', produtos=[])  # Retorne uma página vazia ou com uma mensagem
    finally:
        if cur:
            cur.close()
        if conn and not conn.closed:
            conn.close()

@app.route('/deletar_produto/<int:produto_id>', methods=['POST'])
def deletar_produto(produto_id):
    global cur
    if not verificar_sessao():
        return redirect(url_for('home'))

    conn = dao.conectardb()
    try:
        cur = conn.cursor()

        cur.execute("DELETE FROM produtos WHERE id = %s AND loginuser = %s",
                    (produto_id, session['login_user']))
        conn.commit()
        flash("Produto deletado com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao deletar o produto: {e}", "error")
    finally:
        if cur:
            cur.close()
        if conn and not conn.closed:
            conn.close()

    return redirect(url_for('lista_produtos'))

@app.route('/grafico_vendas', methods=['GET'])
def grafico_vendas():
    if not verificar_sessao():
        return redirect(url_for('home'))

    conn = dao.conectardb()
    cur = None
    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT 
                produto_id,
                COALESCE(SUM(quantidade), 0) AS quantidade
            FROM vendas
            WHERE loginuser = %s
            GROUP BY produto_id
            ORDER BY produto_id
        """, (session['login_user'],))

        vendas_data = cur.fetchall()


        df = pd.DataFrame(vendas_data, columns=["produto_id", "quantidade"])

        fig = px.bar(
            df,
            x="produto_id",
            y="quantidade",
            color="produto_id",
            title="Quantidade de Produtos Vendidos",
            labels={"produto_id": "ID do Produto", "quantidade": "Quantidade Vendida"}
        )

        fig.update_layout(xaxis_title="ID do Produto", yaxis_title="Quantidade Vendida")


        graph_html = fig.to_html(full_html=False)
        return render_template('grafico_vendas.html', graph_html=graph_html)

    except Exception as e:
        flash(f"Erro ao gerar gráfico de vendas: {e}")
        return redirect(url_for('dashboard'))

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/cadastrar_venda', methods=['GET', 'POST'])
def cadastrar_venda():
    if not verificar_sessao():
        return redirect(url_for('home'))

    conn = dao.conectardb()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, produto FROM produtos WHERE loginUser = %s", (session['login_user'],))
        produtos = cur.fetchall()

        if not produtos:
            flash("Nenhum produto encontrado. Por favor, cadastre um produto primeiro.")
            return redirect(url_for('cadastrar_produto'))

        if request.method == 'POST':
            produto_id = int(request.form.get('produto_id'))
            quantidade = int(request.form.get('quantidade'))
            preco_unitario = float(request.form.get('preco_unitario'))

            if dao.registrar_venda(produto_id, session['login_user'], quantidade, preco_unitario, conn):
                flash('Venda registrada com sucesso!')
                return redirect(url_for('grafico_vendas'))
            else:
                flash('Erro ao registrar a venda.')

        return render_template('cadastrar_venda.html', produtos=produtos)

    except Exception as e:
        flash(f"Erro ao carregar a página de vendas: {e}")
        return redirect(url_for('dashboard'))

    finally:
        cur.close()
        conn.close()

@app.route('/logout')
def logout():
    session.pop('login_user', None)
    return redirect(url_for('home'))

@app.route('/api/produtos', methods=['POST'])
def api_inserir_produto():
    global cur
    if not request.json or 'Produto' not in request.json or 'qtde' not in request.json or 'preco' not in request.json:
        return jsonify({'error': 'Dados incompletos'}), 400

    produto = request.json['Produto']
    qtde = request.json['qtde']
    preco = request.json['preco']

    conn = dao.conectardb()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO produtos (Produto, loginUser, qtde, preco) VALUES (%s, %s, %s, %s)",
                    (produto, session.get('login_user', 'anonimo'), qtde, preco))
        conn.commit()
        return jsonify({'message': 'Produto inserido com sucesso'}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/produtos/<id_or_name>', methods=['GET'])
def api_buscar_produto(id_or_name):
    global cur
    conn = dao.conectardb()
    try:
        cur = conn.cursor()
        if id_or_name.isdigit():
            cur.execute("SELECT * FROM produtos WHERE id = %s", (id_or_name,))
        else:
            cur.execute("SELECT * FROM produtos WHERE Produto = %s", (id_or_name,))
        produto = cur.fetchone()
        if produto:
            produto_dict = {
                'id': produto[0],
                'Produto': produto[1],
                'loginUser': produto[2],
                'qtde': produto[3],
                'preco': produto[4]
            }
            return jsonify(produto_dict)
        else:
            return jsonify({'error': 'Produto não encontrado'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/api/produtos', methods=['GET'])
def api_listar_produtos():
    conn = dao.conectardb()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM produtos")
        produtos = cur.fetchall()
        produtos_lista = []
        for produto in produtos:
            produto_dict = {
                'id': produto[0],
                'Produto': produto[1],
                'loginUser': produto[2],
                'qtde': produto[3],
                'preco': produto[4]
            }
            produtos_lista.append(produto_dict)

        return jsonify(produtos_lista)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/usuarios', methods=['GET'])
def listar_usuarios():
    conn = dao.conectardb()
    try:
        cur = conn.cursor()
        cur.execute("SELECT loginuser, tipouser FROM usuarios")
        usuarios = cur.fetchall()
        usuarios_lista = []
        for usuario in usuarios:
            usuario_dict = {
                'loginuser': usuario[0],
                'tipouser': usuario[1]
            }
            usuarios_lista.append(usuario_dict)

        return jsonify(usuarios_lista)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()