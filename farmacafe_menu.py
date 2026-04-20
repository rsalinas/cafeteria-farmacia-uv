#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup

def extraure_menu_cafeteria():
    url = "https://www.qrcarta.com/restaurant/burjassot/cafeteria-de-farmacia-uv/3616/?type=menu"
    
    try:
        # 1. Descarregar l'HTML
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 2. Localitzar el contenidor del menú
        menu_div = soup.find('div', class_='menu')
        if not menu_div:
            print("No s'ha trobat el contingut del menú.")
            return

        # 3. Extraure títol i data
        data_menu = menu_div.find('h6').get_text(strip=True) if menu_div.find('h6') else "Sense data"
        print(f"=== {data_menu} ===")

        # 4. Processar seccions (Primers, Segons, Preu)
        # Busquem els títols de les seccions (h4)
        seccions = menu_div.find_all('h4')
        for seccio in seccions:
            nom_seccio = seccio.get_text(strip=True)
            print(f"\n{nom_seccio}:")
            
            # Els plats estan en etiquetes <p class='plato'> immediatament després
            element = seccio.find_next_sibling()
            while element and element.name != 'h4' and 'precio_menu' not in element.get('class', []):
                if element.name == 'p' and 'plato' in element.get('class', []):
                    plat = element.find('b').get_text(strip=True) if element.find('b') else element.get_text(strip=True)
                    print(f"  - {plat}")
                element = element.find_next_sibling()

        # 5. Extraure el preu final
        preu = menu_div.find('p', class_='precio_menu')
        if preu:
            print(f"\nPREU: {preu.get_text(strip=True)}")

        print(f"\nMés informació: {url}")

    except Exception as e:
        print(f"Error en l'extracció: {e}")

if __name__ == "__main__":
    extraure_menu_cafeteria()
