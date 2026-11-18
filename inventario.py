import sqlite3
from contextlib import contextmanager
from colorama import Fore, init

init(autoreset=True)

BASE_DATOS = "inventario.db"


def conectar():
    return sqlite3.connect(BASE_DATOS)


@contextmanager
def conexion_segura():
    """Confirma cambios si todo sale bien; ante un error, revierte y cierra."""
    conexion = conectar()
    try:
        yield conexion
        conexion.commit()
    except sqlite3.Error:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def crear_tabla():
    try:
        with conexion_segura() as conexion:
            cursor = conexion.cursor()

            # Crea la tabla solo si todavía no existe.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS productos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    descripcion TEXT,
                    cantidad INTEGER NOT NULL,
                    precio REAL NOT NULL,
                    categoria TEXT
                )
            """)
    except sqlite3.Error as error:
        print(Fore.RED + f"Error al crear la tabla: {error}")


def pedir_entero(mensaje, minimo=0):
    # Repite el pedido hasta recibir un entero que cumpla el mínimo.
    while True:
        try:
            numero = int(input(mensaje))
            if numero >= minimo:
                return numero
            print(Fore.RED + f"Ingresá un número igual o mayor que {minimo}.")
        except ValueError:
            print(Fore.RED + "Ingresá un número entero válido.")


def pedir_precio(mensaje):
    # Acepta coma o punto decimal y vuelve a pedir el dato si no es válido.
    while True:
        try:
            precio = float(input(mensaje).replace(",", "."))
            if precio >= 0:
                return precio
            print(Fore.RED + "El precio no puede ser negativo.")
        except ValueError:
            print(Fore.RED + "Ingresá un precio válido.")


def registrar_producto():
    print(Fore.CYAN + "\n--- Registrar producto ---")
    nombre = input("Nombre: ").strip()

    # El nombre es obligatorio para registrar el producto.
    if not nombre:
        print(Fore.RED + "El nombre es obligatorio.")
        return

    descripcion = input("Descripción: ").strip()
    cantidad = pedir_entero("Cantidad: ")
    precio = pedir_precio("Precio: $")
    categoria = input("Categoría: ").strip()

    try:
        with conexion_segura() as conexion:
            cursor = conexion.cursor()

            # Los ? pasan los datos como parámetros y ayudan a prevenir SQL injection.
            cursor.execute(
                """INSERT INTO productos
                   (nombre, descripcion, cantidad, precio, categoria)
                   VALUES (?, ?, ?, ?, ?)""",
                (nombre, descripcion, cantidad, precio, categoria)
            )
    except sqlite3.Error as error:
        print(Fore.RED + f"No se pudo registrar el producto: {error}")
        return

    print(Fore.GREEN + "Producto registrado correctamente.")


def mostrar_productos(productos):
    if not productos:
        print(Fore.YELLOW + "No se encontraron productos.")
        return

    print("\nID | Nombre | Descripción | Cantidad | Precio | Categoría")
    print("-" * 75)

    for producto in productos:
        id_producto, nombre, descripcion, cantidad, precio, categoria = producto
        print(
            f"{id_producto} | {nombre} | {descripcion or '-'} | "
            f"{cantidad} | $"
            f"{precio:.2f} | {categoria or '-'}"
        )


def listar_productos():
    try:
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            cursor.execute("SELECT * FROM productos ORDER BY id")
            productos = cursor.fetchall()
    except sqlite3.Error as error:
        print(Fore.RED + f"No se pudieron consultar los productos: {error}")
        return

    mostrar_productos(productos)


def obtener_producto(id_producto):
    try:
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            cursor.execute(
                "SELECT * FROM productos WHERE id = ?",
                (id_producto,)
            )
            return cursor.fetchone()
    except sqlite3.Error as error:
        print(Fore.RED + f"No se pudo buscar el producto: {error}")
        return None


def actualizar_producto():
    print(Fore.CYAN + "\n--- Actualizar producto ---")
    id_producto = pedir_entero("ID del producto: ", 1)
    producto = obtener_producto(id_producto)

    # Verifica que el producto exista antes de actualizarlo.
    if producto is None:
        print(Fore.RED + "No existe un producto con ese ID.")
        return

    print("Dejá el campo vacío para conservar el valor actual.")
    nombre = input(f"Nombre [{producto[1]}]: ").strip() or producto[1]
    descripcion = input(
        f"Descripción [{producto[2] or ''}]: "
    ).strip() or producto[2]
    categoria = input(
        f"Categoría [{producto[5] or ''}]: "
    ).strip() or producto[5]

    cantidad_texto = input(f"Cantidad [{producto[3]}]: ").strip()
    if cantidad_texto:
        try:
            cantidad = int(cantidad_texto)
            if cantidad < 0:
                raise ValueError
        except ValueError:
            print(Fore.RED + "La cantidad debe ser un entero igual o mayor que 0.")
            return
    else:
        cantidad = producto[3]

    precio_texto = input(f"Precio [{producto[4]}]: ").strip()
    if precio_texto:
        try:
            precio = float(precio_texto.replace(",", "."))
            if precio < 0:
                raise ValueError
        except ValueError:
            print(Fore.RED + "El precio debe ser un número igual o mayor que 0.")
            return
    else:
        precio = producto[4]

    try:
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            cursor.execute(
                """UPDATE productos
                   SET nombre = ?, descripcion = ?, cantidad = ?,
                       precio = ?, categoria = ?
                   WHERE id = ?""",
                (nombre, descripcion, cantidad, precio, categoria, id_producto)
            )
    except sqlite3.Error as error:
        print(Fore.RED + f"No se pudo actualizar el producto: {error}")
        return

    print(Fore.GREEN + "Producto actualizado correctamente.")


def eliminar_producto():
    print(Fore.CYAN + "\n--- Eliminar producto ---")
    id_producto = pedir_entero("ID del producto: ", 1)
    producto = obtener_producto(id_producto)

    if producto is None:
        print(Fore.RED + "No existe un producto con ese ID.")
        return

    # Pide confirmación antes de borrar el producto.
    confirmar = input(Fore.YELLOW + f"¿Eliminar '{producto[1]}'? (s/n): ").lower()

    if confirmar == "s":
        try:
            with conexion_segura() as conexion:
                cursor = conexion.cursor()
                cursor.execute(
                    "DELETE FROM productos WHERE id = ?",
                    (id_producto,)
                )
        except sqlite3.Error as error:
            print(Fore.RED + f"No se pudo eliminar el producto: {error}")
            return

        print(Fore.GREEN + "Producto eliminado.")
    else:
        print(Fore.YELLOW + "Se canceló la eliminación.")


def buscar_producto():
    print(Fore.CYAN + "\n--- Buscar producto ---")
    print("1. Por ID")
    print("2. Por nombre")
    print("3. Por categoría")
    opcion = input("Elegí una opción: ")

    if opcion not in ("1", "2", "3"):
        print(Fore.RED + "Opción inválida.")
        return

    if opcion == "1":
        id_producto = pedir_entero("ID: ", 1)
        consulta = "SELECT * FROM productos WHERE id = ?"
        parametros = (id_producto,)
    elif opcion == "2":
        nombre = input("Nombre o parte del nombre: ").strip()

        # LIKE permite buscar coincidencias parciales por nombre.
        consulta = "SELECT * FROM productos WHERE nombre LIKE ?"
        parametros = (f"%{nombre}%",)
    else:
        categoria = input("Categoría o parte de la categoría: ").strip()
        consulta = "SELECT * FROM productos WHERE categoria LIKE ?"
        parametros = (f"%{categoria}%",)

    try:
        with conexion_segura() as conexion:
            cursor = conexion.cursor()
            cursor.execute(consulta, parametros)
            productos = cursor.fetchall()
    except sqlite3.Error as error:
        print(Fore.RED + f"No se pudo realizar la búsqueda: {error}")
        return

    mostrar_productos(productos)


def reporte_bajo_stock():
    print(Fore.CYAN + "\n--- Reporte de bajo stock ---")
    limite = pedir_entero("Mostrar productos con cantidad igual o menor a: ")

    try:
        with conexion_segura() as conexion:
            cursor = conexion.cursor()

            # Busca productos con una cantidad igual o menor al límite indicado.
            cursor.execute(
                "SELECT * FROM productos WHERE cantidad <= ? ORDER BY cantidad",
                (limite,)
            )
            productos = cursor.fetchall()
    except sqlite3.Error as error:
        print(Fore.RED + f"No se pudo generar el reporte: {error}")
        return

    mostrar_productos(productos)


def mostrar_menu():
    print(Fore.CYAN + "\n===== INVENTARIO =====")
    print("1. Registrar producto")
    print("2. Ver todos los productos")
    print("3. Actualizar producto")
    print("4. Eliminar producto")
    print("5. Buscar producto")
    print("6. Reporte de bajo stock")
    print("0. Salir")


def main():
    # Prepara la base de datos antes de mostrar el menú.
    crear_tabla()

    while True:
        mostrar_menu()
        opcion = input("Seleccioná una opción: ")

        if opcion == "1":
            registrar_producto()
        elif opcion == "2":
            listar_productos()
        elif opcion == "3":
            actualizar_producto()
        elif opcion == "4":
            eliminar_producto()
        elif opcion == "5":
            buscar_producto()
        elif opcion == "6":
            reporte_bajo_stock()
        elif opcion == "0":
            print(Fore.GREEN + "¡Hasta luego!")
            break
        else:
            print(Fore.RED + "Opción inválida.")


if __name__ == "__main__":
    main()

