**SISTEMA WEB PARA "SUCESOS Y MÁS" - DOCUMENTACIÓN TÉCNICA**



**1. DESCRIPCIÓN DEL PROYECTO (PARTE I)**



Este proyecto representa una solución integral de desarrollo web para la Pyme

"SUCESOS Y MÁS". El objetivo principal es proporcionar un prototipo 

funcional programado en Python que permita la navegación fluida entre las 

secciones estratégicas de la empresa.



El diseño sigue los valores corporativos de AdComSolution: innovación y

confiabilidad tecnológica para la resolución de problemas organizacionales.



**2. ARQUITECTURA DE ARCHIVOS**



La aplicación se estructura de la siguiente manera:



\* Backend principal: app.py (Gestión de rutas y servidor Flask).

\* Estilos visuales: style.css (Diseño de interfaz y creatividad).

\* Base de datos: noticias.json (Almacenamiento persistente de noticias).

\* Plantillas HTML (Vistas):

&#x20;   - base.html: Estructura maestra y menú principal.

&#x20;   - index.html: Página de inicio con Misión y Visión.

&#x20;   - servicios.html: Catálogo de servicios profesionales.

&#x20;   - productos.html: Galería de productos disponibles.

&#x20;   - contactos.html: Formas de contacto y redes sociales.

&#x20;   - clientes.html: Sección dedicada a la cartera de clientes.

&#x20;   - admin.html: Panel de gestión exclusivo.



**3. MÓDULO DE ADMINISTRACIÓN (ADMIN)**



Para cumplir con el requisito de actualización de noticias en tiempo real, 

se implementó un panel seguro:



\* Acceso: Únicamente mediante la ruta específica "http://127.0.0.1:5000/ADMIN".

\* Seguridad: El ingreso está restringido mediante una contraseña obligatoria.

\* Funciones: Permite subir, editar y eliminar noticias de forma dinámica. 

\* Persistencia: Los cambios se guardan automáticamente en el archivo JSON,

&#x20; asegurando que la información se mantenga actualizada sin bases de datos complejas.



**4. DESPLIEGUE Y CONECTIVIDAD EN SERVIDOR LINUX (PARTE II)**



El sistema ha sido diseñado para operar en un entorno de Servidor de Datos Linux 

(Lubuntu).



\* Configuración de Red: Se utiliza un adaptador de red en modo "Adaptador Puente" 

&#x20; dentro de la máquina virtual para permitir la visibilidad en la red local.

\* Conectividad Externa: El archivo app.py incluye la instrucción:

&#x20; "app.run(debug=True, host='0.0.0.0', port=5000)"

&#x20; 

&#x20; Esto es fundamental porque el host '0.0.0.0' indica al servidor Flask que debe 

&#x20; escuchar peticiones en todas las direcciones IP disponibles. Esto permite que 

&#x20; cualquier equipo en la red (incluida la VM de Lubuntu) acceda a la web 

&#x20; usando la IP del host.



\* Gestión de Archivos: Se han configurado los protocolos SSH y FTP en el 

&#x20; servidor para facilitar el respaldo del código y del archivo de datos 

&#x20; noticias.json.





*Desarrollado para la asignatura de Programación II\[cite: 1].*

*Profesor: Napoleón Ibarra.*

