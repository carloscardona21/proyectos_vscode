from flask import Flask, render_template, jsonify, request
from ping3 import ping
import socket
import threading
import json
import time
from datetime import datetime

app = Flask(__name__)

# Archivo para almacenar dispositivos
DISPOSITIVOS_FILE = 'dispositivos.json'
# Estado de los dispositivos en memoria
estado_dispositivos = {}
# Historial de estados
historial_estados = {}

class MonitorRed:
    def __init__(self):
        self.cargar_dispositivos()
        self.iniciar_monitoreo()
    
    def cargar_dispositivos(self):
        """Carga la lista de dispositivos desde archivo JSON"""
        try:
            with open(DISPOSITIVOS_FILE, 'r', encoding='utf-8') as f:
                self.dispositivos = json.load(f)
        except FileNotFoundError:
            # Dispositivos de ejemplo
            self.dispositivos = [
                {"id": 1, "nombre": "Router Principal", "ip": "192.168.1.1", "tipo": "router", "activo": True},
                {"id": 2, "nombre": "Servidor Web", "ip": "192.168.1.10", "tipo": "servidor", "activo": True},
                {"id": 3, "nombre": "Google DNS", "ip": "8.8.8.8", "tipo": "externo", "activo": True},
                {"id": 4, "nombre": "Cloudflare DNS", "ip": "1.1.1.1", "tipo": "externo", "activo": True},
                {"id": 5, "nombre": "Impresora Oficina", "ip": "192.168.1.20", "tipo": "impresora", "activo": True}
            ]
            self.guardar_dispositivos()
    
    def guardar_dispositivos(self):
        """Guarda la lista de dispositivos en archivo JSON"""
        with open(DISPOSITIVOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.dispositivos, f, indent=2, ensure_ascii=False)
    
    def verificar_ip(self, ip):
        """Verifica si una IP responde a ping"""
        try:
            # Intentar ping con timeout de 2 segundos
            respuesta = ping(ip, timeout=2)
            if respuesta is not None:
                return {"estado": "activo", "latencia": round(respuesta * 1000, 2)}
            else:
                return {"estado": "inactivo", "latencia": None}
        except Exception as e:
            return {"estado": "error", "latencia": None, "error": str(e)}
    
    def monitorear_dispositivo(self, dispositivo):
        """Monitorea un dispositivo individual"""
        while dispositivo["activo"]:
            resultado = self.verificar_ip(dispositivo["ip"])
            resultado["timestamp"] = datetime.now().isoformat()
            resultado["nombre"] = dispositivo["nombre"]
            resultado["ip"] = dispositivo["ip"]
            
            # Actualizar estado actual
            estado_dispositivos[dispositivo["id"]] = resultado
            
            # Guardar en historial (mantener últimos 20 estados)
            if dispositivo["id"] not in historial_estados:
                historial_estados[dispositivo["id"]] = []
            
            historial_estados[dispositivo["id"]].append(resultado)
            # Mantener solo los últimos 20 registros
            if len(historial_estados[dispositivo["id"]]) > 20:
                historial_estados[dispositivo["id"]].pop(0)
            
            # Esperar 30 segundos antes de la próxima verificación
            time.sleep(30)
    
    def iniciar_monitoreo(self):
        """Inicia hilos de monitoreo para todos los dispositivos activos"""
        for dispositivo in self.dispositivos:
            if dispositivo["activo"]:
                hilo = threading.Thread(
                    target=self.monitorear_dispositivo,
                    args=(dispositivo,),
                    daemon=True
                )
                hilo.start()
    
    def agregar_dispositivo(self, nombre, ip, tipo):
        """Agrega un nuevo dispositivo a la lista"""
        nuevo_id = max([d["id"] for d in self.dispositivos], default=0) + 1
        nuevo_dispositivo = {
            "id": nuevo_id,
            "nombre": nombre,
            "ip": ip,
            "tipo": tipo,
            "activo": True
        }
        self.dispositivos.append(nuevo_dispositivo)
        self.guardar_dispositivos()
        
        # Iniciar monitoreo para el nuevo dispositivo
        hilo = threading.Thread(
            target=self.monitorear_dispositivo,
            args=(nuevo_dispositivo,),
            daemon=True
        )
        hilo.start()
        
        return nuevo_dispositivo
    
    def eliminar_dispositivo(self, dispositivo_id):
        """Elimina un dispositivo de la lista"""
        self.dispositivos = [d for d in self.dispositivos if d["id"] != dispositivo_id]
        self.guardar_dispositivos()
        
        # Limpiar estados
        if dispositivo_id in estado_dispositivos:
            del estado_dispositivos[dispositivo_id]
        if dispositivo_id in historial_estados:
            del historial_estados[dispositivo_id]

# Inicializar monitor
monitor = MonitorRed()

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/api/dispositivos')
def obtener_dispositivos():
    """API para obtener lista de dispositivos"""
    dispositivos_con_estado = []
    for dispositivo in monitor.dispositivos:
        estado_actual = estado_dispositivos.get(dispositivo["id"], {
            "estado": "verificando",
            "latencia": None,
            "timestamp": None
        })
        dispositivos_con_estado.append({
            **dispositivo,
            "estado_actual": estado_actual
        })
    return jsonify(dispositivos_con_estado)

@app.route('/api/estado/<int:dispositivo_id>')
def obtener_estado(dispositivo_id):
    """API para obtener estado de un dispositivo específico"""
    if dispositivo_id in estado_dispositivos:
        return jsonify(estado_dispositivos[dispositivo_id])
    return jsonify({"error": "Dispositivo no encontrado"}), 404

@app.route('/api/historial/<int:dispositivo_id>')
def obtener_historial(dispositivo_id):
    """API para obtener historial de un dispositivo"""
    if dispositivo_id in historial_estados:
        return jsonify(historial_estados[dispositivo_id])
    return jsonify([])

@app.route('/api/dispositivos', methods=['POST'])
def agregar_dispositivo():
    """API para agregar un nuevo dispositivo"""
    data = request.json
    nombre = data.get('nombre')
    ip = data.get('ip')
    tipo = data.get('tipo', 'servidor')
    
    if not nombre or not ip:
        return jsonify({"error": "Nombre e IP son requeridos"}), 400
    
    # Verificar que la IP no exista ya
    if any(d["ip"] == ip for d in monitor.dispositivos):
        return jsonify({"error": "Ya existe un dispositivo con esta IP"}), 400
    
    nuevo = monitor.agregar_dispositivo(nombre, ip, tipo)
    return jsonify(nuevo), 201

@app.route('/api/dispositivos/<int:dispositivo_id>', methods=['DELETE'])
def eliminar_dispositivo(dispositivo_id):
    """API para eliminar un dispositivo"""
    monitor.eliminar_dispositivo(dispositivo_id)
    return jsonify({"success": True})

@app.route('/api/dispositivos/<int:dispositivo_id>/toggle', methods=['POST'])
def toggle_dispositivo(dispositivo_id):
    """API para activar/desactivar monitoreo de dispositivo"""
    for dispositivo in monitor.dispositivos:
        if dispositivo["id"] == dispositivo_id:
            dispositivo["activo"] = not dispositivo.get("activo", True)
            monitor.guardar_dispositivos()
            return jsonify({"activo": dispositivo["activo"]})
    return jsonify({"error": "Dispositivo no encontrado"}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)