import tkinter

def centrar_ventana(ventana, ancho, alto):
    p_ancho = ventana.winfo_screenwidth()
    p_alto = ventana.winfo_screenheight()
    x = int((p_ancho / 2) - (ancho / 2))
    y = int((p_alto / 2) - (alto / 2))
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")