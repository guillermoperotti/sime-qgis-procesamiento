# SIME – Procesamiento en QGIS

Este repositorio contiene scripts en **Python para QGIS** que realizan el **procesamiento y análisis de datos del SIME** (Sistema de Inspecciones de Montevideo).  

Es el **segundo paso** del flujo de trabajo:  
1. Usar el plugin [`mi-plugin-qgis`](https://github.com/TU-USUARIO/mi-plugin-qgis) para cargar y normalizar los CSV exportados desde la base de datos.  
2. Aplicar estos scripts para realizar análisis avanzados dentro de QGIS.

---

## ⚙️ Funcionalidades

El script principal (`Procesamiento.py`) permite:

- Aplicar **módulos de transformación y limpieza** de atributos.  
- Generar capas con simbología preparada para visualización.  
- Automatizar cálculos repetitivos que antes se hacían manualmente en QGIS.  
- Exportar resultados listos para informes o mapas.

---

## 🚀 Cómo usarlo

1. Abrir **QGIS**.
2. Ir al menú **Complementos → Consola de Python**.
3. Cargar el script con:  
   ```python
   exec(open("ruta/al/Procesamiento.py").read())
   


---


🧩 Requisitos

QGIS 3.x

Python 3.x (incluido en QGIS)

👉 No se requieren instalaciones adicionales, ya que se apoya en librerías estándar de QGIS.

📖 Flujo de trabajo completo

1. Carga y normalización del CSV:
    Repositorio: mi-plugin-qgis
2. Procesamiento y análisis avanzado:
Este repositorio (sime-qgis-procesamiento).


---

Autor

Guillermo Perotti

📧 guillermoperottichape@gmail.com

