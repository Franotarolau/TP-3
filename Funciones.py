from tkinter import *

ventanaPrincipal = Tk()
ventanaPrincipal.title("Sistema de Parqueo")
ventanaPrincipal.geometry("400x400")

def ventanaPrincipalObtenerVehiculos():
    ventanaSecundaria = Toplevel()
    ventanaSecundaria.title("Obtener Vehículos")

def ventanaPrincipalEstacionamiento():
    ventanaSecundaria = Toplevel()
    ventanaSecundaria.title("Estacionamiento")

def ventanaPrincipalReportes():
    ventanaSecundaria = Toplevel()
    ventanaSecundaria.title("Reportes")

def ventanaPrincipalConfiguracion():
    ventanaSecundaria = Toplevel()
    ventanaSecundaria.title("Configuración")

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