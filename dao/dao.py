import psycopg2


def conectardb():

    conn = psycopg2.connect(
        host='dpg-crl0aru8ii6s73etcad0-a.oregon-postgres.render.com',
        password='n2AWLPnla2GWy5BUNiKHsPUD4TMIrFW1',
        database='system_y0qa',
        user='system_y0qa_user',
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

    conn.commit()
    cur.close()
    conn.close()


def verificar_login(login, senha, conn):

    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios WHERE loginUser = %s AND senha = %s", (login, senha))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user is not None


def cadastrar_usuario(login, senha, tipo, conn):

    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO usuarios (loginUser, senha, tipoUser) VALUES (%s, %s, %s)", (login, senha, tipo))
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def cadastrar_produto(login_user, nome, qtde, preco, conn):
    cur = conn.cursor()
    try:

        cur = conn.cursor()
        print(f"Dados a serem inseridos: nome={nome}, login_user={login_user}, qtde={qtde}, preco={preco}")

        cur.execute("INSERT INTO produtos (nome, loginUser, qtde, preco) VALUES (%s, %s, %s, %s)",
                    (nome, login_user, qtde, preco))

        conn.commit()
        print("Produto cadastrado com sucesso!")
        return True


    except psycopg2.IntegrityError:

        conn.rollback()
        return False

    finally:

        cur.close()
        conn.close()


def verificar_tipo_usuario(login, conn):

    cur = conn.cursor()
    cur.execute("SELECT tipoUser FROM usuarios WHERE loginUser = %s", (login,))
    tipo = cur.fetchone()
    cur.close()
    conn.close()
    return tipo[0] if tipo else None


def contar_produtos(login, conn):

    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM produtos WHERE loginUser = %s", (login,))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count

criar_tabelas()
