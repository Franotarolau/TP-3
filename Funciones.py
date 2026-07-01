from tkinter import *
from tkinter import messagebox
from tkinter import ttk
import os
import json
import random
import datetime
import urllib.request
import urllib.error
import csv
import xml.etree.ElementTree as ET
from math import *
import qrcode
from fpdf import FPDF

ventanaPrincipal = Tk()
ventanaPrincipal.title("Sistema de Parqueo - Versión Unificada")
ventanaPrincipal.geometry("400x400")
ventanaPrincipal["bg"] = "#2C3E50"

ARCHIVO_CONFIGURACION = "configuracion.json"
ARCHIVO_CATALOGOS = "catalogoVehiculos.json"
ARCHIVO_BASE_DATOS = "baseDatosEstacionamiento.json"
ARCHIVO_CLAVE_API = "mockarooApiKey.txt"

TIPOS_VEHICULO = ["Sedán", "SUV", "Pickup", "Hatchback", "Motocicleta"]

listaEstacionamientos = []

#-
class Estacionamiento:
    def __init__(self, idVehiculo, placa, marca, color, tipo, ubicacion,
                 fechaHoraEntrada, fechaHoraSalida, monto, tipoPago):
        self.id = idVehiculo
        self.info = (placa, marca, color, tipo)
        self.estadia = [ubicacion, fechaHoraEntrada, fechaHoraSalida]
        self.pago = (monto, tipoPago)

    def aDiccionario(self):
        return {
            "id": self.id,
            "placa": self.info[0],
            "marca": self.info[1],
            "color": self.info[2],
            "tipo": self.info[3],
            "ubicacion": self.estadia[0],
            "fechaHoraEntrada": self.estadia[1],
            "fechaHoraSalida": self.estadia[2],
            "monto": self.pago[0],
            "tipoPago": self.pago[1]
        }

def estacionamientoDesdeDiccionario(d):
    return Estacionamiento(
        d["id"], d["placa"], d["marca"], d["color"], d["tipo"],
        d["ubicacion"], d["fechaHoraEntrada"], d["fechaHoraSalida"],
        d["monto"], d["tipoPago"]
    )

#
def cargarBaseDatos():
    if not os.path.exists(ARCHIVO_BASE_DATOS):
        return []
    try:
        with open(ARCHIVO_BASE_DATOS, "r", encoding="utf-8") as archivo:
            registros = json.load(archivo)
        return [estacionamientoDesdeDiccionario(r) for r in registros]
    except Exception:
        return []

def guardarBaseDatos(lista):
    diccionarios = [obj.aDiccionario() for obj in lista]
    with open(ARCHIVO_BASE_DATOS, "w", encoding="utf-8") as archivo:
        json.dump(diccionarios, archivo, indent=4, ensure_ascii=False)

def cargarCatalogos():
    if os.path.exists(ARCHIVO_CATALOGOS):
        with open(ARCHIVO_CATALOGOS, "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    catalogos = {"marca": {}, "color": {}, "tipo": {}}
    for i, tipo in enumerate(TIPOS_VEHICULO):
        catalogos["tipo"][tipo] = i + 1
    return catalogos

def guardarCatalogos(catalogos):
    with open(ARCHIVO_CATALOGOS, "w", encoding="utf-8") as archivo:
        json.dump(catalogos, archivo, indent=4, ensure_ascii=False)

#
def obtenerCodigo(catalogos, categoria, nombre):
    cat = catalogos[categoria]
    if nombre in cat:
        return cat[nombre]
    nuevo = len(cat) + 1
    cat[nombre] = nuevo
    return nuevo

def obtenerNombrePorCodigo(catalogos, categoria, codigo):
    for nombre, cod in catalogos[categoria].items():
        if cod == codigo:
            return nombre
    return "Desconocido"

def obtenerNombreTipoPago(codigo):
    return {0: "Pendiente",
            1: "Efectivo",
            2: "SINPE",
            3: "Tarjeta"}.get(codigo, "Desconocido")

def obtenerConfiguracion():
    if not os.path.exists(ARCHIVO_CONFIGURACION):
        messagebox.showerror("Error", "Primero debe configurar el sistema.")
        return None
    with open(ARCHIVO_CONFIGURACION, "r") as archivo:
        return json.load(archivo)

def obtenerSiguienteId():
    if not listaEstacionamientos:
        return 1
    return max(obj.id for obj in listaEstacionamientos) + 1

def generarPlaca():
    letras = "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(3))
    numeros = "".join(random.choice("0123456789") for _ in range(3))
    return letras + numeros

def generarFechaHoraEntradaAleatoria():
    ahora = datetime.datetime.now()
    apertura = ahora.replace(hour=7, minute=0, second=0, microsecond=0)
    if ahora <= apertura:
        return apertura.strftime("%d-%m-%Y %H:%M")
    segundos = int((ahora - apertura).total_seconds())
    aleatorio = random.randint(0, segundos)
    return (apertura + datetime.timedelta(seconds=aleatorio)).strftime("%d-%m-%Y %H:%M")

def calcularMonto(vehiculo, configuracion):
    entrada = datetime.datetime.strptime(vehiculo.estadia[1], "%d-%m-%Y %H:%M")
    salida = datetime.datetime.now()
    minutos = (salida - entrada).total_seconds() / 60
    if minutos <= configuracion["tiempoGracia"]:
        return 0, salida
    horas = ceil((minutos - configuracion["tiempoGracia"]) / 60)
    return horas * configuracion["cobroHora"], salida

#
def generarQR(texto, nombreArchivo):
    qr = qrcode.make(texto)
    qr.save(nombreArchivo)

def generarVoucherPDF(vehiculo):
    catalogos = cargarCatalogos()
    marca = obtenerNombrePorCodigo(catalogos, "marca", vehiculo.info[1])
    tipo = obtenerNombrePorCodigo(catalogos, "tipo", vehiculo.info[3])
    fechaArchivo = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M")
    datosQR = f"{vehiculo.info[0]}-{marca}-{tipo}-{vehiculo.estadia[1]}"
    nombreQR = f"QR_V_{vehiculo.info[0]}.png"
    generarQR(datosQR, nombreQR)
    nombrePDF = f"voucher_{vehiculo.info[0]}_{fechaArchivo}.pdf"
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "VOUCHER DE PARQUEO", ln=True, align="C")
    pdf.ln(8)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Placa: {vehiculo.info[0]}", ln=True)
    pdf.cell(0, 8, f"Marca: {marca}", ln=True)
    pdf.cell(0, 8, f"Tipo: {tipo}", ln=True)
    pdf.cell(0, 8, f"Ubicacion: {vehiculo.estadia[0]}", ln=True)
    pdf.cell(0, 8, f"Fecha entrada: {vehiculo.estadia[1]}", ln=True)
    pdf.ln(8)
    pdf.image(nombreQR, x=65, w=80)
    pdf.output(nombrePDF)
    if os.path.exists(nombreQR):
        os.remove(nombreQR)

def generarFacturaPDF(vehiculo):
    catalogos = cargarCatalogos()
    marca = obtenerNombrePorCodigo(catalogos, "marca", vehiculo.info[1])
    color = obtenerNombrePorCodigo(catalogos, "color", vehiculo.info[2])
    tipo = obtenerNombrePorCodigo(catalogos, "tipo", vehiculo.info[3])
    tipoPago = obtenerNombreTipoPago(vehiculo.pago[1])
    fechaArchivo = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M")
    datosQR = f"Factura Parqueo\nPlaca: {vehiculo.info[0]}\nMonto: {vehiculo.pago[0]}\nPago: {tipoPago}"
    nombreQR = f"QR_F_{vehiculo.info[0]}.png"
    generarQR(datosQR, nombreQR)
    nombrePDF = f"factura_{vehiculo.info[0]}_{fechaArchivo}.pdf"
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "FACTURA DE PARQUEO", ln=True, align="C")
    pdf.ln(8)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Placa: {vehiculo.info[0]}", ln=True)
    pdf.cell(0, 8, f"Marca: {marca}", ln=True)
    pdf.cell(0, 8, f"Color: {color}", ln=True)
    pdf.cell(0, 8, f"Tipo: {tipo}", ln=True)
    pdf.cell(0, 8, f"Ubicacion: {vehiculo.estadia[0]}", ln=True)
    pdf.cell(0, 8, f"Fecha entrada: {vehiculo.estadia[1]}", ln=True)
    pdf.cell(0, 8, f"Fecha salida: {vehiculo.estadia[2]}", ln=True)
    pdf.cell(0, 8, f"Monto pagado: CRC {vehiculo.pago[0]}", ln=True)
    pdf.cell(0, 8, f"Metodo de pago: {tipoPago}", ln=True)
    pdf.ln(8)
    pdf.image(nombreQR, x=65, w=80)
    pdf.output(nombrePDF)
    if os.path.exists(nombreQR):
        os.remove(nombreQR)

#
def dibujarBotonesParqueo(marco, configuracion):
    for widget in marco.winfo_children():
        widget.destroy()
    total = configuracion["cantidadParqueos"]
    electrico = configuracion["tieneElectricos"]
    especiales = max(2, ceil(total * 0.05))
    columnas = 10
    
    for numero in range(1, total + 1):
        color = "#38b000"
        texto = str(numero)
        espacio_id = f"G-{str(numero).zfill(3)}"
        
        if numero <= especiales:
            color = "#072ac8"
            texto = f"E{numero}"
        elif electrico and numero == especiales + 1:
            color = "#fcf300"
            texto = "VE"
            
        for v in listaEstacionamientos:
            if v.estadia[0] == espacio_id:
                color = "#ff002b"
                break
                
        boton = Button(
            marco, text=texto, bg=color, width=8, height=3,
            command=lambda n=numero, m=marco, c=configuracion: observarEspacio(n, m, c)
        )
        boton.grid(row=(numero - 1) // columnas, column=(numero - 1) % columnas, padx=5, pady=5)

#
def ventanaPago(vehiculo, ventanaInfo, marcoParqueos, configuracion):
    ventanaPagoVehiculo = Toplevel()
    ventanaPagoVehiculo.title("Pago")
    ventanaPagoVehiculo.geometry("350x300")
    ventanaPagoVehiculo["bg"] = "#2C3E50"
    
    monto, tiempoSalida = calcularMonto(vehiculo, configuracion)
    Label(ventanaPagoVehiculo, text=f"Monto a pagar: CRC {monto}",
          font=("Arial", 12, "bold"), fg="white", bg="#2C3E50").pack(pady=15)
    
    metodoPago = IntVar()
    Radiobutton(ventanaPagoVehiculo, text="Efectivo", variable=metodoPago,
                value=1, bg="#2C3E50", fg="white", selectcolor="#2C3E50").pack()
    Radiobutton(ventanaPagoVehiculo, text="SINPE", variable=metodoPago,
                value=2, bg="#2C3E50", fg="white", selectcolor="#2C3E50").pack()
    Radiobutton(ventanaPagoVehiculo, text="Tarjeta", variable=metodoPago,
                value=3, bg="#2C3E50", fg="white", selectcolor="#2C3E50").pack()

    def confirmarPago():
        tipoPago = metodoPago.get()
        if tipoPago == 0:
            messagebox.showerror("Error", "Seleccione un método de pago.")
            return
        vehiculo.estadia[2] = tiempoSalida.strftime("%d-%m-%Y %H:%M")
        vehiculo.pago = (monto, tipoPago)
        generarFacturaPDF(vehiculo)
        if vehiculo in listaEstacionamientos:
            listaEstacionamientos.remove(vehiculo)
        guardarBaseDatos(listaEstacionamientos)
        dibujarBotonesParqueo(marcoParqueos, configuracion)
        messagebox.showinfo("Pago", "Pago realizado. Factura generada.")
        ventanaPagoVehiculo.destroy()
        ventanaInfo.destroy()

    Button(ventanaPagoVehiculo, text="Confirmar Pago",
           command=confirmarPago, bg="#38b000", fg="white").pack(pady=20)

def observarEspacio(numeroEspacio, marcoParqueos, configuracion):
    espacio = f"G-{str(numeroEspacio).zfill(3)}"
    catalogos = cargarCatalogos()
    for vehiculo in listaEstacionamientos:
        if vehiculo.estadia[0] == espacio:
            ventanaInfo = Toplevel()
            ventanaInfo.title(f"Espacio Ocupado - {espacio}")
            ventanaInfo.geometry("400x360")
            ventanaInfo["bg"] = "#2C3E50"
            
            campos = [
                ("Ubicación", vehiculo.estadia[0]),
                ("Placa", vehiculo.info[0]),
                ("Marca", obtenerNombrePorCodigo(catalogos, "marca", vehiculo.info[1])),
                ("Color", obtenerNombrePorCodigo(catalogos, "color", vehiculo.info[2])),
                ("Hora de entrada", vehiculo.estadia[1])
            ]
            for etiqueta, valor in campos:
                Label(ventanaInfo, text=etiqueta, fg="white", bg="#2C3E50").pack()
                entrada = Entry(ventanaInfo)
                entrada.insert(0, valor)
                entrada.config(state="readonly")
                entrada.pack()
            
            Button(
                ventanaInfo, text="Realizar Pago", bg="green", fg="white",
                command=lambda v=vehiculo, vi=ventanaInfo: ventanaPago(v, vi, marcoParqueos, configuracion)
            ).pack(pady=10)
            Button(ventanaInfo, text="Regresar", command=ventanaInfo.destroy).pack(pady=5)
            return
    ventanaEstacionarVehiculo(marcoParqueos, configuracion, espacio)

def ventanaEstacionarVehiculo(marcoParqueos, configuracion, ubicacionPreseleccionada=None):
    catalogos = cargarCatalogos()
    if not catalogos["marca"] or not catalogos["color"]:
        messagebox.showwarning("Catálogos vacíos", "Primero debe obtener los vehículos desde la API.")
        return

    ventana = Toplevel()
    ventana.title("Estacionar Vehículo")
    ventana.geometry("400x450")
    ventana["bg"] = "#2C3E50"
    
    Label(ventana, text="Placa", fg="white", bg="#2C3E50").pack()
    entradaPlaca = Entry(ventana)
    entradaPlaca.pack(pady=5)
    
    Label(ventana, text="Marca", fg="white", bg="#2C3E50").pack()
    comboMarca = ttk.Combobox(ventana, values=sorted(catalogos["marca"].keys()), state="readonly")
    comboMarca.pack(pady=5)
    
    Label(ventana, text="Color", fg="white", bg="#2C3E50").pack()
    comboColor = ttk.Combobox(ventana, values=sorted(catalogos["color"].keys()), state="readonly")
    comboColor.pack(pady=5)
    
    Label(ventana, text="Tipo de Vehículo", fg="white", bg="#2C3E50").pack()
    comboTipo = ttk.Combobox(ventana, values=sorted(catalogos["tipo"].keys()), state="readonly")
    comboTipo.pack(pady=5)
    
    Label(ventana, text="Ubicación", fg="white", bg="#2C3E50").pack()
    comboUbicacion = ttk.Combobox(ventana, state="readonly")
    comboUbicacion.pack(pady=5)
    
    ocupados = [v.estadia[0] for v in listaEstacionamientos]
    total = configuracion["cantidadParqueos"]
    electrico = configuracion["tieneElectricos"]
    especiales = max(2, ceil(total * 0.05))
    inicio = especiales + 2 if electrico else especiales + 1
        
    disponibles = []
    for i in range(inicio, total + 1):
        espacio = f"G-{str(i).zfill(3)}"
        if espacio not in ocupados:
            disponibles.append(espacio)
        
    comboUbicacion["values"] = disponibles
    if ubicacionPreseleccionada in disponibles:
        comboUbicacion.set(ubicacionPreseleccionada)
    elif disponibles:
        comboUbicacion.current(0)

    def estacionar():
        catalogosActuales = cargarCatalogos()
        placa = entradaPlaca.get().strip()
        marca = comboMarca.get()
        color = comboColor.get()
        tipo = comboTipo.get()
        ubicacion = comboUbicacion.get()
        
        if not all([placa, marca, color, tipo, ubicacion]):
            messagebox.showerror("Error", "Debe completar todos los campos.")
            return
        if not messagebox.askyesno("Confirmar", f"¿Confirma estacionar en {ubicacion}?"):
            return
            
        codigoMarca = obtenerCodigo(catalogosActuales, "marca", marca)
        codigoColor = obtenerCodigo(catalogosActuales, "color", color)
        codigoTipo = obtenerCodigo(catalogosActuales, "tipo", tipo)
        
        nuevoVehiculo = Estacionamiento(
            obtenerSiguienteId(), placa, codigoMarca, codigoColor, codigoTipo,
            ubicacion, datetime.datetime.now().strftime("%d-%m-%Y %H:%M"), "", 0, 0
        )
        listaEstacionamientos.append(nuevoVehiculo)
        guardarCatalogos(catalogosActuales)
        guardarBaseDatos(listaEstacionamientos)
        generarVoucherPDF(nuevoVehiculo)
        dibujarBotonesParqueo(marcoParqueos, configuracion)
        messagebox.showinfo("Éxito", "Vehículo estacionado correctamente. Voucher generado.")
        ventana.destroy()

    Button(ventana, text="Estacionar", command=estacionar, bg="#38b000", fg="white").pack(pady=10)
    Button(ventana, text="Regresar", command=ventana.destroy).pack()

def ventanaPrincipalEstacionamiento():
    configuracion = obtenerConfiguracion()
    if not configuracion: return
    ventanaSecundaria = Toplevel()
    ventanaSecundaria.title("Mapa del Estacionamiento")
    ventanaSecundaria.geometry("1000x700")
    ventanaSecundaria["bg"] = "#2C3E50"
    
    Label(ventanaSecundaria, text="Estado del Estacionamiento",
          font=("Arial", 16, "bold"), fg="white",
          bg="#2C3E50").pack(pady=10)
    marcoParqueos = Frame(ventanaSecundaria)
    marcoParqueos.pack()
    dibujarBotonesParqueo(marcoParqueos, configuracion)
    
    Label(ventanaSecundaria, text="Casetilla de Cobro", bg="orange", width=20, height=2).pack(pady=10)
    Label(ventanaSecundaria, text="Baño", bg="lightblue", width=20, height=2).pack(pady=5)

#
def solicitarVehiculosMockaroo(cantidad, claveApi):
    columnas = [
        {"name": "marca", "type": "Car Make"},
        {"name": "color", "type": "Color"},
        {"name": "tipo", "type": "Custom List", "values": TIPOS_VEHICULO}
    ]
    cuerpo = json.dumps(columnas).encode("utf-8")
    url = f"https://api.mockaroo.com/api/generate.json?key={claveApi}&count={cantidad}"
    solicitud = urllib.request.Request(url, data=cuerpo,
                                       headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(solicitud, timeout=20) as respuesta:
        return json.loads(respuesta.read().decode("utf-8"))

def ventanaPrincipalObtenerVehiculos():
    configuracion = obtenerConfiguracion()
    if not configuracion: return
    
    ocupados = [v.estadia[0] for v in listaEstacionamientos]
    total = configuracion["cantidadParqueos"]
    electrico = configuracion["tieneElectricos"]
    especiales = max(2, ceil(total * 0.05))
    inicio = especiales + 2 if electrico else especiales + 1
    
    disponibles = [f"G-{str(i).zfill(3)}" for i in range(inicio, total + 1) if f"G-{str(i).zfill(3)}" not in ocupados]
    cantidadDisponibles = len(disponibles)

    ventanaSecundaria = Toplevel()
    ventanaSecundaria.title("Obtener Vehículos Masivos")
    ventanaSecundaria.geometry("550x500")
    ventanaSecundaria["bg"] = "#2C3E50"
    
    Label(ventanaSecundaria,
          text=f"Espacios disponibles para llenado: {cantidadDisponibles}",
          fg="white", bg="#2C3E50").pack(pady=10)
    
    entradaClaveApi = Entry(ventanaSecundaria, width=40)
    entradaClaveApi.pack(pady=5)
    if os.path.exists(ARCHIVO_CLAVE_API):
        with open(ARCHIVO_CLAVE_API, "r") as f: entradaClaveApi.insert(0, f.read().strip())
    
    marcoTexto = Frame(ventanaSecundaria)
    marcoTexto.pack(pady=10, fill=BOTH, expand=True)
    barra = Scrollbar(marcoTexto)
    barra.pack(side=RIGHT, fill=Y)
    textoResultado = Text(marcoTexto, height=15, yscrollcommand=barra.set)
    textoResultado.pack(side=LEFT, fill=BOTH, expand=True)
    barra.config(command=textoResultado.yview)

    def procesarLlenadoMasivo():
        if cantidadDisponibles <= 0:
            messagebox.showerror("Error", "No hay espacios comunes vacíos.")
            return
        claveApi = entradaClaveApi.get().strip()
        if not claveApi:
            messagebox.showerror("Error", "Debe ingresar la clave de API.")
            return
            
        with open(ARCHIVO_CLAVE_API, "w") as f: f.write(claveApi)
        
        try:
            registros = solicitarVehiculosMockaroo(cantidadDisponibles, claveApi)
        except Exception as e:
            messagebox.showerror("Error de Conexión", f"Fallo al contactar Mockaroo: {str(e)}")
            return
            
        if not messagebox.askyesno("Confirmar", f"¿Confirma estacionar {len(registros)} vehículos automáticamente?"):
            return
            
        catalogos = cargarCatalogos()
        textoResultado.delete("1.0", END)
        
        for idx, reg in enumerate(registros):
            placa = generarPlaca()
            ubicacion = disponibles[idx]
            
            codigoMarca = obtenerCodigo(catalogos, "marca", reg["marca"])
            codigoColor = obtenerCodigo(catalogos, "color", reg["color"])
            codigoTipo = obtenerCodigo(catalogos, "tipo", reg["tipo"])
            
            nuevoVehiculo = Estacionamiento(
                obtenerSiguienteId(), placa, codigoMarca, codigoColor, codigoTipo,
                ubicacion, generarFechaHoraEntradaAleatoria(), "", 0, 0
            )
            listaEstacionamientos.append(nuevoVehiculo)
            generarVoucherPDF(nuevoVehiculo)
            
            textoResultado.insert(END, f"{placa} | {reg['marca']} | {reg['color']} | {reg['tipo']} | {ubicacion}\n")
            
        guardarCatalogos(catalogos)
        guardarBaseDatos(listaEstacionamientos)
        messagebox.showinfo("Éxito", "Llenado completado de manera limpia.")
        ventanaSecundaria.destroy()

    Button(ventanaSecundaria, text="Ejecutar Carga desde API",
           command=procesarLlenadoMasivo, bg="#38b000",
           fg="white").pack(pady=10)

#
def cierreDiarioPDF():
    configuracion = obtenerConfiguracion()
    if not configuracion: return

    tiposPago = [1, 2, 3]
    for idx, vehiculo in enumerate(listaEstacionamientos):
        if vehiculo.pago[1] == 0:
            monto, salida = calcularMonto(vehiculo, configuracion)
            vehiculo.estadia[2] = salida.strftime("%d-%m-%Y %H:%M")
            vehiculo.pago = (monto, tiposPago[idx % 3])
            generarFacturaPDF(vehiculo)
            
    guardarBaseDatos(listaEstacionamientos)
    fechaHoy = datetime.datetime.now().strftime("%d-%m-%Y")
    nombrePDF = f"cierre_diario_{fechaHoy}.pdf"
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 12, "CIERRE DIARIO DE PARQUEO", ln=True, align="C")
    pdf.ln(5)
    
    encabezados = ["Ubicación", "Placa", "Entrada", "Salida", "Método", "Monto"]
    anchos = [25, 25, 35, 35, 25, 25]
    pdf.set_font("Arial", "B", 10)
    for i, h in enumerate(encabezados):
        pdf.cell(anchos[i], 8, h, border=1)
    pdf.ln()
    
    pdf.set_font("Arial", "", 9)
    totales = {1: 0, 2: 0, 3: 0}
    
    for v in listaEstacionamientos:
        pdf.cell(anchos[0], 7, v.estadia[0], border=1)
        pdf.cell(anchos[1], 7, v.info[0], border=1)
        pdf.cell(anchos[2], 7, v.estadia[1], border=1)
        pdf.cell(anchos[3], 7, v.estadia[2], border=1)
        pdf.cell(anchos[4], 7, obtenerNombreTipoPago(v.pago[1]), border=1)
        pdf.cell(anchos[5], 7, str(v.pago[0]), border=1)
        pdf.ln()
        if v.pago[1] in totales:
            totales[v.pago[1]] += v.pago[0]
            
    pdf.ln(5)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 6, f"Efectivo: CRC {totales[1]}", ln=True)
    pdf.cell(0, 6, f"SINPE: CRC {totales[2]}", ln=True)
    pdf.cell(0, 6, f"Tarjeta: CRC {totales[3]}", ln=True)
    pdf.cell(0, 8, f"TOTAL DIARIO: CRC {sum(totales.values())}", ln=True)
    pdf.output(nombrePDF)
    messagebox.showinfo("Reporte", f"PDF de cierre creado: {nombrePDF}")

def cierrePorTipoPagoXML():
    catalogos = cargarCatalogos()
    raiz = ET.Element("cierrePago")
    secciones = {1: ET.SubElement(raiz, "efectivo"),
                 2: ET.SubElement(raiz, "sinpe"),
                 3: ET.SubElement(raiz, "tarjeta")}
    
    for vehiculo in listaEstacionamientos:
        padre = secciones.get(vehiculo.pago[1])
        if padre is None: continue
        
        v = ET.SubElement(padre, "vehiculo")
        ET.SubElement(v, "id").text = str(vehiculo.id)
        ET.SubElement(v, "placa").text = vehiculo.info[0]
        ET.SubElement(v, "marca").text = obtenerNombrePorCodigo(catalogos, "marca", vehiculo.info[1])
        ET.SubElement(v, "ubicacion").text = vehiculo.estadia[0]
        ET.SubElement(v, "monto").text = str(vehiculo.pago[0])
        
    arbol = ET.ElementTree(raiz)
    ET.indent(arbol, space="    ")
    nombreXML = f"cierre_tipo_pago_{datetime.datetime.now().strftime('%d-%m-%Y')}.xml"
    arbol.write(nombreXML, encoding="utf-8", xml_declaration=True)
    messagebox.showinfo("XML", f"Archivo XML listo: {nombreXML}")

def exportarCSV():
    nombreCSV = f"cierre_diario_{datetime.datetime.now().strftime('%d-%m-%Y')}.csv"
    with open(nombreCSV, "w", newline="",
              encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        for v in listaEstacionamientos:
            escritor.writerow([v.estadia[0], v.info[0],
                               v.estadia[1], v.estadia[2],
                               obtenerNombreTipoPago(v.pago[1]),
                               v.pago[0]])
    messagebox.showinfo("CSV", f"Archivo CSV guardado: {nombreCSV}")

def ventanaPrincipalReportes():
    ventanaSecundaria = Toplevel()
    ventanaSecundaria.title("Módulo de Reportes")
    ventanaSecundaria.geometry("300x250")
    ventanaSecundaria["bg"] = "#2C3E50"
    
    Button(ventanaSecundaria, text="Cierre Diario (PDF)",
           width=30, command=cierreDiarioPDF).pack(pady=10)
    Button(ventanaSecundaria, text="Cierre por Métodos (XML)",
           width=30, command=cierrePorTipoPagoXML).pack(pady=10)
    Button(ventanaSecundaria, text="Exportar Datos (CSV)",
           width=30, command=exportarCSV).pack(pady=10)

#
def ventanaPrincipalConfiguracion():
    ventanaSecundaria = Toplevel()
    ventanaSecundaria.title("Configuración")
    ventanaSecundaria.geometry("350x350")
    ventanaSecundaria["bg"] = "#2C3E50"
    
    Label(ventanaSecundaria, text="Cantidad de parqueos:", fg="white", bg="#2C3E50").pack()
    entradaCantidad = Entry(ventanaSecundaria)
    entradaCantidad.pack(pady=5)
    
    Label(ventanaSecundaria, text="Tiempo de gracia (minutos):", fg="white", bg="#2C3E50").pack()
    entradaTiempoGracia = Entry(ventanaSecundaria)
    entradaTiempoGracia.pack(pady=5)
    
    Label(ventanaSecundaria, text="Cobro por hora (CRC):",
          fg="white", bg="#2C3E50").pack()
    entradaCobroHora = Entry(ventanaSecundaria)
    entradaCobroHora.pack(pady=5)
    
    carrosElectricos = IntVar()
    Checkbutton(ventanaSecundaria,
                text="¿Espacios Eléctricos?",
                variable=carrosElectricos,
                bg="#2C3E50", fg="white").pack(pady=5)

    def guardarConfiguracion():
        try:
            config = {
                "cantidadParqueos": int(entradaCantidad.get()),
                "tiempoGracia": int(entradaTiempoGracia.get()),
                "cobroHora": int(entradaCobroHora.get()),
                "tieneElectricos": bool(carrosElectricos.get())
            }
            if config["cantidadParqueos"] <= 0: raise ValueError
            with open(ARCHIVO_CONFIGURACION, "w") as archivo: json.dump(config, archivo, indent=4)
            messagebox.showinfo("Configuración", "Datos guardados.")
            ventanaSecundaria.destroy()
        except ValueError:
            messagebox.showerror("Error", "Campos numéricos no válidos.")

    Button(ventanaSecundaria, text="Guardar Cambios",
           command=guardarConfiguracion, bg="#38b000",
           fg="white").pack(pady=10)

#
def ventanaPrincipalAcercaDe():
    ventanaSecundaria = Toplevel()
    ventanaSecundaria.title("Acerca De")
    ventanaSecundaria.geometry("450x250")
    ventanaSecundaria["bg"] = "#2C3E50"
    Label(ventanaSecundaria, text="SISTEMA DE GESTIÓN DE PARQUEOS",
          font=("Arial", 12, "bold"),
          fg="white", bg="#2C3E50").pack(pady=20)
    Label(ventanaSecundaria,
          text="Desarrollado por:\n• Caleb Córdoba Durán\n• José Francisco Otárola Ulate",
          font=("Arial", 10), fg="white", bg="#2C3E50",
          justify=LEFT).pack(pady=10)

listaEstacionamientos = cargarBaseDatos()

Label(ventanaPrincipal, text="Menú Principal",
      font=("Arial", 14, "bold"), fg="white", bg="#2C3E50").pack(pady=15)
Button(ventanaPrincipal, text="Carga Masiva (API)",
       width=25, command=ventanaPrincipalObtenerVehiculos).pack(pady=10)
Button(ventanaPrincipal, text="Mapa del Estacionamiento",
       width=25, command=ventanaPrincipalEstacionamiento).pack(pady=10)
Button(ventanaPrincipal, text="Panel de Reportes",
       width=25, command=ventanaPrincipalReportes).pack(pady=10)
Button(ventanaPrincipal, text="Configuraciones",
       width=25, command=ventanaPrincipalConfiguracion).pack(pady=10)
Button(ventanaPrincipal, text="Acerca De",
       width=25, command=ventanaPrincipalAcercaDe).pack(pady=10)

ventanaPrincipal.mainloop()
