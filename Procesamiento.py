from qgis.core import (
    QgsProject, QgsRuleBasedRenderer, QgsSymbol, QgsVectorLayer,
    QgsFeature, QgsGeometry
)
from PyQt5.QtGui import QColor
from qgis.utils import iface
from datetime import datetime, timedelta

# -----------------------------
# 1. Generador de colores degradados (violeta → verde)
# -----------------------------
def interpolar_colores(fecha_inicio, fecha_fin, total_rangos):
    r1, g1, b1 = 148, 0, 211  # violeta
    r2, g2, b2 = 0, 255, 0    # verde

    colores = []
    for i in range(total_rangos):
        t = i / (total_rangos - 1) if total_rangos > 1 else 0
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        colores.append(QColor(r, g, b).name())
    return colores

# -----------------------------
# 2. Detectar fechas min/max
# -----------------------------
def obtener_rango_fechas(capa, campo_fecha):
    fechas = []
    for f in capa.getFeatures():
        valor = f[campo_fecha]
        if valor:
            try:
                fecha = datetime.strptime(str(valor)[:10], "%Y-%m-%d")
                fechas.append(fecha)
            except ValueError:
                continue
    if not fechas:
        return None, None
    fecha_min = min(fechas)
    fecha_max = max(fechas)
    return fecha_min.strftime("%Y-%m-%d"), fecha_max.strftime("%Y-%m-%d")

# -----------------------------
# 3. Crear capa filtrada y aplicar simbología por año
# -----------------------------
def crear_capa_asignar(capa_origen, nombre, valor_filtro, campo_fecha, geometria_str, crs):
    nombre_capa = f"{nombre}_A_ASIGNAR {capa_origen.name()}"
    capa_asig = QgsVectorLayer(f"{geometria_str}?crs={crs}", nombre_capa, "memory")
    prov = capa_asig.dataProvider()
    prov.addAttributes(capa_origen.fields())
    capa_asig.updateFields()

    features = [f for f in capa_origen.getFeatures() if f["#A_asignar_ubicacion"] == valor_filtro]
    prov.addFeatures(features)
    QgsProject.instance().addMapLayer(capa_asig, False)
    nodo = QgsProject.instance().layerTreeRoot().insertLayer(0, capa_asig)
    nodo.setItemVisibilityChecked(False)

    print(f"Se creó la capa '{nombre_capa}'.")

    # Aplicar simbología por año
    simbolo_base = QgsSymbol.defaultSymbol(capa_asig.geometryType())
    raiz = QgsRuleBasedRenderer.Rule(None)

    fi_ini, fi_fin = obtener_rango_fechas(capa_asig, campo_fecha)
    if not fi_ini or not fi_fin:
        print(f"No se encontraron fechas válidas en {campo_fecha} para {nombre}.")
        return

    for fi, ff, color, etiqueta in generar_rangos_fechas(fi_ini, fi_fin):
        regla = QgsRuleBasedRenderer.Rule(simbolo_base.clone())
        expresion = (
            f'"{campo_fecha}" >= \'{fi}\' AND '
            f'"{campo_fecha}" < \'{ff}\''
        ) if ff else f'"{campo_fecha}" >= \'{fi}\''
        regla.setLabel(etiqueta)
        regla.setFilterExpression(expresion)
        regla.symbol().setColor(QColor(color))
        raiz.appendChild(regla)

    capa_asig.setRenderer(QgsRuleBasedRenderer(raiz))
    capa_asig.triggerRepaint()

# -----------------------------
# 4. Generador de rangos anuales con colores y etiquetas (usado en A_ASIGNAR)
# -----------------------------
def generar_rangos_fechas(inicio_str, fin_str):
    inicio = datetime.strptime(inicio_str, "%Y-%m-%d")
    fin = datetime.strptime(fin_str, "%Y-%m-%d")
    fechas = []
    actual = inicio
    while actual < fin:
        siguiente = actual.replace(year=actual.year + 1)
        fechas.append((actual, siguiente))
        actual = siguiente

    total = len(fechas)
    colores = interpolar_colores(inicio, fin, total)
    rangos = []

    for i, ((fi, ff), color) in enumerate(zip(fechas, colores)):
        if i < total // 3:
            etapa = "Antiguo"
        elif i < 2 * total // 3:
            etapa = "Medio"
        else:
            etapa = "Reciente"
        etiqueta = f"Año {fi.year} - {etapa}"
        rangos.append((fi.strftime("%Y-%m-%d"), ff.strftime("%Y-%m-%d"), color, etiqueta))

    # Último rango abierto
    rangos.append((fin.strftime("%Y-%m-%d"), None, colores[-1], f">= {fin.year} - Reciente"))

    return rangos

# -----------------------------
# 5. Función principal
# -----------------------------
def procesar_capa(nombre_capa):
    proyecto = QgsProject.instance()
    capa = proyecto.mapLayersByName(nombre_capa)
    if not capa:
        print(f"No se encontró la capa '{nombre_capa}'.")
        return
    capa = capa[0]

    geometria_str = {0: "Point", 1: "LineString", 2: "Polygon"}.get(capa.geometryType(), "Unknown")
    crs = capa.crs().authid()

    # -----------------------------
    # Simbología por #Fecha_Ultima_Habilitacion
    # -----------------------------
    simbolo_base = QgsSymbol.defaultSymbol(capa.geometryType())
    raiz = QgsRuleBasedRenderer.Rule(None)

    fi_ini, fi_fin = obtener_rango_fechas(capa, "#Fecha_Ultima_Habilitacion")
    if not fi_ini or not fi_fin:
        print("No se encontraron fechas válidas en #Fecha_Ultima_Habilitacion.")
        return

    fecha_inicio = datetime.strptime(fi_ini, "%Y-%m-%d")
    fecha_fin = datetime.strptime(fi_fin, "%Y-%m-%d")

    primera_cota_superior = datetime(fecha_inicio.year, 1, 10)
    if fecha_inicio > primera_cota_superior:
        primera_cota_superior = datetime(fecha_inicio.year + 1, 1, 10)

    fechas_rangos = []
    fechas_rangos.append((fecha_inicio, primera_cota_superior))

    actual = primera_cota_superior
    while actual < fecha_fin:
        siguiente = datetime(actual.year + 1, 1, 10)
        if siguiente >= fecha_fin:
            break
        fechas_rangos.append((actual, siguiente))
        actual = siguiente

    fechas_rangos.append((actual, None))  # último rango abierto

    colores = interpolar_colores(fecha_inicio, fecha_fin, len(fechas_rangos))
    umbral_habilitados = datetime(2020, 1, 10)

    for (fi, ff), color in zip(fechas_rangos, colores):
        regla = QgsRuleBasedRenderer.Rule(simbolo_base.clone())
        if ff:
            expresion = (
                f'"#Fecha_Ultima_Habilitacion" >= \'{fi.strftime("%Y-%m-%d")}\' AND '
                f'"#Fecha_Ultima_Habilitacion" < \'{ff.strftime("%Y-%m-%d")}\''
            )
            etiqueta = f"{fi.strftime('%Y-%m-%d')} a {ff.strftime('%Y-%m-%d')}"
        else:
            expresion = f'"#Fecha_Ultima_Habilitacion" >= \'{fi.strftime("%Y-%m-%d")}\''
            etiqueta = f">= {fi.strftime('%Y-%m-%d')}"

        if fi < umbral_habilitados:
            etiqueta += " - VENCIDOS"
        else:
            etiqueta += " - HABILITADOS"

        regla.setLabel(etiqueta)
        regla.setFilterExpression(expresion)
        regla.symbol().setColor(QColor(color))
        raiz.appendChild(regla)

    capa.setRenderer(QgsRuleBasedRenderer(raiz))
    capa.triggerRepaint()

    # -----------------------------
    # Crear capas A_ASIGNAR
    # -----------------------------
    crear_capa_asignar(capa, "MAQUINARIAS", "MAQUINARIAS", "#A_asignar_desde", geometria_str, crs)
    crear_capa_asignar(capa, "MOLESTIAS", "MOLESTIAS", "#A_asignar_desde", geometria_str, crs)
    crear_capa_asignar(capa, "VENTILACION", "VENTILACION", "#A_asignar_desde", geometria_str, crs)

    # -----------------------------
    # Crear capa Hab<2020
    # -----------------------------
    capa_hab_2020 = QgsVectorLayer(f"{geometria_str}?crs={crs}", f"Hab<2020 {nombre_capa}", "memory")
    hab_data = capa_hab_2020.dataProvider()
    hab_data.addAttributes(capa.fields())
    capa_hab_2020.updateFields()

    hab_features = [
    f for f in capa.getFeatures()
    if f["#Fecha_Ultima_Habilitacion"] and f["#Fecha_Ultima_Habilitacion"] < '2020-01-10'
    ]

    hab_data.addFeatures(hab_features)
    QgsProject.instance().addMapLayer(capa_hab_2020, False)
    nodo = QgsProject.instance().layerTreeRoot().insertLayer(0, capa_hab_2020)
    nodo.setItemVisibilityChecked(False)

    print(f"Se creó la capa 'Hab<2020 {nombre_capa}'.")

    # -----------------------------
    # Top 10 por #Capacidad
    # -----------------------------
    capacidades = [(f.id(), f["#Capacidad"]) for f in capa_hab_2020.getFeatures() if f["#Capacidad"] is not None]
    top_10_ids = [i[0] for i in sorted(capacidades, key=lambda x: x[1], reverse=True)[:10]]
    capa_hab_2020.selectByIds(top_10_ids)

    capa_top10 = QgsVectorLayer(f"{geometria_str}?crs={crs}", f"10MayoresHp {nombre_capa}", "memory")
    top10_data = capa_top10.dataProvider()
    top10_data.addAttributes(capa_hab_2020.fields())
    capa_top10.updateFields()
    top10_data.addFeatures(capa_hab_2020.selectedFeatures())
    QgsProject.instance().addMapLayer(capa_top10, False)
    nodo = QgsProject.instance().layerTreeRoot().insertLayer(0, capa_top10)
    nodo.setItemVisibilityChecked(False)

    print(f"Se creó la capa '10MayoresHp {nombre_capa}'.")

    # -----------------------------
    # Crear centroides
    # -----------------------------
    capa_centroides = QgsVectorLayer("Point?crs=" + crs, f"Centroides_10MayoresHp {nombre_capa}", "memory")
    centroides_data = capa_centroides.dataProvider()
    centroides_data.addAttributes(capa_top10.fields())
    capa_centroides.updateFields()

    for f in capa_top10.getFeatures():
        centroide = QgsFeature()
        centroide.setGeometry(f.geometry().centroid())
        centroide.setAttributes(f.attributes())
        centroides_data.addFeature(centroide)

    QgsProject.instance().addMapLayer(capa_centroides, False)
    nodo = QgsProject.instance().layerTreeRoot().insertLayer(0, capa_centroides)
    nodo.setItemVisibilityChecked(False)

    print(f"Se creó la capa 'Centroides_10MayoresHp {nombre_capa}'.")

    # -----------------------------
    # Crear buffers de 500m
    # -----------------------------
    capa_buffer = QgsVectorLayer("Polygon?crs=" + crs, f"Buffer{nombre_capa}", "memory")
    buffer_data = capa_buffer.dataProvider()
    buffer_data.addAttributes(capa_centroides.fields())
    capa_buffer.updateFields()

    for f in capa_centroides.getFeatures():
        buffer = QgsFeature()
        buffer.setGeometry(f.geometry().buffer(500, 5))
        buffer.setAttributes(f.attributes())
        buffer_data.addFeature(buffer)

    capa_buffer.renderer().symbol().setOpacity(0.5)
    capa_buffer.triggerRepaint()
    QgsProject.instance().addMapLayer(capa_buffer, False)
    nodo = QgsProject.instance().layerTreeRoot().insertLayer(0, capa_buffer)
    nodo.setItemVisibilityChecked(False)
    print(f"Se creó la capa de buffer 'Buffer{nombre_capa}'.")


    iface.mapCanvas().setExtent(capa_buffer.extent())
    iface.mapCanvas().refresh()
    print(f"Se creó la capa de buffer 'Buffer{nombre_capa}'.")


import csv
import os
import subprocess
from datetime import datetime

def procesar_interseccion_y_union(buffer_capa):
    proyecto = QgsProject.instance()

    buffer_layer = proyecto.mapLayersByName(buffer_capa)
    if not buffer_layer:
        print(f"No se encontró la capa buffer '{buffer_capa}'.")
        return
    else:
        buffer_layer = buffer_layer[0]

    capas_base = [
        "Hab<2020 Capa_unida_1",
        "Hab<2020 Capa_unida_2",
        "VENTILACION_A_ASIGNAR Capa_unida_1",
        "MOLESTIAS_A_ASIGNAR Capa_unida_1",
        "MAQUINARIAS_A_ASIGNAR Capa_unida_1",
        "VENTILACION_A_ASIGNAR Capa_unida_2",
        "MOLESTIAS_A_ASIGNAR Capa_unida_2",
        "MAQUINARIAS_A_ASIGNAR Capa_unida_2"
    ]

    capas_interseccion = []

    for capa_nombre in capas_base:
        capa = proyecto.mapLayersByName(capa_nombre)
        if not capa:
            print(f"⚠ No se encontró la capa '{capa_nombre}'.")
            continue
        capa = capa[0]

        processing.run("native:selectbylocation", {
            'INPUT': capa,
            'PREDICATE': [0],  # intersects
            'INTERSECT': buffer_layer,
            'METHOD': 0
        })

        if capa.selectedFeatureCount() > 0:
            nombre_interseccion = f"{capa_nombre} ∩ {buffer_capa}"
            capa_resultado = processing.run("native:saveselectedfeatures", {
                'INPUT': capa,
                'OUTPUT': 'memory:',
                'OUTPUT_LAYER_NAME': nombre_interseccion
            })['OUTPUT']
            capa_resultado.setName(nombre_interseccion)

            layer = QgsProject.instance().addMapLayer(capa_resultado, False)
            root = QgsProject.instance().layerTreeRoot()
            node = root.insertLayer(0, layer)
            node.setItemVisibilityChecked(False)

            capas_interseccion.append(capa_resultado)
            print(f"✔ Intersección creada: '{nombre_interseccion}'")
        else:
            print(f"⚠ No hay intersección en '{capa_nombre}' con '{buffer_capa}'.")

    if not capas_interseccion:
        print("❌ No se generó la capa 'UNION_DE_INTERSECCIONES' porque no hubo intersecciones.")
        return

    capa_union = processing.run("native:mergevectorlayers", {
        'LAYERS': capas_interseccion,
        'CRS': capas_interseccion[0].crs(),
        'OUTPUT': 'memory:'
    })['OUTPUT']

    nombre_corto = buffer_capa.replace("Capa_unida_", "")
    nombre_union = f"UNION_DE_INTERSECCIONES_{nombre_corto}"
    capa_union.setName(nombre_union)

    layer = QgsProject.instance().addMapLayer(capa_union, False)
    root = QgsProject.instance().layerTreeRoot()
    node = root.insertLayer(0, layer)
    node.setItemVisibilityChecked(False)

    print(f"✅ Se creó la capa '{nombre_union}'.")

    # -----------------------------
    # Exportar a CSV
    # -----------------------------
    campos = [
        "#Expediente", "#Padron", "#Concepto", "#Descripcion",
        "#Capacidad", "#Fecha_Ultima_Habilitacion", "#A_asignar_desde",
        "#A_asignar_ubicacion", "#A_asignar_observaciones", "AREA_DIFER"
    ]

    # Detectar capa top10 correspondiente
    if "1" in nombre_corto:
        capa_top_nombre = "10MayoresHp Capa_unida_1"
    elif "2" in nombre_corto:
        capa_top_nombre = "10MayoresHp Capa_unida_2"
    else:
        capa_top_nombre = None

    expedientes_top10 = set()
    if capa_top_nombre:
        capa_top = proyecto.mapLayersByName(capa_top_nombre)
        if capa_top:
            capa_top = capa_top[0]
            for f in capa_top.getFeatures():
                expediente = str(f["#Expediente"]) if f["#Expediente"] else ""
                if expediente:
                    expedientes_top10.add(expediente)

    # -----------------------------
    # Construir mapa de expedientes con la feature de mayor capacidad
    # -----------------------------
    mayor_por_expediente = {}
    for f in capa_union.getFeatures():
        expediente = str(f["#Expediente"]) if f["#Expediente"] else ""
        capacidad = f["#Capacidad"] if "#Capacidad" in f.fields().names() and f["#Capacidad"] is not None else -1
        if expediente in expedientes_top10:
            if expediente not in mayor_por_expediente:
                mayor_por_expediente[expediente] = (f.id(), capacidad)
            else:
                _, cap_actual = mayor_por_expediente[expediente]
                if capacidad > cap_actual:
                    mayor_por_expediente[expediente] = (f.id(), capacidad)

    # -----------------------------
    # Preparar y exportar CSV
    # -----------------------------
    registros = []
    for f in capa_union.getFeatures():
        fila = [f[field] if field in capa_union.fields().names() else "" for field in campos]
        expediente = str(f["#Expediente"]) if f["#Expediente"] else ""
        marcar_si = (
            expediente in mayor_por_expediente and f.id() == mayor_por_expediente[expediente][0]
        )
        fila.append("Sí" if marcar_si else "")
        registros.append(fila)

    registros_ordenados = sorted(registros, key=lambda x: str(x[9]) if x[9] else "")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"{nombre_union}_{timestamp}.csv"
    # Crear subcarpeta 'salidas' si no existe
    carpeta_salida = os.path.join(QgsProject.instance().homePath(), "salidas")
    os.makedirs(carpeta_salida, exist_ok=True)

    ruta_csv = os.path.join(carpeta_salida, nombre_archivo)

    with open(ruta_csv, mode='w', newline='', encoding='utf-8') as archivo:
        writer = csv.writer(archivo)
        writer.writerow(campos + ["MAYOR"])
        writer.writerows(registros_ordenados)

    print(f"📄 CSV exportado: {ruta_csv}")

    # Abrir automáticamente
    try:
        subprocess.Popen(['xdg-open', ruta_csv])
        print("📂 Archivo abierto automáticamente.")
    except Exception as e:
        print(f"⚠ No se pudo abrir el archivo automáticamente: {e}")



# -----------------------------
# Función: Deseleccionar y eliminar capas intermedias
# -----------------------------
def limpieza_final():
    proyecto = QgsProject.instance()
    root = proyecto.layerTreeRoot()

    capas_a_remover = []

    for layer in proyecto.mapLayers().values():
        if isinstance(layer, QgsVectorLayer):
            layer.removeSelection()  # Deseleccionar entidades
            nombre = layer.name()
            nodo = root.findLayer(layer.id())

            # Marcar para eliminar si es intersección o capa Hab<2020
            if "∩ Buffer" in nombre or nombre.startswith("Hab<2020 "):
                capas_a_remover.append(layer.id())

            # Asegurar visibilidad para capas UNION e Centroides
            elif nombre.startswith("UNION_DE_INTERSECCIONES_") and nodo:
                nodo.setItemVisibilityChecked(True)

            elif nombre.startswith("Centroides_10MayoresHp") and nodo:
                nodo.setItemVisibilityChecked(True)

    # Eliminar capas marcadas
    for layer_id in capas_a_remover:
        proyecto.removeMapLayer(layer_id)

    print("🧹 Limpieza completada: se eliminaron capas intermedias y se dejaron visibles las capas finales.")


# -----------------------------
# Ejecutar procesos
# -----------------------------
procesar_capa("Capa_unida_1")
procesar_capa("Capa_unida_2")
procesar_interseccion_y_union("BufferCapa_unida_1")
procesar_interseccion_y_union("BufferCapa_unida_2")
limpieza_final()

