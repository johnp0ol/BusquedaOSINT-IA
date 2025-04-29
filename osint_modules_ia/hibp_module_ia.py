import os
import requests
import matplotlib.pyplot as plt
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from collections import Counter
import spacy

# ⚠ Coloca tu API Key válida
API_KEY = "cc1cd7d7a8fe4c47936dfdd31e65fe08"

# Modelos de IA
modelo_ia = SentenceTransformer("all-MiniLM-L6-v2")
nlp_spacy = spacy.load("en_core_web_sm")  # Modelo para entidades nombradas

# Criterios de clasificación semántica
CATEGORIAS = {
    "Alta sensibilidad": ["password", "hash", "token", "credentials", "credit card", "security questions"],
    "Media sensibilidad": ["email", "username", "phone number", "IP", "device info"],
    "Baja sensibilidad": ["location", "gender", "date of birth", "name", "interests"]
}

HEADERS = {
    "hibp-api-key": API_KEY,
    "user-agent": "OSINT-TFM-Script"
}

def ejecutar_hibp_ia(correo, output_dir):
    print(f"[+] Consultando HaveIBeenPwned con IA para: {correo}")
    url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{correo}?truncateResponse=false"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)

        if response.status_code == 200:
            brechas = response.json()
            resultados = procesar_brechas(brechas)
            guardar_resultados(correo, resultados, output_dir)
            generar_grafico(correo, resultados, output_dir)

            # 🔥 Ya no generamos el gráfico de entidades
            # generar_grafico_entidades(correo, resultados, output_dir)

            # 🧹 Eliminamos el gráfico de entidades si existe
            safe_name = correo.replace("@", "_").replace(".", "_")
            ruta_ner = os.path.join(output_dir, f"grafico_entidades_ner_{safe_name}.png")
            if os.path.exists(ruta_ner):
                os.remove(ruta_ner)
                print(f"[-] Gráfico NER eliminado: {ruta_ner}")

            return resultados

        elif response.status_code == 404:
            print("[-] No se encontraron filtraciones para este correo.")
            return []

        elif response.status_code == 401:
            print("[-] Error 401: Verifica tu API KEY.")
            return []

        else:
            print(f"[-] Error inesperado ({response.status_code}): {response.text}")
            return []

    except Exception as e:
        print("[-] Error al consultar HIBP:", e)
        return []

def procesar_brechas(brechas):
    resultados = []
    etiquetas = list(CATEGORIAS.keys())
    ejemplos = [" ".join(valores) for valores in CATEGORIAS.values()]
    embeddings_base = modelo_ia.encode(ejemplos)

    for b in brechas:
        breach_name = b.get("Name")
        fecha = b.get("BreachDate")
        dominio = b.get("Domain")
        descripcion = b.get("Description", "").strip()
        datos_expuestos = ", ".join(b.get("DataClasses", []))

        # Clasificación IA
        emb = modelo_ia.encode([datos_expuestos])[0]
        sims = cosine_similarity([emb], embeddings_base)[0]
        categoria = etiquetas[int(np.argmax(sims))]

        # Extracción de entidades con spaCy
        doc = nlp_spacy(descripcion)
        entidades = [(ent.text, ent.label_) for ent in doc.ents]

        resultados.append({
            "nombre": breach_name,
            "fecha": fecha,
            "dominio": dominio,
            "descripcion": descripcion,
            "datos": datos_expuestos,
            "categoria": categoria,
            "entidades": entidades
        })

    return resultados

def guardar_resultados(correo, resultados, output_dir):
    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    safe_name = correo.replace("@", "_").replace(".", "_")
    archivo = os.path.join(output_dir, f"hibp_ia_{safe_name}_{fecha}.txt")
    os.makedirs(output_dir, exist_ok=True)

    with open(archivo, "w", encoding="utf-8") as f:
        for r in resultados:
            f.write(f"[{r['categoria']}] {r['nombre']} ({r['fecha']}) - {r['dominio']}\n")
            f.write(f"  Datos expuestos: {r['datos']}\n")
            f.write(f"  Descripción: {r['descripcion']}\n")
            if r["entidades"]:
                entidades_texto = ", ".join([f"{e[0]} ({e[1]})" for e in r["entidades"]])
                f.write(f"  Entidades extraídas: {entidades_texto}\n")
            f.write("\n")

    print(f"[+] Resultados de HIBP + IA guardados en: {archivo}")

def generar_grafico(correo, resultados, output_dir):
    if not resultados:
        print("[-] No hay datos suficientes para generar gráfico HIBP.")
        return

    categorias = [r["categoria"] for r in resultados]
    conteo = Counter(categorias)

    if not conteo:
        print("[-] No se encontraron categorías válidas para graficar.")
        return

    etiquetas = list(conteo.keys())
    valores = list(conteo.values())

    safe_name = correo.replace("@", "_").replace(".", "_")
    ruta_grafico = os.path.join(output_dir, f"grafico_hibp_{safe_name}.png")

    # Gráfico de barras
    plt.figure(figsize=(8, 5))
    plt.bar(etiquetas, valores, color="crimson")
    plt.title("Filtraciones HIBP por categoría")
    plt.xlabel("Categoría")
    plt.ylabel("Cantidad")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(ruta_grafico)
    plt.close()

    print(f"[+] Gráfico de HIBP generado en: {ruta_grafico}")

    # Gráfico circular
    ruta_grafico_pie = os.path.join(output_dir, f"grafico_hibp_pie_{safe_name}.png")
    plt.figure(figsize=(7, 7))
    plt.pie(valores, labels=etiquetas, autopct='%1.1f%%', startangle=140)
    plt.title(f"HIBP - Distribución porcentual ({correo})")
    plt.axis('equal')
    plt.savefig(ruta_grafico_pie)
    plt.close()

    print(f"[+] Gráfico circular de HIBP generado en: {ruta_grafico_pie}")
