from flask import Flask, render_template, request, redirect, url_for, flash, Response
from database import db, ActivoTIC
import csv
import io

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///activos_tic.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'tu-clave-secreta-aqui'

db.init_app(app)

# Crear tablas
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    activos = ActivoTIC.query.order_by(ActivoTIC.id.desc()).all()
    return render_template('index.html', activos=activos)

@app.route('/agregar', methods=['GET', 'POST'])
def agregar():
    if request.method == 'POST':
        try:
            activo = ActivoTIC(
                tipo_dispositivo=request.form['tipo_dispositivo'],
                dispositivos=request.form['dispositivos'],
                marca=request.form['marca'],
                modelo=request.form['modelo'],
                numero_serie=request.form['numero_serie'],
                procesador=request.form['procesador'],
                generacion=request.form['generacion'],
                velocidad_ghz=request.form['velocidad_ghz'],
                memoria_ram_gb=request.form['memoria_ram_gb'],
                tipo_almacenamiento=request.form['tipo_almacenamiento'],
                capacidad_almacenamiento_gb=request.form['capacidad_almacenamiento_gb'],
                sistema_operativo_version=request.form['sistema_operativo_version'],
                activo_fijo_uam=request.form['activo_fijo_uam'],
                ubicacion=request.form['ubicacion'],
                bloque=request.form['bloque'],
                piso=request.form['piso'],
                espacio=request.form['espacio'],
                puesto_numeracion=request.form['puesto_numeracion'],
                modalidad_laboral=request.form['modalidad_laboral'],
                pais=request.form['pais'],
                departamento=request.form['departamento'],
                municipio=request.form['municipio'],
                barrio=request.form['barrio'],
                direccion_sede=request.form['direccion_sede'],
                direccion_teletrabajo=request.form['direccion_teletrabajo'],
                observaciones_teletrabajo=request.form['observaciones_teletrabajo'],
                estado=request.form['estado'],
                responsable_usuario=request.form['responsable_usuario'],
                fecha_adquisicion=request.form['fecha_adquisicion'],
                comentarios=request.form['comentarios']
            )
            db.session.add(activo)
            db.session.commit()
            flash('Activo agregado exitosamente', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar: {str(e)}', 'danger')
    
    return render_template('agregar.html')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    activo = ActivoTIC.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            activo.tipo_dispositivo = request.form['tipo_dispositivo']
            activo.dispositivos = request.form['dispositivos']
            activo.marca = request.form['marca']
            activo.modelo = request.form['modelo']
            activo.numero_serie = request.form['numero_serie']
            activo.procesador = request.form['procesador']
            activo.generacion = request.form['generacion']
            activo.velocidad_ghz = request.form['velocidad_ghz']
            activo.memoria_ram_gb = request.form['memoria_ram_gb']
            activo.tipo_almacenamiento = request.form['tipo_almacenamiento']
            activo.capacidad_almacenamiento_gb = request.form['capacidad_almacenamiento_gb']
            activo.sistema_operativo_version = request.form['sistema_operativo_version']
            activo.activo_fijo_uam = request.form['activo_fijo_uam']
            activo.ubicacion = request.form['ubicacion']
            activo.bloque = request.form['bloque']
            activo.piso = request.form['piso']
            activo.espacio = request.form['espacio']
            activo.puesto_numeracion = request.form['puesto_numeracion']
            activo.modalidad_laboral = request.form['modalidad_laboral']
            activo.pais = request.form['pais']
            activo.departamento = request.form['departamento']
            activo.municipio = request.form['municipio']
            activo.barrio = request.form['barrio']
            activo.direccion_sede = request.form['direccion_sede']
            activo.direccion_teletrabajo = request.form['direccion_teletrabajo']
            activo.observaciones_teletrabajo = request.form['observaciones_teletrabajo']
            activo.estado = request.form['estado']
            activo.responsable_usuario = request.form['responsable_usuario']
            activo.fecha_adquisicion = request.form['fecha_adquisicion']
            activo.comentarios = request.form['comentarios']
            
            db.session.commit()
            flash('Activo actualizado exitosamente', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')
    
    return render_template('editar.html', activo=activo)

@app.route('/ver/<int:id>')
def ver(id):
    activo = ActivoTIC.query.get_or_404(id)
    return render_template('ver.html', activo=activo)

@app.route('/eliminar/<int:id>')
def eliminar(id):
    try:
        activo = ActivoTIC.query.get_or_404(id)
        db.session.delete(activo)
        db.session.commit()
        flash('Activo eliminado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar: {str(e)}', 'danger')
    
    return redirect(url_for('index'))

@app.route('/exportar_csv')
def exportar_csv():
    activos = ActivoTIC.query.all()
    
    # Crear archivo CSV en memoria
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Escribir encabezados
    writer.writerow([
        'ID', 'Tipo de dispositivo', 'Dispositivos', 'Marca', 'Modelo', 'Número de serie',
        'Procesador', 'Generación', 'Velocidad (GHz)', 'Memoria RAM (GB)', 'Tipo de almacenamiento',
        'Capacidad almacenamiento (GB)', 'Sistema operativo/versión', 'Activo Fijo UAM', 'Ubicación',
        'Bloque', 'Piso', 'Espacio', 'Puesto/Numeración', 'Modalidad laboral', 'País',
        'Departamento', 'Municipio', 'Barrio', 'Dirección Sede', 'Dirección Teletrabajo',
        'Observaciones Teletrabajo', 'Estado', 'Responsable/usuario', 'Fecha adquisición', 'Comentarios'
    ])
    
    # Escribir datos
    for activo in activos:
        writer.writerow([
            activo.id, activo.tipo_dispositivo, activo.dispositivos, activo.marca, activo.modelo,
            activo.numero_serie, activo.procesador, activo.generacion, activo.velocidad_ghz,
            activo.memoria_ram_gb, activo.tipo_almacenamiento, activo.capacidad_almacenamiento_gb,
            activo.sistema_operativo_version, activo.activo_fijo_uam, activo.ubicacion,
            activo.bloque, activo.piso, activo.espacio, activo.puesto_numeracion,
            activo.modalidad_laboral, activo.pais, activo.departamento, activo.municipio,
            activo.barrio, activo.direccion_sede, activo.direccion_teletrabajo,
            activo.observaciones_teletrabajo, activo.estado, activo.responsable_usuario,
            activo.fecha_adquisicion, activo.comentarios
        ])
    
    # Preparar respuesta
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=activos_tic.csv"}
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)