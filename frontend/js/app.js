let allContacts = [];
let selectedContactId = null;
let allPayments = [];

// Generar siguiente ID automáticamente
async function generateNextAppointmentId() {
    try {
        const response = await fetch('http://localhost:8000/api/payments');
        const data = await response.json();
        
        if (data.success && data.payments.length > 0) {
            allPayments = data.payments;
            
            const testIds = data.payments
                .map(p => p.appointment_id)
                .filter(id => id && id.startsWith('Cita_N'))
                .map(id => {
                    const match = id.match(/Cita_N(\d+)/);
                    return match ? parseInt(match[1]) : 0;
                })
                .filter(num => !isNaN(num));
            
            const maxNumber = testIds.length > 0 ? Math.max(...testIds) : 0;
            const nextNumber = maxNumber + 1;
            const nextId = `Cita_N${String(nextNumber).padStart(3, '0')}`;
            document.getElementById('appointmentId').value = nextId;
            
            console.log(`ID generado: ${nextId}`);
        } else {
            document.getElementById('appointmentId').value = 'Cita_N001';
        }
    } catch (error) {
        console.error('Error generando ID:', error);
        document.getElementById('appointmentId').value = 'Cita_N001';
    }
}

// Cargar contactos
async function loadContacts() {
    try {
        const response = await fetch('http://localhost:8000/api/contacts');
        const data = await response.json();
        
        const listContainer = document.getElementById('contact-list');
        
        if (data.success && data.contacts.length > 0) {
            allContacts = data.contacts;
            document.getElementById('total-contacts').textContent = data.contacts.length;
            renderContacts(allContacts);
        } else {
            document.getElementById('total-contacts').textContent = '0';
            listContainer.innerHTML = '<div class="no-data" style="padding: 20px;">No hay contactos disponibles</div>';
        }
    } catch (error) {
        console.error('Error cargando contactos:', error);
        showAlert('error', 'Error cargando contactos de GoHighLevel', 'alert-create');
    }
}

// Renderizar contactos
function renderContacts(contacts) {
    const listContainer = document.getElementById('contact-list');
    
    if (contacts.length === 0) {
        listContainer.innerHTML = '<div class="no-data" style="padding: 20px;">No se encontraron contactos</div>';
        return;
    }
    
    listContainer.innerHTML = contacts.map(contact => {
        const tags = contact.tags || [];
        const tagsHtml = tags.length > 0 
            ? `<div class="contact-tags">
                ${tags.map(tag => `<span class="tag ${tag === 'pago_confirmado' ? 'paid' : ''}">${tag}</span>`).join('')}
               </div>`
            : '<div class="contact-tags"><span class="tag">Sin etiquetas</span></div>';
        
        return `
            <div class="contact-item" data-id="${contact.id}" data-name="${contact.name}" data-email="${contact.email}">
                <div class="contact-name">${contact.name}</div>
                ${contact.email ? `<div class="contact-email">${contact.email}</div>` : ''}
                ${tagsHtml}
            </div>
        `;
    }).join('');
    
    document.querySelectorAll('.contact-item').forEach(item => {
        item.addEventListener('click', () => selectContact(item));
    });
}

// Seleccionar contacto
function selectContact(item) {
    document.querySelectorAll('.contact-item').forEach(el => {
        el.classList.remove('selected');
        el.classList.add('hidden');
    });
    
    item.classList.add('selected');
    item.classList.remove('hidden');
    selectedContactId = item.dataset.id;
    document.getElementById('contactId').value = selectedContactId;
    
    document.getElementById('searchContact').style.display = 'none';
    document.getElementById('contact-list').classList.add('collapsed');
    
    const tags = item.querySelectorAll('.tag');
    const tagsHtml = tags.length > 0 
        ? `<div class="contact-tags" style="margin-top: 8px;">${Array.from(tags).map(tag => tag.outerHTML).join('')}</div>`
        : '';
    
    const detailsDiv = document.getElementById('selected-contact-details');
    detailsDiv.innerHTML = `
        <div class="contact-name">✓ ${item.dataset.name}</div>
        ${item.dataset.email ? `<div class="contact-email">${item.dataset.email}</div>` : ''}
        ${tagsHtml}
    `;
    
    document.getElementById('selected-contact-info').classList.add('show');
}

// Deseleccionar contacto
function deselectContact() {
    selectedContactId = null;
    document.getElementById('contactId').value = '';
    
    document.querySelectorAll('.contact-item').forEach(el => {
        el.classList.remove('selected', 'hidden');
    });
    
    document.getElementById('searchContact').style.display = 'block';
    document.getElementById('searchContact').value = '';
    document.getElementById('contact-list').classList.remove('collapsed');
    document.getElementById('selected-contact-info').classList.remove('show');
    
    renderContacts(allContacts);
}

// Búsqueda de contactos
document.getElementById('searchContact').addEventListener('input', (e) => {
    const search = e.target.value.toLowerCase();
    
    if (search === '') {
        renderContacts(allContacts);
        return;
    }
    
    const filtered = allContacts.filter(contact => {
        const name = contact.name.toLowerCase();
        const email = (contact.email || '').toLowerCase();
        const tags = (contact.tags || []).join(' ').toLowerCase();
        
        return name.includes(search) || email.includes(search) || tags.includes(search);
    });
    
    renderContacts(filtered);
});

// Cargar historial de pagos
async function loadPayments() {
    const loadingEl = document.getElementById('loading-history');
    const containerEl = document.getElementById('payments-container');
    const recentEl = document.getElementById('recent-payments');
    
    loadingEl.style.display = 'block';
    containerEl.innerHTML = '';
    
    try {
        const response = await fetch('http://localhost:8000/api/payments');
        const data = await response.json();
        
        loadingEl.style.display = 'none';
        
        if (data.success && data.payments.length > 0) {
            document.getElementById('total-payments').textContent = data.total;
            const approved = data.payments.filter(p => p.status === 'approved').length;
            const pending = data.payments.filter(p => p.status === 'pending').length;
            document.getElementById('approved-payments').textContent = approved;
            document.getElementById('pending-payments').textContent = pending;
            
            const recent = data.payments.slice(0, 3);
            recentEl.innerHTML = recent.map(p => `
                <div style="padding: 10px 0; border-bottom: 1px solid #e2e8f0;">
                    <div style="font-weight: 500; color: #2d3748;">${p.contact_name}</div>
                    <div style="display: flex; justify-content: space-between; margin-top: 4px;">
                        <span>S/ ${p.amount.toFixed(2)}</span>
                        <span class="status-badge status-${p.status}" style="font-size: 0.75rem; padding: 2px 8px;">${p.status}</span>
                    </div>
                </div>
            `).join('');
            
            const table = document.createElement('table');
            table.className = 'payments-table';
            table.innerHTML = `
                <thead>
                    <tr>
                        <th>Nro de Cita</th>
                        <th>Contacto</th>
                        <th>Monto</th>
                        <th>Estado</th>
                        <th>Fecha</th>
                        <th>Payment ID</th>
                        <th>Acción</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.payments.map(payment => `
                        <tr>
                            <td style="font-family: monospace; font-size: 0.875rem;">${payment.appointment_id}</td>
                            <td>${payment.contact_name}</td>
                            <td style="font-weight: 500;">S/ ${payment.amount.toFixed(2)}</td>
                            <td><span class="status-badge status-${payment.status}">${payment.status}</span></td>
                            <td style="font-size: 0.875rem; color: #718096;">${new Date(payment.created_at).toLocaleString('es-PE')}</td>
                            <td style="font-family: monospace; font-size: 0.8125rem; color: #718096;">${payment.payment_id || '-'}</td>
                            <td>
                                ${payment.status === 'pending' && payment.init_point 
                                    ? `<a href="${payment.init_point}" target="_blank" class="btn-pay">Pagar Ahora</a>` 
                                    : '-'}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            `;
            containerEl.appendChild(table);
        } else {
            containerEl.innerHTML = '<div class="no-data">No hay pagos registrados</div>';
            recentEl.innerHTML = '<div style="padding: 20px; text-align: center; color: #a0aec0;">Sin pagos</div>';
            document.getElementById('total-payments').textContent = '0';
            document.getElementById('approved-payments').textContent = '0';
            document.getElementById('pending-payments').textContent = '0';
        }
    } catch (error) {
        loadingEl.style.display = 'none';
        console.error('Error cargando pagos:', error);
        containerEl.innerHTML = '<div class="no-data">Error cargando historial</div>';
        recentEl.innerHTML = '<div style="padding: 20px; text-align: center; color: #f56565;">Error</div>';
    }
}

// Mostrar alertas
function showAlert(type, message, alertId) {
    const alert = document.getElementById(alertId);
    alert.className = `alert ${type}`;
    alert.textContent = message;
    alert.style.display = 'block';
    
    setTimeout(() => {
        alert.style.display = 'none';
    }, 5000);
}

// Enviar formulario
document.getElementById('payment-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = {
        appointmentId: formData.get('appointmentId'),
        contactId: formData.get('contactId'),
        amount: parseFloat(formData.get('amount')),
        description: formData.get('description') || 'Cita ReflexoPerú'
    };
    
    const submitBtn = document.getElementById('submit-btn');
    const loadingEl = document.getElementById('loading-create');
    
    submitBtn.disabled = true;
    loadingEl.style.display = 'block';
    
    try {
        const response = await fetch('http://localhost:8000/api/create-payment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        loadingEl.style.display = 'none';
        submitBtn.disabled = false;
        
        if (result.success) {
            showAlert('success', 'Preferencia creada exitosamente. Abriendo Mercado Pago...', 'alert-create');
            
            window.open(result.init_point, '_blank');
            
            document.getElementById('amount').value = '';
            document.getElementById('description').value = 'Cita ReflexoPerú';
            
            deselectContact();
            
            await generateNextAppointmentId();
            
            setTimeout(() => loadPayments(), 1000);
        } else {
            showAlert('error', 'Error: ' + (result.error || 'Error desconocido'), 'alert-create');
        }
    } catch (error) {
        loadingEl.style.display = 'none';
        submitBtn.disabled = false;
        console.error('Error:', error);
        showAlert('error', 'Error de conexión al crear el pago', 'alert-create');
    }
});

// Inicializar aplicación
async function initializeApp() {
    await loadContacts();
    await generateNextAppointmentId();
    await loadPayments();
}

initializeApp();

// Auto-refresh cada 30 segundos
setInterval(loadPayments, 60000);
