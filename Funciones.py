from tkinter import *


ventana = Toplevel()

def obtenerVehiculos(ventana):
    botonVehiculos = Button(
        ventana,
        text= "Obtener Vehiculos",
        command= ventana
    )

    botonVehiculos.pack(pady=10)

def verEstacionamiento(ventana):
    botonEstacionamiento = Button(
        ventana,
        text= "Ver Estacionamiento",
        command= ventana
    )

    botonEstacionamiento.pack(pady=10)


def botonReportes(ventana):
    botonReportes = Button (
        ventana,
        text = "Reportes",
        command= ventana
    )

    botonReportes.pack(pady=10)


def botonConfiguracion(ventana):
    botonConfiguracion = Button (
        ventana,
        text = "Configuración",
        command= ventana
    )

    botonConfiguracion.pack(pady=10)


def botonAcercaDe(ventana):
    botonAcercaDe = Button (
        ventana,
        text = "Acerca De",
        command= ventana
    )

    botonAcercaDe.pack(pady=10)