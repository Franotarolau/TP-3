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
ventanaPrincipal.title("Sistema de Parqueo")
ventanaPrincipal.geometry("400x400")

ARCHIVO_CONFIGURACION = "configuracion.json"
ARCHIVO_CATALOGOS = "catalogoVehiculos.json"
ARCHIVO_BASE_DATOS = "baseDatosEstacionamiento.json"
ARCHIVO_CLAVE_API = "mockarooApiKey.txt"

TIPOS_VEHICULO = ["Sedan", "SUV", "Pickup", "Hatchback", "Motocicleta","Van"]

listaEstacionamientos = []


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


def cargarBaseDatos():
    if not os.path.exists(ARCHIVO_BASE_DATOS):
        return []
    with open(ARCHIVO_BASE_DATOS, "r", encoding="utf-8") as archivo:
        registros = json.load(archivo)
    resultado = []
    for r in registros:
        resultado.append(estacionamientoDesdeDiccionario(r))
    return resultado


def guardarBaseDatos(lista):
    diccionarios = []
    for obj in lista:
        diccionarios.append(obj.aDiccionario())
    with open(ARCHIVO_BASE_DATOS, "w", encoding="utf-8") as archivo:
        json.dump(diccionarios, archivo, indent=4, ensure_ascii=False)


def cargarCatalogos():
    if os.path.exists(ARCHIVO_CATALOGOS):
        with open(ARCHIVO_CATALOGOS, "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    catalogos = {"marca": {}, "color": {}, "tipo": {}}
    i = 0
    while i < len(TIPOS_VEHICULO):
        catalogos["tipo"][TIPOS_VEHICULO[i]] = i + 1
        i = i + 1
    return catalogos


def guardarCatalogos(catalogos):
    with open(ARCHIVO_CATALOGOS, "w", encoding="utf-8") as archivo:
        json.dump(catalogos, archivo, indent=4, ensure_ascii=False)


def obtenerCodigo(catalogos, categoria, nombre):
    cat = catalogos[categoria]
    if nombre in cat:
        return cat[nombre]
    nuevo = len(cat) + 1
    cat[nombre] = nuevo
    return nuevo


def obtenerNombrePorCodigo(catalogos, categoria, codigo):
    for nombre in catalogos[categoria]:
        if catalogos[categoria][nombre] == codigo:
            return nombre
    return "Desconocido"


def obtenerNombreTipoPago(codigo):
    nombres = {0: "Pendiente", 1: "Efectivo", 2: "SINPE", 3: "Tarjeta"}
    if codigo in nombres:
        return nombres[codigo]
    return "Desconocido"


def obtenerConfiguracion():
    if not os.path.exists(ARCHIVO_CONFIGURACION):
        messagebox.showerror("Error", "Primero debe configurar el sistema.")
        return None
    with open(ARCHIVO_CONFIGURACION, "r") as archivo:
        return json.load(archivo)


def obtenerSiguienteId(lista):
    if len(lista) == 0:
        return 1
    maximo = 0
    for obj in lista:
        if obj.id > maximo:
            maximo = obj.id
    return maximo + 1


def obtenerUbicacionesGeneralesDisponibles(configuracion, lista):
    total = configuracion["cantidadParqueos"]
    electrico = configuracion["tieneElectricos"]
    especiales = ceil(total * 0.05)
    if especiales < 2:
        especiales = 2
    inicio = especiales + 1
    if electrico:
        inicio = inicio + 1
    ocupados = []
    for v in lista:
        ocupados.append(v.estadia[0])
    disponibles = []
    i = inicio
    while i <= total:
        espacio = "G-" + str(i).zfill(3)
        if espacio not in ocupados:
            disponibles.append(espacio)
        i = i + 1
    return disponibles


def generarFechaHoraEntradaAleatoria():
    ahora = datetime.datetime.now()
    apertura = ahora.replace(hour=7, minute=0, second=0, microsecond=0)
    if ahora <= apertura:
        return apertura.strftime("%d-%m-%Y %H:%M")
    segundos = int((ahora - apertura).total_seconds())
    aleatorio = random.randint(0, segundos)
    return (apertura + datetime.timedelta(seconds=aleatorio)).strftime("%d-%m-%Y %H:%M")


def cargarClaveApiGuardada():
    if not os.path.exists(ARCHIVO_CLAVE_API):
        return ""
    with open(ARCHIVO_CLAVE_API, "r") as archivo:
        return archivo.read().strip()


def guardarClaveApi(clave):
    with open(ARCHIVO_CLAVE_API, "w") as archivo:
        archivo.write(clave)


def generarPlaca():
    letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    placa = ""
    i = 0
    while i < 3:
        placa = placa + letras[random.randint(0, 25)]
        i = i + 1
    i = 0
    while i < 3:
        placa = placa + str(random.randint(0, 9))
        i = i + 1
    return placa


def solicitarVehiculosMockaroo(cantidad, claveApi):
    url = "https://api.mockaroo.com/api/b3675a70?count=" + str(cantidad) + "&key=" + claveApi
 
    peticion = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"}
    )
    try:
        with urllib.request.urlopen(peticion, timeout=20) as respuesta:
            contenido = respuesta.read().decode("utf-8")
        return json.loads(contenido)
    except urllib.error.HTTPError as error:
        detalle = ""
        try:
            detalle = error.read().decode("utf-8")
        except Exception:
            pass
        print("DETALLE DEL ERROR MOCKAROO:", detalle)
       
        error.detalleMockaroo = detalle
        raise error


def construirDiccionarioVehiculos(registros):
    diccionario = {}

    for registro in registros:

        placa = registro["placa"]

        while placa in diccionario:
            placa = generarPlaca()

        diccionario[placa] = {
            "marca": registro["marca"],
            "color": registro["color"],
            "tipo": registro["tipo"],
            "ubicacion": "",
            "fechaHoraEntrada": "",
            "fechaHoraSalida": "",
            "monto": 0,
            "tipoPago": 0
        }

    return diccionario


def calcularCantidadVehiculos():
    configuracion = obtenerConfiguracion()
    if configuracion == None:
        return None
    total = configuracion["cantidadParqueos"]
    electrico = configuracion["tieneElectricos"]
    especiales = ceil(total * 0.05)
    if especiales < 2:
        especiales = 2
    disponibles = total - especiales
    if electrico:
        disponibles = disponibles - 1
    libres = ceil(disponibles * 0.05)
    cantidad = disponibles - libres
    print("Total parqueos:", total)
    print("Especiales:", especiales)
    print("Electrico:", electrico)
    print("Disponibles:", disponibles)
    print("Libres reservados:", libres)
    print("A solicitar:", cantidad)
    return cantidad


def calcularMonto(vehiculo, configuracion):
    entrada = datetime.datetime.strptime(vehiculo.estadia[1], "%d-%m-%Y %H:%M")
    salida = datetime.datetime.now()
    minutos = (salida - entrada).total_seconds() / 60
    if minutos <= configuracion["tiempoGracia"]:
        return 0, salida
    horas = ceil((minutos - configuracion["tiempoGracia"]) / 60)
    return horas * configuracion["cobroHora"], salida


def generarQR(texto, nombreArchivo):
    qr = qrcode.make(texto)
    qr.save(nombreArchivo)


def generarVoucherPDF(vehiculo):
    catalogos = cargarCatalogos()
    marca = obtenerNombrePorCodigo(catalogos, "marca", vehiculo.info[1])
    tipo = obtenerNombrePorCodigo(catalogos, "tipo", vehiculo.info[3])
    fechaArchivo = datetime.datetime.now().strftime("%d-%m-%Y_%H-%M")
    datosQR = vehiculo.info[0] + "-" + marca + "-" + tipo + "-" + vehiculo.estadia[1]
    nombreQR = "QR_V_" + vehiculo.info[0] + ".png"
    generarQR(datosQR, nombreQR)
    nombrePDF = "voucher_" + vehiculo.info[0] + "_" + fechaArchivo + ".pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "VOUCHER DE PARQUEO", ln=True, align="C")
    pdf.ln(8)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, "Placa: " + vehiculo.info[0], ln=True)
    pdf.cell(0, 8, "Marca: " + marca, ln=True)
    pdf.cell(0, 8, "Tipo: " + tipo, ln=True)
    pdf.cell(0, 8, "Ubicacion: " + vehiculo.estadia[0], ln=True)
    pdf.cell(0, 8, "Fecha entrada: " + vehiculo.estadia[1], ln=True)
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
    datosQR = (
        "Factura Parqueo\nPlaca: " + vehiculo.info[0] +
        "\nMarca: " + marca + "\nTipo: " + tipo +
        "\nUbicacion: " + vehiculo.estadia[0] +
        "\nEntrada: " + vehiculo.estadia[1] +
        "\nSalida: " + vehiculo.estadia[2] +
        "\nMonto: " + str(vehiculo.pago[0]) +
        "\nPago: " + tipoPago
    )
    nombreQR = "QR_F_" + vehiculo.info[0] + ".png"
    generarQR(datosQR, nombreQR)
    nombrePDF = "factura_" + vehiculo.info[0] + "_" + fechaArchivo + ".pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "FACTURA DE PARQUEO", ln=True, align="C")
    pdf.ln(8)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, "Placa: " + vehiculo.info[0], ln=True)
    pdf.cell(0, 8, "Marca: " + marca, ln=True)
    pdf.cell(0, 8, "Color: " + color, ln=True)
    pdf.cell(0, 8, "Tipo: " + tipo, ln=True)
    pdf.cell(0, 8, "Ubicacion: " + vehiculo.estadia[0], ln=True)
    pdf.cell(0, 8, "Fecha entrada: " + vehiculo.estadia[1], ln=True)
    pdf.cell(0, 8, "Fecha salida: " + vehiculo.estadia[2], ln=True)
    pdf.cell(0, 8, "Monto pagado: CRC " + str(vehiculo.pago[0]), ln=True)
    pdf.cell(0, 8, "Metodo de pago: " + tipoPago, ln=True)
    pdf.ln(8)
    pdf.image(nombreQR, x=65, w=80)
    pdf.output(nombrePDF)
    if os.path.exists(nombreQR):
        os.remove(nombreQR)


def dibujarBotonesParqueo(marco, configuracion):
    for widget in marco.winfo_children():
        widget.destroy()
    total = configuracion["cantidadParqueos"]
    electrico = configuracion["tieneElectricos"]
    especiales = ceil(total * 0.05)
    if especiales < 2:
        especiales = 2
    columnas = 10
    for numero in range(1, total + 1):
        color = "#38b000"
        texto = str(numero)
        if numero <= especiales:
            color = "#072ac8"
            texto = "E" + str(numero)
        elif electrico and numero == especiales + 1:
            color = "#fcf300"
            texto = "VE"
        for v in listaEstacionamientos:
            if v.estadia[0] == "G-" + str(numero).zfill(3):
                color = "#ff002b"
                break
        boton = Button(
            marco, text=texto, bg=color, width=8, height=3,
            command=lambda n=numero, m=marco, c=configuracion: observarEspacio(n, m, c)
        )
        boton.grid(row=(numero - 1) // columnas, column=(numero - 1) % columnas, padx=5, pady=5)


def ventanaPago(vehiculo, ventanaInfo, marcoParqueos, configuracion):
    ventanaPagoVehiculo = Toplevel()
    ventanaPagoVehiculo.title("Pago")
    ventanaPagoVehiculo.geometry("350x300")
    monto, tiempoSalida = calcularMonto(vehiculo, configuracion)
    Label(ventanaPagoVehiculo, text="Monto a pagar: CRC " + str(monto), font=("Arial", 12, "bold")).pack(pady=15)
    metodoPago = IntVar()
    Radiobutton(ventanaPagoVehiculo, text="Efectivo", variable=metodoPago, value=1).pack()
    Radiobutton(ventanaPagoVehiculo, text="SINPE", variable=metodoPago, value=2).pack()
    Radiobutton(ventanaPagoVehiculo, text="Tarjeta", variable=metodoPago, value=3).pack()

    def confirmarPago():
        tipoPago = metodoPago.get()
        if tipoPago == 0:
            messagebox.showerror("Error", "Seleccione un metodo de pago.")
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

    Button(ventanaPagoVehiculo, text="Confirmar Pago", command=confirmarPago).pack(pady=20)


def observarEspacio(numeroEspacio, marcoParqueos, configuracion):
    espacio = "G-" + str(numeroEspacio).zfill(3)
    catalogos = cargarCatalogos()
    for vehiculo in listaEstacionamientos:
        if vehiculo.estadia[0] == espacio:
            ventanaInfo = Toplevel()
            ventanaInfo.title("Espacio Ocupado - " + espacio)
            ventanaInfo.geometry("400x360")
            campos = [
                ("Ubicacion", vehiculo.estadia[0]),
                ("Placa", vehiculo.info[0]),
                ("Marca", obtenerNombrePorCodigo(catalogos, "marca", vehiculo.info[1])),
                ("Color", obtenerNombrePorCodigo(catalogos, "color", vehiculo.info[2])),
                ("Hora de entrada", vehiculo.estadia[1])
            ]
            for etiqueta, valor in campos:
                Label(ventanaInfo, text=etiqueta).pack()
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
    ventana = Toplevel()
    ventana.title("Estacionar Vehiculo")
    ventana.geometry("400x420")
    Label(ventana, text="Placa").pack()
    entradaPlaca = Entry(ventana)
    entradaPlaca.pack(pady=5)
    Label(ventana, text="Marca").pack()
    entradaMarca = Entry(ventana)
    entradaMarca.pack(pady=5)

    Label(ventana, text="Color").pack()
    entradaColor = Entry(ventana)
    entradaColor.pack(pady=5)
    Label(ventana, text="Tipo de vehiculo").pack()
    comboTipo = ttk.Combobox(ventana, values=sorted(catalogos["tipo"].keys()), state="readonly")
    comboTipo.pack(pady=5)
    Label(ventana, text="Ubicacion").pack()
    comboUbicacion = ttk.Combobox(ventana, state="readonly")
    comboUbicacion.pack(pady=5)
    disponibles = obtenerUbicacionesGeneralesDisponibles(configuracion, listaEstacionamientos)
    comboUbicacion["values"] = disponibles
    if ubicacionPreseleccionada != None and ubicacionPreseleccionada in disponibles:
        comboUbicacion.set(ubicacionPreseleccionada)
    elif len(disponibles) > 0:
        comboUbicacion.current(0)

    def estacionar():
        catalogosActuales = cargarCatalogos()
        placa = entradaPlaca.get().strip()
        marca = entradaMarca.get().strip()
        color = entradaColor.get().strip()
        tipo = comboTipo.get()
        ubicacion = comboUbicacion.get()
        if placa == "" or marca == "" or color == "" or tipo == "" or ubicacion == "":
            messagebox.showerror("Error", "Debe completar todos los campos.")
            return
        if not messagebox.askyesno("Confirmar", "Confirma estacionar en " + ubicacion + "?"):
            return
        codigoMarca = obtenerCodigo(catalogosActuales, "marca", marca)
        codigoColor = obtenerCodigo(catalogosActuales, "color", color)
        codigoTipo = obtenerCodigo(catalogosActuales, "tipo", tipo)
        nuevoVehiculo = Estacionamiento(
            obtenerSiguienteId(listaEstacionamientos),
            placa, codigoMarca, codigoColor, codigoTipo,
            ubicacion, datetime.datetime.now().strftime("%d-%m-%Y %H:%M"), "", 0, 0
        )
        listaEstacionamientos.append(nuevoVehiculo)
        guardarCatalogos(catalogosActuales)
        guardarBaseDatos(listaEstacionamientos)
        generarVoucherPDF(nuevoVehiculo)
        dibujarBotonesParqueo(marcoParqueos, configuracion)
        messagebox.showinfo("Exito", "Vehiculo estacionado. Voucher generado.")
        ventana.destroy()

    Button(ventana, text="Estacionar", command=estacionar).pack(pady=10)
    Button(ventana, text="Regresar", command=ventana.destroy).pack()


def ventanaPrincipalEstacionamiento():
    configuracion = obtenerConfiguracion()
    if configuracion == None:
        return
    ventanaSecundaria = Toplevel()
    ventanaSecundaria.title("Mapa del Estacionamiento")
    ventanaSecundaria.geometry("1000x700")
    Label(ventanaSecundaria, text="Estado del Estacionamiento", font=("Arial", 16, "bold")).pack(pady=10)
    marcoParqueos = Frame(ventanaSecundaria)
    marcoParqueos.pack()
    dibujarBotonesParqueo(marcoParqueos, configuracion)
    Label(ventanaSecundaria, text="Casetilla de Cobro", bg="orange", width=20, height=2).pack(pady=10)
    Label(ventanaSecundaria, text="Bano", bg="lightblue", width=20, height=2).pack(pady=5)


def cierreDiarioPDF():
    configuracion = obtenerConfiguracion()
    if configuracion == None:
        return
    tiposPago = [1, 2, 3]
    indice = 0
    for vehiculo in listaEstacionamientos:
        if vehiculo.pago[1] == 0:
            monto, salida = calcularMonto(vehiculo, configuracion)
            vehiculo.estadia[2] = salida.strftime("%d-%m-%Y %H:%M")
            vehiculo.pago = (monto, tiposPago[indice % 3])
            generarFacturaPDF(vehiculo)
            indice = indice + 1
    guardarBaseDatos(listaEstacionamientos)
    catalogos = cargarCatalogos()
    fechaHoy = datetime.datetime.now().strftime("%d-%m-%Y")
    nombrePDF = "cierre_diario_" + fechaHoy + ".pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(True, 15)
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(0, 51, 153)
    pdf.cell(0, 12, "CIERRE DIARIO DE PARQUEO", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, "Fecha: " + fechaHoy, ln=True, align="C")
    pdf.ln(6)
    encabezados = ["Ubicacion", "Placa", "Entrada", "Salida", "Pago", "Monto"]
    anchos = [28, 22, 35, 35, 25, 25]
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(0, 51, 153)
    pdf.set_text_color(255, 255, 255)
    i = 0
    while i < len(encabezados):
        pdf.cell(anchos[i], 8, encabezados[i], border=1, fill=True)
        i = i + 1
    pdf.ln()
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(0, 0, 0)
    totalEfectivo = 0
    totalSinpe = 0
    totalTarjeta = 0
    for vehiculo in listaEstacionamientos:
        salida = vehiculo.estadia[2] if vehiculo.estadia[2] != "" else "-"
        pdf.cell(anchos[0], 7, vehiculo.estadia[0], border=1)
        pdf.cell(anchos[1], 7, vehiculo.info[0], border=1)
        pdf.cell(anchos[2], 7, vehiculo.estadia[1], border=1)
        pdf.cell(anchos[3], 7, salida, border=1)
        pdf.cell(anchos[4], 7, obtenerNombreTipoPago(vehiculo.pago[1]), border=1)
        pdf.cell(anchos[5], 7, str(vehiculo.pago[0]), border=1)
        pdf.ln()
        if vehiculo.pago[1] == 1:
            totalEfectivo = totalEfectivo + vehiculo.pago[0]
        elif vehiculo.pago[1] == 2:
            totalSinpe = totalSinpe + vehiculo.pago[0]
        elif vehiculo.pago[1] == 3:
            totalTarjeta = totalTarjeta + vehiculo.pago[0]
    pdf.ln(6)
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(180, 0, 0)
    pdf.cell(0, 8, "Efectivo: CRC " + str(totalEfectivo), ln=True)
    pdf.cell(0, 8, "SINPE: CRC " + str(totalSinpe), ln=True)
    pdf.cell(0, 8, "Tarjeta: CRC " + str(totalTarjeta), ln=True)
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(0, 100, 0)
    pdf.cell(0, 10, "TOTAL GENERAL: CRC " + str(totalEfectivo + totalSinpe + totalTarjeta), ln=True)
    pdf.output(nombrePDF)
    messagebox.showinfo("Cierre Diario", "PDF generado: " + nombrePDF)


def cierrePorTipoPagoXML():
    catalogos = cargarCatalogos()
    raiz = ET.Element("cierrePago")
    efectivoElem = ET.SubElement(raiz, "efectivo")
    sinpeElem = ET.SubElement(raiz, "sinpe")
    tarjetaElem = ET.SubElement(raiz, "tarjeta")
    for vehiculo in listaEstacionamientos:
        tipoPago = vehiculo.pago[1]
        if tipoPago == 1:
            padre = efectivoElem
        elif tipoPago == 2:
            padre = sinpeElem
        elif tipoPago == 3:
            padre = tarjetaElem
        else:
            continue
        v = ET.SubElement(padre, "vehiculo")
        ET.SubElement(v, "id").text = str(vehiculo.id)
        ET.SubElement(v, "placa").text = vehiculo.info[0]
        ET.SubElement(v, "marca").text = obtenerNombrePorCodigo(catalogos, "marca", vehiculo.info[1])
        ET.SubElement(v, "color").text = obtenerNombrePorCodigo(catalogos, "color", vehiculo.info[2])
        ET.SubElement(v, "tipo").text = obtenerNombrePorCodigo(catalogos, "tipo", vehiculo.info[3])
        ET.SubElement(v, "ubicacion").text = vehiculo.estadia[0]
        ET.SubElement(v, "fechaHoraEntrada").text = vehiculo.estadia[1]
        ET.SubElement(v, "fechaHoraSalida").text = vehiculo.estadia[2]
        ET.SubElement(v, "monto").text = str(vehiculo.pago[0])
        ET.SubElement(v, "tipoPago").text = obtenerNombreTipoPago(tipoPago)
    arbol = ET.ElementTree(raiz)
    ET.indent(arbol, space="    ")
    nombreXML = "cierre_tipo_pago_" + datetime.datetime.now().strftime("%d-%m-%Y") + ".xml"
    arbol.write(nombreXML, encoding="utf-8", xml_declaration=True)
    messagebox.showinfo("Cierre por Tipo de Pago", "XML generado: " + nombreXML)


def exportarCSV():
    nombreCSV = "cierre_diario_" + datetime.datetime.now().strftime("%d-%m-%Y") + ".csv"
    with open(nombreCSV, "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.writer(archivo)
        for vehiculo in listaEstacionamientos:
            salida = vehiculo.estadia[2] if vehiculo.estadia[2] != "" else ""
            escritor.writerow([
                vehiculo.estadia[0],
                vehiculo.info[0],
                vehiculo.estadia[1],
                salida,
                obtenerNombreTipoPago(vehiculo.pago[1]),
                vehiculo.pago[0]
            ])
    messagebox.showinfo("Exportar CSV", "CSV generado: " + nombreCSV)


def ventanaPrincipalReportes():
    configuracion = obtenerConfiguracion()
    if configuracion == None:
        return
    ventanaSecundaria = Toplevel()
    ventanaSecundaria.title("Reportes")
    ventanaSecundaria.geometry("300x250")
    Label(ventanaSecundaria, text="Reportes", font=("Arial", 14, "bold")).pack(pady=15)
    Button(ventanaSecundaria, text="Cierre Diario (PDF)", width=30, command=cierreDiarioPDF).pack(pady=10)
    Button(ventanaSecundaria, text="Cierre por Tipo de Pago (XML)", width=30, command=cierrePorTipoPagoXML).pack(pady=10)
    Button(ventanaSecundaria, text="Exportar Cierre Diario a CSV", width=30, command=exportarCSV).pack(pady=10)
    Button(ventanaSecundaria, text="Regresar", command=ventanaSecundaria.destroy).pack(pady=10)


def ventanaPrincipalObtenerVehiculos():
    configuracion = obtenerConfiguracion()
    if configuracion == None:
        return
    cantidadVehiculos = calcularCantidadVehiculos()
    ventanaSecundaria = Toplevel()
    ventanaSecundaria.title("Obtener Vehiculos")
    ventanaSecundaria.geometry("550x500")
    Label(ventanaSecundaria, text="Vehiculos a solicitar: " + str(cantidadVehiculos)).pack(pady=10)
    marcoTexto = Frame(ventanaSecundaria)
    marcoTexto.pack(pady=10, fill=BOTH, expand=True)
    barra = Scrollbar(marcoTexto)
    barra.pack(side=RIGHT, fill=Y)
    textoResultado = Text(marcoTexto, height=15, yscrollcommand=barra.set)
    textoResultado.pack(side=LEFT, fill=BOTH, expand=True)
    barra.config(command=textoResultado.yview)

    def procesarLlenadoMasivo():
        configuracionActual = obtenerConfiguracion()
        if configuracionActual == None:
            return
        cantidadASolicitar = calcularCantidadVehiculos()
        if cantidadASolicitar == None or cantidadASolicitar <= 0:
            messagebox.showerror("Error", "No hay espacios disponibles.")
            return
        claveApi = "51cdf520"
        if claveApi == "":
            messagebox.showerror("Error", "Debe ingresar la clave de API.")
            return
        guardarClaveApi(claveApi)
        try:
            registrosMockaroo = solicitarVehiculosMockaroo(cantidadASolicitar, claveApi)
        except urllib.error.HTTPError as error:
            detalle = getattr(error, "detalleMockaroo", "")
            messagebox.showerror(
                "Error de API",
                "Mockaroo respondio con error: " + str(error.code) + "\n" + detalle
            )
            return
        except urllib.error.URLError:
            messagebox.showerror("Error de Conexion", "No fue posible conectarse con la API.")
            return
        except (ValueError, KeyError):
            messagebox.showerror("Error", "La respuesta de la API no tiene el formato esperado.")
            return
        if len(registrosMockaroo) == 0:
            messagebox.showerror("Error", "La API no devolvio vehiculos para el llenado masivo.")
            return

        diccionario = construirDiccionarioVehiculos(registrosMockaroo)
        print(json.dumps(diccionario, indent=4, ensure_ascii=False))

    
        ubicacionesDisponibles = obtenerUbicacionesGeneralesDisponibles(configuracionActual, listaEstacionamientos)

        cantidadFinal = cantidadASolicitar
        if len(ubicacionesDisponibles) < cantidadFinal:
            cantidadFinal = len(ubicacionesDisponibles)

        if cantidadFinal <= 0:
            messagebox.showerror("Error", "No hay espacios generales disponibles para el llenado masivo.")
            return

        if not messagebox.askyesno("Confirmar", "Confirma el llenado masivo de " + str(cantidadFinal) + " vehiculos?"):
            return

      
        placasOriginales = list(diccionario.keys())
        datosOriginales = list(diccionario.values())
        totalOriginales = len(placasOriginales)

        catalogos = cargarCatalogos()
        siguienteId = obtenerSiguienteId(listaEstacionamientos)
        textoResultado.delete("1.0", END)

        indice = 0
        while indice < cantidadFinal:
            datos = datosOriginales[indice % totalOriginales]
            if indice < totalOriginales:
                placaAsignada = placasOriginales[indice]
            else:
                placaAsignada = generarPlaca()
                while placaAsignada in diccionario:
                    placaAsignada = generarPlaca()
                diccionario[placaAsignada] = datos

            codigoMarca = obtenerCodigo(catalogos, "marca", datos["marca"])
            codigoColor = obtenerCodigo(catalogos, "color", datos["color"])
            codigoTipo = obtenerCodigo(catalogos, "tipo", datos["tipo"])
            ubicacion = ubicacionesDisponibles[indice]
            fechaHoraEntrada = generarFechaHoraEntradaAleatoria()
            nuevoVehiculo = Estacionamiento(
                siguienteId, placaAsignada, codigoMarca, codigoColor, codigoTipo,
                ubicacion, fechaHoraEntrada, "", 0, 0
            )
            listaEstacionamientos.append(nuevoVehiculo)
            generarVoucherPDF(nuevoVehiculo)
            textoResultado.insert(END, placaAsignada + " | " + datos["marca"] + " | " + datos["color"] + " | " + datos["tipo"] + " | " + ubicacion + " | " + fechaHoraEntrada + "\n")
            siguienteId = siguienteId + 1
            indice = indice + 1

        guardarCatalogos(catalogos)
        guardarBaseDatos(listaEstacionamientos)
        messagebox.showinfo("Obtener Vehiculos", "Se registraron " + str(cantidadFinal) + " vehiculos y se generaron los vouchers.")

    Button(ventanaSecundaria, text="Solicitar vehiculos a la API", command=procesarLlenadoMasivo).pack(pady=10)


def ventanaPrincipalConfiguracion():
    ventanaSecundaria = Toplevel()
    ventanaSecundaria.title("Configuracion")
    ventanaSecundaria.geometry("350x350")
    Label(ventanaSecundaria, text="Cantidad de parqueos:").pack(pady=5)
    entradaCantidad = Entry(ventanaSecundaria)
    entradaCantidad.pack(pady=5)
    Label(ventanaSecundaria, text="Tiempo de gracia (minutos):").pack(pady=5)
    entradaTiempoGracia = Entry(ventanaSecundaria)
    entradaTiempoGracia.pack(pady=5)
    Label(ventanaSecundaria, text="Cobro por hora (CRC):").pack(pady=5)
    entradaCobroHora = Entry(ventanaSecundaria)
    entradaCobroHora.pack(pady=5)
    carrosElectricos = IntVar()
    Checkbutton(ventanaSecundaria, text="Posee espacios para vehiculos electricos?", variable=carrosElectricos).pack(pady=10)

    def guardarConfiguracion():
        try:
            cantidadParqueos = int(entradaCantidad.get())
            tiempoGracia = int(entradaTiempoGracia.get())
            cobroHora = int(entradaCobroHora.get())
            tieneElectricos = bool(carrosElectricos.get())
            if cantidadParqueos <= 0:
                raise ValueError
            if os.path.exists(ARCHIVO_BASE_DATOS):
                if not messagebox.askyesno("Confirmar", "Ya existe una BD. Desea actualizar la configuracion?"):
                    return
            configuracion = {
                "cantidadParqueos": cantidadParqueos,
                "tiempoGracia": tiempoGracia,
                "cobroHora": cobroHora,
                "tieneElectricos": tieneElectricos
            }
            with open(ARCHIVO_CONFIGURACION, "w") as archivo:
                json.dump(configuracion, archivo, indent=4)
            messagebox.showinfo("Configuracion", "Configuracion guardada correctamente.")
            ventanaSecundaria.destroy()
        except ValueError:
            messagebox.showerror("Error", "Ingrese valores validos.")

    Button(ventanaSecundaria, text="Guardar Configuracion", command=guardarConfiguracion).pack(pady=15)


def ventanaPrincipalAcercaDe():
    ventanaSecundaria = Toplevel()
    ventanaSecundaria.title("Acerca De")
    ventanaSecundaria.geometry("1200x1000")
    Label(ventanaSecundaria, text="Desarrollado por Caleb Cordoba Duran y Jose Francisco Otarola Ulate").pack(pady=15)
    botonRegresar = Button(
        ventanaSecundaria, text="Regresar",
        width=100, height=200, font=("Arial", 120),
        command=ventanaSecundaria.destroy
    )
    botonRegresar.pack(pady=100)


listaEstacionamientos = cargarBaseDatos()

Button(ventanaPrincipal, text="Obtener Vehiculos", command=ventanaPrincipalObtenerVehiculos).pack(pady=20)
Button(ventanaPrincipal, text="Ver Estacionamiento", command=ventanaPrincipalEstacionamiento).pack(pady=20)
Button(ventanaPrincipal, text="Reportes", command=ventanaPrincipalReportes).pack(pady=20)
Button(ventanaPrincipal, text="Configuracion", command=ventanaPrincipalConfiguracion).pack(pady=20)
Button(ventanaPrincipal, text="Acerca De", command=ventanaPrincipalAcercaDe).pack(pady=20)

ventanaPrincipal.mainloop()