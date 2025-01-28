import os
import streamlit as st
import pandas as pd
import json
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Obtener las credenciales
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# Autenticación en Streamlit
def autenticar():
    st.sidebar.title("Inicio de sesión")
    username_input = st.sidebar.text_input("Usuario")
    password_input = st.sidebar.text_input("Contraseña", type="password")

    if st.sidebar.button("Iniciar sesión"):
        if username_input == USERNAME and password_input == PASSWORD:
            st.sidebar.success("Inicio de sesión exitoso")
            return True
        else:
            st.sidebar.error("Credenciales incorrectas")
            return False
    return False

# Verificar autenticación
if not autenticar():
    st.stop()

# Archivos para almacenar los datos
DATA_FILE = "ventas.csv"
TOTALS_FILE = "totales.csv"
PRODUCTS_FILE = "productos.json"

# Cargar o inicializar el archivo de productos
def cargar_productos():
    try:
        with open(PRODUCTS_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        productos = {
            "Galleta Oreo": 1.25,
            "Chocobanano": 0.75,
            "Jabón": 2.50,
            "Shampoo": 5.00,
            "Cereal": 3.40,
        }
        with open(PRODUCTS_FILE, "w") as file:
            json.dump(productos, file)
        return productos

# Guardar productos en el archivo JSON
def guardar_productos(productos):
    with open(PRODUCTS_FILE, "w") as file:
        json.dump(productos, file)

# Guardar el total de ventas en un archivo CSV con la fecha
def guardar_totales_en_csv(total_ventas, fecha):
    total_df = pd.DataFrame({"Fecha": [fecha], "Total Ventas": [total_ventas]})
    total_df.to_csv(TOTALS_FILE, index=False)

# Calcular el total de ventas
def calcular_total(datos):
    if not datos.empty:
        total_precio = datos["Precio"].sum()
        fecha_actual = pd.to_datetime("today").strftime("%Y-%m-%d")  # Obtener la fecha actual
        return {"Fecha": fecha_actual, "Total Ventas": total_precio}
    else:
        return {"Fecha": None, "Total Ventas": 0}

# Cargar productos al inicio
productos = cargar_productos()

# Verificar si el archivo de ventas existe, sino crearlo
try:
    datos = pd.read_csv(DATA_FILE)
except FileNotFoundError:
    datos = pd.DataFrame(columns=["Fecha", "Producto", "Precio"])
    datos.to_csv(DATA_FILE, index=False)

# Título de la app
st.title("Gestión de Ventas")

# Contenedores fijos para el historial y el total de ventas
st.header("Historial de Ventas")
tabla_placeholder = st.empty()  # Contenedor para el historial de ventas

st.subheader("Total de Ventas")
total_placeholder = st.empty()  # Contenedor para el total de ventas

# Mostrar el historial de ventas
def mostrar_historial(datos):
    datos_con_indice = datos.reset_index()
    tabla_placeholder.dataframe(datos_con_indice)

# Mostrar el total de ventas
def mostrar_total(datos):
    totales = calcular_total(datos)
    total_df = pd.DataFrame([totales])
    total_placeholder.table(total_df)
    guardar_totales_en_csv(totales["Total Ventas"], totales["Fecha"])

# Mostrar el historial y el total al cargar la página
mostrar_historial(datos)
mostrar_total(datos)

# Formulario dinámico para registrar ventas
st.header("Registrar una venta")
fecha = st.date_input("Fecha de la venta")

# Menú dinámico con los productos del JSON
precio = None
producto = st.selectbox(
    "Selecciona un producto (o elige 'Otro' para agregar uno nuevo)", 
    options=list(productos.keys()) + ["Otro"]
)

if producto == "Otro":
    # Si selecciona "Otro", se solicitan los datos del nuevo producto
    nuevo_producto = st.text_input("Nombre del nuevo producto")
    nuevo_precio = st.number_input("Precio del nuevo producto", min_value=0.0, step=0.01)
    
    if nuevo_producto and nuevo_precio > 0:
        producto = nuevo_producto
        precio = nuevo_precio
    else:
        st.warning("Por favor, ingresa un nombre y un precio válido para el nuevo producto.")
else:
    precio = productos[producto]

# Mostrar el precio dinámicamente solo si está definido
if precio is not None:
    st.write(f"**Precio para {producto}:** ${precio:.2f}")

# Botón para registrar la venta
if st.button("Registrar venta"):
    if producto and precio > 0:
        # Agregar el nuevo producto al JSON (si no existe)
        if producto not in productos:
            productos[producto] = precio
            guardar_productos(productos)

        # Registrar la venta en el historial
        nueva_fila = pd.DataFrame([{"Fecha": fecha, "Producto": producto, "Precio": precio}])
        datos = pd.concat([datos, nueva_fila], ignore_index=True)
        datos.to_csv(DATA_FILE, index=False)
        st.success("Venta registrada correctamente")
        # Actualizar las tablas
        mostrar_historial(datos)
        mostrar_total(datos)
    else:
        st.error("Por favor, selecciona un producto y verifica el precio.")

# Eliminar un registro de venta
st.header("Eliminar un registro de venta")
if len(datos) > 0:
    index_to_delete = st.selectbox("Selecciona el índice del registro a eliminar", options=datos.index.tolist())
    if st.button("Eliminar registro"):
        datos = datos.drop(index=index_to_delete).reset_index(drop=True)
        datos.to_csv(DATA_FILE, index=False)
        st.success(f"Registro con índice {index_to_delete} eliminado correctamente")
        # Actualizar las tablas
        mostrar_historial(datos)
        mostrar_total(datos)
else:
    st.warning("No hay registros para eliminar.")

# Eliminar un producto del JSON
st.header("Eliminar un producto")
producto_a_eliminar = st.selectbox("Selecciona un producto a eliminar", options=list(productos.keys()))
if st.button("Eliminar producto"):
    if producto_a_eliminar in productos:
        del productos[producto_a_eliminar]
        guardar_productos(productos)
        st.success(f"Producto '{producto_a_eliminar}' eliminado correctamente")
    else:
        st.error(f"El producto '{producto_a_eliminar}' no existe.")
