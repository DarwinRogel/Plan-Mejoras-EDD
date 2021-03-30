<h1 align="center"> PLAN MEJORAS DE LA EVALUACIÓN AL DESEMPEÑO DOCENTE</h1>
<p align="center"> UNIVERSIDAD NACIONAL DE LOJA</p>
<p align="center"><img src="https://pbs.twimg.com/profile_images/1225522326487347211/FaNm0ISf_400x400.jpg" width="200" height="200"/></p> 

## Tabla de contenidos:
---
- [Autores](#autores)
- [Descripción y contexto](#descripción-y-contexto)
- [Guía de usuario](#guía-de-usuario)
- [Guía de instalación](#guía-de-instalación)
- [Información adicional](#información-adicional)

## Autores
---
El presente Trabajo de Titulación fue desarrollado por:
-   Darwin Alexander Rogel Rivera - darogelr@unl.edu.ec
-   Robin Lenin Cordova Alvarado - robin.cordova@unl.edu.ec<br/><br/>

Con la dirección del:
-   Ing. Pablo Fernando Ordoñez Ordoñez - pfordonez@unl.edu.ec

## Descripción y contexto
---
El presente repositorio contiene el código documentado del proyecto de Titulación <b>"Módulo de software para el Plan Mejoras de la Evaluación al Desempeño Docente"</b> de la Carrera de Ingeniería en Sistemas de la Universidad Nacional de Loja.
<br/><br/>
Este proceso es parte del Sistema de Evaluación al Desempeño Docente implementado por cada Carrera de la Universidad Nacional de Loja, formulado a partir de los resultados de la evaluación con el propósito de modificar o mejorar el estado actual del desempeño, mediante la implementación de acciones que logren mejorar la calidad en docencia 
<br/><br/>
Las funcionalidades con las que cuenta el módulo de sofware son:<br/>
-   Gestión del Informe del Plan Mejoras
-   Gestión de Debilidades
-   Gestión de Criterios de Evaluación
-   Gestión de Estados
-   Gestión de Etiquetas
-   Gestión de Roles y Permisos
-   Gestión de Usuarios
-   Gestión de Plan de Actividades del Plan Mejoras
-   Comunicación y/o notificación de inicio del Plan Mejoras
-   Comunicación y/o notificación de cumplimiento del Plan Mejoras
-   Visualización del Reporte del Plan Mejoras
-   Gestión de Evidencias del Plan de Actividades
-   Control y Seguimiento del Plan Mejoras
<br/><br/>

El objetivo del módulo es la optimización técnica de todas las actividades y etapas que conlleva el proceso del Plan Mejoras de la Evaluación al Desempeño Docente, y a su vez servir de apoyo a las tareas de seguimiento y control, otorgando funcionalidades que optimicen los procesos y ayuden a cumplir el objetivo del Plan Mejoras

## Guía de usuario
---
Para ingresar al módulo de software solicitar la dirección url al correo: direccion.cis@unl.edu.ec o su vez a los autores.
<br/><br/>
Para acceder al manual de usuario (Gestor de la CIS/C, Consejo Consultivo) del módulo de software ingrese al siguiente enlace: https://drive.google.com/file/d/1Y9z8aw7zdjAzlMk6PyCScE7vufUZq8kJ/view?usp=sharing
<br/><br/>
Para acceder al manual de usuario (Docente) del módulo de software ingrese al siguiente enlace: https://drive.google.com/file/d/1r1TRm8-9pcTBHBRKUgvfWdWCE0g2GIuK/view?usp=sharing

 	
## Guía de instalación
---
Para comenzar con la instalación del módulo de software se recomienda acceder al siguiente enlace: hps://drive.google.com/file/d/1O-xapR0NC_oOJvLrRy5JsZdmO_FtZdSM/view?usp=sharing el cual proporciona una guía referente a la implantación del módulo en el Sistema Odoo ERP.
<br/><br/>
Las Tecnologías y Herramientas utilizadas fueron:
-   Plataforma de Google en la Nube (GCP)
-   Sistema Operativo Centos 8
-   Lenguaje de Programación Pyhton versión 3.6.8
-   Gestor de Base de Datos PostgreSQL versión 10
-   Framework Odoo versión 13
-   Entorno de Desarrollo Integrado​​ PyCharm

### Dependencias
Para Instalar Python 3 , Git, pip y todas las bibliotecas y herramientas necesarias para construir Odoo desde la fuente ejecute el siguiente comando:

    sudo dnf install python3 python3-devel git gcc redhat-rpm-config libxslt-devel bzip2-devel openldap-devel libjpeg-devel freetype-devel

Para la instalación del wkhtmltox (paquete proporciona un conjunto de herramientas de línea de comandos de código abierto que pueden convertir HTML en PDF y varios formatos de imagen) ejecute el siguiente comando:

    sudo dnf install https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox-0.12.5-1.centos8.x86_64.rpm

Para la instalación de los módulos de Python necesarios ejecute el siguimiente comando:

    pip3 install -r odoo/requirements.txt

## Información adicional
---
Para conocer más de Odoo ingrese a https://www.odoo.com/es_ES/
<br/><br/>
Para acceder a la documentación de Desarrolladores de Odoo ingrese a https://www.odoo.com/documentation/13.0/
<br/><br/>
Para instruirse en el desarrollo en Framework Odoo ingrese a https://escuelafullstack.com/slides/curso-de-odoo-13-framework-backend-2