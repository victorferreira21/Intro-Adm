import psycopg2

def conectardb():
    conn = psycopg2.connect(
        host='localhost',
        password='postgres',
        database='trabalho',
        user='postgres',
        port='5432',
    )
    return conn

def criar_tabelas():
    conn = conectardb()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        loginUser VARCHAR(50) PRIMARY KEY,
        senha VARCHAR(50),
        tipoUser VARCHAR(10)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        id SERIAL PRIMARY KEY,
        nome VARCHAR(100),
        loginUser VARCHAR(50) REFERENCES usuarios(loginUser),
        qtde INTEGER,
        preco DECIMAL(10, 2)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS vendas (
        id SERIAL PRIMARY KEY,
        produto_id INTEGER REFERENCES produtos(id),
        loginUser VARCHAR(50) REFERENCES usuarios(loginUser),
        data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        quantidade INTEGER,
        preco_unitario DECIMAL(10, 2)
    )
    """)

    conn.commit()
    cur.close()
    conn.close()

def registrar_venda(produto_id, loginuser, quantidade, preco_unitario, conn):
    try:
        cur = conn.cursor()


        cur.execute("""
            INSERT INTO vendas (produto_id, loginuser, quantidade, preco_unitario)
            VALUES (%s, %s, %s, %s)
        """, (produto_id, loginuser, quantidade, preco_unitario))

        conn.commit()
        cur.close()
        return True
    except Exception as e:
        print(f"Erro ao registrar venda: {e}")
        conn.rollback()
        return False


def verificar_tipo_usuario(login, conn):
    cur = conn.cursor()
    cur.execute("SELECT tipoUser FROM usuarios WHERE loginUser = %s", (login,))
    tipo = cur.fetchone()
    cur.close()
    if tipo:
        return tipo[0]
    return None

def verificar_login(login, senha, conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios WHERE loginUser = %s AND senha = %s", (login, senha))
    usuario = cur.fetchone()
    cur.close()
    return usuario is not None

def cadastrar_usuario(login, senha, tipo, conn):
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO usuarios (loginUser, senha, tipoUser) VALUES (%s, %s, %s)", (login, senha, tipo))
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro ao cadastrar usuário: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
