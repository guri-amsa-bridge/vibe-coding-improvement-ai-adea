/**
 * 프론트엔드 메인 앱 — API 클라이언트와 렌더러를 조합
 */
import { ApiClient } from './api_client.js';
import { renderUserProfile, renderItemList } from './renderer.js';

const api = new ApiClient('/api');

async function init() {
    const user = await api.getCurrentUser();
    renderUserProfile(user);

    const items = await api.getItems();
    renderItemList(items);
}

document.addEventListener('DOMContentLoaded', init);
