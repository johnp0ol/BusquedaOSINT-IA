# BusquedaOSINT_TFM_IA.py
print("\nCargando scripts... por favor espera...\n")
import os
from datetime import datetime
from osint_modules_ia import (
    serpapi_module_ia,
    sherlock_module_ia,
    maigret_module_ia,
    holehe_module_ia,
    hibp_module_ia,
    twiteridfinder_module_ia
)
from generador_reporte_ia import generar_html_ia

def crear_directorio_resultados(objetivo):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    safe_objetivo = objetivo.replace("@", "_").replace(".", "_")
    ruta = f"resultados_ia/{safe_objetivo}_{timestamp}"
    os.makedirs(ruta, exist_ok=True)
    return ruta

os.system('clear')

def main():
    print("\n=== MODELO OSINT CON IA - TFM ===\n")
    objetivo = input("Introduce un correo o nombre de usuario: ").strip()

    # Crea carpeta unica para cada busqueda
    ruta_resultados = crear_directorio_resultados(objetivo)

    resultado_serpapi_ia = []
    resultado_sherlock_ia = []
    resultado_maigret_ia = []
    resultado_holehe_ia = []
    resultado_hibp_ia = []
    resultado_twitterid = None

    if "@" in objetivo:
        print("\n[1] Holehe + IA") 
        resultado_holehe_ia = holehe_module_ia.ejecutar_holehe_ia(objetivo, ruta_resultados)

        print("\n[2] HIBP + IA") 
        resultado_hibp_ia = hibp_module_ia.ejecutar_hibp_ia(objetivo, ruta_resultados)

        print("\n[3] SerpAPI (Correo) + IA") 
        resultado_serpapi_ia = serpapi_module_ia.buscar_serpapi_ia(objetivo, ruta_resultados)

    else:
        print("\n[1] Maigret + IA") 
        resultado_maigret_ia = maigret_module_ia.ejecutar_maigret_ia(objetivo, ruta_resultados)

        print("\n[2] Sherlock + IA") 
        resultado_sherlock_ia = sherlock_module_ia.ejecutar_sherlock_ia(objetivo, ruta_resultados)

        print("\n[3] SerpAPI (Username) + IA") 
        resultado_serpapi_ia = serpapi_module_ia.buscar_serpapi_ia(objetivo, ruta_resultados)

        print("\n[4] Twitter ID Finder") 
        resultado_twitterid = twiteridfinder_module_ia.buscar_twitter_id(objetivo)

        if resultado_twitterid and resultado_twitterid.get("exito"):
            print(f"✔ Twitter ID: {resultado_twitterid.get('id')}")
        else:
            print("✖ No se pudo obtener el Twitter ID.")

    # Genera reporte HTML con todos los resultados
    generar_html_ia(
        email=objetivo,
        serpapi_data=resultado_serpapi_ia,
        sherlock_data=resultado_sherlock_ia,
        maigret_data=resultado_maigret_ia,
        holehe_data=resultado_holehe_ia,
        hibp_data=resultado_hibp_ia,
        output_dir=ruta_resultados,
        twitter_data=resultado_twitterid
    )

if __name__ == "__main__":
    main()
