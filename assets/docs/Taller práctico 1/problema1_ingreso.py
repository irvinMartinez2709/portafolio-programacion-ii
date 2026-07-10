import tkinter
from tkinter import messagebox
from funciones import centrar_ventana
import problema1
import json
import os

archivo_user = "usuarios.json"

def cargar_usuario():
    if os.path.exists(archivo_user):
        with open(archivo_user, "r") as f:
            return json.load(f)
    return {"user": "admin", "passwd": "1234"}


def ejecutar(menu):
    menu.withdraw()

    problema1_ingreso = tkinter.Toplevel()
    problema1_ingreso.title("Inicio de sesión")
    problema1_ingreso.resizable(False, False)
    problema1_ingreso.configure(bg="#9ccdff")
    centrar_ventana(problema1_ingreso, 720, 480)

    tkinter.Label(problema1_ingreso, font=("Arial", 25),
                  bg="#9ccdff",
                  text="Ingrese su usuario y contraseña.").place(x=125, y=48)

    user_entry = tkinter.Entry(problema1_ingreso, width=20, font=("Arial", 20))
    user_entry.place(x=280, y=150)

    tkinter.Label(problema1_ingreso, text="Usuario:", font=("Arial", 20), bg="#9ccdff").place(x=150, y=150)

    pass_entry = tkinter.Entry(problema1_ingreso, width=20, font=("Arial", 20), show="*")
    pass_entry.place(x=280, y=250)

    tkinter.Label(problema1_ingreso, text="Contraseña:", font=("Arial", 20), bg="#9ccdff").place(x=105, y=250)

    tkinter.Button(
        problema1_ingreso,
        text="Ingresar",
        bg="#7ed957",
        command=lambda: verificar_usuario(user_entry, pass_entry, problema1_ingreso, menu),
        font=("Arial", 15)
    ).place(x=320, y=350)

    tkinter.Button(
        problema1_ingreso,
        text="Volver",
        bg="#ff5757",
        command=lambda: volver_menu(problema1_ingreso, menu),
        font=("Arial", 15)
    ).place(x=10, y=10)

    problema1_ingreso.mainloop()


def verificar_usuario(user_name, password, ventana, menu):
    cred = cargar_usuario()

    if user_name.get() == cred["user"] and password.get() == cred["passwd"]:
        ventana.destroy()
        problema1.ejecutar(menu)
    else:
        messagebox.showerror("Error", "Credenciales incorrectas")


def volver_menu(ventana_actual, menu):
    ventana_actual.destroy()
    menu.deiconify()