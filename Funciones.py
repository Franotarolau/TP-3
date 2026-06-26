from tkinter import *
from tkinter import messagebox
import os
import json

ventanaPrincipal = Tk()
ventanaPrincipal.title("Sistema de Parqueo")
ventanaPrincipal.geometry("400x400")


def obtenerConfiguracion():
    if not os.path.exists("configuracion.json"):
        messagebox.showerror(
            "Error",
            "Primero debe configurar el sistema."
        )
        return None

    with open("configuracion.json", "r") as archivo:
        return json.load(archivo)


def ventanaPrincipalObtenerVehiculos():
    configuracion = obtenerConfiguracion()

    if configuracion == None:
        return

    ventanaSecundaria = Toplevel()
    ventanaSecundaria.title("Obtener Vehículos")


def ventanaPrincipalEstacionamiento():
    configuracion = obtenerConfiguracion()

    if configuracion == None:
        return

    cantidadParqueos = configuracion["cantidadParqueos"]

    ventanaSecundaria = Toplevel()
    ventanaSecundaria.title("Estacionamiento")

    Label(
        ventanaSecundaria,
        text="Cantidad de parqueos: " + str(cantidadParqueos)
    ).pack(pady=10)


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

            with open("configuracion.json", "w") as archivo:
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