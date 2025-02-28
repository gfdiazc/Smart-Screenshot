import streamlit as st
import os
import time
import zipfile
import re
from playwright.sync_api import sync_playwright
import requests
import json
import random
from PIL import Image
import pandas as pd
import tempfile
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def get_proxy():
    try:
        response = requests.get(
            'https://proxylist.geonode.com/api/proxy-list?limit=100&page=1&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps&anonymityLevel=elite&anonymityLevel=anonymous',
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            proxies = [f"{proxy['ip']}:{proxy['port']}" for proxy in data['data'] 
                      if proxy.get('protocols', []) and 'https' in proxy['protocols']]
            return random.choice(proxies) if proxies else None
    except (requests.RequestException, json.JSONDecodeError, KeyError, IndexError):
        return None
    return None

def find_chromium_executable():
    """Busca el ejecutable de Chromium en diferentes ubicaciones comunes"""
    possible_paths = [
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/usr/bin/chrome",
        "/snap/bin/chromium",
        "/usr/lib/chromium/chromium",
        "/usr/lib/chromium-browser/chromium-browser"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

def setup_browser(playwright, device_profile="desktop", custom_width=None, custom_height=None):
    """Configura y retorna una instancia del navegador con manejo de errores mejorado"""
    # Configuración del navegador
    browser_args = []
    proxy = get_proxy()
    
    # Buscar el ejecutable de Chromium
    chromium_path = find_chromium_executable()
    if not chromium_path:
        st.error("No se encontró el ejecutable de Chromium en ninguna ubicación conocida")
        raise Exception("Chromium executable not found")
    
    # Configuración específica para el navegador
    launch_options = {
        "headless": True,
        "executable_path": chromium_path,
        "args": [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-accelerated-2d-canvas",
            "--disable-gpu",
            "--window-size=1920,1080",
        ]
    }
    
    # Intentar primero con proxy si está disponible
    try:
        if proxy:
            launch_options["args"].append(f'--proxy-server={proxy}')
            browser = playwright.chromium.launch(**launch_options)
        else:
            browser = playwright.chromium.launch(**launch_options)
    except Exception as e:
        st.error(f"Error launching browser: {str(e)}")
        # Si falla con proxy, intentar sin proxy y sin executable_path
        try:
            # Intentar sin especificar executable_path
            del launch_options["executable_path"]
            browser = playwright.chromium.launch(**launch_options)
        except Exception as e:
            st.error(f"Error launching browser without executable path: {str(e)}")
            raise e
    
    # Configuración del contexto según el dispositivo
    context_settings = {}
    
    if device_profile == "mobile":
        context_settings = {
            "viewport": {"width": 375, "height": 812},
            "device_scale_factor": 2,
            "is_mobile": True,
            "has_touch": True
        }
    elif device_profile == "tablet":
        context_settings = {
            "viewport": {"width": 768, "height": 1024},
            "device_scale_factor": 2,
            "is_mobile": True,
            "has_touch": True
        }
    elif device_profile == "custom" and custom_width and custom_height:
        context_settings = {
            "viewport": {"width": custom_width, "height": custom_height},
            "device_scale_factor": 1
        }
    else:  # desktop
        context_settings = {
            "viewport": {"width": 1920, "height": 1080},
            "device_scale_factor": 1
        }
    
    # Crear contexto con configuraciones y timeouts más largos
    context = browser.new_context(**context_settings)
    context.set_default_timeout(30000)  # 30 segundos
    context.set_default_navigation_timeout(30000)  # 30 segundos
    
    return browser, context

def get_loading_message():
    """Retorna un mensaje aleatorio divertido durante la carga"""
    messages = [
        "🎨 Making your screenshots pixel-perfect...",
        "🚀 Zooming through the internet...",
        "🎭 Dealing with those pesky pop-ups...",
        "🍪 Handling cookies (the digital ones)...",
        "📱 Teaching your website to pose...",
        "🎯 Capturing the perfect shot...",
        "🎪 Juggling with different screen sizes...",
        "🎮 Playing hide and seek with pop-ups...",
        "🎭 Preparing the website for its photoshoot...",
        "🌈 Collecting all the pixels...",
        "🎨 Mixing the perfect pixel palette...",
        "🎯 Calibrating the screenshot sensors..."
    ]
    return random.choice(messages)

def capture_screenshot(url, device_profile="desktop", custom_width=None, custom_height=None):
    """Captura screenshots con manejo mejorado de errores y reintentos"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            with sync_playwright() as playwright:
                browser = None
                temp_dir = tempfile.mkdtemp()
                safe_filename = sanitize_filename(url)
                screenshot_path = os.path.join(temp_dir, f"{safe_filename}_{device_profile}.png")
                
                try:
                    browser, context = setup_browser(playwright, device_profile, custom_width, custom_height)
                    page = context.new_page()
                    
                    # Navegar a la página con timeout extendido
                    page.goto(url, wait_until="networkidle", timeout=30000)
                    
                    # Esperar a que la página cargue completamente
                    page.wait_for_load_state("domcontentloaded", timeout=30000)
                    page.wait_for_load_state("networkidle", timeout=30000)
                    
                    # Intentar cerrar pop-ups o cookies si existen
                    try:
                        selectors = [
                            "text=Accept",
                            "text=Aceptar",
                            "[aria-label*='cookie' i] button",
                            "[id*='cookie' i] button",
                            "[class*='cookie' i] button",
                            "button:has-text('Accept')",
                            "button:has-text('Aceptar')"
                        ]
                        
                        for selector in selectors:
                            try:
                                if page.locator(selector).count() > 0:
                                    page.locator(selector).first.click(timeout=2000)
                                    page.wait_for_timeout(200)
                            except:
                                continue
                    except:
                        pass
    
                    # Scroll suave por la página para cargar contenido lazy
                    page.evaluate("""
                        window.scrollTo(0, 0);
                        new Promise((resolve) => {
                            let totalHeight = 0;
                            const distance = 100;
                            const timer = setInterval(() => {
                                const scrollHeight = document.body.scrollHeight;
                                window.scrollBy(0, distance);
                                totalHeight += distance;
                                
                                if(totalHeight >= scrollHeight){
                                    clearInterval(timer);
                                    resolve();
                                }
                            }, 100);
                        });
                    """)
                    
                    # Esperar un momento para que se cargue todo
                    page.wait_for_timeout(2000)
                    
                    # Ocultar elementos flotantes
                    page.evaluate("""
                        document.querySelectorAll('*').forEach(el => {
                            const style = window.getComputedStyle(el);
                            if (style.position === 'fixed' || style.position === 'sticky') {
                                el.style.display = 'none';
                            }
                        });
                    """)
                    
                    # Tomar screenshot de toda la página
                    page.screenshot(path=screenshot_path, full_page=True)
                    
                    # Verificar que se guardó correctamente
                    if not os.path.exists(screenshot_path):
                        raise Exception("Screenshot was not saved")
                        
                    # Verificar que la imagen es válida
                    img = Image.open(screenshot_path)
                    img.verify()
                    
                    # Verificar que la imagen no está en blanco
                    img = Image.open(screenshot_path)
                    extrema = img.convert("L").getextrema()
                    if extrema[0] == extrema[1]:  # Si min y max son iguales, la imagen está en blanco
                        raise Exception("Captured image is blank")
                    
                    return screenshot_path
                except Exception as e:
                    st.warning(f"Error en intento {retry_count + 1} de {max_retries}: {str(e)}")
                    retry_count += 1
                    if retry_count == max_retries:
                        st.error(f"No se pudo capturar la screenshot después de {max_retries} intentos")
                    continue
                finally:
                    if browser:
                        browser.close()
                        
        except Exception as e:
            st.error(f"Error crítico: {str(e)}")
            return None
    
    return None

def extract_urls(url):
    """Extrae las URLs principales de una página web usando Playwright"""
    try:
        with sync_playwright() as playwright:
            browser = None
            urls = set()
            try:
                browser, context = setup_browser(playwright)
                page = context.new_page()
                
                # Navegar a la página y esperar a que cargue completamente
                page.goto(url, wait_until="networkidle")
                page.wait_for_load_state("domcontentloaded")
                page.wait_for_load_state("networkidle")
                
                # Obtener el dominio base
                base_domain = urlparse(url).netloc
                
                # Extraer todos los enlaces usando JavaScript
                links = page.evaluate("""
                    Array.from(document.querySelectorAll('a[href]')).map(a => {
                        return {
                            href: a.href,
                            isVisible: window.getComputedStyle(a).display !== 'none' && a.offsetParent !== null
                        }
                    });
                """)
                
                # Filtrar y procesar los enlaces
                for link in links:
                    if not link['href'] or not link['isVisible']:
                        continue
                        
                    try:
                        parsed_url = urlparse(link['href'])
                        # Solo incluir URLs del mismo dominio y con protocolo http/https
                        if (parsed_url.netloc == base_domain and 
                            parsed_url.scheme in ['http', 'https']):
                            # Limpiar la URL (eliminar fragmentos y parámetros)
                            clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                            if clean_url != url:  # Excluir la URL original
                                urls.add(clean_url)
                    except:
                        continue
                
                # Scroll para encontrar más enlaces
                page.evaluate("""
                    window.scrollTo(0, 0);
                    new Promise((resolve) => {
                        let totalHeight = 0;
                        const distance = 100;
                        const timer = setInterval(() => {
                            const scrollHeight = document.body.scrollHeight;
                            window.scrollBy(0, distance);
                            totalHeight += distance;
                            
                            if(totalHeight >= scrollHeight){
                                clearInterval(timer);
                                resolve();
                            }
                        }, 100);
                    });
                """)
                
                # Esperar un momento y buscar más enlaces
                page.wait_for_timeout(1000)
                
                # Extraer enlaces adicionales que puedan haber aparecido
                additional_links = page.evaluate("""
                    Array.from(document.querySelectorAll('a[href]')).map(a => {
                        return {
                            href: a.href,
                            isVisible: window.getComputedStyle(a).display !== 'none' && a.offsetParent !== null
                        }
                    });
                """)
                
                # Procesar los enlaces adicionales
                for link in additional_links:
                    if not link['href'] or not link['isVisible']:
                        continue
                        
                    try:
                        parsed_url = urlparse(link['href'])
                        if (parsed_url.netloc == base_domain and 
                            parsed_url.scheme in ['http', 'https']):
                            clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                            if clean_url != url:
                                urls.add(clean_url)
                    except:
                        continue
                
                return sorted(list(urls))
                
            except Exception as e:
                st.warning(f"Error extracting URLs: {str(e)}")
                return []
                
            finally:
                if browser:
                    browser.close()
                    
    except Exception as e:
        st.error(f"Critical error: {str(e)}")
        return []

def sanitize_filename(url):
    """Sanitiza una URL para usarla como nombre de archivo"""
    # Eliminar el protocolo (http:// o https://)
    url = re.sub(r'^https?://', '', url)
    # Eliminar caracteres no válidos para nombres de archivo
    url = re.sub(r'[<>:"/\\|?*]', '_', url)
    # Limitar la longitud del nombre del archivo
    return url[:50]

def main():
    # Parámetro para controlar el ancho máximo (se puede cambiar según necesidades)
    max_width = 800
    
    # Ajustar ancho de la aplicación para landing page
    st.markdown(f"""
    <style>
    /* Contenedor principal */
    .reportview-container .main .block-container {{
        max-width: {max_width}px;
        padding-top: 0.5rem;
        padding-bottom: 0.5rem;
        margin: 0 auto;
    }}
    
    /* Aplicación completa */
    .stApp {{
        max-width: 100%;
        display: flex;
        justify-content: center;
    }}
    
    /* Contenedor principal de Streamlit */
    .main > div:first-child {{
        max-width: {max_width}px !important;
        margin: 0 auto !important;
        padding: 0 1rem !important;
    }}
    
    /* Centrar todos los elementos */
    .element-container, 
    .stMarkdown,
    .stButton,
    .stTextArea,
    [data-testid="stVerticalBlock"],
    [data-testid="stHorizontalBlock"],
    .stMetric {{
        max-width: {max_width}px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }}
    
    /* Expanders y sus contenedores */
    .streamlit-expanderHeader,
    .stExpander,
    [data-testid="stExpander"] {{
        max-width: {max_width}px !important;
        margin: 0 auto !important;
        width: 100% !important;
    }}
    
    /* Contenedor de imágenes */
    .stImage {{
        max-width: {max_width}px !important;
        margin: 0 auto !important;
        width: 100% !important;
    }}
    
    /* Imágenes dentro de los resultados */
    .stImage img {{
        max-width: {max_width}px !important;
        width: 100% !important;
        margin: 0 auto !important;
        display: block !important;
    }}
    
    /* Pestañas y sus contenedores */
    .stTabs [data-baseweb="tab-list"],
    .stTabs [data-baseweb="tab-panel"] {{
        max-width: {max_width}px !important;
        margin: 0 auto !important;
        width: 100% !important;
    }}
    
    /* Contenido dentro de los expanders */
    [data-testid="stExpander"] > div {{
        width: 100% !important;
        max-width: {max_width}px !important;
    }}
    
    /* Encabezados */
    .st-emotion-cache-18ni7ap h1, 
    .st-emotion-cache-18ni7ap h2, 
    .st-emotion-cache-18ni7ap h3, 
    .st-emotion-cache-18ni7ap h4, 
    .st-emotion-cache-18ni7ap h5, 
    .st-emotion-cache-18ni7ap h6 {{
        font-size: 1.1rem;
        margin-top: 0.4rem;
        margin-bottom: 0.4rem;
        font-weight: 600;
        text-align: center;
    }}
    
    /* Estilos base para todos los botones */
    .stButton button {{
        border-radius: 6px;
        min-height: 2.5rem;
        padding: 0.5rem 1rem;
        font-size: 0.95rem;
        margin-top: 0.3rem;
        margin-bottom: 0.3rem;
        touch-action: manipulation;
        width: 100%;
        max-width: {max_width}px;
        margin-left: auto;
        margin-right: auto;
    }}
    
    /* Estilo específico para el botón de captura */
    [data-testid="baseButton-primary"] {{
        background-color: #4CAF50 !important;
        color: white !important;
        font-size: 20px !important;
        font-weight: bold !important;
        height: 3.5em !important;
        border-radius: 16px !important;
        border: none !important;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15) !important;
        margin-top: 15px !important;
        margin-bottom: 15px !important;
        animation: pulse 2s infinite;
        width: 100%;
        max-width: {max_width}px;
        margin-left: auto;
        margin-right: auto;
    }}
    
    /* Botones de eliminar URL */
    button[key^="delete_"] {{
        background-color: #D87093 !important;
        color: white !important;
        border: none !important;
        min-width: 40px !important;
        min-height: 36px !important;
    }}
    
    /* Botones de descarga */
    button[key^="dl_"] {{
        background-color: #4CAF50 !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
        width: 100% !important;
        margin: 0.5rem auto !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    }}
    
    /* Botón de descarga ZIP */
    button[key="dl_all"] {{
        background-color: #4CAF50 !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        padding: 0.75rem 1.5rem !important;
        margin: 1rem auto !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        max-width: 400px !important;
        display: block !important;
    }}
    
    /* Efectos hover */
    [data-testid="baseButton-primary"]:hover {{
        background-color: #45a049 !important;
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2) !important;
    }}
    
    button[key^="delete_"]:hover {{
        background-color: #C76085 !important;
    }}
    
    button[key^="dl_"]:hover {{
        background-color: #45a049 !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15) !important;
    }}
    
    button[key="dl_all"]:hover {{
        background-color: #45a049 !important;
        box-shadow: 0 6px 10px rgba(0, 0, 0, 0.2) !important;
        transform: translateY(-1px);
    }}
    
    /* Animación de pulso */
    @keyframes pulse {{
        0% {{ box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.4); }}
        70% {{ box-shadow: 0 0 0 10px rgba(76, 175, 80, 0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(76, 175, 80, 0); }}
    }}
    
    /* Asegurar que los contenedores de resultados mantengan el ancho */
    [data-testid="stVerticalBlock"] {{
        max-width: {max_width}px !important;
        margin: 0 auto !important;
        width: 100% !important;
    }}
    
    /* Contenedores de columnas */
    [data-testid="column"] {{
        width: 100% !important;
        max-width: {max_width}px !important;
        margin: 0 auto !important;
    }}
    
    /* Centrar el área de texto */
    .stTextArea textarea {{
        width: 100% !important;
        max-width: {max_width}px !important;
        margin: 0 auto !important;
    }}
    
    /* Centrar los selectores múltiples */
    .stMultiSelect {{
        max-width: {max_width}px !important;
        margin: 0 auto !important;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Inicializar session_state
    if 'temp_dir' not in st.session_state:
        st.session_state.temp_dir = None
    if 'screenshot_paths' not in st.session_state:
        st.session_state.screenshot_paths = []
    if 'extracted_urls' not in st.session_state:
        st.session_state.extracted_urls = []
    if 'selected_urls' not in st.session_state:
        st.session_state.selected_urls = []
    if 'selected_urls_set' not in st.session_state:
        st.session_state.selected_urls_set = set()
    if 'manual_urls' not in st.session_state:
        st.session_state.manual_urls = set()
    if 'manual_urls_input' not in st.session_state:
        st.session_state.manual_urls_input = ""
    if 'url_selector' not in st.session_state:
        st.session_state.url_selector = []
    
    # Estilos adicionales para mejorar la experiencia en tablets
    st.markdown("""
    <style>
    /* Mejorar multiselect para tablets */
    .stMultiSelect span[data-baseweb="tag"] {
        height: 28px;
        padding: 5px 8px;
        margin: 4px 4px 4px 0;
    }
    .stMultiSelect span[role="option"] {
        padding: 10px 8px;
        font-size: 0.95rem;
    }
    /* Iconos más grandes para mejor visibilidad en tablet */
    .stMarkdown h3 svg, .stMarkdown h4 svg {
        vertical-align: middle;
        margin-right: 0.5rem;
        font-size: 1.2rem;
    }
    /* Mejorar botones de eliminar en lista de URLs */
    button.stButton[kind="secondary"] {
        min-width: 40px;
        height: 40px;
    }
    /* Mejorar contraste de métricas */
    [data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        color: #2E7D32;
    }
    /* Mejorar campos de texto */
    [data-testid="stTextArea"] {
        font-size: 16px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Inicializar variables que se usarán más adelante
    devices = []
    custom_width = None
    custom_height = None
    
    # URL Input Section
    st.markdown("""
    <style>
    /* Añadir espacio al inicio de la página */
    h3:first-of-type {
        margin-top: 1rem !important;
        padding-top: 1rem !important;
    }
    </style>
    
    ### 🌐 Step 1: Add URLs to Capture
    Enter the URLs you want to capture screenshots of.
    """, unsafe_allow_html=True)
    
    # Campo de texto para ingresar URLs manualmente (ahora acepta múltiples líneas)
    manual_urls_input = st.text_area(
        "Enter URLs (one per line):",
        value=st.session_state.manual_urls_input,
        placeholder="https://www.example.com\nhttps://www.example.com/about-us",
        help="Enter complete URLs including http:// or https://"
    )
    
    add_button = st.button("➕ Add URLs", help="Add these URLs to the list", key="add_urls", use_container_width=True)
    if add_button:
        if manual_urls_input:
            # Procesar múltiples URLs (una por línea)
            urls_to_add = [url.strip() for url in manual_urls_input.split('\n') if url.strip()]
            
            for manual_url in urls_to_add:
                # Asegurar que la URL comience con http:// o https://
                if not manual_url.startswith(('http://', 'https://')):
                    manual_url = 'https://' + manual_url
                
                # Añadir la URL directamente a las URLs manuales y seleccionadas
                st.session_state.manual_urls.add(manual_url)
                st.session_state.selected_urls_set.add(manual_url)
            
            st.session_state.selected_urls = list(st.session_state.selected_urls_set)
            st.success(f"Added {len(urls_to_add)} URLs!")
            # Limpiar el input después de añadir
            st.session_state.manual_urls_input = ""
            st.rerun()
        else:
            st.warning("Please enter at least one valid URL")

    clear_button = st.button("🗑️ Clear All", help="Remove all manually added URLs", key="clear_all", use_container_width=True)
    if clear_button:
        st.session_state.manual_urls.clear()
        # Actualizar las URLs seleccionadas
        st.session_state.selected_urls_set = set(url for url in st.session_state.selected_urls_set 
                                           if url not in st.session_state.manual_urls)
        st.session_state.selected_urls = list(st.session_state.selected_urls_set)
        st.rerun()
    
    # Mostrar las URLs añadidas manualmente
    if st.session_state.manual_urls:
        st.markdown("#### Added URLs:")
        url_list = sorted(st.session_state.manual_urls)
        for i, url in enumerate(url_list):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"{i+1}. {url}")
            with col2:
                delete_button = st.button("🗑️", key=f"delete_{url}", help=f"Remove {url}")
                if delete_button:
                    st.session_state.manual_urls.remove(url)
                    st.session_state.selected_urls_set.discard(url)
                    st.session_state.selected_urls = list(st.session_state.selected_urls_set)
                    st.rerun()
        
        # Automáticamente seleccionar todas las URLs añadidas
        st.session_state.selected_urls = list(st.session_state.manual_urls)
        st.session_state.selected_urls_set = set(st.session_state.manual_urls)
        
        # Mostrar el número de URLs seleccionadas
        st.metric(
            "URLs to capture",
            len(st.session_state.selected_urls),
            help="Number of URLs that will be captured"
        )
    
    # Device selection with detailed help - ahora se convierte en Step 2
    st.markdown("""
    ### 📱 Step 2: Configure Device Settings
    Choose which device types you want to capture screenshots for. Each URL will be captured in all selected device sizes.
    """)

    devices = st.multiselect(
        "Select devices:",
        ["desktop", "mobile", "tablet", "custom"],
        default=["desktop"],
        help="""
        Choose one or more device types:
        - Desktop: 1920x1080px (Full HD)
        - Mobile: 375x812px (iPhone X)
        - Tablet: 768x1024px (iPad)
        - Custom: Define your own dimensions
        """
    )

    # Custom device configuration
    if "custom" in devices:
        st.markdown("""
        #### Custom Device Settings
        Define custom dimensions for your screenshots. This is useful for capturing specific viewport sizes.
        """)
        col1, col2 = st.columns(2)
        with col1:
            custom_width = st.number_input(
                "Custom width (px):",
                min_value=400,
                value=1200,
                help="Minimum width is 400px"
            )
        with col2:
            custom_height = st.number_input(
                "Custom height (px):",
                min_value=600,
                value=3000,
                help="Minimum height is 600px"
            )
    
    # Capture button
    if st.button("📸 Capture Screenshots", help="Click to start capturing screenshots of selected URLs", key="capture-button", type="primary", use_container_width=True):
        if not st.session_state.selected_urls and not st.session_state.manual_urls:
            st.warning("Please select at least one URL to capture screenshots.")
            return
            
        status_container = st.empty()
        progress_container = st.empty()
        message_container = st.empty()
        
        with st.spinner("Processing screenshots... This may take a few moments."):
            # Crear nuevo directorio temporal solo si no existe
            if not st.session_state.temp_dir:
                st.session_state.temp_dir = tempfile.mkdtemp()
                st.session_state.screenshot_paths = []
            
            # Combinar URLs seleccionadas y manuales
            urls_to_capture = list(set(st.session_state.selected_urls).union(st.session_state.manual_urls))
            
            # Progress tracking
            total_captures = len(urls_to_capture) * len(devices)
            current_capture = 0
            
            for url in urls_to_capture:
                for device in devices:
                    try:
                        # Update progress and show fun message
                        current_capture += 1
                        progress = current_capture / total_captures
                        status_container.text(f"Processing: {url} ({device})")
                        progress_container.progress(progress)
                        message_container.info(get_loading_message())
                        
                        screenshot_path = capture_screenshot(url, device, custom_width, custom_height)
                        
                        if screenshot_path and screenshot_path not in st.session_state.screenshot_paths:
                            st.session_state.screenshot_paths.append(screenshot_path)
                    except Exception as e:
                        st.error(f"Error capturing {url} ({device}): {str(e)}")
            
            # Clear progress indicators
            status_container.empty()
            progress_container.empty()
            message_container.empty()
            
            # Show celebration balloons after successful capture
            if st.session_state.screenshot_paths:
                st.success("¡Screenshots captured successfully! 🎉")
                st.balloons()
    
    # Show results if there are screenshots
    if st.session_state.screenshot_paths:
        st.markdown("### 📊 Results")
        
        # Group screenshots by URL
        screenshots_by_url = {}
        for path in st.session_state.screenshot_paths:
            if os.path.exists(path):  # Verificar que el archivo aún existe
                filename = os.path.basename(path)
                url = filename.rsplit('_', 1)[0]  # Separar URL del tipo de dispositivo
                if url not in screenshots_by_url:
                    screenshots_by_url[url] = []
                screenshots_by_url[url].append(path)
        
        # Mostrar screenshots agrupados por URL
        for url, paths in screenshots_by_url.items():
            with st.expander(f"🌐 Website: {url}", expanded=False):
                st.markdown("#### Available Screenshots:")
                
                # Crear tabs para cada dispositivo
                device_tabs = st.tabs([f"📱 {os.path.basename(path).split('_')[-1].replace('.png', '').title()}" for path in paths])
                
                for tab, path in zip(device_tabs, paths):
                    if os.path.exists(path):
                        with tab:
                            try:
                                st.image(
                                    path,
                                    use_container_width=True
                                )
                                col1, col2 = st.columns([3, 1])
                                with col2:
                                    with open(path, "rb") as f:
                                        st.download_button(
                                            label=f"⬇️ Download",
                                            data=f,
                                            file_name=os.path.basename(path),
                                            help=f"Download screenshot",
                                            key=f"dl_{path}",
                                            use_container_width=True
                                        )
                            except Exception as e:
                                st.error(f"Error displaying image {path}: {str(e)}")
                
                st.markdown("---")
        
        # Create ZIP with all screenshots
        if len(st.session_state.screenshot_paths) > 0:
            st.markdown("### 📦 Batch Download")
            zip_path = os.path.join(st.session_state.temp_dir, "screenshots.zip")
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for file in st.session_state.screenshot_paths:
                    if os.path.exists(file):
                        zipf.write(file, os.path.basename(file))
            
            if os.path.exists(zip_path):
                with open(zip_path, "rb") as f:
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        st.download_button(
                            label="📥 Download All Screenshots as ZIP",
                            data=f,
                            file_name="screenshots.zip",
                            help="Download all screenshots in a single ZIP file",
                            key="dl_all",
                            use_container_width=True
                        )

if __name__ == "__main__":
    main()