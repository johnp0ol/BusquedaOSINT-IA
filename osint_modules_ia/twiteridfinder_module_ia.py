from playwright.sync_api import sync_playwright
from datetime import datetime
import re
import time

def calcular_confiabilidad(resultado):
    score = 0

    # 1. Presencia de email (+1)
    if resultado["email"]:
        score += 1

    # 2. Seguidores
    try:
        seguidores = int(resultado["seguidores"].split("/")[-1].replace("follower", "").strip().replace(",", ""))
        if seguidores > 1000:
            score += 2
        elif seguidores > 500:
            score += 1
    except:
        pass

    # 3. Antigüedad de la cuenta (> 5 años) (+1)
    try:
        fecha_str = resultado["fecha_creacion"]
        fecha_obj = datetime.strptime(fecha_str, "%a %b %d %H:%M:%S %z %Y")
        dias_activa = (datetime.now(fecha_obj.tzinfo) - fecha_obj).days
        if dias_activa >= 5 * 365:
            score += 1
        elif dias_activa < 7:
            score -= 1  # Penalizar si es muy reciente
    except:
        pass

    # 4. Descripción no vacía (+1)
    descripcion = resultado.get("descripcion", "").strip()
    if descripcion:
        score += 1

        # 5. Penalización si parece sospechosa (-1)
        patrones_spam = ["free", "bitcoin", "sexo", "ganancias", "work from home", "dinero rápido", r"http[s]?://"]
        if any(re.search(p, descripcion.lower()) for p in patrones_spam):
            score -= 1

    # 6. Clasificación final basada en score total
    if score >= 4:
        return "Alta"
    elif score >= 2:
        return "Media"
    else:
        return "Baja"

def buscar_twitter_id(username):
    resultado = {
        "username": username,
        "id": None,
        "estado": None,
        "descripcion": None,
        "email": None,
        "seguidores": None,
        "fecha_creacion": None,
        "confiabilidad": None,
        "exito": False
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Acceder al sitio
            page.goto("https://twiteridfinder.com", timeout=60000)
            page.wait_for_selector("input#tweetbox2", timeout=15000)
            page.fill("input#tweetbox2", username)
            page.click("button#button_convert")

            # Esperar 10 segundos por carga completa
            time.sleep(10)

            # Obtener datos
            resultado["estado"] = page.inner_text("#js-results-status")
            resultado["id"] = page.inner_text("#js-results-id")
            resultado["username"] = page.inner_text("#js-results-username")
            resultado["descripcion"] = page.inner_text("#js-results-description")
            resultado["email"] = page.inner_text("#js-results-email")
            resultado["seguidores"] = page.inner_text("#js-results-followers")
            resultado["fecha_creacion"] = page.inner_text("#js-results-date")

            # Calcular confiabilidad
            resultado["confiabilidad"] = calcular_confiabilidad(resultado)
            resultado["exito"] = True

            browser.close()
    except Exception as e:
        resultado["error"] = str(e)

    return resultado
