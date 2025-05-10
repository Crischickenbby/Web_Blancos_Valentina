from flask import Flask, jsonify, render_template, flash, redirect, request, session
from config import get_db_connection, SECRET_KEY
from functools import wraps
from flask import redirect, url_for
from datetime import datetime

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('sesion'))  # Redirige al formulario de inicio de sesión
        return f(*args, **kwargs)
    return decorated_function

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
@login_required
def punto_venta():
    return render_template('punto_venta.html')



#===========================================RUTA DEL APARTADO DE VENTA========================================================
@app.route('/venta')
@login_required
def venta():
    return render_template('venta.html')   #prueba mientras se verifica la parte del dashboard  


@app.route('/api/registrar_venta', methods=['POST'])
def registrar_venta():
    data = request.get_json()

    productos = data.get('productos')
    total = data.get('total')
    metodo_pago = data.get('metodo_pago')

    if not productos or not total or not metodo_pago:
        return jsonify({'message': 'Datos incompletos'}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Fecha y hora actuales como timestamp
        fecha_hora_actual = datetime.now()

        # Insertar en la tabla Sale
        cur.execute('INSERT INTO "Sale" ("Date", "Total_Amount", "ID_User") '
                    'VALUES (%s, %s, %s) RETURNING "ID_Sale";',
                    (fecha_hora_actual, total, 1))  # Asumimos user_id = 1
        result = cur.fetchone()
        print("Resultado de la consulta INSERT:", result)
        id_sale = result[0]

        # Insertar en Sale_Detail y actualizar stock
        for producto in productos:
            subtotal = producto['cantidad'] * producto['precio']
            cur.execute('INSERT INTO "Sale_Details" ("ID_Sale", "ID_Product", "Quanty", "Subtotal") '
                        'VALUES (%s, %s, %s, %s);',
                        (id_sale, producto['id'], producto['cantidad'], subtotal))
            
            cur.execute('UPDATE "Product" SET "Quanty" = "Quanty" - %s WHERE "ID_Product" = %s;',
                        (producto['cantidad'], producto['id']))

        # Obtener el saldo actual en caja
        cur.execute('SELECT "Current_Effective" FROM "Cash" ORDER BY "ID_Cash" DESC LIMIT 1;')
        row = cur.fetchone()
        saldo_actual = row[0] if row else 0

        # Ajustar el saldo según el método de pago
        if metodo_pago == 1:  # Efectivo
            nuevo_saldo = saldo_actual + total
            monto = total  # Monto positivo para reflejar el ingreso
        else:  # Tarjeta o transferencia
            nuevo_saldo = saldo_actual  # El saldo no cambia
            monto = 0  # No afecta el efectivo

        # Insertar en la tabla Cash
        cur.execute(
            '''INSERT INTO "Cash" ("Date", "Amount", "Current_Effective", "ID_Sale", "ID_Transaction_Type", "ID_Payment_Method", "ID_User")
               VALUES (%s, %s, %s, %s, 1, %s, %s);''',
            (fecha_hora_actual, monto, nuevo_saldo, id_sale, metodo_pago, 1)  # Asumimos user_id = 1
        )

        conn.commit()
        return jsonify({'message': 'Venta registrada exitosamente'}), 200

    except Exception as e:
        conn.rollback()
        print('Error al registrar venta:', e)
        return jsonify({'message': 'Error al registrar la venta'}), 500

    finally:
        cur.close()
        conn.close()

@app.route('/api/productos', methods=['GET'])
@login_required
def api_productos():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT "ID_Product", "Name", "Description", "Price", "Quanty" FROM "Product" WHERE "ID_Product_Status" = 1 AND "Quanty" > 0;')
        productos = cur.fetchall()
        return jsonify([{
            "id": p[0],
            "nombre": p[1],
            "descripcion": p[2],
            "precio": float(p[3]),
            "stock": p[4]
        } for p in productos])
    finally:
        cur.close()
        conn.close()


#===========================================FIN RUTA DEL APARTADO DE VENTA======================================================



#===========================================RUTA DEL APARTADO DE ALMACÉN========================================================
@app.route('/almacen')
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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

#===========================================RUTAS DEL APARTADO DE DEVOLUCIÓN========================================================

@app.route('/devolucion')
@login_required
def devolucion():
    return render_template('devolucion.html')   #prueba mientras se verifica la parte del dashboard 

@app.route('/api/registrar_devolucion', methods=['POST'])
@login_required
def registrar_devolucion():
    data = request.get_json()
    if not data or 'id_venta' not in data:
        return jsonify({'success': False, 'message': 'El ID de la venta es obligatorio.'}), 400

    id_venta = data['id_venta']
    productos = data.get('productos', [])
    reintegrar_stock = bool(int(data.get('reintegrar_stock', 0)))
    metodo_reembolso = int(data.get('metodo_reembolso'))
    observaciones = data.get('observaciones', '').strip()
    id_usuario = session.get('user_id')

    if not productos:
        return jsonify({'success': False, 'message': 'No se seleccionaron productos para devolver.'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 1. Actualizar stock si toca reintegrar
        if reintegrar_stock:
            for p in productos:
                cur.execute(
                    'UPDATE "Product" SET "Quanty" = "Quanty" + %s WHERE "ID_Product" = %s;',
                    (p['cantidad'], p['id_producto'])
                )

        # 2. Calcular total a devolver
        total_devolver = sum(float(p['precio']) * int(p['cantidad']) for p in productos)

        # 3. Registrar en Return
        fecha_hora_actual = datetime.now()
        cur.execute(
            '''INSERT INTO "Return" ("ID_Sale","Date_Return","Total_Refund","ID_User","ID_Payment_Method","Observations")
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING "ID_Return";''',
            (id_venta, fecha_hora_actual, total_devolver, id_usuario, metodo_reembolso, observaciones)
        )
        id_return = cur.fetchone()[0]

        # 4. Registrar cada producto en Return_Details
        for p in productos:
            cur.execute(
                '''INSERT INTO "Return_Details" ("ID_Return","ID_Product","Quanty","Price")
                   VALUES (%s, %s, %s, %s);''',
                (id_return, p['id_producto'], p['cantidad'], p['precio'])
            )

        # 5. Registrar egreso en caja según el método de reembolso
        cur.execute('SELECT "Current_Effective" FROM "Cash" ORDER BY "ID_Cash" DESC LIMIT 1;')
        row = cur.fetchone()
        saldo_actual = float(row[0]) if row else 0.0

        if metodo_reembolso == 1:  # Efectivo
            nuevo_saldo = saldo_actual - total_devolver
            monto = -total_devolver  # Monto negativo para reflejar el egreso
        else:  # Tarjeta o transferencia
            nuevo_saldo = saldo_actual  # El saldo no cambia
            monto = 0  # No afecta el efectivo

        cur.execute(
            '''INSERT INTO "Cash" ("Date","Amount","Current_Effective","ID_Transaction_Type","ID_User","ID_Sale","ID_Payment_Method")
               VALUES (CURRENT_TIMESTAMP, %s, %s, 2, %s, %s, %s);''',
            (monto, nuevo_saldo, id_usuario, id_venta, metodo_reembolso)
        )

        conn.commit()
        return jsonify({'success': True, 'message': 'Devolución registrada correctamente.'})

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error al procesar la devolución: {e}'}), 500

    finally:
        cur.close()
        conn.close()



@app.route('/api/buscar_venta')
@login_required
def buscar_venta():
    buscar = request.args.get('buscar')
    fecha = request.args.get('fecha')

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        if buscar:  # Buscar por ID de venta
            cur.execute('SELECT "ID_Sale","Date","Total_Amount" FROM "Sale" WHERE "ID_Sale" = %s;', (buscar,))
            venta = cur.fetchone()
            if not venta:
                return jsonify({'success': False, 'message': 'Venta no encontrada.'}), 404

            venta_data = {
                'id_sale': venta[0],
                'date': venta[1].strftime('%Y-%m-%d %H:%M:%S'),  # Incluye fecha y hora
                'total_amount': float(venta[2])
            }

            # Traer detalle de venta
            cur.execute(
                '''SELECT sd."ID_Product", p."Name", sd."Quanty", (sd."Subtotal"/sd."Quanty") AS unit_price
                   FROM "Sale_Details" sd
                   JOIN "Product" p ON sd."ID_Product" = p."ID_Product"
                   WHERE sd."ID_Sale" = %s;''',
                (venta[0],)
            )
            productos = cur.fetchall()
            venta_data['productos'] = [
                {'id': r[0], 'name': r[1], 'quantity': r[2], 'precio': float(r[3])}
                for r in productos
            ]

            # Traer devoluciones
            cur.execute(
                '''SELECT r."ID_Return", r."Date_Return", r."Total_Refund", r."ID_Payment_Method", r."Observations"
                   FROM "Return" r
                   WHERE r."ID_Sale" = %s
                   ORDER BY r."ID_Return";''',
                (venta[0],)
            )
            devoluciones = cur.fetchall()
            devoluciones_data = []
            for devolucion in devoluciones:
                id_ret, date_ret, tot_ref, met_pay, obs = devolucion
                cur.execute(
                    '''SELECT rd."ID_Product", rd."Quanty", rd."Price", p."Name"
                       FROM "Return_Details" rd
                       JOIN "Product" p ON rd."ID_Product" = p."ID_Product"
                       WHERE rd."ID_Return" = %s;''',
                    (id_ret,)
                )
                detalles = cur.fetchall()
                devoluciones_data.append({
                    'id_return': id_ret,
                    'date_return': date_ret.strftime('%Y-%m-%d %H:%M:%S'),
                    'total_refund': float(tot_ref),
                    'payment_method': met_pay,
                    'observations': obs,
                    'productos': [
                        {'id': d[0], 'name': d[3], 'quantity': d[1], 'price': float(d[2])}
                        for d in detalles
                    ]
                })

            venta_data['devoluciones'] = devoluciones_data

            return jsonify({'success': True, 'venta': venta_data})

        elif fecha:  # Buscar por fecha
            cur.execute(
                '''SELECT "ID_Sale", "Date", "Total_Amount"
                   FROM "Sale"
                   WHERE DATE("Date") = %s;''',  # Extrae solo la fecha del TIMESTAMP
                (fecha,)
            )
            ventas = cur.fetchall()
            if not ventas:
                return jsonify({'success': False, 'message': 'No se encontraron ventas para esta fecha.'}), 404

            ventas_data = [
                {
                    'id_sale': v[0],
                    'date': v[1].strftime('%Y-%m-%d'),
                    'total_amount': float(v[2])
                }
                for v in ventas
            ]
            return jsonify({'success': True, 'ventas': ventas_data})

        else:
            return jsonify({'success': False, 'message': 'Debe proporcionar un ID de venta o una fecha.'}), 400

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

    finally:
        cur.close()
        conn.close()


#===========================================FIN RUTAS DEL APARTADO DE DEVOLUCIÓN========================================================

@app.route('/corte')
@login_required
def corte():
    return render_template('corte.html')   #prueba mientras se verifica la parte del dashboard     



#===========================================RUTAS DEL APARTADO DE APARTADO========================================================

@app.route('/apartado')
@login_required
def apartado():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Obtener apartados
        cur.execute('''
            SELECT l."ID_Layaway", l."Name", l."Last_Name", p."Name" AS product_name, 
                   l."Due_Date", l."Pending_Amount"
            FROM "Layaway" l
            JOIN "Product" p ON l."ID_Product" = p."ID_Product"
            WHERE l."ID_Status" = 1;
        ''')
        apartados = cur.fetchall()

        # Obtener productos
        cur.execute('''
            SELECT "ID_Product", "Name" FROM "Product" WHERE "ID_Product_Status" = 1;
        ''')
        productos = cur.fetchall()

        return render_template('apartado.html', apartados=apartados, productos=productos)
    finally:
        cur.close()
        conn.close()

#===========================================FIN DE RUTAS DEL APARTADO DE APARTADO========================================================


# =========================================FIN DE RUTAS DE PUNTO DE VENTA====================================================


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)