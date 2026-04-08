from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class ActivoTIC(db.Model):
    __tablename__ = 'activos_tic'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo_dispositivo = db.Column(db.String(50), nullable=False)
    dispositivos = db.Column(db.String(100))
    marca = db.Column(db.String(100))
    modelo = db.Column(db.String(100))
    numero_serie = db.Column(db.String(100), unique=True)
    procesador = db.Column(db.String(100))
    generacion = db.Column(db.String(50))
    velocidad_ghz = db.Column(db.String(20))
    memoria_ram_gb = db.Column(db.String(20))
    tipo_almacenamiento = db.Column(db.String(50))
    capacidad_almacenamiento_gb = db.Column(db.String(50))
    sistema_operativo_version = db.Column(db.String(100))
    activo_fijo_uam = db.Column(db.String(100))
    ubicacion = db.Column(db.String(200))
    bloque = db.Column(db.String(50))
    piso = db.Column(db.String(50))
    espacio = db.Column(db.String(100))
    puesto_numeracion = db.Column(db.String(50))
    modalidad_laboral = db.Column(db.String(50))
    pais = db.Column(db.String(50))
    departamento = db.Column(db.String(50))
    municipio = db.Column(db.String(50))
    barrio = db.Column(db.String(100))
    direccion_sede = db.Column(db.String(200))
    direccion_teletrabajo = db.Column(db.String(200))
    observaciones_teletrabajo = db.Column(db.Text)
    estado = db.Column(db.String(50), default='Activo')
    responsable_usuario = db.Column(db.String(100))
    fecha_adquisicion = db.Column(db.String(20))
    comentarios = db.Column(db.Text)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'tipo_dispositivo': self.tipo_dispositivo,
            'dispositivos': self.dispositivos,
            'marca': self.marca,
            'modelo': self.modelo,
            'numero_serie': self.numero_serie,
            'procesador': self.procesador,
            'generacion': self.generacion,
            'velocidad_ghz': self.velocidad_ghz,
            'memoria_ram_gb': self.memoria_ram_gb,
            'tipo_almacenamiento': self.tipo_almacenamiento,
            'capacidad_almacenamiento_gb': self.capacidad_almacenamiento_gb,
            'sistema_operativo_version': self.sistema_operativo_version,
            'activo_fijo_uam': self.activo_fijo_uam,
            'ubicacion': self.ubicacion,
            'bloque': self.bloque,
            'piso': self.piso,
            'espacio': self.espacio,
            'puesto_numeracion': self.puesto_numeracion,
            'modalidad_laboral': self.modalidad_laboral,
            'pais': self.pais,
            'departamento': self.departamento,
            'municipio': self.municipio,
            'barrio': self.barrio,
            'direccion_sede': self.direccion_sede,
            'direccion_teletrabajo': self.direccion_teletrabajo,
            'observaciones_teletrabajo': self.observaciones_teletrabajo,
            'estado': self.estado,
            'responsable_usuario': self.responsable_usuario,
            'fecha_adquisicion': self.fecha_adquisicion,
            'comentarios': self.comentarios
        }