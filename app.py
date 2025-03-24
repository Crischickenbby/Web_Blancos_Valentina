from flask import Flask, render_template
from config import get_db_connection

# Inicializa la aplicación Flask
app = Flask(__name__, template_folder='app/templates', static_folder='app/static')

# Ruta de la página principal
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

#Ruta de la seccion de sesion
@app.route('/sesion')
def sesion():
    return render_template('sesion.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
