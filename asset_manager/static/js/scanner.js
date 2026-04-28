let currentCode = '';
let scannerActive = false;

// Inicializar Quagga para escaneo de códigos de barras
function startScanner() {
    if (scannerActive) return;
    
    Quagga.init({
        inputStream: {
            name: "Live",
            type: "LiveStream",
            target: document.querySelector('#scanner-viewport'),
            constraints: {
                facingMode: "environment"
            },
        },
        decoder: {
            readers: [
                "code_128_reader",
                "ean_reader",
                "ean_8_reader",
                "code_39_reader",
                "code_39_vin_reader",
                "codabar_reader",
                "upc_reader",
                "upc_e_reader",
                "i2of5_reader"
            ]
        }
    }, function(err) {
        if (err) {
            console.error(err);
            alert('Error al iniciar la cámara. Por favor, verifique los permisos.');
            return;
        }
        
        Quagga.start();
        scannerActive = true;
        
        document.getElementById('start-scanner').style.display = 'none';
        document.getElementById('stop-scanner').style.display = 'inline-block';
    });

    Quagga.onDetected(function(result) {
        if (result && result.codeResult && result.codeResult.code) {
            currentCode = result.codeResult.code;
            document.getElementById('manual-code').value = currentCode;
            
            // Hacer sonido de confirmación
            playBeepSound();
            
            // Detener escáner y buscar el activo
            stopScanner();
            searchByCode();
        }
    });
}

function stopScanner() {
    if (scannerActive) {
        Quagga.stop();
        scannerActive = false;
        
        document.getElementById('start-scanner').style.display = 'inline-block';
        document.getElementById('stop-scanner').style.display = 'none';
    }
}

function playBeepSound() {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.value = 800;
    oscillator.type = 'square';
    
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.2);
}

// Búsqueda manual por código
function searchByCode() {
    const code = document.getElementById('manual-code').value.trim();
    
    if (!code) {
        showAlert('Por favor, ingrese un código válido', 'error');
        return;
    }
    
    currentCode = code;
    
    // Buscar si el activo ya existe
    fetch(`/api/asset/${code}`)
        .then(response => {
            if (response.status === 404) {
                // Activo no encontrado, mostrar formulario vacío
                showForm(null, code);
            } else if (response.ok) {
                return response.json();
            } else {
                throw new Error('Error al buscar el activo');
            }
        })
        .then(data => {
            if (data) {
                showForm(data, code);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error al buscar el activo', 'error');
        });
}

// Mostrar el formulario con datos
function showForm(asset, code) {
    const form = document.getElementById('asset-form');
    form.style.display = 'block';
    
    document.getElementById('code').value = code;
    
    if (asset) {
        document.getElementById('form-title').textContent = 'Actualizar Activo';
        document.getElementById('asset-id').value = asset.id;
        document.getElementById('device_type').value = asset.device_type;
        document.getElementById('brand').value = asset.brand || '';
        document.getElementById('model').value = asset.model || '';
        document.getElementById('serial_number').value = asset.serial_number || '';
        document.getElementById('processor').value = asset.processor || '';
        document.getElementById('memory').value = asset.memory || '';
        document.getElementById('operating_system').value = asset.operating_system || '';
        document.getElementById('location').value = asset.location || '';
        document.getElementById('assigned_to').value = asset.assigned_to || '';
        document.getElementById('status').value = asset.status;
        document.getElementById('notes').value = asset.notes || '';
        
        toggleComputerFields();
    } else {
        document.getElementById('form-title').textContent = 'Registrar Nuevo Activo';
        document.getElementById('asset-id').value = '';
        document.getElementById('asset-form-data').reset();
        document.getElementById('code').value = code;
        document.getElementById('device_type').value = '';
        document.getElementById('status').value = 'Activo';
        
        document.getElementById('computer-fields').style.display = 'none';
    }
    
    // Hacer scroll al formulario
    form.scrollIntoView({ behavior: 'smooth' });
}

// Mostrar/ocultar campos específicos de computador
function toggleComputerFields() {
    const deviceType = document.getElementById('device_type').value;
    const computerFields = document.getElementById('computer-fields');
    
    if (deviceType === 'Computador' || deviceType === 'Laptop') {
        computerFields.style.display = 'block';
    } else {
        computerFields.style.display = 'none';
        // Limpiar campos específicos de computador
        document.getElementById('processor').value = '';
        document.getElementById('memory').value = '';
        document.getElementById('operating_system').value = '';
    }
}

// Limpiar formulario
function clearForm() {
    document.getElementById('asset-form-data').reset();
    document.getElementById('asset-id').value = '';
    document.getElementById('code').value = '';
    document.getElementById('computer-fields').style.display = 'none';
    document.getElementById('asset-form').style.display = 'none';
}

// Guardar activo
document.getElementById('asset-form-data').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const data = Object.fromEntries(formData.entries());
    
    // Crear objeto con los datos del formulario
    const assetData = {
        code: data.code,
        device_type: data.device_type,
        brand: data.brand,
        model: data.model,
        serial_number: data.serial_number,
        processor: data.processor || null,
        memory: data.memory || null,
        operating_system: data.operating_system || null,
        location: data.location,
        assigned_to: data.assigned_to,
        status: data.status || 'Activo',
        notes: data.notes || null
    };
    
    fetch('/api/asset', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(assetData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            setTimeout(() => {
                clearForm();
                loadAssetsList();
            }, 1000);
        } else {
            showAlert(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error al guardar el activo', 'error');
    });
});

// Cargar lista de activos
function loadAssetsList() {
    fetch('/api/assets')
        .then(response => response.json())
        .then(assets => {
            const tbody = document.getElementById('assets-table-body');
            tbody.innerHTML = '';
            
            assets.forEach(asset => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td><strong>${asset.code}</strong></td>
                    <td>${asset.device_type}</td>
                    <td>${asset.brand || '-'}</td>
                    <td>${asset.location || '-'}</td>
                    <td>${asset.assigned_to || '-'}</td>
                    <td>
                        <span class="status-badge status-${asset.status.toLowerCase().replace(' ', '-')}">
                            ${asset.status}
                        </span>
                    </td>
                    <td>
                        <button class="btn-small btn-edit" onclick="editAsset('${asset.code}')">✏️</button>
                        <button class="btn-small btn-delete" onclick="deleteAsset(${asset.id})">🗑️</button>
                    </td>
                `;
            });
        });
}

// Editar activo
function editAsset(code) {
    document.getElementById('manual-code').value = code;
    searchByCode();
}

// Eliminar activo
function deleteAsset(id) {
    if (!confirm('¿Está seguro de eliminar este activo?')) return;
    
    fetch(`/api/asset/${id}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Activo eliminado exitosamente', 'success');
            loadAssetsList();
        } else {
            showAlert(data.message, 'error');
        }
    });
}

// Mostrar alertas
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    const mainContent = document.querySelector('.main-content');
    mainContent.insertBefore(alertDiv, mainContent.firstChild);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Estadísticas y reportes
function loadStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(stats => {
            document.getElementById('total-assets').textContent = stats.total_assets;
            
            // Crear gráficos
            createChart('type-chart', 'pie', 
                Object.keys(stats.by_type),
                Object.values(stats.by_type),
                'Activos por Tipo'
            );
            
            createChart('location-chart', 'doughnut',
                Object.keys(stats.by_location),
                Object.values(stats.by_location),
                'Activos por Ubicación'
            );
        });
}

function createChart(canvasId, type, labels, data, title) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    new Chart(ctx, {
        type: type,
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    '#667eea', '#764ba2', '#f59e0b', '#10b981', '#ef4444',
                    '#3b82f6', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                title: {
                    display: true,
                    text: title
                }
            }
        }
    });
}

function loadReportTable() {
    const deviceType = document.getElementById('filter-type')?.value || '';
    const location = document.getElementById('filter-location')?.value || '';
    const status = document.getElementById('filter-status')?.value || '';
    
    let url = '/api/assets?';
    if (deviceType) url += `device_type=${deviceType}&`;
    if (location) url += `location=${location}&`;
    if (status) url += `status=${status}&`;
    
    fetch(url)
        .then(response => response.json())
        .then(assets => {
            const tbody = document.getElementById('report-table-body');
            if (tbody) {
                tbody.innerHTML = '';
                
                assets.forEach(asset => {
                    const row = tbody.insertRow();
                    row.innerHTML = `
                        <td>${asset.code}</td>
                        <td>${asset.device_type}</td>
                        <td>${asset.brand || '-'}</td>
                        <td>${asset.model || '-'}</td>
                        <td>${asset.location || '-'}</td>
                        <td>${asset.assigned_to || '-'}</td>
                        <td>${asset.status}</td>
                    `;
                });
            }
        });
}

function downloadReport() {
    const deviceType = document.getElementById('filter-type')?.value || '';
    const location = document.getElementById('filter-location')?.value || '';
    const status = document.getElementById('filter-status')?.value || '';
    
    let url = '/api/report/csv?';
    if (deviceType) url += `device_type=${deviceType}&`;
    if (location) url += `location=${location}&`;
    if (status) url += `status=${status}&`;
    
    window.location.href = url;
}

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    loadAssetsList();
    
    // Permitir escaneo con teclado (lectores de código de barras)
    document.addEventListener('keypress', function(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
            return; // No interferir con inputs normales
        }
        
        // Si el escáner está mapeado a una tecla específica (ej: Enter después de escanear)
        if (e.key === 'Enter' && window.scannerBuffer) {
            document.getElementById('manual-code').value = window.scannerBuffer;
            searchByCode();
            window.scannerBuffer = '';
        }
    });
});