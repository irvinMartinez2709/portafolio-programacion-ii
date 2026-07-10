import sys

#MODO CRON
if len(sys.argv) > 1 and sys.argv[1] == "cron":
    print("Ejecutado desde cron sin interfaz gráfica")

#MODO NORMAL (Windows o Linux manual)
else:
    import tkinter
    from funciones import centrar_ventana
    import problema1_ingreso
    import problema2

    print("Ejecutando con interfaz gráfica")

    #Ventanas de problemas
    def abrir_problema1():
        menu.withdraw()
        problema1_ingreso.ejecutar(menu)

    def abrir_problema2():
        menu.withdraw()
        problema2.ejecutar(menu)

    #Configuración del menú
    menu = tkinter.Tk()
    menu.resizable(False, False)
    menu.configure(bg="#9ccdff")
    menu.title("Menú Principal")
    centrar_ventana(menu, 400, 300)

    #Botones
    boton_problema1 = tkinter.Button(menu,
                                     relief="solid",
                                     cursor="hand2",
                                     bg="#ff5757",
                                     font=1,
                                     height=1,
                                     width=15,
                                     text="Programa 1",
                                     command=abrir_problema1)
    boton_problema1.place(x=15, y=223)

    boton_problema2 = tkinter.Button(menu,
                                     relief="solid",
                                     cursor="hand2",
                                     bg="#7ed957",
                                     font=1,
                                     height=1,
                                     width=15,
                                     text="Programa 2",
                                     command=abrir_problema2)
    boton_problema2.place(x=210, y=223)

    #Labels
    seleccion = tkinter.Label(menu, bg="#9ccdff", font=("Arial", 16),
                              text="Selecciona el programa que \n deseas ejecutar.")
    seleccion.place(x=70, y=38)

    p1 = tkinter.Label(menu, bg="#9ccdff",
                       text="Aplicación de \nprofesores para la \nUniversidad X.",
                       font=("Arial", 13))
    p1.place(x=30, y=130)

    p2 = tkinter.Label(menu, bg="#9ccdff",
                       text="Programa para \nencriptar y \ndesencriptar.",
                       font=("Arial", 13))
    p2.place(x=240, y=130)

    menu.mainloop()

print("Programa ejecutado correctamente")