from tkinter import *
from tkinter import messagebox
import os
import json
import random
import datetime
import urllib.request
import urllib.error
from math import *

ventanaPrincipal = Tk()
ventanaPrincipal.title("Sistema de Parqueo")
ventanaPrincipal.geometry("400x400")


ARCHIVO_CONFIGURACION = "configuracion.json"
ARCHIVO_CATALOGOS = "catalogoVehiculos.json"
ARCHIVO_BASE_DATOS = "baseDatosEstacionamiento.json"
ARCHIVO_CLAVE_API = "mockarooApiKey.txt"

TIPOS_VEHICULO = ["Sedán", "SUV", "Pickup", "Hatchback", "Motocicleta"]

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


def estacionamientoDesdeDiccionario(diccionario):
    return Estacionamiento(
        diccionario["id"],
        diccionario["placa"],
        diccionario["marca"],
        diccionario["color"],
        diccionario["tipo"],
        diccionario["ubicacion"],
        diccionario["fechaHoraEntrada"],
        diccionario["fechaHoraSalida"],
        diccionario["monto"],
        diccionario["tipoPago"]
    )


def cargarBaseDatos():
    if not os.path.exists(ARCHIVO_BASE_DATOS):
        return []

    with open(ARCHIVO_BASE_DATOS, "r", encoding="utf-8") as archivo:
        registros = json.load(archivo)

    listaResultado = []
    for registro in registros:
        listaResultado.append(estacionamientoDesdeDiccionario(registro))

    return listaResultado


def guardarBaseDatos(listaObjetos):
    listaDiccionarios = []
    for objeto in listaObjetos:
        listaDiccionarios.append(objeto.aDiccionario())

    with open(ARCHIVO_BASE_DATOS, "w", encoding="utf-8") as archivo:
        json.dump(listaDiccionarios, archivo, indent=4, ensure_ascii=False)


def cargarCatalogos():
    if os.path.exists(ARCHIVO_CATALOGOS):
        with open(ARCHIVO_CATALOGOS, "r", encoding="utf-8") as archivo:
            return json.load(archivo)

    catalogosIniciales = {"marca": {}, "color": {}, "tipo": {}}

    indice = 0
    while indice < len(TIPOS_VEHICULO):
        catalogosIniciales["tipo"][TIPOS_VEHICULO[indice]] = indice + 1
        indice = indice + 1

    return catalogosIniciales


def guardarCatalogos(catalogos):
    with open(ARCHIVO_CATALOGOS, "w", encoding="utf-8") as archivo:
        json.dump(catalogos, archivo, indent=4, ensure_ascii=False)


def obtenerCodigo(catalogos, categoria, nombre):
    diccionarioCategoria = catalogos[categoria]

    if nombre in diccionarioCategoria:
        return diccionarioCategoria[nombre]

    nuevoCodigo = len(diccionarioCategoria) + 1
    diccionarioCategoria[nombre] = nuevoCodigo
    return nuevoCodigo


def obtenerNombrePorCodigo(catalogos, categoria, codigo):
    diccionarioCategoria = catalogos[categoria]

    for nombre in diccionarioCategoria:
        if diccionarioCategoria[nombre] == codigo:
            return nombre

    return "Desconocido"


def obtenerNombreTipoPago(codigoTipoPago):
    nombresTipoPago = {0: "Pendiente", 1: "Efectivo", 2: "SINPE", 3: "Tarjeta"}

    if codigoTipoPago in nombresTipoPago:
        return nombresTipoPago[codigoTipoPago]

    return "Desconocido"


def obtenerConfiguracion():
    if not os.path.exists(ARCHIVO_CONFIGURACION):
        messagebox.showerror(
            "Error",
            "Primero debe configurar el sistema."
        )
        return None

    with open(ARCHIVO_CONFIGURACION, "r") as archivo:
        return json.load(archivo)


def obtenerSiguienteId(listaObjetos):
    if len(listaObjetos) == 0:
        return 1

    idMaximo = 0
    for objeto in listaObjetos:
        if objeto.id > idMaximo:
            idMaximo = objeto.id

    return idMaximo + 1


def obtenerSiguienteNumeroGeneral(listaObjetos):
    contador = 0
    for objeto in listaObjetos:
        ubicacionActual = objeto.estadia[0]
        if ubicacionActual.startswith("G-"):
            contador = contador + 1

    return contador + 1


def generarFechaHoraEntradaAleatoria():
    ahora = datetime.datetime.now()
    apertura = ahora.replace(hour=7, minute=0, second=0, microsecond=0)

    if ahora <= apertura:
        return apertura.strftime("%d-%m-%Y %H:%M")

    segundosTotales = int((ahora - apertura).total_seconds())
    segundosAleatorios = random.randint(0, segundosTotales)
    fechaHoraAleatoria = apertura + datetime.timedelta(seconds=segundosAleatorios)

    return fechaHoraAleatoria.strftime("%d-%m-%Y %H:%M")


def cargarClaveApiGuardada():
    if not os.path.exists(ARCHIVO_CLAVE_API):
        return ""

    with open(ARCHIVO_CLAVE_API, "r") as archivo:
        return archivo.read().strip()


def guardarClaveApi(claveApi):
    with open(ARCHIVO_CLAVE_API, "w") as archivo:
        archivo.write(claveApi)


def solicitarVehiculosMockaroo(cantidad, claveApi):
    columnas = [
        {"name": "placa", "type": "Regular Expression", "value": "[A-Z]{3}[0-9]{3}"},
        {"name": "marca", "type": "Car Make"},
        {"name": "color", "type": "Color"},
        {"name": "tipo", "type": "Custom List", "values": TIPOS_VEHICULO}
    ]

    cuerpoSolicitud = json.dumps(columnas).encode("utf-8")

    url = "https://api.mockaroo.com/api/generate.json?key=" + claveApi + "&count=" + str(cantidad)

    solicitud = urllib.request.Request(
        url,
        data=cuerpoSolicitud,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(solicitud, timeout=20) as respuesta:
        contenido = respuesta.read().decode("utf-8")

    return json.loads(contenido)


def construirDiccionarioVehiculos(registrosMockaroo):
    diccionarioVehiculos = {}

    for registro in registrosMockaroo:
        placa = registro["placa"]
        diccionarioVehiculos[placa] = {
            "marca": registro["marca"],
            "color": registro["color"],
            "tipo": registro["tipo"],
            "ubicacion": "",
            "fechaHoraEntrada": "",
            "fechaHoraSalida": "",
            "monto": 0,
            "tipoPago": 0
        }

    return diccionarioVehiculos


def calcularCantidadVehiculos():
    configuracion = obtenerConfiguracion()

    if configuracion == None:
        return None

    cantidadParqueos = configuracion["cantidadParqueos"]
    tieneElectricos = configuracion["tieneElectricos"]

    espacioEspecial = ceil(cantidadParqueos * 0.05)

    if espacioEspecial < 2:
        espacioEspecial = 2

    espaciosDisponibles = cantidadParqueos - espacioEspecial

    if tieneElectricos:
        espaciosDisponibles = espaciosDisponibles - 1

    espaciosLibres = ceil(espaciosDisponibles * 0.05)

    cantidadVehiculos = espaciosDisponibles - espaciosLibres

    print("Cantidad de parqueos:", cantidadParqueos)
    print("Espacios especiales:", espacioEspecial)
    print("Tiene espacio eléctrico:", tieneElectricos)
    print("Espacios disponibles:", espaciosDisponibles)
    print("Espacios libres:", espaciosLibres)
    print("Vehículos a solicitar:", cantidadVehiculos)

    return cantidadVehiculos


def ventanaPrincipalObtenerVehiculos():
    configuracion = obtenerConfiguracion()

    if configuracion == None:
        return

    cantidadVehiculos = calcularCantidadVehiculos()

    ventanaSecundaria = Toplevel()
    ventanaSecundaria.title("Obtener Vehículos")
    ventanaSecundaria.geometry("550x500")

    Label(
        ventanaSecundaria,
        text="Vehículos disponibles a solicitar masivamente: " + str(cantidadVehiculos)
    ).pack(pady=10)

    Label(
        ventanaSecundaria,
        text="Clave de API de Mockaroo:"
    ).pack(pady=5)

    entradaClaveApi = Entry(ventanaSecundaria, width=40)
    entradaClaveApi.pack(pady=5)
    entradaClaveApi.insert(0, cargarClaveApiGuardada())

    marcoTexto = Frame(ventanaSecundaria)
    marcoTexto.pack(pady=10, fill=BOTH, expand=True)

    barraDesplazamiento = Scrollbar(marcoTexto)
    barraDesplazamiento.pack(side=RIGHT, fill=Y)

    textoResultado = Text(marcoTexto, height=15, yscrollcommand=barraDesplazamiento.set)
    textoResultado.pack(side=LEFT, fill=BOTH, expand=True)
    barraDesplazamiento.config(command=textoResultado.yview)

    def procesarLlenadoMasivo():
        configuracionActual = obtenerConfiguracion()

        if configuracionActual == None:
            return

        cantidadASolicitar = calcularCantidadVehiculos()

        if cantidadASolicitar == None or cantidadASolicitar <= 0:
            messagebox.showerror(
                "Error",
                "No hay espacios disponibles para solicitar vehículos."
            )
            return

        claveApi = entradaClaveApi.get().strip()

        if claveApi == "":
            messagebox.showerror(
                "Error",
                "Debe ingresar la clave de API de Mockaroo."
            )
            return

        guardarClaveApi(claveApi)

        try:
            registrosMockaroo = solicitarVehiculosMockaroo(cantidadASolicitar, claveApi)
        except urllib.error.HTTPError as error:
            messagebox.showerror(
                "Error de API",
                "Mockaroo respondió con un error: " + str(error.code)
            )
            return
        except urllib.error.URLError:
            messagebox.showerror(
                "Error de Conexión",
                "No fue posible conectarse con la API de Mockaroo."
            )
            return
        except (ValueError, KeyError):
            messagebox.showerror(
                "Error",
                "La respuesta de la API no tiene el formato esperado."
            )
            return

        diccionarioVehiculos = construirDiccionarioVehiculos(registrosMockaroo)

        print(json.dumps(diccionarioVehiculos, indent=4, ensure_ascii=False))

        catalogos = cargarCatalogos()

        siguienteId = obtenerSiguienteId(listaEstacionamientos)
        siguienteNumeroGeneral = obtenerSiguienteNumeroGeneral(listaEstacionamientos)

        textoResultado.delete("1.0", END)

        for placa in diccionarioVehiculos:
            datosVehiculo = diccionarioVehiculos[placa]

            codigoMarca = obtenerCodigo(catalogos, "marca", datosVehiculo["marca"])
            codigoColor = obtenerCodigo(catalogos, "color", datosVehiculo["color"])
            codigoTipo = obtenerCodigo(catalogos, "tipo", datosVehiculo["tipo"])

            ubicacion = "G-" + str(siguienteNumeroGeneral).zfill(3)
            fechaHoraEntrada = generarFechaHoraEntradaAleatoria()

            nuevoVehiculo = Estacionamiento(
                siguienteId,
                placa,
                codigoMarca,
                codigoColor,
                codigoTipo,
                ubicacion,
                fechaHoraEntrada,
                "",
                0,
                0
            )

            listaEstacionamientos.append(nuevoVehiculo)

            lineaResumen = (
                placa + " | " + datosVehiculo["marca"] + " | " +
                datosVehiculo["color"] + " | " + datosVehiculo["tipo"] +
                " | " + ubicacion + " | " + fechaHoraEntrada + " | Pago: " +
                obtenerNombreTipoPago(0) + "\n"
            )
            textoResultado.insert(END, lineaResumen)

            siguienteId = siguienteId + 1
            siguienteNumeroGeneral = siguienteNumeroGeneral + 1

        guardarCatalogos(catalogos)
        guardarBaseDatos(listaEstacionamientos)

        messagebox.showinfo(
            "Obtener Vehículos",
            "Se registraron " + str(len(diccionarioVehiculos)) + " vehículos y se respaldó la base de datos."
        )

    Button(
        ventanaSecundaria,
        text="Solicitar vehículos a la API",
        command=procesarLlenadoMasivo
    ).pack(pady=10)


def observarEspacio(numeroEspacio):
    espacio="G-"+str(numeroEspacio).zfill(3)
    for vehiculo in listaEstacionamientos:
        if vehiculo.estadia[0]==espacio:
            messagebox.showinfo(
                "Espacio ocupado",
                "Placa: "+vehiculo.info[0] + "\n" +
                "Ubicación: "+vehiculo.estadia[0] + "\n" +
                "Entrada: "+vehiculo.estadia[1]
            )
            return

    messagebox.showinfo(
        "Espacio libre",
        "El espacio " + espacio + " está disponible."
    )
def ventanaPrincipalEstacionamiento():
    configuracion=obtenerConfiguracion()
    if configuracion==None:
        return
    cantidadParqueos=configuracion["cantidadParqueos"]
    tieneElectricos=configuracion["tieneElectricos"]
    ventanaSecundaria=Toplevel()
    ventanaSecundaria.title("Mapa del Estacionamiento")
    ventanaSecundaria.geometry("1000x700")
    Label(
        ventanaSecundaria,
        text="Estado del Estacionamiento",
        font=("Arial", 16, "bold")
    ).pack(pady=10)
    marcoParqueos=Frame(ventanaSecundaria)
    marcoParqueos.pack()
    espaciosEspeciales=ceil(cantidadParqueos*0.05)

    if espaciosEspeciales<2:
        espaciosEspeciales=2

    columnas=10
    #E=Espacio especial
    #VE=Veiculo Electrico
    for numero in range(1, cantidadParqueos+1):

        colorEspacio="green"
        textoEspacio=str(numero)

        if numero <= espaciosEspeciales:
            colorEspacio="blue"
            textoEspacio="E" + str(numero)

        elif tieneElectricos and numero==espaciosEspeciales + 1:
            colorEspacio="yellow"
            textoEspacio="VE"

        for vehiculo in listaEstacionamientos:
            ubicacionVehiculo=vehiculo.estadia[0]

            if ubicacionVehiculo=="G-"+str(numero).zfill(3):
                colorEspacio="red"
                break

        botonEspacio=Button(
            marcoParqueos,
            text=textoEspacio,
            bg=colorEspacio,
            width=8,
            height=3,
            command=lambda n=numero: observarEspacio(n)
        )

        fila=(numero-1)//columnas
        columna=(numero-1)%columnas

        botonEspacio.grid(
            row=fila,
            column=columna,
            padx=5,
            pady=5
        )

    Label(
        ventanaSecundaria,
        text="Casetilla de Cobro",
        bg="orange",
        width=20,
        height=2
    ).pack(pady=10)

    Label(
        ventanaSecundaria,
        text="Baño",
        bg="lightblue",
        width=20,
        height=2
    ).pack(pady=5)


def ventanaPrincipalReportes():
    configuracion = obtenerConfiguracion()

    if configuracion == None:
        return

    ventanaSecundaria = Toplevel()
    ventanaSecundaria.title("Reportes")


def ventanaPrincipalConfiguracion():
    ventanaSecundaria = Toplevel()
    ventanaSecundaria.title("Configuración")
    ventanaSecundaria.geometry("350x350")

    Label(
        ventanaSecundaria,
        text="¿Cuántos parqueos tiene su estacionamiento?"
    ).pack(pady=5)

    entradaCantidad = Entry(ventanaSecundaria)
    entradaCantidad.pack(pady=5)

    Label(
        ventanaSecundaria,
        text="Tiempo de gracia (minutos):"
    ).pack(pady=5)

    entradaTiempoGracia = Entry(ventanaSecundaria)
    entradaTiempoGracia.pack(pady=5)

    Label(
        ventanaSecundaria,
        text="Cobro por hora (₡):"
    ).pack(pady=5)

    entradaCobroHora = Entry(ventanaSecundaria)
    entradaCobroHora.pack(pady=5)

    carrosElectricos = IntVar()

    Checkbutton(
        ventanaSecundaria,
        text="¿Posee espacios para vehículos eléctricos?",
        variable=carrosElectricos
    ).pack(pady=10)

    def guardarConfiguracion():
        try:
            cantidadParqueos = int(entradaCantidad.get())
            tiempoGracia = int(entradaTiempoGracia.get())
            cobroHora = int(entradaCobroHora.get())
            tieneElectricos = bool(carrosElectricos.get())

            if cantidadParqueos <= 0:
                raise ValueError

            configuracion = {
                "cantidadParqueos": cantidadParqueos,
                "tiempoGracia": tiempoGracia,
                "cobroHora": cobroHora,
                "tieneElectricos": tieneElectricos
            }

            with open(ARCHIVO_CONFIGURACION, "w") as archivo:
                json.dump(configuracion, archivo, indent=4)

            messagebox.showinfo(
                "Configuración",
                "Configuración guardada correctamente."
            )

            ventanaSecundaria.destroy()

        except ValueError:
            messagebox.showerror(
                "Error",
                "Ingrese valores válidos."
            )

    Button(
        ventanaSecundaria,
        text="Guardar Configuración",
        command=guardarConfiguracion
    ).pack(pady=15)


def ventanaPrincipalAcercaDe():
    ventanaSecundaria = Toplevel()
    ventanaSecundaria.title("Acerca De")
    ventanaSecundaria.geometry("1200x1000")
    Label(
        ventanaSecundaria,
        text="Desarrollado por Caleb Cordoba Duran y Jose Francisco Otarola Ulate"
    ).pack(pady=15)
    botonRegresar = Button(ventanaSecundaria, text="Regresar",
                           width=100,
                           height=200,
                           font=("Arial", 120),
                           command=ventanaSecundaria.destroy)
    botonRegresar.pack(pady=100)


listaEstacionamientos = cargarBaseDatos()


Button(
    ventanaPrincipal,
    text="Obtener Vehículos",
    command=ventanaPrincipalObtenerVehiculos
).pack(pady=20)

Button(
    ventanaPrincipal,
    text="Ver Estacionamiento",
    command=ventanaPrincipalEstacionamiento
).pack(pady=20)

Button(
    ventanaPrincipal,
    text="Reportes",
    command=ventanaPrincipalReportes
).pack(pady=20)

Button(
    ventanaPrincipal,
    text="Configuración",
    command=ventanaPrincipalConfiguracion
).pack(pady=20)

Button(
    ventanaPrincipal,
    text="Acerca De",
    command=ventanaPrincipalAcercaDe
).pack(pady=20)


ventanaPrincipal.mainloop()
