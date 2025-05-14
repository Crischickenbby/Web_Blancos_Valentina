from flask import Flask, jsonify, render_template, flash, redirect, request, session
from config import get_db_connection, SECRET_KEY
from functools import wraps
from flask import redirect, url_for
from datetime import datetime, timedelta
from decimal import Decimal

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
            nuevo_saldo = saldo_actual  # No cambia el saldo efectivo
            monto = total  # Entra el monto en la tabla Cash, pero no afecta el efectivo en caja

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
            cur.execute('''
                SELECT "ID_Sale", "Date", "Total_Amount" 
                FROM "Sale" 
                WHERE "ID_Sale" = %s AND "ID_Sale_Status" = 1;
            ''', (buscar,))
            venta = cur.fetchone()
            if not venta:
                return jsonify({'success': False, 'message': 'Venta no encontrada o no está completada.'}), 404

            venta_data = {
                'id_sale': venta[0],
                'date': venta[1].strftime('%Y-%m-%d %H:%M:%S'),
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
                   WHERE DATE("Date") = %s AND "ID_Sale_Status" = 1;''',
                (fecha,)
            )
            ventas = cur.fetchall()
            if not ventas:
                return jsonify({'success': False, 'message': 'No se encontraron ventas completadas para esta fecha.'}), 404

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

#===========================================RUTAS DEL APARTADO DE APARTADO========================================================

@app.route('/apartado')
@login_required
def apartado():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute('''SELECT l."ID_Layaway", l."Name", l."Last_Name", l."Phone", l."Date", l."Due_Date", 
                              l."Pending_Amount", p."Name" AS product_name, s."Status"
                       FROM "Layaway" l
                       JOIN "Product" p ON l."ID_Product" = p."ID_Product"
                       JOIN "Status" s ON l."ID_Status" = s."ID_Status"
                       WHERE l."ID_Status" = 3
                       ORDER BY l."Date" DESC;''')

        resultados = cur.fetchall()

        apartados = []
        for r in resultados:
            apartados.append({
                'id': r[0],
                'name': r[1],
                'last_name': r[2],
                'phone': r[3],
                'date': r[4].strftime('%Y-%m-%d'),
                'due_date': r[5].strftime('%Y-%m-%d'),
                'pending_amount': float(r[6]),
                'product_name': r[7],
                'status': r[8]
            })

        return render_template('apartado.html', apartados=apartados)

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

    finally:
        cur.close()
        conn.close()

#este apartado es para buscar los productos al momento de crear un apartado 
@app.route('/api/buscar_productos')
def buscar_productos():
    query = request.args.get('q', '')
    if query:
        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute('''SELECT p."ID_Product", p."Name", p."Description", c."Category"
                           FROM "Product" p
                           JOIN "Category" c ON p."ID_Category" = c."ID_Category"
                           WHERE (p."Name" ILIKE %s OR p."Description" ILIKE %s OR c."Category" ILIKE %s)
                           AND p."ID_Product_Status" = 1
                           ORDER BY p."Name" ASC;''', (f'%{query}%', f'%{query}%', f'%{query}%'))

            productos = cur.fetchall()
            productos_lista = []

            for p in productos:
                productos_lista.append({
                    'id': p[0],
                    'nombre': p[1],
                    'descripcion': p[2],
                    'categoria': p[3]
                })

            return jsonify(productos_lista)

        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            cur.close()
            conn.close()

    return jsonify([])



#esto es para darle al boton de crear apartado y guardalo, no mover nada de esto porque ya sirve
@app.route('/api/crear_apartado', methods=['POST'])
def crear_apartado():
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        apellido = data.get('apellido')
        telefono = data.get('telefono')
        id_producto = data.get('id_producto')
        abono_inicial = Decimal(str(data.get('abono_inicial')))
        id_metodo_pago = int(data.get('metodo_pago'))  # 1 = efectivo, 2 = transferencia, 3 = tarjeta
        id_usuario = 1  # Cambiar según el sistema de login

        conn = get_db_connection()
        cur = conn.cursor()

        # 1. Verificar stock
        cur.execute('SELECT "Quanty" FROM "Product" WHERE "ID_Product" = %s', (id_producto,))
        stock_result = cur.fetchone()
        if not stock_result or stock_result[0] <= 0:
            return jsonify({'success': False, 'message': 'No hay stock disponible para este producto.'})

        # 2. Obtener precio
        cur.execute('SELECT "Price" FROM "Product" WHERE "ID_Product" = %s', (id_producto,))
        precio_result = cur.fetchone()
        if not precio_result:
            return jsonify({'success': False, 'message': 'Producto no encontrado.'})
        precio = precio_result[0]

        if abono_inicial > precio or abono_inicial < 0:
            return jsonify({'success': False, 'message': 'Monto inicial inválido.'})

        pendiente = precio - abono_inicial

        # 3. Fechas
        fecha_apartado = datetime.now()
        fecha_vencimiento = fecha_apartado + timedelta(days=15)

        # 4. Insertar en Layaway
        cur.execute(''' 
            INSERT INTO "Layaway" 
            ("Name", "Last_Name", "Phone", "Date", "Due_Date", "Pending_Amount", "ID_Product", "ID_Status", "ID_User")
            VALUES (%s, %s, %s, %s, %s, %s, %s, 3, %s)  -- ID_Status 3 (en proceso)
            RETURNING "ID_Layaway"
        ''', (nombre, apellido, telefono, fecha_apartado, fecha_vencimiento, pendiente, id_producto, id_usuario))
        id_layaway = cur.fetchone()[0]

        # 5. Crear la venta con estado 'en proceso' (Sale_Status = 2)
        cur.execute(''' 
            INSERT INTO "Sale" ("Date", "Total_Amount", "ID_User", "ID_Sale_Status")
            VALUES (%s, %s, %s, %s)
            RETURNING "ID_Sale"
        ''', (fecha_apartado, precio, id_usuario, 2))  # Sale_Status = 2 (en proceso)
        id_sale = cur.fetchone()[0]

        # 6. Insertar el detalle de la venta (Sale_Details)
        cur.execute('''
            INSERT INTO "Sale_Details" ("Quanty", "Subtotal", "ID_Sale", "ID_Product")
            VALUES (1, %s, %s, %s)
        ''', (precio, id_sale, id_producto))

        # 7. Insertar el primer pago en Layaway_Payments
        cur.execute(''' 
            INSERT INTO "Layaway_Payments" 
            ("ID_Layaway", "Amount_Paid", "Payment_Date")
            VALUES (%s, %s, %s)
        ''', (id_layaway, abono_inicial, fecha_apartado))

        # 8. Insertar en Layaway_Products con fecha
        cur.execute(''' 
            INSERT INTO "Layaway_Products"
            ("ID_Layaway", "ID_Product", "Quantity", "Date", "ID_Product_Status")
            VALUES (%s, %s, 1, %s, 4)
        ''', (id_layaway, id_producto, fecha_apartado))

        # 9. Reducir stock
        cur.execute(''' 
            UPDATE "Product"
            SET "Quanty" = "Quanty" - 1
            WHERE "ID_Product" = %s
        ''', (id_producto,))

        # 10. Obtener saldo actual de caja
        cur.execute('SELECT "Current_Effective" FROM "Cash" ORDER BY "ID_Cash" DESC LIMIT 1')
        saldo_result = cur.fetchone()
        saldo_actual = saldo_result[0] if saldo_result else Decimal('0.00')

        # 11. Calcular nuevo saldo si aplica (para efectivo)
        nuevo_saldo = saldo_actual
        if id_metodo_pago == 1:  # Efectivo
            nuevo_saldo += abono_inicial

        # 12. Insertar el movimiento de caja
        cur.execute(''' 
            INSERT INTO "Cash"
            ("Amount", "Current_Effective", "ID_Sale", "ID_Transaction_Type", "ID_Payment_Method", "ID_User", "Date")
            VALUES (%s, %s, %s, 1, %s, %s, %s)
        ''', (abono_inicial, nuevo_saldo, id_sale, id_metodo_pago, id_usuario, fecha_apartado))

        # Commit y cierre
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Apartado registrado correctamente.'})

    except Exception as e:
        print("Error al registrar apartado:", e)
        return jsonify({'success': False, 'message': f'Error al registrar el apartado: {str(e)}'})



@app.route('/api/realizar_pago', methods=['POST'])
def realizar_pago():
    data = request.get_json()
    id_layaway = data.get('id_layaway')
    monto = data.get('monto')
    metodo_pago = int(data.get('metodo_pago'))  # 1 = efectivo, 2 = transferencia, 3 = tarjeta
    id_usuario = 1  # Ajustar según login

    if not id_layaway or not monto:
        return jsonify({'success': False, 'message': 'Faltan datos necesarios'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 1. Obtener el total de pagos previos
        cur.execute('''
            SELECT SUM("Amount_Paid") FROM "Layaway_Payments"
            WHERE "ID_Layaway" = %s
        ''', (id_layaway,))
        total_pagado = cur.fetchone()[0] or 0

        # 2. Obtener el monto original del producto y el usuario
        cur.execute('''
            SELECT p."Price", l."ID_User"
            FROM "Layaway" l
            JOIN "Layaway_Products" lp ON l."ID_Layaway" = lp."ID_Layaway"
            JOIN "Product" p ON lp."ID_Product" = p."ID_Product"
            WHERE l."ID_Layaway" = %s
        ''', (id_layaway,))
        resultado = cur.fetchone()
        if not resultado:
            return jsonify({'success': False, 'message': 'Apartado no encontrado'}), 404
        monto_original, id_user_layaway = resultado

        # 3. Calcular nuevo saldo
        saldo_pendiente = monto_original - total_pagado
        nuevo_saldo = saldo_pendiente - monto

        fecha_pago = datetime.now()

        # 4. Insertar el nuevo pago
        cur.execute('''
            INSERT INTO "Layaway_Payments" ("ID_Layaway", "Amount_Paid", "Payment_Date")
            VALUES (%s, %s, %s)
        ''', (id_layaway, monto, fecha_pago))

        # 5. Buscar o crear ID_Sale asociado al apartado
        cur.execute('''
            SELECT s."ID_Sale"
            FROM "Sale" s
            JOIN "Sale_Details" sd ON s."ID_Sale" = sd."ID_Sale"
            JOIN "Layaway_Products" lp ON sd."ID_Product" = lp."ID_Product"
            WHERE lp."ID_Layaway" = %s
            ORDER BY s."ID_Sale" DESC
            LIMIT 1
        ''', (id_layaway,))
        row = cur.fetchone()
        id_sale = row[0] if row else None

        # Si no existe venta asociada (primer pago), crearla
        if id_sale is None:
            cur.execute('''
                INSERT INTO "Sale" ("Date", "Total_Amount", "ID_User", "ID_Sale_Status")
                VALUES (%s, %s, %s, %s)
                RETURNING "ID_Sale"
            ''', (fecha_pago, monto_original, id_user_layaway, 2))  # 2 = En proceso
            id_sale = cur.fetchone()[0]

            # Insertar detalle de la venta
            cur.execute('''
                INSERT INTO "Sale_Details" ("Quanty", "Subtotal", "ID_Sale", "ID_Product")
                SELECT 1, p."Price", %s, lp."ID_Product"
                FROM "Layaway_Products" lp
                JOIN "Product" p ON lp."ID_Product" = p."ID_Product"
                WHERE lp."ID_Layaway" = %s
            ''', (id_sale, id_layaway))

        # 6. Registrar en caja si es efectivo (todos los pagos llevan ID_Sale)
        if metodo_pago == 1:
            cur.execute('SELECT "Current_Effective" FROM "Cash" ORDER BY "ID_Cash" DESC LIMIT 1')
            saldo_result = cur.fetchone()
            saldo_actual = saldo_result[0] if saldo_result else Decimal('0.00')
            nuevo_saldo_caja = saldo_actual + Decimal(str(monto))

            cur.execute('''
                INSERT INTO "Cash"
                ("Amount", "Current_Effective", "ID_Sale", "ID_Transaction_Type", "ID_Payment_Method", "ID_User", "Date")
                VALUES (%s, %s, %s, 1, %s, %s, %s)
            ''', (monto, nuevo_saldo_caja, id_sale, metodo_pago, id_usuario, fecha_pago))

        # 7. Si se completó el pago
        if nuevo_saldo <= 0:
            cur.execute('''
                UPDATE "Layaway"
                SET "ID_Status" = 1, "Pending_Amount" = 0
                WHERE "ID_Layaway" = %s
            ''', (id_layaway,))

            cur.execute('''
                UPDATE "Layaway_Products"
                SET "ID_Product_Status" = 2
                WHERE "ID_Layaway" = %s
            ''', (id_layaway,))

            cur.execute('''
                UPDATE "Sale"
                SET "ID_Sale_Status" = 1
                WHERE "ID_Sale" = %s
            ''', (id_sale,))

        else:
            # 8. Aún hay saldo pendiente
            cur.execute('''
                UPDATE "Layaway"
                SET "Pending_Amount" = %s
                WHERE "ID_Layaway" = %s
            ''', (nuevo_saldo, id_layaway))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'success': True, 'message': 'Pago realizado exitosamente'})

    except Exception as e:
        print('Error al realizar el pago:', e)
        return jsonify({'success': False, 'message': 'Error al realizar el pago'}), 500







@app.route('/api/cancelar_apartado', methods=['POST'])
def cancelar_apartado():
    data = request.get_json()
    id_layaway = data.get('id_layaway')
    id_usuario = 1  # Reemplaza por el ID real del usuario que cancela

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 1. Obtener el ID_Product e ID_Sale correcto
        cur.execute('''
            SELECT lp."ID_Product", s."ID_Sale"
            FROM "Layaway_Products" lp
            JOIN "Sale_Details" sd ON lp."ID_Product" = sd."ID_Product"
            JOIN "Sale" s ON sd."ID_Sale" = s."ID_Sale"
            WHERE lp."ID_Layaway" = %s
            AND s."ID_Sale" = (
                SELECT MAX(s2."ID_Sale")
                FROM "Sale" s2
                JOIN "Sale_Details" sd2 ON s2."ID_Sale" = sd2."ID_Sale"
                WHERE sd2."ID_Product" = lp."ID_Product"
            )
            LIMIT 1
        ''', (id_layaway,))
        resultado = cur.fetchone()
        if not resultado:
            return jsonify({'success': False, 'message': 'No se encontró el producto o venta asociada'}), 404

        id_producto, id_sale = resultado

        # 2. Cambiar estado del producto a disponible
        cur.execute('''
            UPDATE "Product"
            SET "ID_Product_Status" = 1,
                "Quanty" = "Quanty" + 1  -- ✅ sumamos el stock
            WHERE "ID_Product" = %s
        ''', (id_producto,))

        # 3. Cambiar estado del apartado a cancelado
        cur.execute('''
            UPDATE "Layaway"
            SET "ID_Status" = 2
            WHERE "ID_Layaway" = %s
        ''', (id_layaway,))

        # 4. Cambiar estado de la venta a cancelado
        cur.execute('''
            UPDATE "Sale"
            SET "ID_Sale_Status" = 3
            WHERE "ID_Sale" = %s
        ''', (id_sale,))

        # 5. Borrar relación en Layaway_Products
        cur.execute('''
            DELETE FROM "Layaway_Products"
            WHERE "ID_Layaway" = %s
        ''', (id_layaway,))

        # 6. Obtener total abonado
        cur.execute('''
            SELECT COALESCE(SUM("Amount_Paid"), 0)
            FROM "Layaway_Payments"
            WHERE "ID_Layaway" = %s
        ''', (id_layaway,))
        total_abonado = cur.fetchone()[0] or 0

        # 7. Obtener el último saldo de efectivo
        cur.execute('''
            SELECT "Current_Effective"
            FROM "Cash"
            ORDER BY "ID_Cash" DESC
            LIMIT 1
        ''')
        resultado = cur.fetchone()
        saldo_actual = resultado[0] if resultado else Decimal('0.00')

        nuevo_saldo = saldo_actual - Decimal(str(total_abonado))
        fecha_cancelacion = datetime.now()

        # 8. Registrar egreso en caja
        cur.execute('''
            INSERT INTO "Cash"
            ("Amount", "Current_Effective", "ID_Sale", "ID_Transaction_Type", "ID_Payment_Method", "ID_User", "Date")
            VALUES (%s, %s, %s, 2, 1, %s, %s)
        ''', (total_abonado, nuevo_saldo, id_sale, id_usuario, fecha_cancelacion))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'success': True})

    except Exception as e:
        print('Error al cancelar apartado:', e)
        return jsonify({'success': False, 'message': str(e)}), 500






#===========================================FIN DE RUTAS DEL APARTADO DE APARTADO========================================================

#===========================================RUTAS DEL APARTADO DE CORTES========================================================


# Página del corte de caja
@app.route('/corte')
@login_required
def corte():
    return render_template('corte.html')

#Para saber si hay una caja abierta o no
@app.route('/api/caja/estado', methods=['GET'])
def estado_caja():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Verificar si hay caja abierta (End_DateTime es NULL)
        cur.execute('''
            SELECT "ID_Cash_Cut", "Star_DateTime"
            FROM "Cash_Cut"
            WHERE "End_DateTime" IS NULL
            LIMIT 1
        ''')
        caja_abierta = cur.fetchone()
        
        if caja_abierta:
            return jsonify({
                'abierta': True,
                'id_cash_out': caja_abierta[0],
                'fecha_apertura': caja_abierta[1].isoformat()
            })
        
        return jsonify({'abierta': False})
        
    except Exception as e:
        print('Error al verificar estado de caja:', e)
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()


#Para abrir la caja
@app.route('/api/caja/abrir', methods=['POST'])
@login_required
def abrir_caja():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Verificamos si ya hay una caja abierta
        cur.execute('''
            SELECT 1 FROM "Cash_Cut" WHERE "End_DateTime" IS NULL
        ''')
        if cur.fetchone():
            return jsonify({'error': 'Ya hay una caja abierta.'}), 400

        # Obtenemos el monto inicial desde el cuerpo del request
        data = request.get_json()
        monto_inicial = data.get('monto')

        if monto_inicial is None or monto_inicial < 0:
            return jsonify({'error': 'Monto inválido.'}), 400

        ahora = datetime.now()
        id_usuario = 1  # Puedes cambiar esto si estás usando session o current_user

        # Insertar en Cash_Cut
        cur.execute('''
            INSERT INTO "Cash_Cut" 
                ("Expected_Cash", "Counted_Cash", "Difference", "Obvservations", "ID_User", "Star_DateTime", "End_DateTime")
            VALUES (NULL, NULL, NULL, NULL, %s, %s, NULL)
            RETURNING "ID_Cash_Cut"
        ''', (id_usuario, ahora))
        id_cash_cut = cur.fetchone()[0]

        # Insertar en Cash
        cur.execute('''
            INSERT INTO "Cash"
                ("Amount", "Current_Effective", "ID_Sale", "ID_Transaction_Type", "ID_Payment_Method", "ID_User", "Date")
            VALUES (%s, %s, NULL, 1, 1, %s, %s)
        ''', (monto_inicial, monto_inicial, id_usuario, ahora))

        conn.commit()

        return jsonify({
            'success': True,
            'mensaje': 'Caja abierta correctamente',
            'id_cash_cut': id_cash_cut,
            'fecha_apertura': ahora.isoformat()
        }), 200

    except Exception as e:
        print('Error al abrir caja:', e)
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/caja/cerrar', methods=['POST'])
def cerrar_caja():
    data = request.json
    efectivo_contado = data.get('efectivo_contado')
    diferencia = data.get('diferencia')
    observaciones = data.get('observaciones', '')

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Ingresos en efectivo
        cur.execute("""
            SELECT COALESCE(SUM("Amount"), 0) 
            FROM "Cash" 
            WHERE "ID_Transaction_Type" = 1 AND "ID_Payment_Method" = 1
        """)
        ingresos_efectivo = cur.fetchone()[0]

        # Egresos en efectivo
        cur.execute("""
            SELECT COALESCE(SUM("Amount"), 0) 
            FROM "Cash" 
            WHERE "ID_Transaction_Type" = 2 AND "ID_Payment_Method" = 1
        """)
        egresos_efectivo = cur.fetchone()[0]

        # Ganancia general = todos los ingresos - todos los egresos
        cur.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN "ID_Transaction_Type" = 1 THEN "Amount" ELSE 0 END), 0) -
                COALESCE(SUM(CASE WHEN "ID_Transaction_Type" = 2 THEN "Amount" ELSE 0 END), 0)
            FROM "Cash"
        """)
        ganancia_general = cur.fetchone()[0]

        # Efectivo esperado
        efectivo_esperado = ingresos_efectivo - egresos_efectivo

        # Buscar el corte activo
        cur.execute("""
            SELECT "ID_Cash_Cut"
            FROM "Cash_Cut"
            WHERE "End_DateTime" IS NULL
            ORDER BY "Star_DateTime" DESC
            LIMIT 1
        """)
        result = cur.fetchone()
        if not result:
            return jsonify({"error": "No hay caja abierta"}), 400

        id_corte = result[0]

        # Actualizar el corte
        cur.execute("""
            UPDATE "Cash_Cut"
            SET 
                "Expected_Cash" = %s,
                "Counted_Cash" = %s,
                "Difference" = %s,
                "Obvservations" = %s,
                "End_DateTime" = %s
            WHERE "ID_Cash_Cut" = %s
        """, (
            efectivo_esperado,
            efectivo_contado,
            diferencia,
            observaciones,
            datetime.now(),
            id_corte
        ))

        conn.commit()
        return jsonify({
            "message": "Caja cerrada correctamente",
            "efectivo_esperado": efectivo_esperado,
            "ganancia_general": ganancia_general
        }), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        cur.close()
        conn.close()

@app.route('/api/caja/datos-corte', methods=['GET'])
@login_required
def obtener_datos_corte():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Primero obtenemos la fecha de apertura del corte actual
        cur.execute('''
            SELECT "Star_DateTime" FROM "Cash_Cut" 
            WHERE "End_DateTime" IS NULL 
            LIMIT 1
        ''')
        corte_actual = cur.fetchone()
        
        if not corte_actual:
            return jsonify({'error': 'No hay caja abierta'}), 400

        fecha_apertura = corte_actual[0]

        # Consultas modificadas para filtrar por fecha de apertura
        # Ingresos en efectivo (ID_Payment_Method = 1 es efectivo, ID_Transaction_Type = 1 es ingreso)
        cur.execute('''
            SELECT COALESCE(SUM("Amount"), 0) FROM "Cash" 
            WHERE "ID_Transaction_Type" = 1 
            AND "ID_Payment_Method" = 1
            AND "Date" >= %s
        ''', (fecha_apertura,))
        ingresos_efectivo = cur.fetchone()[0]

        # Egresos en efectivo
        cur.execute('''
            SELECT COALESCE(SUM("Amount"), 0) FROM "Cash" 
            WHERE "ID_Transaction_Type" = 2 
            AND "ID_Payment_Method" = 1
            AND "Date" >= %s
        ''', (fecha_apertura,))
        egresos_efectivo = cur.fetchone()[0]

        # Ingresos por tarjetas
        cur.execute('''
            SELECT COALESCE(SUM("Amount"), 0) FROM "Cash" 
            WHERE "ID_Payment_Method" = 2 
            AND "ID_Transaction_Type" = 1
            AND "Date" >= %s
        ''', (fecha_apertura,))
        tarjetas = cur.fetchone()[0]

        # Ingresos por transferencias
        cur.execute('''
            SELECT COALESCE(SUM("Amount"), 0) FROM "Cash" 
            WHERE "ID_Payment_Method" = 3 
            AND "ID_Transaction_Type" = 1
            AND "Date" >= %s
        ''', (fecha_apertura,))
        transferencias = cur.fetchone()[0]

        # Egresos por transferencias
        cur.execute('''
            SELECT COALESCE(SUM("Amount"), 0) FROM "Cash" 
            WHERE "ID_Payment_Method" = 3 
            AND "ID_Transaction_Type" = 2
            AND "Date" >= %s
        ''', (fecha_apertura,))
        transferencias_egreso = cur.fetchone()[0]

        # Egresos por tarjetas
        cur.execute('''
            SELECT COALESCE(SUM("Amount"), 0) FROM "Cash" 
            WHERE "ID_Payment_Method" = 2 
            AND "ID_Transaction_Type" = 2
            AND "Date" >= %s
        ''', (fecha_apertura,))
        tarjeta_egreso = cur.fetchone()[0]

        # Cálculos finales
        egreso_total = egresos_efectivo + transferencias_egreso + tarjeta_egreso
        ganancia_general = (ingresos_efectivo + transferencias + tarjetas) - egreso_total
        total_efectivo = ingresos_efectivo - egresos_efectivo

        return jsonify({
            'success': True,
            'ingresos_efectivo': float(ingresos_efectivo),
            'egresos_efectivo': float(egresos_efectivo),
            'total_efectivo': float(total_efectivo),
            'tarjetas': float(tarjetas),
            'transferencias': float(transferencias),
            'ganancia_general': float(ganancia_general),
            'diferencia': float(total_efectivo - (ingresos_efectivo + tarjetas + transferencias - egreso_total)),
            'fecha_apertura': fecha_apertura.isoformat()  # Para referencia en el frontend
        })

    except Exception as e:
        print(f'Error: {e}')
        return jsonify({'error': 'Error al obtener los datos de corte', 'detalle': str(e)}), 500
    finally:
        cur.close()
        conn.close()


#===========================================FIN DE RUTAS DEL APARTADO DE CORTES========================================================


# =========================================FIN DE RUTAS DE PUNTO DE VENTA====================================================


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)