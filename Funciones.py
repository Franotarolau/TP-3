from tkinter import *

ventanaPrincipal = Tk()
ventanaPrincipal.title("Sistema de Parqueo")
ventanaPrincipal.geometry("400x400")
#2
#Configuracion
tamanoEstacionamiento=0
tiempoGracia=0
montoHora=0
tieneElectrico=False

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
        #2
    ventanaSecundaria.geometry("350x300")
    Label(
        ventanaSecundaria,
        text="Tamaño del estacionamiento:"
    ).pack(pady=5)
    entradaTamano=Entry(ventanaSecundaria)
    entradaTamano.pack()
    Label(
        ventanaSecundaria,
        text="Tiempo de gracia (minutos):"
    ).pack(pady=5)
    entradaTiempoGracia=Entry(ventanaSecundaria)
    entradaTiempoGracia.pack()
    Label(
        ventanaSecundaria,
        text="Monto por hora:").pack(pady=5)
    entradaMontoHora=Entry(ventanaSecundaria)
    entradaMontoHora.pack()
    electrico=IntVar()
    Checkbutton(
        ventanaSecundaria,
        text="Posee espacio para vehículos eléctricos",
        variable=electrico
    ).pack(pady=10)
    def guardarConfiguracion():
        global tamanoEstacionamiento
        global tiempoGracia
        global montoHora
        global tieneElectrico
        try:
            tamanoEstacionamiento=int(entradaTamano.get())
            tiempoGracia=int(entradaTiempoGracia.get())
            montoHora=int(entradaMontoHora.get())
            tieneElectrico=bool(electrico.get())
            messagebox.showinfo("Configuración","Configuración guardada correctamente.")
            ventanaSecundaria.destroy()
        except ValueError:
            messagebox.showerror("Error","Ingrese únicamente números.")
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
#3 para si??
