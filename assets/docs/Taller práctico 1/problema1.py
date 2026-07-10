import tkinter
from tkinter import ttk
import json
import os

def ejecutar(menu):
    menu.withdraw()

    problema1 = tkinter.Toplevel()
    problema1.title("Sistema profesores  Universidad X")
    problema1.resizable(False, False)
    problema1.configure(bg="#EDF1F2")
    problema1.geometry("520x400")

    archivo_estudiantes = "estudiantes.json"
    archivo_asignaturas = "asignaturas.json"
    archivo_notas = "notas.json"
    archivo_user = "usuarios.json"

    max_estudiantes = 0
    contador_estudiantes = 0

    max_asignaturas = 0
    contador_asignaturas = 0

    max_notas = 0
    contador_notas = 0

    #  USUARIO
    def cargar_usuario():
        if os.path.exists(archivo_user):
            with open(archivo_user, "r") as f:
                return json.load(f)
        return {"user": "admin", "passwd": "1234"}

    def guardar_usuario(user, passwd):
        with open(archivo_user, "w") as f:
            json.dump({"user": user, "passwd": passwd}, f)

    #  ESTUDIANTES
    def generar_id():
        if not os.path.exists(archivo_estudiantes):
            return 1
        try:
            with open(archivo_estudiantes, "r", encoding="utf8") as f:
                datos = json.load(f)
                if not datos:
                    return 1
                return max(int(e["id"]) for e in datos) + 1
        except:
            return 1

    def cargar_estudiantes():
        estudiantes_tabla.delete(0, "end")
        if not os.path.exists(archivo_estudiantes):
            return
        try:
            with open(archivo_estudiantes, "r", encoding="utf8") as f:
                datos = json.load(f)
                for est in datos:
                    estudiantes_tabla.insert("end", f"{est['nombre']} {est['apellido']}")
        except:
            pass

    def fijar_cantidad_estudiantes():
        nonlocal max_estudiantes, contador_estudiantes
        try:
            max_estudiantes = int(combo_estudiantes.get())
            contador_estudiantes = 0
        except:
            max_estudiantes = 0

    def guardar_estudiante():
        nonlocal contador_estudiantes

        if contador_estudiantes >= max_estudiantes:
            return

        id_v = generar_id()  # automático
        nom_v = nombre_input.get()
        ape_v = apellido_input.get()
        ced_v = cedula_input.get()

        if not nom_v:
            return

        nuevo = {"id": id_v, "nombre": nom_v, "apellido": ape_v, "cedula": ced_v}

        lista = []
        if os.path.exists(archivo_estudiantes):
            try:
                with open(archivo_estudiantes, "r", encoding="utf8") as f:
                    lista = json.load(f)
            except:
                pass

        lista.append(nuevo)

        with open(archivo_estudiantes, "w", encoding="utf8") as f:
            json.dump(lista, f, indent=4, ensure_ascii=False)

        cargar_estudiantes()
        cargar_combobox()

        contador_estudiantes += 1

        id_input.delete(0, "end")
        nombre_input.delete(0, "end")
        apellido_input.delete(0, "end")
        cedula_input.delete(0, "end")

    def eliminar_estudiante():
        seleccion = estudiantes_tabla.curselection()
        if not seleccion:
            return

        index = seleccion[0]
        estudiantes_tabla.delete(index)

        if os.path.exists(archivo_estudiantes):
            with open(archivo_estudiantes, "r", encoding="utf8") as f:
                datos = json.load(f)

            datos.pop(index)

            with open(archivo_estudiantes, "w", encoding="utf8") as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)

    #  ASIGNATURAS
    def fijar_cantidad_asignaturas():
        nonlocal max_asignaturas, contador_asignaturas
        try:
            max_asignaturas = int(combo_asignaturas.get())
            contador_asignaturas = 0
        except:
            max_asignaturas = 0

    def cargar_asignaturas():
        asig_lista.delete(0, "end")
        if not os.path.exists(archivo_asignaturas):
            return
        try:
            with open(archivo_asignaturas, "r", encoding="utf8") as f:
                datos = json.load(f)
            for a in datos:
                asig_lista.insert("end", f"{a['nombre']}  Grupo {a['grupo']}")
        except:
            pass

    def guardar_asignatura():
        nonlocal contador_asignaturas

        if contador_asignaturas >= max_asignaturas:
            return

        nombre = asig_nombre.get()
        grupo = asig_grupo.get()
        modalidad = modalidad_cb.get()

        try:
            tareas = int(p_tareas.get())
            parcial = int(p_parcial.get())
            final = int(p_final.get())
        except:
            return

        if tareas + parcial + final != 100:
            resultado_label.config(text="Error: suma ≠ 100%", fg="red")
            return

        nueva = {
            "nombre": nombre,
            "grupo": grupo,
            "modalidad": modalidad,
            "porcentajes": {
                "tareas": tareas,
                "parcial": parcial,
                "final": final
            }
        }

        lista = []
        if os.path.exists(archivo_asignaturas):
            try:
                with open(archivo_asignaturas, "r", encoding="utf8") as f:
                    lista = json.load(f)
            except:
                pass

        lista.append(nueva)

        with open(archivo_asignaturas, "w", encoding="utf8") as f:
            json.dump(lista, f, indent=4)

        asig_lista.insert("end", f"{nombre}  Grupo {grupo}")
        resultado_label.config(text="Guardado ✔", fg="green")

        contador_asignaturas += 1
        cargar_combobox()

    def eliminar_asignatura():
        seleccion = asig_lista.curselection()
        if not seleccion:
            return

        index = seleccion[0]
        asig_lista.delete(index)

        if os.path.exists(archivo_asignaturas):
            with open(archivo_asignaturas, "r", encoding="utf8") as f:
                datos = json.load(f)

            datos.pop(index)

            with open(archivo_asignaturas, "w", encoding="utf8") as f:
                json.dump(datos, f, indent=4)

    #  CALIFICACIONES
    def fijar_cantidad_notas():
        nonlocal max_notas, contador_notas
        try:
            max_notas = int(combo_notas.get())
            contador_notas = 0
        except:
            max_notas = 0

    def guardar_nota():
        nonlocal contador_notas

        if contador_notas >= max_notas:
            return

        estudiante = est_cb.get()
        asignatura = asig_cb.get()

        try:
            tareas = float(n_tareas.get())
            parcial = float(n_parcial.get())
            final = float(n_final.get())
        except:
            return

        if not (0 <= tareas <= 100 and 0 <= parcial <= 100 and 0 <= final <= 100):
            resultado_notas.config(text="Notas deben estar entre 0 y 100", fg="red")
            return

        if not os.path.exists(archivo_asignaturas):
            return

        try:
            with open(archivo_asignaturas, "r", encoding="utf8") as f:
                asignaturas = json.load(f)
        except:
            return

        porc = None
        for a in asignaturas:
            if a["nombre"] == asignatura:
                porc = a["porcentajes"]

        if not porc:
            return

        nota_final = (
            tareas * porc["tareas"]/100 +
            parcial * porc["parcial"]/100 +
            final * porc["final"]/100
        )

        nueva = {
            "estudiante": estudiante,
            "asignatura": asignatura,
            "nota_final": round(nota_final, 2)
        }

        lista = []
        if os.path.exists(archivo_notas):
            try:
                with open(archivo_notas, "r", encoding="utf8") as f:
                    lista = json.load(f)
            except:
                pass

        lista.append(nueva)

        with open(archivo_notas, "w", encoding="utf8") as f:
            json.dump(lista, f, indent=4)

        resultado_notas.config(text=f"Nota final: {round(nota_final,2)}", fg="green")

        contador_notas += 1

    #  REPORTES
    def cargar_reportes():
        reporte_lista.delete(0, "end")

        if not os.path.exists(archivo_notas):
            return

        try:
            # Cargar notas
            with open(archivo_notas, "r", encoding="utf8") as f:
                datos = json.load(f)

            # Cargar asignaturas (para obtener modalidad y grupo)
            asignaturas = []
            if os.path.exists(archivo_asignaturas):
                with open(archivo_asignaturas, "r", encoding="utf8") as f:
                    asignaturas = json.load(f)

            for r in datos:
                estado = "Aprobado" if r["nota_final"] >= 61 else "Reprobado"

                modalidad = ""
                grupo = ""

                # Buscar datos de la asignatura
                for a in asignaturas:
                    if a["nombre"] == r["asignatura"]:
                        modalidad = a.get("modalidad", "")
                        grupo = a.get("grupo", "")
                        break

                linea = (
                    f"{r['estudiante']} | "
                    f"{r['asignatura']} (Grupo {grupo}  {modalidad}) | "
                    f"{r['nota_final']} ({estado})"
                )

                reporte_lista.insert("end", linea)

        except:
            pass

    def eliminar_reporte():
        seleccion = reporte_lista.curselection()
        if not seleccion:
            return

        index = seleccion[0]
        reporte_lista.delete(index)

        if os.path.exists(archivo_notas):
            with open(archivo_notas, "r", encoding="utf8") as f:
                datos = json.load(f)

            datos.pop(index)

            with open(archivo_notas, "w", encoding="utf8") as f:
                json.dump(datos, f, indent=4)

    #  UI
    notebook = ttk.Notebook(problema1)
    notebook.pack(expand=True, fill="both")

    tab_estudiantes = tkinter.Frame(notebook, bg="#EDF1F2")
    tab_asignaturas = tkinter.Frame(notebook)
    tab_calificaciones = tkinter.Frame(notebook)
    tab_reportes = tkinter.Frame(notebook)
    tab_seguridad = tkinter.Frame(notebook)

    notebook.add(tab_estudiantes, text="Estudiantes")
    notebook.add(tab_asignaturas, text="Asignaturas")
    notebook.add(tab_calificaciones, text="Calificaciones")
    notebook.add(tab_reportes, text="Reportes")
    notebook.add(tab_seguridad, text="Seguridad")

    #  ESTUDIANTES
    tkinter.Label(tab_estudiantes, text="Cantidad").place(x=200, y=10)
    combo_estudiantes = ttk.Combobox(tab_estudiantes, values=list(range(1,31)), width=5)
    combo_estudiantes.place(x=270, y=10)
    tkinter.Button(tab_estudiantes, text="Fijar", command=fijar_cantidad_estudiantes).place(x=320, y=10)

    estudiantes_tabla = tkinter.Listbox(tab_estudiantes, width=30, height=10)
    estudiantes_tabla.place(x=20, y=40)

    labels = ["ID", "Nombre", "Apellido", "Cédula"]
    inputs = []

    for i, t in enumerate(labels):
        tkinter.Label(tab_estudiantes, text=t).place(x=200, y=50 + i*40)
        e = tkinter.Entry(tab_estudiantes)
        e.place(x=270, y=50 + i*40)
        inputs.append(e)

    id_input, nombre_input, apellido_input, cedula_input = inputs

    tkinter.Button(tab_estudiantes, text="Guardar", command=guardar_estudiante).place(x=250, y=210)
    tkinter.Button(tab_estudiantes, text="Eliminar", bg="red", command=eliminar_estudiante).place(x=350, y=210)

    cargar_estudiantes()

    #  ASIGNATURAS
    tkinter.Label(tab_asignaturas, text="Cantidad").place(x=250, y=10)
    combo_asignaturas = ttk.Combobox(tab_asignaturas, values=list(range(1,7)), width=5)
    combo_asignaturas.place(x=320, y=10)
    tkinter.Button(tab_asignaturas, text="Fijar", command=fijar_cantidad_asignaturas).place(x=380, y=10)

    asig_nombre = tkinter.Entry(tab_asignaturas)
    asig_grupo = tkinter.Entry(tab_asignaturas)

    asig_nombre.place(x=100, y=50)
    asig_grupo.place(x=100, y=80)

    tkinter.Label(tab_asignaturas, text="Nombre").place(x=20, y=50)
    tkinter.Label(tab_asignaturas, text="Grupo").place(x=20, y=80)

    modalidad_cb = ttk.Combobox(tab_asignaturas, values=["Presencial", "Distancia"])
    modalidad_cb.place(x=100, y=110)

    tkinter.Label(tab_asignaturas, text="Modalidad").place(x=20, y=110)

    p_tareas = tkinter.Entry(tab_asignaturas, width=5)
    p_parcial = tkinter.Entry(tab_asignaturas, width=5)
    p_final = tkinter.Entry(tab_asignaturas, width=5)

    p_tareas.place(x=100, y=150)
    p_parcial.place(x=100, y=180)
    p_final.place(x=100, y=210)

    tkinter.Label(tab_asignaturas, text="Tareas").place(x=20, y=150)
    tkinter.Label(tab_asignaturas, text="Parcial").place(x=20, y=180)
    tkinter.Label(tab_asignaturas, text="Final").place(x=20, y=210)

    tkinter.Button(tab_asignaturas, text="Guardar", command=guardar_asignatura).place(x=100, y=240)
    tkinter.Button(tab_asignaturas, text="Eliminar", bg="red", command=eliminar_asignatura).place(x=250, y=240)
    tkinter.Button(tab_asignaturas, text="Cargar", command=cargar_asignaturas).place(x=180, y=240)

    resultado_label = tkinter.Label(tab_asignaturas, text="")
    resultado_label.place(x=20, y=270)

    asig_lista = tkinter.Listbox(tab_asignaturas, width=30)
    asig_lista.place(x=250, y=50)

    #  CALIFICACIONES
    tkinter.Label(tab_calificaciones, text="Cantidad").place(x=300, y=10)
    combo_notas = ttk.Combobox(tab_calificaciones, values=list(range(1,11)), width=5)
    combo_notas.place(x=370, y=10)
    tkinter.Button(tab_calificaciones, text="Fijar", command=fijar_cantidad_notas).place(x=430, y=10)

    est_cb = ttk.Combobox(tab_calificaciones)
    asig_cb = ttk.Combobox(tab_calificaciones)

    def cargar_combobox():
        try:
            if os.path.exists(archivo_estudiantes):
                with open(archivo_estudiantes, "r") as f:
                    datos = json.load(f)
                    est_cb["values"] = [f"{e['nombre']} {e['apellido']}" for e in datos]

            if os.path.exists(archivo_asignaturas):
                with open(archivo_asignaturas, "r") as f:
                    datos = json.load(f)
                    asig_cb["values"] = [a["nombre"] for a in datos]
        except:
            pass

    cargar_combobox()

    tkinter.Label(tab_calificaciones, text="Estudiante").place(x=20, y=50)
    est_cb.place(x=120, y=50)

    tkinter.Label(tab_calificaciones, text="Asignatura").place(x=20, y=80)
    asig_cb.place(x=120, y=80)

    n_tareas = tkinter.Entry(tab_calificaciones)
    n_parcial = tkinter.Entry(tab_calificaciones)
    n_final = tkinter.Entry(tab_calificaciones)

    n_tareas.place(x=120, y=120)
    n_parcial.place(x=120, y=150)
    n_final.place(x=120, y=180)

    tkinter.Label(tab_calificaciones, text="Tareas").place(x=20, y=120)
    tkinter.Label(tab_calificaciones, text="Parcial").place(x=20, y=150)
    tkinter.Label(tab_calificaciones, text="Final").place(x=20, y=180)

    tkinter.Button(tab_calificaciones, text="Guardar Nota", command=guardar_nota).place(x=120, y=220)

    resultado_notas = tkinter.Label(tab_calificaciones, text="")
    resultado_notas.place(x=120, y=260)

    #  REPORTES
    tkinter.Button(tab_reportes, text="Cargar Reportes", command=cargar_reportes).pack(pady=10)
    tkinter.Button(tab_reportes, text="Eliminar", bg="red", command=eliminar_reporte).pack()

    reporte_lista = tkinter.Listbox(tab_reportes, width=60, height=15)
    reporte_lista.pack()

    #  SEGURIDAD
    tkinter.Label(tab_seguridad, text="Cambio de Credenciales", font=("Arial", 14)).pack(pady=10)

    tkinter.Label(tab_seguridad, text="Usuario actual").place(x=50, y=60)
    usuario_actual = tkinter.Entry(tab_seguridad)
    usuario_actual.place(x=180, y=60)

    tkinter.Label(tab_seguridad, text="Contraseña actual").place(x=50, y=100)
    pass_actual = tkinter.Entry(tab_seguridad, show="*")
    pass_actual.place(x=180, y=100)

    tkinter.Label(tab_seguridad, text="Nuevo usuario").place(x=50, y=140)
    nuevo_usuario = tkinter.Entry(tab_seguridad)
    nuevo_usuario.place(x=180, y=140)

    tkinter.Label(tab_seguridad, text="Nueva contraseña").place(x=50, y=180)
    nuevo_pass = tkinter.Entry(tab_seguridad, show="*")
    nuevo_pass.place(x=180, y=180)

    resultado_seguridad = tkinter.Label(tab_seguridad, text="")
    resultado_seguridad.place(x=50, y=220)

    def cambiar_credenciales():
        cred = cargar_usuario()

        if usuario_actual.get() != cred["user"] or pass_actual.get() != cred["passwd"]:
            resultado_seguridad.config(text="Credenciales incorrectas", fg="red")
            return

        guardar_usuario(nuevo_usuario.get(), nuevo_pass.get())
        resultado_seguridad.config(text="Actualizado ✔", fg="green")

    tkinter.Button(tab_seguridad, text="Guardar cambios", bg="#7ed957", command=cambiar_credenciales).place(x=180, y=260)

    #  VOLVER
    def volver():
        problema1.destroy()
        menu.deiconify()

    tkinter.Button(problema1, text="Volver", command=volver).place(x=460, y=0)