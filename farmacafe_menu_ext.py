#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import re

def extraer_menu_qrcarta(url):
    """
    Extrae el menú diario de una página de QRCarta
    
    Args:
        url: URL completa de la página (ej: https://www.qrcarta.com/restaurant/...)
    
    Returns:
        dict: Diccionario con la información del menú
    """
    
    # Headers para evitar bloqueos
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Obtener la página
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parsear HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar el div del menú
        menu_div = soup.find('div', class_='menu')
        
        if not menu_div:
            return {"error": "No se encontró el menú en la página"}
        
        # Extraer información del restaurante
        info_restaurante = {
            'nombre': None,
            'direccion': None,
            'telefono': None
        }
        
        # Extraer nombre del restaurante
        h1 = soup.find('h1')
        if h1:
            info_restaurante['nombre'] = h1.get_text(strip=True)
        
        # Extraer dirección y teléfono del footer
        copyright_div = soup.find('div', class_='copyright')
        if copyright_div:
            texto = copyright_div.get_text()
            # Buscar dirección
            direccion_match = re.search(r'([^,]+,\s*\d+\s*-\s*[^<]+)', texto)
            if direccion_match:
                info_restaurante['direccion'] = direccion_match.group(1).strip()
            
            # Buscar teléfono
            telefono_match = re.search(r'(\d{3}\s*\d{2}\s*\d{2}\s*\d{2})', texto)
            if telefono_match:
                info_restaurante['telefono'] = telefono_match.group(1)
        
        # Extraer fecha del menú
        fecha = None
        fecha_tag = menu_div.find('h6')
        if fecha_tag:
            fecha_texto = fecha_tag.get_text(strip=True)
            fecha_match = re.search(r'(\d{1,2}-\d{1,2}-\d{4})', fecha_texto)
            if fecha_match:
                fecha = fecha_match.group(1)
        
        # Extraer platos por categoría
        menu_data = {
            'restaurante': info_restaurante,
            'fecha': fecha,
            'categorias': [],
            'precio_por_persona': None,
            'incluye': None,
            'leyenda_alergenos': []
        }
        
        # Encontrar todas las categorías (h4 son los títulos de categorías)
        categorias = menu_div.find_all('h4')
        
        for categoria in categorias:
            nombre_categoria = categoria.get_text(strip=True)
            platos = []
            
            # Los platos están en los p con clase 'plato' que siguen a cada h4
            current = categoria.find_next_sibling()
            
            while current and current.name != 'h4':
                if current.name == 'p' and current.get('class') and 'plato' in current.get('class'):
                    # Es un plato
                    nombre_plato = current.find('b')
                    if nombre_plato:
                        nombre = nombre_plato.get_text(strip=True)
                        
                        # Buscar alergenos en el siguiente p
                        alergenos = []
                        next_p = current.find_next_sibling('p')
                        if next_p and next_p.find_all('img'):
                            for img in next_p.find_all('img'):
                                titulo = img.get('title', '')
                                if titulo:
                                    alergenos.append(titulo)
                        
                        platos.append({
                            'nombre': nombre,
                            'alergenos': alergenos
                        })
                
                current = current.find_next_sibling()
            
            if platos:
                menu_data['categorias'].append({
                    'nombre': nombre_categoria,
                    'platos': platos
                })
        
        # Extraer precio
        precio_tag = menu_div.find('p', class_='precio_menu')
        if precio_tag:
            precio_texto = precio_tag.get_text(strip=True)
            menu_data['precio_por_persona'] = precio_texto
        
        # Extraer información de inclusión (postre, pan, bebida)
        incluye_p = menu_div.find_all('p')
        for p in incluye_p:
            if 'Postre' in p.get_text() or 'pan' in p.get_text() or 'bebida' in p.get_text():
                texto = p.get_text(strip=True)
                if texto and texto != 'hr/':
                    menu_data['incluye'] = texto
                break
        
        # Extraer leyenda de alergenos
        leyenda_div = menu_div.find('div', class_='leyenda')
        if leyenda_div:
            spans = leyenda_div.find_all('span')
            for span in spans:
                texto = span.get_text(strip=True)
                if texto:
                    menu_data['leyenda_alergenos'].append(texto)
        
        return menu_data
        
    except requests.RequestException as e:
        return {"error": f"Error al obtener la página: {e}"}
    except Exception as e:
        return {"error": f"Error al procesar el HTML: {e}"}

def formatear_menu(menu_data):
    """Formatea el menú extraído para mostrarlo bonito"""
    
    if 'error' in menu_data:
        return f"❌ Error: {menu_data['error']}"
    
    resultado = []
    
    # Información del restaurante
    resultado.append("=" * 60)
    if menu_data['restaurante']['nombre']:
        resultado.append(f"🍽️  {menu_data['restaurante']['nombre']}")
    if menu_data['restaurante']['direccion']:
        resultado.append(f"📍 {menu_data['restaurante']['direccion']}")
    if menu_data['restaurante']['telefono']:
        resultado.append(f"📞 {menu_data['restaurante']['telefono']}")
    
    resultado.append("=" * 60)
    
    # Fecha
    if menu_data['fecha']:
        resultado.append(f"\n📅 Menú del día: {menu_data['fecha']}\n")
    
    # Categorías y platos
    for categoria in menu_data['categorias']:
        resultado.append(f"\n🥘 {categoria['nombre'].upper()}")
        resultado.append("-" * 40)
        for plato in categoria['platos']:
            alergenos_str = f" [{' • '.join(plato['alergenos'])}]" if plato['alergenos'] else ""
            resultado.append(f"  • {plato['nombre']}{alergenos_str}")
    
    # Precio
    if menu_data['precio_por_persona']:
        resultado.append(f"\n💰 {menu_data['precio_por_persona']}")
    
    # Incluye
    if menu_data['incluye']:
        resultado.append(f"📌 {menu_data['incluye']}")
    
    # Leyenda de alergenos
    if menu_data['leyenda_alergenos']:
        resultado.append("\n🔍 Leyenda de alérgenos:")
        for item in menu_data['leyenda_alergenos']:
            resultado.append(f"   {item}")
    
    resultado.append("\n" + "=" * 60)
    
    return "\n".join(resultado)

# Ejemplo de uso
if __name__ == "__main__":
    url = "https://www.qrcarta.com/restaurant/burjassot/cafeteria-de-farmacia-uv/3616/?type=menu"
    
    print("🔍 Extrayendo menú...\n")
    menu = extraer_menu_qrcarta(url)
    
    if 'error' not in menu:
        print(formatear_menu(menu))
        
        # También puedes acceder a los datos de forma estructurada:
        print("\n\n📊 DATOS ESTRUCTURADOS:")
        print(f"Restaurante: {menu['restaurante']['nombre']}")
        print(f"Fecha: {menu['fecha']}")
        print(f"Número de categorías: {len(menu['categorias'])}")
        for cat in menu['categorias']:
            print(f"  - {cat['nombre']}: {len(cat['platos'])} platos")
    else:
        print(formatear_menu(menu))