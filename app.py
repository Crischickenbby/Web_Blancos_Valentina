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
        cur.fetchall()  # Si la consulta es exitosa, devolverá algo
        
        # Cierra el cursor y la conexión
        cur.close()
        conn.close()
        
        # Mensaje en la terminal
        print("Conexión exitosa a la base de datos!")
        return render_template('index.html')  # Solo devuelve un mensaje en texto plano
        
    except Exception as e:
        # Muestra el error en la terminal
        print(f"Error en la conexión: {e}")
        return "Error en la conexión"  # Devuelve el mensaje de error en texto plano
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
            return redirect('/punto_venta')  # Redirige a la ruta de punto de venta

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
#===========================================RUTAS DE PUNTO DE VENTA========================================================
@app.route('/punto_venta')
def punto_venta():
    return render_template('punto_venta.html')

@app.route('/venta')
def venta():
    return render_template('venta.html')   #prueba mientras se verifica la parte del dashboard     

@app.route('/almacen')
def almacen():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Solo traemos los campos que sí queremos mostrar
        query = query = '''
            SELECT p."Name", p."Description", p."Quanty", p."Price", c."Category"
            FROM "Product" p
            JOIN "Category" c ON p."ID_Category" = c."ID_Category";
            '''

        cur.execute(query)
        productos = cur.fetchall() #todo se almacena en una variable llamada productos

        return render_template('almacen.html', productos=productos)#Renderiza la plantilla alamacen y se le pasa la variable de productos para que se muestre en la tabla de la plantilla almacen.html

    except Exception as e:
        print(f"Error al obtener productos: {e}", flush=True)
        return "Ocurrió un error al cargar los productos."

    finally:
        if conn:
            cur.close()
            conn.close()
        
  

@app.route('/empleado')
def empleado():
    return render_template('empleado.html')   #prueba mientras se verifica la parte del dashboard     

@app.route('/devolucion')
def devolucion():
    return render_template('devolucion.html')   #prueba mientras se verifica la parte del dashboard     

@app.route('/corte')
def corte():
    return render_template('corte.html')   #prueba mientras se verifica la parte del dashboard     

@app.route('/apartado')
def apartado():
    return render_template('apartado.html')   #prueba mientras se verifica la parte del dashboard     




# =========================================FIN DE RUTAS DE PUNTO DE VENTA====================================================




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)