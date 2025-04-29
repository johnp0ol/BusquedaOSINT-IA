import os
import re
import subprocess
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter
import requests

# Cargar modelo IA
modelo_ia = SentenceTransformer('all-MiniLM-L6-v2')

# Categorías semánticas base
CATEGORIAS = {
    "Red Social": ["facebook", "twitter", "instagram", "tiktok", "snapchat"],
    "Foro": ["reddit", "foro", "board", "stackexchange", "4chan"],
    "Perfil Profesional": ["github", "gitlab", "linkedin", "dev.to", "academia.edu"],
    "Otro": ["personal", "blog", "misc", "about.me"]
}

def verificar_enlace_contenido(url):
    try:
        r = requests.get(url, timeout=7)
        if r.status_code == 200:
            errores_comunes = [
                "no search results", "user not found", "does not exist",
                "page not found", "not available", "not exist",
                "no people found", "not registered"
            ]
            contenido = r.text.lower()
            if any(e in contenido for e in errores_comunes):
                return False
            return True
        return False
    except:
        return False

# Se coloca la ruta especifica donde se instaló maigret
def ejecutar_maigret_ia(username, output_dir):
    print(f"[+] Ejecutando Maigret con IA para: {username}")
    
    comando = [
        "/home/kali/.local/bin/maigret",
        username,
        "-a",
        "--no-color",
        "--no-progressbar"
    ]

    try:
        proceso = subprocess.Popen(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        salida = ""
        for linea in proceso.stdout:
            salida += linea

        # Extraer URLs válidas y verificarlas por contenido
        urls = re.findall(r"https?://[^\s]+", salida)
        urls_verificadas = [url for url in urls if verificar_enlace_contenido(url)]
        resultados = [{"url": url, "categoria": "No clasificado"} for url in urls_verificadas]

        if not resultados:
            print("[-] No se encontraron URLs válidas en la salida de Maigret.")

        resultados_clasificados = clasificar_con_ia(resultados)
        guardar_resultados(username, resultados_clasificados, output_dir)

        return resultados_clasificados

    except Exception as e:
        print(f"[-] Error al ejecutar Maigret: {e}")
        return []

def clasificar_con_ia(resultados):
    etiquetas = list(CATEGORIAS.keys())
    ejemplos = [" ".join(v) for v in CATEGORIAS.values()]
    embeddings_base = modelo_ia.encode(ejemplos)

    for r in resultados:
        emb = modelo_ia.encode([r["url"]])[0]
        sims = cosine_similarity([emb], embeddings_base)[0]
        r["categoria"] = etiquetas[int(np.argmax(sims))]

    return resultados

def guardar_resultados(username, resultados, output_dir):
    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    os.makedirs(output_dir, exist_ok=True)

    archivo = os.path.join(output_dir, f"maigret_ia_{username}_{fecha}.txt")
    with open(archivo, "w", encoding="utf-8") as f:
        for r in resultados:
            f.write(f"[{r['categoria']}] {r['url']}\n")

    print(f"[+] Resultados de Maigret + IA guardados en: {archivo}")

    generar_grafico_maigret(username, resultados, output_dir)

def generar_grafico_maigret(username, resultados, output_dir):
    if not resultados:
        print("[-] No hay datos suficientes para generar gráfico Maigret.")
        return

    conteo = Counter(r["categoria"] for r in resultados)

    if not conteo:
        print("[-] No se encontraron categorías válidas para graficar.")
        return

    categorias = list(conteo.keys())
    cantidades = list(conteo.values())

    safe_name = username.replace("@", "_").replace(".", "_")

    # Gráfico de barras
    plt.figure(figsize=(8, 5))
    plt.bar(categorias, cantidades)
    plt.title("Distribución de coincidencias por categoría (Maigret)")
    plt.ylabel("Cantidad de perfiles")
    plt.xticks(rotation=45)
    plt.tight_layout()

    grafico_barra = os.path.join(output_dir, f"grafico_maigret_{safe_name}.png")
    plt.savefig(grafico_barra)
    plt.close()
    print(f"[+] Gráfico de Maigret guardado en: {grafico_barra}")

    # Gráfico circular
    plt.figure(figsize=(7, 7))
    plt.pie(cantidades, labels=categorias, autopct='%1.1f%%', startangle=140)
    plt.title(f"Maigret - Distribución porcentual ({username})")
    plt.axis('equal')

    grafico_pie = os.path.join(output_dir, f"grafico_maigret_pie_{safe_name}.png")
    plt.savefig(grafico_pie)
    plt.close()
    print(f"[+] Gráfico circular de Maigret guardado en: {grafico_pie}")
