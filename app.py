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

def setup_browser(playwright, device_profile="desktop", custom_width=None, custom_height=None):
    """Configura y retorna una instancia del navegador con manejo de errores mejorado"""
    # Configuración del navegador
    browser_args = []
    proxy = get_proxy()
    
    # Intentar primero con proxy si está disponible
    try:
        if proxy:
            browser_args.append(f'--proxy-server={proxy}')
            browser = playwright.chromium.launch(
                headless=True,
                args=browser_args
            )
        else:
            # Si no hay proxy disponible, intentar sin proxy
            browser = playwright.chromium.launch(
                headless=True
            )
    except Exception as e:
        # Si falla con proxy, intentar sin proxy
        browser = playwright.chromium.launch(
            headless=True
        )
    
    # Configuración del contexto según el dispositivo
    context_settings = {}
    
    if device_profile == "mobile":
        context_settings = playwright.devices['iPhone 12']
    elif device_profile == "tablet":
        context_settings = playwright.devices['iPad Pro 11']
    elif device_profile == "custom" and custom_width and custom_height:
        context_settings = {
            "viewport": {"width": custom_width, "height": custom_height},
            "screen": {"width": custom_width, "height": custom_height}
        }
    else:  # desktop
        context_settings = {
            "viewport": {"width": 1920, "height": 1080},
            "screen": {"width": 1920, "height": 1080}
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
    st.title("📸 Smart Screenshot Capture")
    st.markdown("""
    Capture screenshots of any website in different device sizes. Perfect for responsive design testing and documentation.
    """)
    
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
    if 'url_selector' not in st.session_state:
        st.session_state.url_selector = []
    
    # URL Input Section
    st.markdown("""
    ### 🌐 Step 1: Enter Main Website URL
    Enter the main URL of the website you want to analyze. The tool will automatically extract all accessible URLs from this website.
    """)
    
    base_url = st.text_input(
        "Enter website URL:",
        help="Enter the main URL of the website you want to analyze. Example: https://www.example.com",
        placeholder="https://www.example.com"
    )
    
    # Extract URLs button
    if st.button("🔍 Extract URLs", help="Click to extract main URLs from the website"):
        with st.spinner("Extracting URLs... This may take a moment."):
            if base_url:
                if not base_url.startswith(('http://', 'https://')):
                    base_url = 'https://' + base_url
                extracted = extract_urls(base_url)
                st.session_state.extracted_urls = extracted
                if extracted:
                    st.success(f"Found {len(extracted)} URLs!")
                else:
                    st.warning("No URLs found. You can add URLs manually using the form below.")
    
    # Show extracted URLs
    if st.session_state.extracted_urls or st.session_state.manual_urls:
        st.markdown("""
        ### 🎯 Step 2: Select URLs to Capture
        Choose which URLs you want to capture screenshots of. You can select multiple URLs at once.
        """)
        
        # Combinar URLs extraídas y manuales
        all_available_urls = sorted(list(set(st.session_state.extracted_urls).union(st.session_state.manual_urls)))
        
        # URL selection with improved display
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_urls = st.multiselect(
                "Select URLs to capture:",
                options=all_available_urls,
                default=[],
                help="Select the URLs you want to capture screenshots of.",
                format_func=lambda x: x,
                placeholder="Choose URLs to capture..."
            )
            
            # Actualizar el estado directamente
            st.session_state.selected_urls = selected_urls
            st.session_state.selected_urls_set = set(selected_urls)
        
        # Show selected URLs count
        with col2:
            st.metric(
                "Selected URLs",
                len(selected_urls),
                help="Number of URLs currently selected for capture"
            )
            
            # Botón para limpiar selección
            if st.button("Clear Selection", help="Remove all selected URLs"):
                st.session_state.selected_urls = []
                st.session_state.selected_urls_set = set()
                st.rerun()
    
    # Sección para añadir URLs manualmente
    st.markdown("""
    ### ✍️ Or Add URLs Manually (Optional)
    If some URLs were not automatically extracted or you want to add specific pages, 
    you can manually add them here. Add all the URLs you want and then click "Confirm URLs" to add them to the selection.
    """)
    
    with st.expander("Add URLs manually", expanded=not bool(st.session_state.extracted_urls)):
        st.markdown("""
        Enter complete URLs including http:// or https://. Examples:
        - https://www.example.com/products
        - https://www.example.com/about-us
        """)
        
        # Inicializar el estado para URLs temporales si no existe
        if 'temp_urls' not in st.session_state:
            st.session_state.temp_urls = set()
        
        # Campo de texto para ingresar URLs manualmente
        manual_url = st.text_input(
            "Enter URL:",
            placeholder="https://www.example.com/page",
            help="Enter a complete URL including https:// or http://"
        )
        
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("Add to List", help="Add this URL to the temporary list"):
                if manual_url:
                    # Asegurar que la URL comience con http:// o https://
                    if not manual_url.startswith(('http://', 'https://')):
                        manual_url = 'https://' + manual_url
                    
                    # Añadir la URL a la lista temporal
                    st.session_state.temp_urls.add(manual_url)
                    st.success(f"Added to list: {manual_url}")
                else:
                    st.warning("Please enter a valid URL")
        
        with col2:
            if st.button("Clear List", help="Remove all URLs from the temporary list"):
                st.session_state.temp_urls.clear()
        
        # Mostrar las URLs temporales
        if st.session_state.temp_urls:
            st.markdown("#### URLs to be added:")
            for url in sorted(st.session_state.temp_urls):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"• {url}")
                with col2:
                    if st.button("🗑️", key=f"delete_temp_{url}", help=f"Remove {url}"):
                        st.session_state.temp_urls.remove(url)
            
            # Botón para confirmar todas las URLs
            if st.button("✅ Confirm URLs", help="Add all URLs to the selection"):
                # Añadir todas las URLs temporales a las URLs manuales y seleccionadas
                st.session_state.manual_urls.update(st.session_state.temp_urls)
                st.session_state.selected_urls_set.update(st.session_state.temp_urls)
                st.session_state.selected_urls = list(st.session_state.selected_urls_set)
                if 'url_selector' not in st.session_state:
                    st.session_state.url_selector = []
                st.session_state.url_selector.extend(st.session_state.temp_urls)
                
                # Limpiar las URLs temporales
                st.session_state.temp_urls.clear()
                st.success("URLs added successfully!")
                st.rerun()
    
    # Display selected URLs in a more readable format
    if hasattr(st.session_state, 'selected_urls') and st.session_state.selected_urls:
        with st.expander("Selected URLs for Capture", expanded=True):
            st.markdown("#### URLs that will be captured:")
            for i, url in enumerate(st.session_state.selected_urls, 1):
                st.write(f"{i}. {url}")
                
            # Mostrar instrucciones de uso
            if len(st.session_state.selected_urls) > 0:
                st.info("""
                💡 **Tips for URL Selection:**
                - You can select/deselect multiple URLs at once
                - Use the search box to filter URLs
                - Click 'Clear Selection' to start over
                - Add missing URLs manually using the form above
                """)
    
    # Device selection with detailed help
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
    custom_width = None
    custom_height = None
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
    
    # Advanced options in an expander
    with st.expander("ℹ️ Tips & Information"):
        st.markdown("""
        ### Usage Tips
        - URLs are automatically extracted from the main website
        - Select the specific URLs you want to capture
        - The tool will automatically handle cookies and pop-ups
        - For best results, wait until all screenshots are processed
        
        ### Supported Features
        - URL extraction and filtering
        - Multi-device capture
        - Cookie consent handling
        - Pop-up management
        - Full page screenshots
        - Batch processing
        
        ### Output
        - Screenshots are saved in PNG format
        - Download individual images or all as ZIP
        - Images are named using the website's URL and device type
        """)
    
    # Capture button
    if st.button("📸 Capture Screenshots", help="Click to start capturing screenshots of selected URLs"):
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
                                    use_column_width=True
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