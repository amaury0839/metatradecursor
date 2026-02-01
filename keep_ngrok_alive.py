"""
Script para mantener ngrok activo con auto-restart
"""
import subprocess
import time
import requests
import sys
from datetime import datetime

NGROK_PORT = 8501
CHECK_INTERVAL = 30  # Verificar cada 30 segundos

def is_ngrok_running():
    """Verifica si ngrok está corriendo"""
    try:
        result = subprocess.run(
            ['powershell', '-Command', 'Get-Process ngrok -ErrorAction SilentlyContinue'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return 'ngrok' in result.stdout
    except Exception as e:
        print(f"⚠️ Error checking process: {e}")
        return False

def get_ngrok_url():
    """Obtiene la URL pública de ngrok"""
    try:
        response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
        if response.status_code == 200:
            tunnels = response.json().get('tunnels', [])
            if tunnels:
                return tunnels[0].get('public_url', 'N/A')
    except Exception:
        pass
    return None

def start_ngrok():
    """Inicia ngrok en background"""
    try:
        print(f"🚀 [{datetime.now().strftime('%H:%M:%S')}] Iniciando ngrok...")
        subprocess.Popen(
            ['ngrok', 'http', str(NGROK_PORT)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
        time.sleep(5)  # Esperar a que ngrok se inicie
        
        url = get_ngrok_url()
        if url:
            print(f"✅ Ngrok activo: {url}")
            return True
        else:
            print("⚠️ Ngrok iniciado pero URL no disponible aún")
            return False
    except Exception as e:
        print(f"❌ Error iniciando ngrok: {e}")
        return False

def main():
    print("=" * 70)
    print("🔄 NGROK AUTO-RESTART - Mantiene ngrok siempre activo")
    print("=" * 70)
    print(f"Puerto monitoreado: {NGROK_PORT}")
    print(f"Intervalo de verificación: {CHECK_INTERVAL}s")
    print("Presiona Ctrl+C para detener\n")
    
    consecutive_failures = 0
    last_url = None
    
    try:
        while True:
            # Verificar si ngrok está corriendo
            if not is_ngrok_running():
                consecutive_failures += 1
                print(f"\n⚠️ [{datetime.now().strftime('%H:%M:%S')}] Ngrok no está corriendo (fallo #{consecutive_failures})")
                
                if start_ngrok():
                    consecutive_failures = 0
                    time.sleep(10)  # Esperar más después de reiniciar
                else:
                    print(f"❌ Fallo al reiniciar ngrok (intento #{consecutive_failures})")
                    if consecutive_failures >= 5:
                        print("\n❌ Demasiados fallos consecutivos. Verificar ngrok manualmente.")
                        sys.exit(1)
                    time.sleep(5)
            else:
                # Ngrok está corriendo, verificar URL
                url = get_ngrok_url()
                if url and url != last_url:
                    print(f"\n✅ [{datetime.now().strftime('%H:%M:%S')}] Ngrok activo: {url}")
                    last_url = url
                    consecutive_failures = 0
                elif not url:
                    print(f"⚠️ [{datetime.now().strftime('%H:%M:%S')}] Ngrok corriendo pero API no responde")
                
                # Mostrar heartbeat cada minuto
                if int(time.time()) % 60 == 0:
                    print(f"💓 [{datetime.now().strftime('%H:%M:%S')}] Heartbeat - Ngrok OK")
            
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo monitor de ngrok...")
        print("⚠️ Nota: ngrok seguirá corriendo. Para detenerlo: Stop-Process -Name ngrok")
        sys.exit(0)

if __name__ == "__main__":
    main()
