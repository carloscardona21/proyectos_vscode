from flask import Flask, render_template, request, send_file, jsonify
import nmap
import socket
import subprocess
import platform
import csv
import json
from datetime import datetime
from ping3 import ping
import threading
import os

app = Flask(__name__)

# Datos globales
equipos_red = []
escaneo_activo = False

class InventarioEquipos:
    def __init__(self):
        self.equipos = []
    
    def escanear_red_local(self, red=None):
        """Escanea la red local en busca de equipos"""
        if not red:
            # Detecta la red local automáticamente
            red = self.detectar_red_local()
        
        equipos_encontrados = []
        
        # Usando nmap
        try:
            nm = nmap.PortScanner()
            print(f"Escaneando red: {red}")
            nm.scan(hosts=red, arguments='-sn -T4')
            
            for host in nm.all_hosts():
                if nm[host].state() == 'up':
                    info = {
                        'ip': host,
                        'hostname': nm[host].hostname() if nm[host].hostname() else self.obtener_hostname(host),
                        'mac': nm[host]['addresses'].get('mac', 'No disponible'),
                        'estado': 'Activo',
                        'tipo': self.determinar_tipo_equipo(host),
                        'ultimo_escaneo': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'ubicacion': 'Red Corporativa'
                    }
                    
                    # Obtener sistema operativo (básico)
                    info['sistema'] = self.detectar_so(host)
                    equipos_encontrados.append(info)
                    
        except Exception as e:
            print(f"Error en escaneo nmap: {e}")
            # Método alternativo con ping
            equipos_encontrados = self.escanear_con_ping(red)
        
        return equipos_encontrados
    
    def escanear_vpn(self, subredes_vpn):
        """Escanea equipos conectados por VPN"""
        equipos_vpn = []
        
        for subred in subredes_vpn:
            print(f"Escaneando red VPN: {subred}")
            equipos = self.escanear_red_local(subred)
            for equipo in equipos:
                equipo['ubicacion'] = 'VPN - Remoto'
                equipos_vpn.append(equipo)
        
        return equipos_vpn
    
    def detectar_red_local(self):
        """Detecta automáticamente la red local"""
        try:
            hostname = socket.gethostname()
            ip_local = socket.gethostbyname(hostname)
            ip_parts = ip_local.split('.')
            return f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.0/24"
        except:
            return "192.168.1.0/24"  # Red por defecto
    
    def escanear_con_ping(self, red):
        """Método alternativo usando ping"""
        equipos = []
        base_red = red.split('/')[0].rsplit('.', 1)[0]
        
        for i in range(1, 255):
            ip = f"{base_red}.{i}"
            response = ping(ip, timeout=1)
            if response is not None:
                equipos.append({
                    'ip': ip,
                    'hostname': self.obtener_hostname(ip),
                    'mac': 'No detectable con ping',
                    'estado': 'Activo',
                    'tipo': self.determinar_tipo_equipo(ip),
                    'sistema': 'Desconocido',
                    'ultimo_escaneo': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'ubicacion': 'Red Corporativa'
                })
        
        return equipos
    
    def obtener_hostname(self, ip):
        """Obtiene el nombre del equipo por IP"""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except:
            return "Desconocido"
    
    def determinar_tipo_equipo(self, ip):
        """Determina el tipo de equipo basado en puertos comunes"""
        puertos_comunes = {
            22: 'Linux/Unix Server',
            3389: 'Windows Server',
            445: 'Windows PC',
            548: 'Mac',
            80: 'Servidor Web',
            443: 'Servidor Web Seguro'
        }
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            
            for puerto, tipo in puertos_comunes.items():
                result = sock.connect_ex((ip, puerto))
                if result == 0:
                    sock.close()
                    return tipo
            
            sock.close()
            return 'Estación de trabajo'
        except:
            return 'Desconocido'
    
    def detectar_so(self, ip):
        """Intenta detectar el sistema operativo"""
        try:
            import platform
            if platform.system() == 'Windows':
                result = subprocess.run(['ping', '-n', '1', ip], capture_output=True, text=True)
                if result.returncode == 0:
                    # Intenta con TTL para adivinar SO
                    for line in result.stdout.split('\n'):
                        if 'TTL=' in line or 'ttl=' in line:
                            ttl = int(line.split('TTL=')[-1].split()[0])
                            if ttl <= 64:
                                return 'Linux/Unix'
                            elif ttl <= 128:
                                return 'Windows'
                            elif ttl == 255:
                                return 'Solaris/AIX'
            return 'Indeterminado'
        except:
            return 'No detectable'
    
    def exportar_csv(self, equipos):
        """Exporta los datos a CSV"""
        filename = f'inventario_equipos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['ip', 'hostname', 'mac', 'tipo', 'sistema', 'estado', 'ubicacion', 'ultimo_escaneo']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for equipo in equipos:
                writer.writerow(equipo)
        
        return filename

# Instancia del inventario
inventario = InventarioEquipos()

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/escanear', methods=['POST'])
def escanear():
    """Inicia el escaneo de red"""
    global escaneo_activo, equipos_red
    
    if escaneo_activo:
        return jsonify({'error': 'Ya hay un escaneo en progreso'}), 400
    
    escaneo_activo = True
    
    try:
        datos = request.json
        red_local = datos.get('red_local', '')
        redes_vpn = datos.get('redes_vpn', [])
        
        equipos_red = []
        
        # Escanear red local
        if red_local:
            equipos_local = inventario.escanear_red_local(red_local)
            equipos_red.extend(equipos_local)
        
        # Escanear redes VPN
        if redes_vpn:
            equipos_vpn = inventario.escanear_vpn(redes_vpn)
            equipos_red.extend(equipos_vpn)
        
        return jsonify({
            'success': True,
            'equipos': equipos_red,
            'total': len(equipos_red)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        escaneo_activo = False

@app.route('/exportar', methods=['GET'])
def exportar():
    """Exporta los equipos a CSV"""
    if not equipos_red:
        return jsonify({'error': 'No hay datos para exportar'}), 400
    
    filename = inventario.exportar_csv(equipos_red)
    return send_file(filename, as_attachment=True)

@app.route('/equipos', methods=['GET'])
def obtener_equipos():
    """Obtiene la lista de equipos"""
    return jsonify(equipos_red)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)