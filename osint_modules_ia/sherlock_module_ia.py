import os
import re
import subprocess
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from collections import Counter
import matplotlib.pyplot as plt
import requests

# Modelo de embeddings
modelo_ia = SentenceTransformer('all-MiniLM-L6-v2')

# Categorías semánticas base
CATEGORIAS = {
    "Red Social": ["twitter", "instagram", "facebook", "tiktok", "snapchat"],
    "Foro": ["reddit", "foro", "board", "4chan", "stackexchange"],
    "Perfil Profesional": ["linkedin", "github", "gitlab", "dev", "about.me"],
    "Otro": ["blog", "personal", "misc"]
}

def verificar_enlace_contenido(url):
    try:
        r = requests.get(url, timeout=7)
        if r.status_code == 200:
            errores_comunes = [
                "no search results", "user not found", "does not exist",
                "page not found", "not available", "not exist"
            ]
            contenido = r.text.lower()
            if any(e in contenido for e in errores_comunes):
                return False
            return True
        return False
    except Exception:
        return False

# Se coloca la ruta especifica donde se instaló sherlock
def ejecutar_sherlock_ia(username, output_dir):
    print(f"[+] Ejecutando Sherlock con IA para: {username}")
    comando = ["/home/kali/.local/bin/sherlock", username, "--print-found"]

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

        urls = re.findall(r"https?://[^\s]+", salida)
        urls_verificadas = [url for url in urls if verificar_enlace_contenido(url)]
        resultados = [{"url": url, "categoria": "No clasificado"} for url in urls_verificadas]

        if not resultados:
            print("[-] No se encontraron URLs válidas en la salida de Sherlock.")

        resultados_clasificados = clasificar_con_ia(resultados)
        guardar_resultados(username, resultados_clasificados, output_dir)
        generar_grafico_sherlock(resultados_clasificados, username, output_dir)

        return resultados_clasificados

    except Exception as e:
        print("[-] Error al ejecutar Sherlock:", e)
        return []

def clasificar_con_ia(resultados):
    etiquetas = list(CATEGORIAS.keys())
    ejemplos = [" ".join(valores) for valores in CATEGORIAS.values()]
    embeddings_base = modelo_ia.encode(ejemplos)

    for r in resultados:
        emb = modelo_ia.encode([r["url"]])[0]
        sims = cosine_similarity([emb], embeddings_base)[0]
        r["categoria"] = etiquetas[int(np.argmax(sims))]

    return resultados

def guardar_resultados(username, resultados, output_dir):
    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    os.makedirs(output_dir, exist_ok=True)
    archivo = os.path.join(output_dir, f"sherlock_ia_{username}_{fecha}.txt")

    with open(archivo, "w", encoding="utf-8") as f:
        for r in resultados:
            f.write(f"[{r['categoria']}] {r['url']}\n")

    print(f"[+] Resultados de Sherlock + IA guardados en: {archivo}")

def generar_grafico_sherlock(resultados, username, output_dir):
    if not resultados:
        print("[-] No hay datos suficientes para generar gráfico Sherlock.")
        return

    categorias = [r["categoria"] for r in resultados]
    conteo = Counter(categorias)

    if not conteo:
        print("[-] No se encontraron categorías válidas para graficar.")
        return

    etiquetas = list(conteo.keys())
    valores = list(conteo.values())

    safe_name = username.replace("@", "_").replace(".", "_")

    # Gráfico de barras
    plt.figure(figsize=(8, 6))
    plt.bar(etiquetas, valores)
    plt.title(f"Sherlock - Coincidencias por Categoría ({username})")
    plt.xlabel("Categoría")
    plt.ylabel("Cantidad")
    plt.xticks(rotation=30)
    plt.tight_layout()

    ruta_barra = os.path.join(output_dir, f"grafico_sherlock_{safe_name}.png")
    plt.savefig(ruta_barra)
    plt.close()
    print(f"[+] Gráfico de barras de Sherlock guardado en: {ruta_barra}")

    # Gráfico circular (pie)
    plt.figure(figsize=(7, 7))
    plt.pie(valores, labels=etiquetas, autopct='%1.1f%%', startangle=140)
    plt.title(f"Sherlock - Distribución porcentual ({username})")
    plt.axis('equal')

    ruta_pie = os.path.join(output_dir, f"grafico_sherlock_pie_{safe_name}.png")
    plt.savefig(ruta_pie)
    plt.close()
    print(f"[+] Gráfico circular de Sherlock guardado en: {ruta_pie}")
