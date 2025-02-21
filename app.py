import streamlit as st
import tempfile
import os
import zipfile
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from PIL import Image
import re
import random

def sanitize_filename(url):
    # Eliminar el protocolo (http:// o https://)
    url = re.sub(r'^https?://', '', url)
    # Eliminar caracteres no válidos para nombres de archivo
    url = re.sub(r'[<>:"/\\|?*]', '_', url)
    # Limitar la longitud del nombre del archivo
    return url[:50]

def setup_driver(device_type, custom_width=None, custom_height=None):
    # Configuración de Chrome Options
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-popup-blocking")
    
    # Configuraciones de dispositivo
    device_profiles = {
        "desktop": {"width": 1920, "height": 1080},
        "mobile": {"width": 375, "height": 812},
        "tablet": {"width": 768, "height": 1024},
        "custom": {"width": custom_width, "height": custom_height}
    }
    
    # Obtener dimensiones del dispositivo
    width = device_profiles[device_type]["width"]
    height = device_profiles[device_type]["height"]
    
    if device_type != "custom":
        chrome_options.add_argument(f"--window-size={width},{height}")
    else:
        chrome_options.add_argument(f"--window-size={custom_width},{custom_height}")
    
    # Inicializar el driver
    driver = webdriver.Chrome(options=chrome_options)
    return driver, width, height

# Validate URLs
def validate_url(url):
    if not url.startswith("http://") and not url.startswith("https://"):
        return False
    return True

def handle_popups(driver):
    """Maneja diferentes tipos de pop-ups, cookies y ofertas en múltiples idiomas"""
    
    # Selectores para cookies en múltiples idiomas
    cookie_selectors = [
        # Inglés
        "//button[contains(translate(., 'ACCEPT', 'accept'), 'accept')]",
        "//button[contains(translate(., 'AGREE', 'agree'), 'agree')]",
        "//button[contains(translate(., 'ALLOW', 'allow'), 'allow')]",
        "//button[contains(translate(., 'CONSENT', 'consent'), 'consent')]",
        "//button[contains(., 'Got it')]",
        "//button[contains(., 'I understand')]",
        "//button[contains(., 'Continue')]",
        # Español
        "//button[contains(translate(., 'ACEPT', 'acept'), 'aceptar')]",
        "//button[contains(translate(., 'ENTEND', 'entend'), 'entendido')]",
        "//button[contains(translate(., 'CONTIN', 'contin'), 'continuar')]",
        # Elementos genéricos de cookies
        "//*[@id='cookie-banner']//button",
        "//*[contains(@class, 'cookie')]//button",
        "//*[contains(@id, 'cookie')]//button",
        "//button[contains(., 'cookies')]",
        "//button[contains(., 'Cookies')]",
        # Elementos específicos comunes
        "//button[@id='onetrust-accept-btn-handler']",
        "//button[contains(@class, 'cookie-accept')]",
        "//button[contains(@class, 'accept-cookies')]",
        "//button[contains(@class, 'cookie-consent')]",
        # Links y spans que podrían ser botones
        "//a[contains(translate(., 'ACCEPT', 'accept'), 'accept')]",
        "//a[contains(translate(., 'AGREE', 'agree'), 'agree')]",
        "//span[contains(translate(., 'ACCEPT', 'accept'), 'accept')]"
    ]
    
    # Intentar aceptar cookies primero
    for selector in cookie_selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for element in elements:
                if element.is_displayed():
                    try:
                        element.click()
                        time.sleep(0.5)
                    except:
                        try:
                            driver.execute_script("arguments[0].click();", element)
                        except:
                            continue
        except Exception:
            continue
    
    time.sleep(1)
    
    # Selectores para pop-ups y modales en múltiples idiomas
    popup_selectors = [
        # Botones de cierre en inglés
        "//button[contains(@aria-label, 'Close')]",
        "//button[contains(@aria-label, 'Dismiss')]",
        "//button[contains(@title, 'Close')]",
        "//button[contains(., 'Close')]",
        "//button[contains(., 'Skip')]",
        "//button[contains(., 'No thanks')]",
        "//button[contains(., 'Not now')]",
        # Botones de cierre en español
        "//button[contains(@aria-label, 'Cerrar')]",
        "//button[contains(@title, 'Cerrar')]",
        "//button[contains(., 'Cerrar')]",
        "//button[contains(., 'Saltar')]",
        "//button[contains(., 'No, gracias')]",
        "//button[contains(., 'Ahora no')]",
        # Elementos de cierre genéricos
        "//button[contains(@class, 'close')]",
        "//div[contains(@class, 'close')]",
        "//span[contains(@class, 'close')]",
        "//i[contains(@class, 'close')]",
        "//button[contains(@class, 'modal-close')]",
        "//div[contains(@class, 'modal-close')]",
        # Símbolos comunes de cierre
        "//button[text()='×']",
        "//div[text()='×']",
        "//button[text()='X']",
        "//div[text()='X']",
        "//button[contains(., '×')]",
        "//div[contains(., '×')]",
        "//button[contains(., 'X')]",
        "//div[contains(., 'X')]",
        # Elementos específicos de newsletters y suscripciones
        "//button[contains(., 'Not interested')]",
        "//button[contains(., 'No me interesa')]",
        "//button[contains(@class, 'newsletter-close')]",
        "//button[contains(@class, 'subscription-close')]"
    ]
    
    # Intentar cerrar pop-ups
    for selector in popup_selectors:
        try:
            elements = driver.find_elements(By.XPATH, selector)
            for element in elements:
                if element.is_displayed():
                    try:
                        driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        time.sleep(0.2)
                        element.click()
                        time.sleep(0.5)
                    except:
                        try:
                            driver.execute_script("arguments[0].click();", element)
                            time.sleep(0.5)
                        except:
                            continue
        except Exception:
            continue
    
    # Limpieza final con JavaScript
    try:
        driver.execute_script("""
            function isVisible(elem) {
                return !!(elem.offsetWidth || elem.offsetHeight || elem.getClientRects().length);
            }
            
            // Remover elementos comunes de pop-ups y overlays
            const elementsToRemove = document.querySelectorAll(
                '[class*="promotion"], [class*="offer"], [class*="modal"], ' +
                '[class*="popup"], [class*="overlay"], [id*="modal"], ' +
                '[id*="popup"], [class*="newsletter"], [class*="subscription"], ' +
                '[class*="dialog"], [class*="lightbox"], [class*="banner"], ' +
                '[id*="dialog"], [id*="lightbox"], [id*="banner"]'
            );
            
            elementsToRemove.forEach(el => {
                if (isVisible(el)) {
                    el.remove();
                }
            });
            
            // Restaurar el scroll y estilos
            document.body.style.overflow = 'auto';
            document.body.style.position = 'static';
            document.documentElement.style.overflow = 'auto';
            document.body.classList.remove('modal-open');
            document.body.classList.remove('no-scroll');
            
            // Eliminar overlays y fondos oscuros
            const overlays = document.querySelectorAll(
                '[class*="overlay"], [class*="backdrop"], [class*="background"], ' +
                '[class*="modal-backdrop"], [class*="dialog-backdrop"]'
            );
            overlays.forEach(el => {
                if (isVisible(el)) {
                    el.remove();
                }
            });
        """)
    except Exception:
        pass
    
    time.sleep(1)

def capture_screenshot(driver, url, output_path, width, height):
    try:
        driver.set_window_size(width, height)
        driver.get(url)

        # Wait for the page to load fully
        time.sleep(5)  # Aumentado para dar más tiempo a que cargue la página

        # Manejar pop-ups y cookies
        handle_popups(driver)
        
        # Esperar un momento adicional para asegurarse de que los pop-ups se han cerrado
        time.sleep(2)

        # Ajustar tamaño de ventana para captura completa
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
        
        driver.set_window_size(width, total_height)
        
        # Asegurar que no hay elementos flotantes molestos
        driver.execute_script("""
            // Remover elementos fixed o sticky que puedan obstruir
            document.querySelectorAll('*').forEach(el => {
                const style = window.getComputedStyle(el);
                if (style.position === 'fixed' || style.position === 'sticky') {
                    el.style.display = 'none';
                }
            });
        """)
        
        # Ensure the directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Take and save screenshot
        driver.save_screenshot(output_path)
        return True
    except Exception as e:
        print(f"Error capturing screenshot for {url}: {e}")
        return False

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
            temp_dir = tempfile.mkdtemp()
            screenshot_paths = []
            
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
                        output_path = os.path.join(temp_dir, f"{safe_filename}_{device}.png")
                        
                        if capture_screenshot(driver, url, output_path, width, height):
                            screenshot_paths.append(output_path)
                        driver.quit()
                    except Exception as e:
                        st.error(f"Error capturing {url} ({device}): {str(e)}")
            
            # Clear progress indicators
            status_container.empty()
            progress_container.empty()
            message_container.empty()
            
            # Show results
            if screenshot_paths:
                st.markdown("### 📊 Results")
                
                # Group screenshots by URL
                screenshots_by_url = {}
                for path in screenshot_paths:
                    filename = os.path.basename(path)
                    url = filename.rsplit('_', 1)[0]  # Separar URL del tipo de dispositivo
                    if url not in screenshots_by_url:
                        screenshots_by_url[url] = []
                    screenshots_by_url[url].append(path)
                
                # Mostrar screenshots agrupados por URL
                for url, paths in screenshots_by_url.items():
                    with st.expander(f"🌐 Website: {url}", expanded=True):
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
                if len(screenshot_paths) > 0:
                    st.markdown("### 📦 Batch Download")
                    zip_path = os.path.join(temp_dir, "screenshots.zip")
                    with zipfile.ZipFile(zip_path, "w") as zipf:
                        for file in screenshot_paths:
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
            else:
                st.warning("No screenshots were captured. Please check the URLs and try again.")

if __name__ == "__main__":
    main()