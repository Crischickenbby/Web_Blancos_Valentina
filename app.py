from flask import Flask, jsonify, render_template, flash, redirect, request, session
from config import get_db_connection, SECRET_KEY

# Inicializa la aplicación Flask
app = Flask(__name__, template_folder='app/templates', static_folder='app/static', )

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
#===========================================RUTA DEL APARTADO DE ALMACÉN========================================================
@app.route('/almacen')
def almacen():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Consulta para obtener solo los productos activos (status = 1)
        query_productos = '''
            SELECT p."ID_Product", p."Name", p."Description", p."Quanty", p."Price", c."Category"
            FROM "Product" p
            JOIN "Category" c ON p."ID_Category" = c."ID_Category"
            WHERE p."ID_Product_Status" = 1;
        '''
        cur.execute(query_productos)
        productos = cur.fetchall()

        # Consulta para obtener las categorías
        query_categorias = '''
            SELECT "ID_Category", "Category"
            FROM "Category";
        '''
        cur.execute(query_categorias)
        categorias = cur.fetchall()

        # Consulta para obtener las pructos del modal eliminar
        query_pruductosDelete = '''
            SELECT p."ID_Product", p."Name", p."Description", p."Quanty"
            FROM "Product" p
            WHERE p."ID_Product_Status" = 1;
        '''
        cur.execute(query_pruductosDelete)
        productos1 = cur.fetchall()

        # Renderiza la plantilla y pasa los datos de productos y categorías
        return render_template('almacen.html', productos=productos, categorias=categorias, productos1=productos1)

    except Exception as e:
        print(f"Error al obtener datos: {e}", flush=True)
        return "Ocurrió un error al cargar los datos."

    finally:
        if conn:
            cur.close()
            conn.close()



@app.route('/eliminar_producto/<int:product_id>', methods=['PUT'])
def eliminar_producto(product_id):
    print(f"Petición recibida para eliminar el producto con ID: {product_id}")  # Depuración
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Actualizar el estado del producto a 2 (inactivo)
        query = '''
            UPDATE "Product"
            SET "ID_Product_Status" = 2
            WHERE "ID_Product" = %s;
        '''
        cur.execute(query, (product_id,))
        conn.commit()

        return jsonify({"success": True, "message": "Producto eliminado correctamente."})
    except Exception as e:
        print("Error en el servidor:", e)  # Depuración
        return jsonify({"success": False, "message": str(e)})
    finally:
        if conn:
            cur.close()
            conn.close()


@app.route('/agregar_producto', methods=['POST'])
def agregar_producto():
    try:
        # Obtener datos del formulario
        nombre = request.form.get('productName')
        descripcion = request.form.get('productDescription')
        precio = float(request.form.get('productPrice'))
        cantidad = int(request.form.get('productQuantity'))
        categoria_id = int(request.form.get('productCategory'))
        
        # Conexión a la base de datos
        conn = get_db_connection()
        cur = conn.cursor()

        # Consulta de ejemplo para insertar datos
        query = '''
            INSERT INTO "Product" ("Name", "Description", "Price", "Quanty", "ID_Category", "ID_Product_Status")
            VALUES (%s, %s, %s, %s, %s, 1);
        '''
        cur.execute(query, (nombre, descripcion, precio, cantidad, categoria_id))
        conn.commit()

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    finally:
        # Cerrar la conexión
        if conn:
            cur.close()
            conn.close()

@app.route('/incrementar_cantidad_producto', methods=['POST'])
def incrementar_cantidad_producto():
    try:
        data = request.get_json()
        print("Datos recibidos:", data)  # Depuración
        if not data or 'product_id' not in data or 'quantity_to_add' not in data:
            return jsonify({"success": False, "message": "Datos inválidos"}), 400

        product_id = int(data.get('product_id'))
        cantidad = int(data.get('quantity_to_add'))

        conn = get_db_connection()
        cur = conn.cursor()

        query = '''
            UPDATE "Product"
            SET "Quanty" = "Quanty" + %s
            WHERE "ID_Product" = %s;
        '''
        cur.execute(query, (cantidad, product_id))
        conn.commit()

        return jsonify({"success": True})
    except Exception as e:
        print("Error en el servidor:", e)  # Depuración
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if conn:
            cur.close()
            conn.close()

@app.route('/reducir_cantidad_producto', methods=['POST'])
def reducir_cantidad_producto():
    try:
        data = request.get_json()
        print("Datos recibidos:", data)  # Depuración
        if not data or 'product_id' not in data or 'quantity_to_remove' not in data:
            return jsonify({"success": False, "message": "Datos inválidos"}), 400

        product_id = int(data.get('product_id'))
        cantidad = int(data.get('quantity_to_remove'))

        conn = get_db_connection()
        cur = conn.cursor()

        # Verificar que la cantidad en existencia sea suficiente
        cur.execute('SELECT "Quanty" FROM "Product" WHERE "ID_Product" = %s;', (product_id,))
        stock = cur.fetchone()
        if not stock or stock[0] < cantidad:
            return jsonify({"success": False, "message": "Cantidad insuficiente en existencia"}), 400

        # Reducir la cantidad del producto
        query = '''
            UPDATE "Product"
            SET "Quanty" = "Quanty" - %s
            WHERE "ID_Product" = %s;
        '''
        cur.execute(query, (cantidad, product_id))
        conn.commit()

        return jsonify({"success": True, "message": "Cantidad eliminada correctamente."})
    except Exception as e:
        print("Error en el servidor:", e)  # Depuración
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if conn:
            cur.close()
            conn.close()

@app.route('/actualizar_producto', methods=['POST'])
def actualizar_producto():
    conn = None
    try:
        data = request.json
        product_id = data['product_id']
        name = data['name']
        description = data['description']
        price = data['price']
        category_id = data['category_id']
        
        # Obtener conexión a la base de datos
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Consulta SQL para actualizar el producto
        query = '''
            UPDATE "Product"
            SET "Name" = %s, "Description" = %s, "Price" = %s, "ID_Category" = %s
            WHERE "ID_Product" = %s;
        '''
        
        # Ejecutar la consulta con los parámetros
        cur.execute(query, (name, description, price, category_id, product_id))
        
        # Confirmar la transacción
        conn.commit()
        
        # Devolver respuesta exitosa
        return jsonify({'success': True, 'message': 'Producto actualizado correctamente'})
    
    except Exception as e:
        # En caso de error, registrar el error y devolver mensaje
        print(f"Error al actualizar producto: {e}", flush=True)
        return jsonify({'success': False, 'message': str(e)})
        
    finally:
        # Cerrar cursor y conexión
        if conn:
            cur.close()
            conn.close()

@app.route('/add_category', methods=['POST'])
def add_category():
    try:
        data = request.get_json()
        category_name = data.get('name')

        if not category_name:
            return jsonify({'success': False, 'message': 'El nombre de la categoría es obligatorio'})

        conn = get_db_connection()
        cur = conn.cursor()

        # Verificar si la categoría ya existe
        query_check = '''
            SELECT COUNT(*) FROM "Category" WHERE "Category" = %s;
        '''
        cur.execute(query_check, (category_name,))
        if cur.fetchone()[0] > 0:
            return jsonify({'success': False, 'message': 'La categoría ya existe'})

        # Insertar la nueva categoría en la base de datos
        query_insert = '''
            INSERT INTO "Category" ("Category")
            VALUES (%s)
            RETURNING "ID_Category";
        '''
        cur.execute(query_insert, (category_name,))
        new_category_id = cur.fetchone()[0]
        conn.commit()

        return jsonify({'success': True, 'id': new_category_id})
    except Exception as e:
        print(f"Error al agregar categoría: {e}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if conn:
            cur.close()
            conn.close()

@app.route('/delete_category', methods=['POST'])
def delete_category():
    try:
        data = request.get_json()
        category_id = data.get('id')

        if not category_id:
            return jsonify({'success': False, 'message': 'El ID de la categoría es obligatorio'})

        conn = get_db_connection()
        cur = conn.cursor()

        # Verificar si la categoría está siendo utilizada por algún producto
        query_check = '''
            SELECT COUNT(*) FROM "Product" WHERE "ID_Category" = %s;
        '''
        cur.execute(query_check, (category_id,))
        if cur.fetchone()[0] > 0:
            return jsonify({'success': False, 'message': 'No se puede eliminar la categoría porque está siendo utilizada por un producto'})

        # Eliminar la categoría de la base de datos
        query_delete = '''
            DELETE FROM "Category"
            WHERE "ID_Category" = %s;
        '''
        cur.execute(query_delete, (category_id,))
        conn.commit()

        return jsonify({'success': True})
    except Exception as e:
        print(f"Error al eliminar categoría: {e}")
        return jsonify({'success': False, 'message': str(e)})
    finally:
        if conn:
            cur.close()
            conn.close()

#===========================================FIN RUTAS DEL APARTADO ALMACÉN========================================================

#===========================================RUTAS DEL APARTADO DE EMPLEADO========================================================
@app.route('/empleado')
def empleado():
    try:
        # Conexión a la base de datos
        conn = get_db_connection()
        cur = conn.cursor()

        # Consulta para obtener los usuarios con rol 2
        query = '''
            SELECT "ID_User", "Name", "Last_Name", "Email", "Password", "ID_Rol"
            FROM "User"
            WHERE "ID_Rol" = 2 AND "ID_User_Status" = 1;

        '''
        cur.execute(query)
        empleados = cur.fetchall()

        # Renderizar la plantilla y pasar los datos de los empleados
        return render_template('empleado.html', empleados=empleados)

    except Exception as e:
        print(f"Error al obtener empleados: {e}")
        return "Ocurrió un error al cargar los empleados."

    finally:
        if conn:
            cur.close()
            conn.close()

@app.route('/crear_empleado', methods=['POST'])
def crear_empleado():
    try:
        # Obtener datos del formulario
        nombre = request.form.get('nombreEmpleado')
        apellidos = request.form.get('apellidosEmpleado')
        correo = request.form.get('correoEmpleado')
        contrasena = request.form.get('contrasenaEmpleado')
        privilegios = request.form.get('privilegiosEmpleado')  # Lista separada por comas

        # Conexión a la base de datos
        conn = get_db_connection()
        cur = conn.cursor()

        # Insertar el nuevo empleado en la tabla User
        query_user = '''
            INSERT INTO "User" ("Name", "Last_Name", "Email", "Password", "ID_Rol", "ID_User_Status")
            VALUES (%s, %s, %s, %s, 2, 1)  -- 1 representa el estado "Activo"
            RETURNING "ID_User";
        '''
        cur.execute(query_user, (nombre, apellidos, correo, contrasena))
        id_usuario = cur.fetchone()[0]  # Obtener el ID del usuario recién creado

        # Insertar los permisos en la tabla Permission
        permisos = {
            "Sale": "Vender" in privilegios,
            "Layaway": "Realizar apartado" in privilegios,
            "Cash": "Realizar corte de caja" in privilegios,
            "Product": "Modificar almacén" in privilegios,
            "Repayment": "Realizar devolución" in privilegios
        }

        query_permission = '''
            INSERT INTO "Permission" ("ID_User", "Sale", "Layaway", "Cash", "User", "Product", "Repayment")
            VALUES (%s, %s, %s, %s, false, %s, %s);
        '''
        cur.execute(query_permission, (
            id_usuario,
            permisos["Sale"],
            permisos["Layaway"],
            permisos["Cash"],
            permisos["Product"],
            permisos["Repayment"]
        ))

        # Confirmar transacción
        conn.commit()

        return jsonify({"success": True, "message": "Empleado creado correctamente."})

    except Exception as e:
        print(f"Error al crear empleado: {e}")
        return jsonify({"success": False, "message": str(e)})

    finally:
        if conn:
            cur.close()
            conn.close()

@app.route('/eliminar_empleado/<int:user_id>', methods=['PUT'])
def eliminar_empleado(user_id):
    try:
        # Conexión a la base de datos
        conn = get_db_connection()
        cur = conn.cursor()

        # Actualizar el estado del usuario a 2 (inactivo)
        query = '''
            UPDATE "User"
            SET "ID_User_Status" = 2
            WHERE "ID_User" = %s;
        '''
        cur.execute(query, (user_id,))
        conn.commit()

        return jsonify({"success": True, "message": "Empleado eliminado correctamente."})
    except Exception as e:
        print(f"Error al eliminar empleado: {e}")
        return jsonify({"success": False, "message": str(e)})
    finally:
        if conn:
            cur.close()
            conn.close()

@app.route('/editar_empleado/<int:user_id>', methods=['PUT'])
def editar_empleado(user_id):
    try:
        # Obtener datos del formulario
        data = request.get_json()
        nombre = data.get('nombreEmpleado')
        apellidos = data.get('apellidosEmpleado')
        correo = data.get('correoEmpleado')
        contrasena = data.get('contrasenaEmpleado')
        privilegios = data.get('privilegiosEmpleado')  # Diccionario con los permisos

        # Conexión a la base de datos
        conn = get_db_connection()
        cur = conn.cursor()

        # Actualizar los datos del empleado en la tabla User
        query_user = '''
            UPDATE "User"
            SET "Name" = %s, "Last_Name" = %s, "Email" = %s, "Password" = %s
            WHERE "ID_User" = %s;
        '''
        cur.execute(query_user, (nombre, apellidos, correo, contrasena, user_id))

        # Actualizar los permisos en la tabla Permission
        query_permission = '''
            UPDATE "Permission"
            SET "Sale" = %s, "Layaway" = %s, "Cash" = %s, "Product" = %s, "Repayment" = %s
            WHERE "ID_User" = %s;
        '''
        cur.execute(query_permission, (
            privilegios.get('Sale', False),
            privilegios.get('Layaway', False),
            privilegios.get('Cash', False),
            privilegios.get('Product', False),
            privilegios.get('Repayment', False),
            user_id
        ))

        # Confirmar transacción
        conn.commit()

        return jsonify({"success": True, "message": "Empleado actualizado correctamente."})

    except Exception as e:
        print(f"Error al editar empleado: {e}")
        return jsonify({"success": False, "message": str(e)})

    finally:
        if conn:
            cur.close()
            conn.close()

@app.route('/obtener_empleado/<int:user_id>', methods=['GET'])
def obtener_empleado(user_id):
    try:
        print(f"Obteniendo información del empleado con ID: {user_id}")  # Depuración
        # Conexión a la base de datos
        conn = get_db_connection()
        cur = conn.cursor()

        # Obtener la información del empleado
        query_user = '''
            SELECT "Name", "Last_Name", "Email"
            FROM "User"
            WHERE "ID_User" = %s;
        '''
        cur.execute(query_user, (user_id,))
        user_data = cur.fetchone()

        # Obtener los permisos del empleado
        query_permissions = '''
            SELECT "Sale", "Layaway", "Cash", "Product", "Repayment"
            FROM "Permission"
            WHERE "ID_User" = %s;
        '''
        cur.execute(query_permissions, (user_id,))
        permissions_data = cur.fetchone()

        if user_data and permissions_data:
            return jsonify({
                "success": True,
                "data": {
                    "Name": user_data[0],
                    "Last_Name": user_data[1],
                    "Email": user_data[2],
                    "Permissions": {
                        "Sale": permissions_data[0],
                        "Layaway": permissions_data[1],
                        "Cash": permissions_data[2],
                        "Product": permissions_data[3],
                        "Repayment": permissions_data[4]
                    }
                }
            })
        else:
            print("Empleado no encontrado o permisos no encontrados.")  # Depuración
            return jsonify({"success": False, "message": "Empleado no encontrado."})

    except Exception as e:
        print(f"Error al obtener empleado: {e}")  # Depuración
        return jsonify({"success": False, "message": str(e)})

    finally:
        if conn:
            cur.close()
            conn.close()

#=========================================== FIN RUTAS DEL APARTADO DE EMPLEADO========================================================

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