import psycopg2

# Configuración de la base de datos
DB_HOST = "localhost"
DB_NAME = "Blancos_Valentina"
DB_USER = "postgres"
DB_PASSWORD = "Kantunramirez21"

# Función para obtener una conexión a la base de datos
def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
