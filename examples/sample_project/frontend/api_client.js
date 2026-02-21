/**
 * API 통신 클라이언트
 */
export class ApiClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    async request(endpoint, options = {}) {
        const res = await fetch(`${this.baseUrl}${endpoint}`, {
            headers: { 'Content-Type': 'application/json' },
            ...options,
        });
        return res.json();
    }

    async login(username, password) {
        return this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
        });
    }

    async getCurrentUser() {
        return this.request('/users/me');
    }

    async getItems(category) {
        const query = category ? `?category=${category}` : '';
        return this.request(`/items${query}`);
    }
}
