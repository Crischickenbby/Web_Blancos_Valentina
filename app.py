from flask import Flask, render_template, flash, redirect, request, session
from config import get_db_connection, SECRET_KEY

# Inicializa la aplicación Flask
app = Flask(__name__, template_folder='app/templates', static_folder='app/static')

# Configura la clave secreta desde config.py
app.secret_key = SECRET_KEY


#=====================================RUTAS DE LA SECCION PRINCIPAL(INDEX)=====================================
@app.route('/')
def home():
    try:
        # Intenta obtener la conexión
        conn = get_db_connection()
        
        # Crea un cursor para realizar una consulta
        cur = conn.cursor()
        
        # Ejecuta una consulta simple para verificar la conexión
        cur.execute('SELECT 1;')
        result = cur.fetchall()  # Si la consulta es exitosa, devolverá algo
        
        # Cierra el cursor y la conexión
        cur.close()
        conn.close()
        
        # Si todo salió bien, muestra mensaje de conexión exitosa en la consola
        print("Conexión exitosa a la base de datos!")
        return render_template('index.html')
    
    except Exception as e:
        # Si ocurrió un error, muestra el error en la consola
        print(f"Error en la conexión: {e}")
        return render_template('index.html')
#===============================================================================================================

#=====================================RUTAS DE LA SECCIÓN LOGIN================================================
# Ruta para manejar el inicio de sesión
#Ruta de la seccion de sesion
@app.route('/sesion')
def sesion():
    return render_template('sesion.html')
# Ruta para manejar el proceso de inicio de sesión
@app.route('/login', methods=['POST'])
def login():
    try:
        # Obtiene los datos enviados desde el formulario
        email = request.form.get('Email_sesion')
        password = request.form.get('Password_sesion')

        # Intenta conectarse a la base de datos
        conn = get_db_connection()
        cur = conn.cursor()

        # Consulta la base de datos para verificar el usuario y la contraseña
        query = 'SELECT * FROM "User" WHERE "Email" = %s AND "Password" = %s;'
        cur.execute(query, (email, password))
        user = cur.fetchone()

        # Si el usuario es encontrado, inicia sesión
        if user:
            session['user_id'] = user[0]  # Guarda el ID del usuario en la sesión
            flash("¡Inicio de sesión exitoso!", "success")
            return redirect('/')  # Redirige a la página principal

        # Si no se encuentra el usuario, muestra un mensaje de error
        else:
            flash("Correo o contraseña incorrectos.", "error")
            return redirect('/sesion')  # Redirige al formulario de inicio de sesión nuevamente

    except Exception as e:
        # Manejo de errores
        print(f"Error al intentar iniciar sesión: {e}")
        flash("Ocurrió un problema al intentar iniciar sesión.", "error")
        return redirect('/sesion')  # Redirige al formulario de inicio de sesión

    finally:
        # Cierra la conexión a la base de datos
        if conn:
            cur.close()
            conn.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)