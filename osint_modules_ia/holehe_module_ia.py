import os
import re
import subprocess
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter

modelo_ia = SentenceTransformer("all-MiniLM-L6-v2")

# Categorías para clasificación de servicios
CATEGORIAS = {
    "Red Social": ["facebook", "twitter", "instagram", "tiktok", "linkedin"],
    "Foro": ["reddit", "foro", "disqus", "4chan", "stackexchange"],
    "Tienda o Servicio": ["amazon", "mercadolibre", "paypal", "ebay", "spotify", "netflix"],
    "Otro": ["personal", "juegos", "aplicaciones", "misc"]
}

# Se coloca la ruta especifica donde se instaló holehe, en este caso el servicio está virtualizado
def ejecutar_holehe_ia(correo, output_dir):
    print(f"[+] Ejecutando Holehe con IA para: {correo}")
    comando = ["/home/kali/holehe/venv-holele/bin/holehe", correo] 

    try:
        proceso = subprocess.Popen(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        salida = proceso.communicate()[0]

        # Capturar solo líneas con coincidencias reales, evitar resumen
        lineas = [line for line in salida.splitlines() if line.startswith("[+") and "Email" not in line]
        urls = extraer_servicios(lineas)

        resultados = [{"servicio": url, "categoria": "No clasificado"} for url in urls]
        resultados_clasificados = clasificar_con_ia(resultados)

        guardar_resultados(correo, resultados_clasificados, output_dir)
        generar_grafico_holehe(correo, resultados_clasificados, output_dir)

        return resultados_clasificados

    except Exception as e:
        print(f"[-] Error al ejecutar Holehe: {e}")
        return []

def extraer_servicios(lineas):
    servicios = []
    for l in lineas:
        match = re.search(r"\[\+\]\s*(\S+)", l)
        if match:
            servicios.append(match.group(1))
    return servicios

def clasificar_con_ia(resultados):
    etiquetas = list(CATEGORIAS.keys())
    ejemplos = [" ".join(valores) for valores in CATEGORIAS.values()]
    embeddings_base = modelo_ia.encode(ejemplos)

    for r in resultados:
        emb = modelo_ia.encode([r["servicio"]])[0]
        sims = cosine_similarity([emb], embeddings_base)[0]
        r["categoria"] = etiquetas[int(np.argmax(sims))]

    return resultados

def guardar_resultados(correo, resultados, output_dir):
    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    safe_name = correo.replace("@", "_").replace(".", "_")
    archivo = os.path.join(output_dir, f"holehe_ia_{safe_name}_{fecha}.txt")
    os.makedirs(output_dir, exist_ok=True)

    with open(archivo, "w", encoding="utf-8") as f:
        for r in resultados:
            f.write(f"[{r['categoria']}] {r['servicio']}\n")

    print(f"[+] Resultados de Holehe + IA guardados en: {archivo}")

def generar_grafico_holehe(correo, resultados, output_dir):
    if not resultados:
        print("[-] No hay datos suficientes para generar gráfico Holehe.")
        return

    conteo = Counter([r["categoria"] for r in resultados])
    if not conteo:
        print("[-] No se encontraron categorías válidas para graficar.")
        return

    categorias = list(conteo.keys())
    cantidades = list(conteo.values())
    safe_name = correo.replace("@", "_").replace(".", "_")

    # Gráfico de barras
    plt.figure(figsize=(8, 5))
    plt.bar(categorias, cantidades)
    plt.title(f"Holehe: coincidencias por categoría")
    plt.xlabel("Categoría")
    plt.ylabel("Cantidad de servicios")
    plt.xticks(rotation=45)
    plt.tight_layout()

    nombre_imagen = os.path.join(output_dir, f"grafico_holehe_{safe_name}.png")
    plt.savefig(nombre_imagen)
    plt.close()
    print(f"[+] Gráfico de barras generado en: {nombre_imagen}")

    # Gráfico circular
    plt.figure(figsize=(7, 7))
    plt.pie(cantidades, labels=categorias, autopct='%1.1f%%', startangle=140)
    plt.title(f"Holehe - Distribución porcentual ({correo})")
    plt.axis('equal')

    grafico_pie = os.path.join(output_dir, f"grafico_holehe_pie_{safe_name}.png")
    plt.savefig(grafico_pie)
    plt.close()
    print(f"[+] Gráfico circular generado en: {grafico_pie}")
