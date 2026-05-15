const API_URL = 'http://localhost:8000/api';

function getHeaders() {
    const token = localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
    };
}

function normalizeEndpoint(endpoint) {
    return endpoint;
}

async function apiRequest(endpoint, method = 'GET', data = null) {
    const normalizedEndpoint = normalizeEndpoint(endpoint);
    console.log('Request:', `${API_URL}${normalizedEndpoint}`);
    
    const options = {
        method: method,
        headers: getHeaders()
    };
    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }
    const response = await fetch(`${API_URL}${normalizedEndpoint}`, options);
    
    if (response.status === 401) {
        localStorage.removeItem('token');
        window.location.href = 'login.html';
        throw new Error('Not authenticated');
    }
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Request failed');
    }
    return response.json();
}