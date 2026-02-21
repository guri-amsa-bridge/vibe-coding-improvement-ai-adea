/**
 * UI 렌더링 유틸리티
 */
export function renderUserProfile(user) {
    const el = document.getElementById('user-profile');
    if (!el || !user) return;
    el.innerHTML = `
        <h2>${user.username}</h2>
        <p>${user.email}</p>
    `;
}

export function renderItemList(items) {
    const el = document.getElementById('item-list');
    if (!el || !items) return;
    el.innerHTML = items
        .map(item => `<div class="item">${item.name} — ${item.price}원</div>`)
        .join('');
}
