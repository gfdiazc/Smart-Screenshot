import streamlit as st
import os
import time
import zipfile
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
from selenium_stealth import stealth
import requests
import json
import random
from PIL import Image
import pandas as pd
import tempfile

def get_proxy():
    try:
        response = requests.get('https://proxylist.geonode.com/api/proxy-list?limit=100&page=1&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps&anonymityLevel=elite&anonymityLevel=anonymous')
        data = response.json()
        proxies = [f"{proxy['ip']}:{proxy['port']}" for proxy in data['data']]
        return random.choice(proxies) if proxies else None
    except:
        return None

def setup_driver():
    options = Options()
    options.add_argument('--headless=new')  # Nueva versión de headless
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-notifications')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--start-maximized')
    options.add_argument('--force-device-scale-factor=1')
    
    # Set Chrome binary path for Streamlit Cloud
    options.binary_location = '/usr/bin/chromium'
    
    # Random user agent
    ua = UserAgent()
    user_agent = ua.random
    options.add_argument(f'user-agent={user_agent}')
    
    # Add proxy if available
    proxy = get_proxy()
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')
    
    # Additional evasion options
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Additional options for stability and rendering
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--disable-web-security')
    options.add_argument('--enable-javascript')
    options.add_argument('--hide-scrollbars')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--disable-notifications')
    
    # Performance options
    options.add_argument('--disable-dev-tools')
    options.add_argument('--dns-prefetch-disable')
    options.add_argument('--disable-features=IsolateOrigins,site-per-process')
    
    # Create driver with service
    service = Service('/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)
    
    # Apply stealth settings
    stealth(driver,
        languages=["en-US", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )
    
    # Set window size
    driver.set_window_size(1920, 1080)
    
    # Establecer timeouts
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(10)
    
    return driver, 1920, 1080

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

def capture_screenshot(url, device_profile="desktop"):
    try:
        driver = None
        temp_dir = tempfile.mkdtemp()
        safe_filename = sanitize_filename(url)
        screenshot_path = os.path.join(temp_dir, f"{safe_filename}_{device_profile}.png")
        
        try:
            driver, width, height = setup_driver()
            
            # Load page with timeout and wait for content
            driver.set_page_load_timeout(30)
            driver.get(url)
            
            # Esperar a que la página cargue completamente
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Esperar un tiempo adicional para contenido dinámico
            time.sleep(5)
            
            # Scroll para cargar contenido lazy
            total_height = driver.execute_script("return Math.max( document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight );")
            viewport_height = driver.execute_script("return window.innerHeight")
            slices = 3
            slice_height = total_height // slices
            
            # Scroll suave por la página
            for i in range(slices):
                driver.execute_script(f"window.scrollTo(0, {i * slice_height});")
                time.sleep(1)
            
            # Volver al inicio
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Intentar cerrar pop-ups o cookies si existen
            try:
                # Lista de selectores comunes para botones de cookies y pop-ups
                selectors = [
                    "//button[contains(., 'Accept')]",
                    "//button[contains(., 'Aceptar')]",
                    "//button[contains(., 'Accept All')]",
                    "//button[contains(., 'Aceptar todo')]",
                    "//button[contains(., 'Close')]",
                    "//button[contains(., 'Cerrar')]",
                    "//div[contains(@class, 'cookie')]//button",
                    "//div[contains(@class, 'popup')]//button",
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
            except:
                pass
            
            # Esperar un momento después de manejar pop-ups
            time.sleep(2)
            
            # Ocultar elementos flotantes que puedan interferir
            driver.execute_script("""
                document.querySelectorAll('*').forEach(el => {
                    const style = window.getComputedStyle(el);
                    if (style.position === 'fixed' || style.position === 'sticky') {
                        el.style.display = 'none';
                    }
                });
            """)
            
            time.sleep(1)
            
            # Tomar screenshot
            driver.save_screenshot(screenshot_path)
            
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
            st.warning(f"Error capturing screenshot: {str(e)}")
            return None
            
        finally:
            if driver:
                driver.quit()
                
    except Exception as e:
        st.error(f"Critical error: {str(e)}")
        return None

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
                        
                        screenshot_path = capture_screenshot(url, device)
                        
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