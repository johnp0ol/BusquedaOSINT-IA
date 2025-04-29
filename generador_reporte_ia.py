import os
from datetime import datetime

def generar_html_ia(email, serpapi_data, sherlock_data=None, maigret_data=None, holehe_data=None, hibp_data=None, output_dir="resultados_ia", twitter_data=None):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_name = email.replace("@", "_").replace(".", "_")
    nombre_archivo = os.path.join(output_dir, f"reporte_ia_{safe_name}.html")

    def agrupar_por_categoria(datos):
        categorias = {}
        for r in datos:
            categoria = r.get("categoria", "Otro")
            categorias.setdefault(categoria, []).append(r)
        return categorias

    categorias_serp = agrupar_por_categoria(serpapi_data)
    categorias_sherlock = agrupar_por_categoria(sherlock_data or [])
    categorias_maigret = agrupar_por_categoria(maigret_data or [])
    categorias_holehe = agrupar_por_categoria(holehe_data or [])
    categorias_hibp = agrupar_por_categoria(hibp_data or [])

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Reporte OSINT con IA - {email}</title>
    <style>
        body {{ font-family: Arial; margin: 20px; background: #f9f9f9; }}
        h1 {{ color: #2c3e50; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; vertical-align: top; }}
        th {{ background-color: #e0e0e0; }}
        .categoria {{ background-color: #dfefff; padding: 10px; margin-top: 30px; }}
        a {{ color: #2980b9; text-decoration: none; }}
        .entidad {{
            display: inline-block;
            background-color: #e2ecf9;
            padding: 5px 8px;
            border-radius: 6px;
            margin: 2px 4px 2px 0;
            font-size: 0.9em;
        }}
        .tag {{
            font-size: 0.75em;
            color: #555;
            background-color: #ccddee;
            padding: 2px 5px;
            border-radius: 4px;
            margin-left: 6px;
        }}
    </style>
</head>
<body>
    <h1>Reporte OSINT con Inteligencia Artificial - {email}</h1>
    <p><strong>Fecha:</strong> {fecha}</p>
    <hr>
"""

    total_serp = sum(len(v) for v in categorias_serp.values())
    total_sherlock = sum(len(v) for v in categorias_sherlock.values())
    total_maigret = sum(len(v) for v in categorias_maigret.values())
    total_holehe = sum(len(v) for v in categorias_holehe.values())
    total_hibp = sum(len(v) for v in categorias_hibp.values())

    html += f"<h2>🔍 Resumen General de Resultados</h2><ul>"

    if "@" in email:
        html += f"""
        <li><strong>Holehe:</strong> {total_holehe} coincidencias</li>
        <li><strong>HaveIBeenPwned:</strong> {total_hibp} filtraciones</li>
        <li><strong>SerpAPI:</strong> {total_serp} resultados</li>
        """
    else:
        html += f"""
        <li><strong>Maigret:</strong> {total_maigret} perfiles</li>
        <li><strong>Sherlock:</strong> {total_sherlock} perfiles</li>
        <li><strong>Twitter:</strong> {"1 perfil" if twitter_data else "0 perfiles"}</li>
        <li><strong>SerpAPI:</strong> {total_serp} resultados</li>
        """

    html += "</ul><hr>"

    def incluir_tabla_y_graficos(categorias, herramienta):
        html_bloque = ""
        for categoria, resultados in categorias.items():
            html_bloque += f"<div class='categoria'><h2>[{herramienta}] Categoría: {categoria} ({len(resultados)} resultados)</h2><table>"
            if herramienta in ["Sherlock", "Maigret"]:
                html_bloque += "<tr><th>Enlace</th></tr>"
                for r in resultados:
                    html_bloque += f"<tr><td><a href='{r['url']}' target='_blank'>{r['url']}</a></td></tr>"
            elif herramienta == "Holehe":
                html_bloque += "<tr><th>Sitio</th></tr>"
                for r in resultados:
                    html_bloque += f"<tr><td>{r['servicio']}</td></tr>"
            elif herramienta == "SerpAPI":
                html_bloque += "<tr><th>Fuente</th><th>Título</th><th>Enlace</th><th>Descripción</th><th>Entidades</th></tr>"
                for r in resultados:
                    entidades = r.get("entidades", [])
                    entidades_texto = "".join([
                        f'<span class=\"entidad\">{e[0]} <span class=\"tag\">{e[1]}</span></span>' for e in entidades
                    ]) if entidades else ""
                    html_bloque += f"<tr><td>{r['source']}</td><td>{r['title']}</td><td><a href='{r['link']}' target='_blank'>{r['link']}</a></td><td>{r['snippet']}</td><td>{entidades_texto}</td></tr>"
            html_bloque += "</table></div>"

        ruta_barra = os.path.join(output_dir, f"grafico_{herramienta.lower()}_{safe_name}.png")
        if os.path.exists(ruta_barra):
            html_bloque += f"<div class='categoria'><h3>[{herramienta}] Gráfico por categoría</h3><img src='grafico_{herramienta.lower()}_{safe_name}.png' style='max-width: 100%; border: 1px solid #ccc; padding: 10px;'></div>"

        ruta_pie = os.path.join(output_dir, f"grafico_{herramienta.lower()}_pie_{safe_name}.png")
        if os.path.exists(ruta_pie):
            html_bloque += f"<div class='categoria'><h3>[{herramienta}] Distribución porcentual (gráfico circular)</h3><img src='grafico_{herramienta.lower()}_pie_{safe_name}.png' style='max-width: 100%; border: 1px solid #ccc; padding: 10px;'></div>"

        return html_bloque

# BLOQUE HOLEHE
    html += incluir_tabla_y_graficos(categorias_holehe, "Holehe")
    
# BLOQUE HIBP
    if categorias_hibp:
        html += f"<div class='categoria'><h2>[HIBP] Resultados agrupados por categoría ({total_hibp} filtraciones)</h2>"
        html += f"<div style='margin-bottom: 20px;'><h3>📌 Tipos de información detectada (interpretación)</h3><ul><li>📅 <strong>Fechas (DATE)</strong></li><li>🏢 <strong>Organizaciones (ORG)</strong></li><li>🧑 <strong>Personas (PERSON)</strong></li><li>📦 <strong>Productos o Servicios (PRODUCT)</strong></li><li>🔢 <strong>Números (CARDINAL)</strong></li><li>🌍 <strong>Lugares (GPE)</strong></li></ul></div>"

        for categoria, filtraciones in categorias_hibp.items():
            html += f"<div style='margin-top: 25px;'><h3>Categoría: {categoria} ({len(filtraciones)} filtraciones)</h3><table><tr><th>Nombre</th><th>Fecha</th><th>Dominio</th><th>Datos</th><th>Descripción</th><th>Entidades nombradas</th></tr>"
            for r in filtraciones:
                entidades = r.get("entidades", [])
                entidades_texto = "".join([
                    f'<span class="entidad">{e[0]} <span class="tag">{e[1]}</span></span>' for e in entidades
                ]) if entidades else ""
                html += f"<tr><td>{r['nombre']}</td><td>{r['fecha']}</td><td>{r['dominio']}</td><td>{r['datos']}</td><td>{r['descripcion']}</td><td>{entidades_texto}</td></tr>"
            html += "</table></div>"

        ruta_hibp_barra = os.path.join(output_dir, f"grafico_hibp_{safe_name}.png")
        if os.path.exists(ruta_hibp_barra):
            html += f"<div style='margin-top: 20px;'><h3>[HIBP] Gráfico por categoría</h3><img src='grafico_hibp_{safe_name}.png' style='max-width: 100%; border: 1px solid #ccc; padding: 10px;'></div>"

        ruta_hibp_pie = os.path.join(output_dir, f"grafico_hibp_pie_{safe_name}.png")
        if os.path.exists(ruta_hibp_pie):
            html += f"<div style='margin-top: 20px;'><h3>[HIBP] Distribución porcentual (gráfico circular)</h3><img src='grafico_hibp_pie_{safe_name}.png' style='max-width: 100%; border: 1px solid #ccc; padding: 10px;'></div>"
        html += "</div>"

# BLOQUE MAIGRET
    html += incluir_tabla_y_graficos(categorias_maigret, "Maigret")

# BLOQUE SHERLOCK
    html += incluir_tabla_y_graficos(categorias_sherlock, "Sherlock")
    
# BLOQUE DE TWITTER
    if twitter_data:
        conf = twitter_data.get("confiabilidad", "")
        conf_str = {
            "Alta": "🟢 Alta",
            "Media": "🟡 Media",
            "Baja": "🔴 Baja"
        }.get(conf, "No evaluada")

        html += f"""
<h2>🔗 Twitter ID detectado</h2>
<table>
<tr><th>Campo</th><th>Valor</th></tr>
<tr><td>Username</td><td>{twitter_data.get('username', '')}</td></tr>
<tr><td>ID de Twitter</td><td>{twitter_data.get('id', '')}</td></tr>
<tr><td>Estado</td><td>{twitter_data.get('estado', '')}</td></tr>
<tr><td>Email</td><td>{twitter_data.get('email', '')}</td></tr>
<tr><td>Seguidores</td><td>{twitter_data.get('seguidores', '')}</td></tr>
<tr><td>Fecha de creación</td><td>{twitter_data.get('fecha_creacion', '')}</td></tr>
<tr><td>Descripción</td><td>{twitter_data.get('descripcion', '')}</td></tr>
<tr><td>Confiabilidad estimada (IA)</td><td>{conf_str}</td></tr>
</table>
<hr>
"""

# BLOQUE SERPAPI
    html += incluir_tabla_y_graficos(categorias_serp, "SerpAPI")

    html += "</body></html>"

    with open(nombre_archivo, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[+] Reporte HTML con IA generado en: {nombre_archivo}")
