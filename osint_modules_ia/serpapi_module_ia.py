import os
from datetime import datetime
from serpapi import GoogleSearch
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
import spacy
import requests

API_KEY = "8c12568bfccefd58504a6c83b4d1bc951e6eb3d56db6cdf8cfb6e2d2087778e0"
modelo_ia = SentenceTransformer('all-MiniLM-L6-v2')
nlp_spacy = spacy.load("en_core_web_sm")

CATEGORIAS = {
    "Red Social": ["twitter", "linkedin", "instagram", "facebook", "tiktok"],
    "Foro": ["reddit", "4chan", "foro", "disqus", "stackexchange"],
    "Perfil Público": ["github", "about.me", "gravatar", "site profile"],
    "Filtración de datos": ["pastebin", "leak", "dump", "breach", "hacked"],
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
    except:
        return False

def buscar_serpapi_ia(query, output_dir):
    print(f"[+] Ejecutando búsqueda inteligente SerpAPI+IA para: {query}")
    resultados = []

    query_entre_comillas = f'intext:"{query}"'

    google_params = {
        "q": query_entre_comillas,
        "hl": "es",
        "gl": "es",
        "api_key": API_KEY
    }
    resultados += obtener_resultados("Google", GoogleSearch(google_params), query)

    yt_params = {
        "engine": "youtube",
        "search_query": f'"{query}"',
        "api_key": API_KEY
    }
    resultados += obtener_resultados("YouTube", GoogleSearch(yt_params), query)

    resultados_clasificados = clasificar_resultados_con_ia(resultados)
    guardar_resultados(query, resultados_clasificados, output_dir)
    generar_grafico(query, resultados_clasificados, output_dir)

    return resultados_clasificados

def obtener_resultados(fuente, busqueda, query_original):
    try:
        results = busqueda.get_dict()
        resultados = []
        key = "organic_results" if fuente == "Google" else "video_results"

        for r in results.get(key, []):
            titulo = r.get("title", "")
            link = r.get("link", "") or r.get("url", "")
            snippet = r.get("snippet", "") or r.get("description", "")

            contenido_completo = (titulo + snippet + link).lower()
            if query_original.lower() not in contenido_completo:
                continue

            if not link or not verificar_enlace_contenido(link):
                continue

            doc = nlp_spacy(snippet)
            entidades = [(ent.text, ent.label_) for ent in doc.ents]

            resultados.append({
                "source": fuente,
                "title": titulo,
                "link": link,
                "snippet": snippet,
                "categoria": "No clasificado",
                "entidades": entidades
            })

        return resultados
    except Exception as e:
        print(f"[-] Error al obtener resultados de {fuente}:", e)
        return []

def clasificar_resultados_con_ia(resultados):
    etiquetas = list(CATEGORIAS.keys())
    ejemplos = [" ".join(valores) for valores in CATEGORIAS.values()]
    embeddings_base = modelo_ia.encode(ejemplos)

    for r in resultados:
        texto = f"{r['title']} {r['snippet']} {r['link']}"
        emb = modelo_ia.encode([texto])[0]
        sims = cosine_similarity([emb], embeddings_base)[0]
        idx = int(np.argmax(sims))
        r["categoria"] = etiquetas[idx]

    return resultados

def guardar_resultados(query, resultados, output_dir):
    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    os.makedirs(output_dir, exist_ok=True)
    safe_query = query.replace("@", "_").replace(".", "_")
    nombre_archivo = os.path.join(output_dir, f"serpapi_ia_{safe_query}_{fecha}.txt")

    with open(nombre_archivo, "w", encoding="utf-8") as f:
        for r in resultados:
            f.write(f"[{r['source']}][{r['categoria']}] {r['title']}\n{r['link']}\n{r['snippet']}\n")
            if r.get("entidades"):
                entidades_texto = ", ".join([f"{e[0]} ({e[1]})" for e in r["entidades"]])
                f.write(f"Entidades extraídas: {entidades_texto}\n")
            f.write("\n")

    print(f"[+] Resultados IA guardados en: {nombre_archivo}")

def generar_grafico(query, resultados, output_dir):
    categorias = [r["categoria"] for r in resultados]
    conteo = Counter(categorias)

    if not conteo:
        print("[-] No hay datos suficientes para generar gráfico SerpAPI.")
        return

    etiquetas = list(conteo.keys())
    valores = list(conteo.values())

    plt.figure(figsize=(8, 6))
    plt.bar(etiquetas, valores)
    plt.title("SERPAPI - Resultados por Categoría (IA)")
    plt.xlabel("Categoría")
    plt.ylabel("Cantidad")
    plt.xticks(rotation=25)
    plt.tight_layout()

    safe_query = query.replace("@", "_").replace(".", "_")
    grafico_path = os.path.join(output_dir, f"grafico_serpapi_{safe_query}.png")
    plt.savefig(grafico_path)
    plt.close()

    print(f"[+] Gráfico de barras generado: {grafico_path}")

    # Gráfico circular
    grafico_pie_path = os.path.join(output_dir, f"grafico_serpapi_pie_{safe_query}.png")
    plt.figure(figsize=(7, 7))
    plt.pie(valores, labels=etiquetas, autopct='%1.1f%%', startangle=140)
    plt.title(f"SerpAPI - Distribución porcentual ({query})")
    plt.axis('equal')
    plt.savefig(grafico_pie_path)
    plt.close()

    print(f"[+] Gráfico circular generado: {grafico_pie_path}")
