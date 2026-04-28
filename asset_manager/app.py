from flask import Flask, render_template, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import csv
import io
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///assets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo de Activo Tecnológico
class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)
    device_type = db.Column(db.String(50), nullable=False)
    brand = db.Column(db.String(100))
    model = db.Column(db.String(100))
    serial_number = db.Column(db.String(100))
    processor = db.Column(db.String(200))
    memory = db.Column(db.String(50))
    operating_system = db.Column(db.String(100))
    location = db.Column(db.String(100))
    assigned_to = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(50), default='Activo')
    notes = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'device_type': self.device_type,
            'brand': self.brand,
            'model': self.model,
            'serial_number': self.serial_number,
            'processor': self.processor,
            'memory': self.memory,
            'operating_system': self.operating_system,
            'location': self.location,
            'assigned_to': self.assigned_to,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'status': self.status,
            'notes': self.notes
        }

# Crear tablas
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/reports')
def reports():
    return render_template('reports.html')

# API para agregar/actualizar activo
@app.route('/api/asset', methods=['POST'])
def save_asset():
    try:
        data = request.json
        
        # Buscar si ya existe un activo con el mismo código
        existing_asset = Asset.query.filter_by(code=data['code']).first()
        
        if existing_asset:
            # Actualizar activo existente
            for key, value in data.items():
                if hasattr(existing_asset, key):
                    setattr(existing_asset, key, value)
            
            existing_asset.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'success': True, 'message': 'Activo actualizado exitosamente', 'asset': existing_asset.to_dict()})
        else:
            # Crear nuevo activo
            new_asset = Asset(**data)
            db.session.add(new_asset)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Activo creado exitosamente', 'asset': new_asset.to_dict()})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

# API para obtener todos los activos
@app.route('/api/assets', methods=['GET'])
def get_assets():
    assets = Asset.query.all()
    return jsonify([asset.to_dict() for asset in assets])

# API para buscar activo por código
@app.route('/api/asset/<code>', methods=['GET'])
def get_asset(code):
    asset = Asset.query.filter_by(code=code).first()
    if asset:
        return jsonify(asset.to_dict())
    return jsonify({'error': 'Activo no encontrado'}), 404

# API para eliminar activo
@app.route('/api/asset/<int:id>', methods=['DELETE'])
def delete_asset(id):
    try:
        asset = Asset.query.get_or_404(id)
        db.session.delete(asset)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Activo eliminado exitosamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

# Generar y descargar reporte CSV
@app.route('/api/report/csv', methods=['GET'])
def download_csv_report():
    try:
        # Obtener filtros de la solicitud
        device_type = request.args.get('device_type')
        location = request.args.get('location')
        status = request.args.get('status')
        
        # Construir consulta
        query = Asset.query
        if device_type:
            query = query.filter_by(device_type=device_type)
        if location:
            query = query.filter_by(location=location)
        if status:
            query = query.filter_by(status=status)
        
        assets = query.all()
        
        # Crear archivo CSV en memoria
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Escribir encabezados
        writer.writerow([
            'Código', 'Tipo de Dispositivo', 'Marca', 'Modelo', 'Número de Serie',
            'Procesador', 'Memoria', 'Sistema Operativo', 'Ubicación', 'Asignado a',
            'Estado', 'Notas', 'Fecha de Creación'
        ])
        
        # Escribir datos
        for asset in assets:
            writer.writerow([
                asset.code,
                asset.device_type,
                asset.brand,
                asset.model,
                asset.serial_number,
                asset.processor,
                asset.memory,
                asset.operating_system,
                asset.location,
                asset.assigned_to,
                asset.status,
                asset.notes,
                asset.created_at.strftime('%Y-%m-%d %H:%M:%S') if asset.created_at else ''
            ])
        
        # Preparar respuesta
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'reporte_activos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Obtener estadísticas para reportes
@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        total_assets = Asset.query.count()
        assets_by_type = db.session.query(Asset.device_type, db.func.count(Asset.id)).group_by(Asset.device_type).all()
        assets_by_location = db.session.query(Asset.location, db.func.count(Asset.id)).group_by(Asset.location).all()
        assets_by_status = db.session.query(Asset.status, db.func.count(Asset.id)).group_by(Asset.status).all()
        
        return jsonify({
            'total_assets': total_assets,
            'by_type': dict(assets_by_type),
            'by_location': dict(assets_by_location),
            'by_status': dict(assets_by_status)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)