import streamlit as st
import tempfile
import os
import zipfile
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import random
from PIL import Image
from selenium.webdriver.common.action_chains import ActionChains

def setup_driver(device_type, custom_width=None, custom_height=None):
    """Configura y retorna un webdriver de Chrome con las opciones especificadas"""
    try:
        # Configuraciones de dispositivo con user agents específicos
        device_profiles = {
            "desktop": {
                "width": 1920,
                "height": 1080,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            },
            "mobile": {
                "width": 375,
                "height": 812,
                "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
            },
            "tablet": {
                "width": 768,
                "height": 1024,
                "user_agent": "Mozilla/5.0 (iPad; CPU OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
            },
            "custom": {
                "width": custom_width,
                "height": custom_height,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            }
        }
        
        # Obtener dimensiones y user agent del dispositivo
        width = device_profiles[device_type]["width"]
        height = device_profiles[device_type]["height"]
        user_agent = device_profiles[device_type]["user_agent"]
        
        # Configurar opciones de Chrome
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument(f'--window-size={width},{height}')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--lang=es-ES,es')
        chrome_options.add_argument(f'--user-agent={user_agent}')
        
        # Configuraciones experimentales avanzadas
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option('prefs', {
            'profile.default_content_setting_values.notifications': 2,
            'profile.default_content_settings.popups': 0,
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': True,
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False,
            'profile.managed_default_content_settings.images': 1,
            'profile.managed_default_content_settings.javascript': 1
        })
        
        chrome_options.binary_location = '/usr/bin/chromium'
        
        # Configurar el servicio de Chrome
        service = Service('/usr/lib/chromium-browser/chromedriver')
        
        # Inicializar el driver
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Ejecutar JavaScript para evadir detección
        evasion_js = """
            // Ocultar webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Modificar user agent
            Object.defineProperty(navigator, 'userAgent', {
                get: () => '""" + user_agent + """'
            });
            
            // Simular plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Simular idiomas
            Object.defineProperty(navigator, 'languages', {
                get: () => ['es-ES', 'es', 'en-US', 'en']
            });
            
            // Simular plataforma
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32'
            });
            
            // Ocultar Chrome
            window.chrome = {
                runtime: {}
            };
        """
        
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': evasion_js
        })
        
        # Configurar el tamaño de la ventana
        driver.set_window_size(width, height)
        
        return driver, width, height
    except Exception as e:
        st.error(f"Error setting up Chrome driver: {str(e)}")
        raise e

def handle_popups(driver):
    """Maneja diferentes tipos de pop-ups y cookies"""
    try:
        # Lista de selectores comunes para botones de cookies y pop-ups
        selectors = [
            "//button[contains(translate(., 'ACCEPT', 'accept'), 'accept')]",
            "//button[contains(translate(., 'AGREE', 'agree'), 'agree')]",
            "//button[contains(translate(., 'ALLOW', 'allow'), 'allow')]",
            "//button[contains(., 'Got it')]",
            "//button[contains(., 'Close')]",
            "//button[contains(@class, 'close')]",
            "//div[contains(@class, 'close')]",
            "//button[contains(@class, 'cookie-accept')]",
            "//button[contains(@class, 'accept-cookies')]"
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed():
                        element.click()
                        time.sleep(0.5)
            except:
                continue
                
        time.sleep(1)
    except:
        pass

def capture_screenshot(driver, url, output_path, width, height):
    """Captura un screenshot de la URL especificada"""
    try:
        # Simular comportamiento humano antes de cargar la página
        time.sleep(random.uniform(1, 2))
        
        # Navegar a la URL
        driver.get(url)
        
        # Esperar a que la página cargue completamente
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
        
        # Simular movimiento aleatorio del mouse
        actions = ActionChains(driver)
        for _ in range(3):
            x = random.randint(0, width)
            y = random.randint(0, height)
            actions.move_by_offset(x, y)
            actions.pause(random.uniform(0.1, 0.3))
        actions.perform()
        
        try:
            # Manejar pop-ups y cookies con tiempo de espera aleatorio
            handle_popups(driver)
            time.sleep(random.uniform(0.5, 1))
        except Exception as e:
            st.warning(f"Warning handling popups: {str(e)}")
        
        try:
            # Simular scroll humano
            total_height = driver.execute_script("""
                return Math.max(
                    document.body.scrollHeight,
                    document.documentElement.scrollHeight,
                    document.body.offsetHeight,
                    document.documentElement.offsetHeight,
                    document.body.clientHeight,
                    document.documentElement.clientHeight
                );
            """)
            
            # Scroll suave con velocidad variable
            current_height = 0
            while current_height < total_height:
                # Calcular un paso aleatorio entre 100 y 300 píxeles
                step = random.randint(100, 300)
                current_height += step
                
                # Scroll suave con aceleración y desaceleración
                driver.execute_script(f"""
                    window.scrollTo({{
                        top: {current_height},
                        behavior: 'smooth'
                    }});
                """)
                
                # Pausa aleatoria entre scrolls
                time.sleep(random.uniform(0.2, 0.5))
                
                # Simular pausa ocasional para "leer"
                if random.random() < 0.2:  # 20% de probabilidad
                    time.sleep(random.uniform(0.5, 1.5))
            
            # Volver al inicio suavemente
            driver.execute_script("""
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            """)
            time.sleep(random.uniform(0.5, 1))
            
            # Ajustar tamaño de la ventana
            driver.set_window_size(width, total_height)
            
            # Limpiar elementos flotantes
            driver.execute_script("""
                document.querySelectorAll('*').forEach(el => {
                    const style = window.getComputedStyle(el);
                    if (style.position === 'fixed' || style.position === 'sticky') {
                        el.style.display = 'none';
                    }
                });
            """)
            
            # Esperar a que los elementos flotantes se oculten
            time.sleep(random.uniform(0.3, 0.7))
            
        except Exception as e:
            st.warning(f"Warning adjusting page: {str(e)}")
        
        # Esperar un poco más antes de capturar
        time.sleep(random.uniform(0.5, 1))
        
        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        # Tomar y guardar screenshot
        driver.save_screenshot(output_path)
        
        # Verificar que el archivo se creó correctamente
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
        else:
            st.error("Screenshot file was not created or is empty")
            return False
            
    except Exception as e:
        st.error(f"Error capturing screenshot: {str(e)}")
        return False

def sanitize_filename(url):
    # Eliminar el protocolo (http:// o https://)
    url = re.sub(r'^https?://', '', url)
    # Eliminar caracteres no válidos para nombres de archivo
    url = re.sub(r'[<>:"/\\|?*]', '_', url)
    # Limitar la longitud del nombre del archivo
    return url[:50]

def get_loading_message():
    """Retorna un mensaje aleatorio divertido durante la carga"""
    messages = [
        "🎨 Making your screenshots pixel-perfect...",
        "🚀 Zooming through the internet...",
        "🎭 Dealing with those pesky pop-ups...",
        "🍪 Handling cookies (the digital ones, not the tasty ones)...",
        "📱 Teaching your website to pose for different devices...",
        "🎯 Capturing the perfect shot...",
        "🎪 Juggling with different screen sizes...",
        "🎮 Playing hide and seek with pop-ups...",
        "🎭 Preparing the website for its photoshoot...",
        "🎪 Performing website acrobatics...",
        "🎨 Adding some digital makeup...",
        "🎯 Taking aim at those tricky elements...",
        "🚀 Warming up the quantum screenshot engine...",
        "🎭 Getting the website ready for its close-up...",
        "🌈 Collecting all the pixels...",
        "🎪 Training the browser circus...",
        "🎨 Mixing the perfect pixel palette...",
        "🎯 Calibrating the screenshot sensors..."
    ]
    return random.choice(messages)

def main():
    st.title("📸 Smart Screenshot Capture")
    st.markdown("""
    Capture screenshots of any website in different device sizes. Perfect for responsive design testing and documentation.
    """)
    
    # Inicializar session_state para screenshots
    if 'temp_dir' not in st.session_state:
        st.session_state.temp_dir = None
    if 'screenshot_paths' not in st.session_state:
        st.session_state.screenshot_paths = []
    
    # URL Input with help text
    urls = st.text_area(
        "Enter URLs (one per line):",
        help="Enter the complete URLs of the websites you want to capture. Example: https://www.example.com",
        placeholder="""https://www.example.com
https://www.another-example.com
""",
    ).split("\n")
    
    # Device selection with detailed help
    st.markdown("### Device Settings")
    devices = st.multiselect(
        "Select devices:",
        ["desktop", "mobile", "tablet", "custom"],
        default=["desktop"],
        help="""
        - Desktop: 1920x1080px
        - Mobile: 375x812px (iPhone X)
        - Tablet: 768x1024px (iPad)
        - Custom: Define your own dimensions
        """
    )
    
    # Custom device configuration
    custom_width = None
    custom_height = None
    if "custom" in devices:
        st.markdown("#### Custom Device Settings")
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
        - Make sure to include the full URL (including http:// or https://)
        - The tool will automatically handle cookies and pop-ups
        - For best results, wait until all screenshots are processed
        
        ### Supported Features
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
    
    # Capture button with processing indicator
    if st.button("📸 Capture Screenshots", help="Click to start capturing screenshots of all entered URLs"):
        status_container = st.empty()
        progress_container = st.empty()
        message_container = st.empty()
        
        with st.spinner("Processing screenshots... This may take a few moments."):
            # Crear nuevo directorio temporal solo si no existe
            if not st.session_state.temp_dir:
                st.session_state.temp_dir = tempfile.mkdtemp()
                st.session_state.screenshot_paths = []
            
            # Progress tracking
            total_captures = len([url for url in urls if url.strip()]) * len(devices)
            current_capture = 0
            
            for url in urls:
                if not url.strip():
                    continue
                
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url.strip()
                
                for device in devices:
                    try:
                        # Update progress and show fun message
                        current_capture += 1
                        progress = current_capture / total_captures
                        status_container.text(f"Processing: {url} ({device})")
                        progress_container.progress(progress)
                        message_container.info(get_loading_message())
                        
                        driver, width, height = setup_driver(device, custom_width, custom_height)
                        safe_filename = sanitize_filename(url)
                        output_path = os.path.join(st.session_state.temp_dir, f"{safe_filename}_{device}.png")
                        
                        if capture_screenshot(driver, url, output_path, width, height):
                            if output_path not in st.session_state.screenshot_paths:
                                st.session_state.screenshot_paths.append(output_path)
                            
                        # Cerrar el driver
                        driver.quit()
                            
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