# SIME – Procesamiento en QGIS

Este repositorio contiene scripts en **Python para QGIS** que realizan el **procesamiento y análisis de datos del SIME** (Sistema de Inspecciones de Montevideo).

Es el **segundo paso** del flujo de trabajo:
1. Usar el plugin [`mi-plugin-qgis`](https://github.com/TU-USUARIO/mi-plugin-qgis) para cargar y normalizar los CSV exportados desde la base de datos.
2. Aplicar estos scripts para realizar análisis avanzados dentro de QGIS.

---

## 📂 Scripts disponibles

Este repositorio incluye dos scripts principales:

### 1. Procesamiento.py

Script completo para procesamiento avanzado de datos SIME en QGIS.

**Funcionalidades:**
- Módulos de transformación y limpieza de atributos.
- Generación de capas con simbología preparada.
- Automatización de cálculos repetitivos.
- Exportación de resultados listos para informes o mapas.

**Cómo usarlo:**
1. Abrir **QGIS**.
2. Ir al menú **Complementos → Consola de Python**.
3. Cargar el script con:
    ```python
    exec(open("ruta/al/Procesamiento.py").read())
    ```

---

### 2. Procesamiento_Maquinarias.py

Script simplificado para tareas administrativas del SIME, enfocado solo en el concepto de **Maquinarias**.

**Funcionalidades:**
- Procesamiento básico y rápido de datos de Maquinarias.
- Menos filtros y opciones, ideal para tareas administrativas simples.

**Cómo usarlo:**
1. Abrir **QGIS**.
2. Ir al menú **Complementos → Consola de Python**.
3. Cargar el script con:
    ```python
    exec(open("ruta/al/Procesamiento_Maquinarias.py").read())
    ```

---

## 🧩 Requisitos

- QGIS 3.x
- Python 3.x (incluido en QGIS)
- 👉 No se requieren instalaciones adicionales, ya que se apoya en librerías estándar de QGIS.

---

## 📖 Flujo de trabajo completo

1. Carga y normalización del CSV:  
   Repositorio: mi-plugin-qgis
2. Procesamiento y análisis avanzado:  
   Este repositorio (sime-qgis-procesamiento).

---

## Autor

Guillermo Perotti  
📧 guillermoperottichape@gmail.com
    exec(open("ruta/al/Procesamiento_Maquinarias.py").read())
    ```

