import streamlit as st
import tempfile
import os
import zipfile
import time
from playwright.sync_api import sync_playwright
import re
import random
from PIL import Image

@st.cache_resource
def get_playwright():
    return sync_playwright().start()

def setup_browser(device_type, custom_width=None, custom_height=None):
    """Configura y retorna un navegador con las opciones especificadas"""
    try:
        playwright = get_playwright()
        browser = playwright.chromium.launch()
        
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
        
        context = browser.new_context(
            viewport={'width': width, 'height': height}
        )
        
        return context, browser, width, height
    except Exception as e:
        st.error(f"Error setting up browser: {str(e)}")
        raise e

def sanitize_filename(url):
    # Eliminar el protocolo (http:// o https://)
    url = re.sub(r'^https?://', '', url)
    # Eliminar caracteres no válidos para nombres de archivo
    url = re.sub(r'[<>:"/\\|?*]', '_', url)
    # Limitar la longitud del nombre del archivo
    return url[:50]

def capture_screenshot(context, url, output_path, width, height):
    """Captura un screenshot de la URL especificada"""
    page = None
    try:
        # Crear nueva página
        page = context.new_page()
        
        # Navegar a la URL
        page.goto(url, wait_until='networkidle')
        
        # Esperar un poco más para contenido dinámico
        page.wait_for_timeout(2000)
        
        # Ajustar tamaño para captura completa
        page.set_viewport_size({"width": width, "height": height})
        
        # Obtener altura total de la página
        total_height = page.evaluate("""
            Math.max(
                document.body.scrollHeight,
                document.documentElement.scrollHeight,
                document.body.offsetHeight,
                document.documentElement.offsetHeight,
                document.body.clientHeight,
                document.documentElement.clientHeight
            )
        """)
        
        # Ajustar viewport para captura completa
        page.set_viewport_size({"width": width, "height": total_height})
        
        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        # Tomar screenshot
        page.screenshot(path=output_path, full_page=True)
        
        # Verificar que el archivo se creó correctamente
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
        else:
            st.error("Screenshot file was not created or is empty")
            return False
            
    except Exception as e:
        st.error(f"Error capturing screenshot: {str(e)}")
        return False
    finally:
        if page:
            page.close()

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
                        
                        context, browser, width, height = setup_browser(device, custom_width, custom_height)
                        safe_filename = sanitize_filename(url)
                        output_path = os.path.join(temp_dir, f"{safe_filename}_{device}.png")
                        
                        if capture_screenshot(context, url, output_path, width, height):
                            screenshot_paths.append(output_path)
                            
                        # Cerrar el contexto y el navegador
                        context.close()
                        browser.close()
                            
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