import tkinter
from tkinter import filedialog, messagebox
from funciones import centrar_ventana
from cryptography.fernet import Fernet
import os


#FUNCIONES

def generar_clave():
    clave = Fernet.generate_key()
    with open("clave.key", "wb") as archivo_clave:
        archivo_clave.write(clave)
    messagebox.showinfo("Clave", "Clave generada correctamente")


def cargar_clave():
    try:
        with open("clave.key", "rb") as archivo_clave:
            return archivo_clave.read()
    except:
        messagebox.showerror("Error", "No existe la clave. Genérala primero.")
        return None


def seleccionar_archivo():
    ruta = filedialog.askopenfilename()
    if ruta:
        entry_ruta.delete(0, tkinter.END)
        entry_ruta.insert(0, ruta)


# ENCRIPTAR CON SELECCIÓN DE DESTINO
def encriptar_archivo():
    ruta = entry_ruta.get()
    clave = cargar_clave()

    if not ruta or not clave:
        return

    f = Fernet(clave)

    try:
        with open(ruta, "rb") as archivo:
            datos = archivo.read()

        datos_encriptados = f.encrypt(datos)

        #Preguntar dónde guardar
        nueva_ruta = filedialog.asksaveasfilename(
            defaultextension=".enc",
            filetypes=[("Archivo encriptado", "*.enc")]
        )

        if not nueva_ruta:
            return  # usuario canceló

        with open(nueva_ruta, "wb") as archivo:
            archivo.write(datos_encriptados)

        messagebox.showinfo("Éxito", f"Archivo encriptado:\n{nueva_ruta}")

    except Exception as e:
        messagebox.showerror("Error", str(e))


# DESENCRIPTAR CON SELECCIÓN DE DESTINO
def desencriptar_archivo():
    ruta = entry_ruta.get()
    clave = cargar_clave()

    if not ruta or not clave:
        return

    f = Fernet(clave)

    try:
        with open(ruta, "rb") as archivo:
            datos = archivo.read()

        datos_desencriptados = f.decrypt(datos)

        # Preguntar dónde guardar
        nueva_ruta = filedialog.asksaveasfilename(
            defaultextension="_desencriptado",
            filetypes=[("Archivo desencriptado", "*.*")]
        )

        if not nueva_ruta:
            return  # usuario canceló

        with open(nueva_ruta, "wb") as archivo:
            archivo.write(datos_desencriptados)

        messagebox.showinfo("Éxito", f"Archivo desencriptado:\n{nueva_ruta}")

    except Exception as e:
        messagebox.showerror("Error", "Error al desencriptar. ¿Clave incorrecta?")


#INTERFAZ

def ejecutar(ventana_anterior):
    ventana_anterior.withdraw()

    problema2 = tkinter.Toplevel()
    problema2.title("Encriptador de Archivos")
    problema2.resizable(False, False)
    centrar_ventana(problema2, 500, 300)

    # Label
    titulo = tkinter.Label(problema2, text="Encriptar / Desencriptar Archivos", font=("Arial", 14))
    titulo.pack(pady=10)

    # Entrada de ruta
    global entry_ruta
    entry_ruta = tkinter.Entry(problema2, width=50)
    entry_ruta.pack(pady=5)

    # Botón seleccionar archivo
    boton_buscar = tkinter.Button(problema2, text="Seleccionar archivo", command=seleccionar_archivo)
    boton_buscar.pack(pady=5)

    # Botones principales
    boton_clave = tkinter.Button(problema2, text="Generar clave", bg="#f7d154", command=generar_clave)
    boton_clave.pack(pady=5)

    boton_encriptar = tkinter.Button(problema2, text="Encriptar", bg="#7ed957", command=encriptar_archivo)
    boton_encriptar.pack(pady=5)

    boton_desencriptar = tkinter.Button(problema2, text="Desencriptar", bg="#ff5757", command=desencriptar_archivo)
    boton_desencriptar.pack(pady=5)

    #BOTÓN VOLVER
    def volver():
        problema2.destroy()
        ventana_anterior.deiconify()

    tkinter.Button(problema2, text="Volver", command=volver, bg="#cccccc").place(x=430, y=10)

    problema2.mainloop()