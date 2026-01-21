(function () {
    // Termos Ativos - client-side logic moved to external JS
    // Reutiliza conexão Socket.IO se já existir (dashboard.html cria uma), para evitar conexões duplicadas
    const socket = (typeof window !== 'undefined' && window.socket) ? window.socket : (typeof io !== 'undefined' ? io() : null);
    if (typeof window !== 'undefined' && !window.socket && socket) window.socket = socket;
    let PAGE_SIZE = 5;
    let offset = 0;
    let currentPage = 1;
    let totalPages = 1;

    function getField(obj, keys) {
        for (const k of keys) {
            if (obj == null) continue;
            if (Object.prototype.hasOwnProperty.call(obj, k)) return obj[k];
            const lower = k.toLowerCase();
            for (const prop of Object.keys(obj)) {
                if (prop.toLowerCase() === lower) return obj[prop];
            }
        }
        return undefined;
    }

    function renderTerms(terms) {
        const tbody = document.querySelector('#terms-table tbody');
        if (!tbody) return;
        tbody.innerHTML = '';
        terms.forEach(t => {
            const tr = document.createElement('tr');

            const tdId = document.createElement('td');
            tdId.textContent = getField(t, ['ID_BASE','id_base','Id_Base','ID','id']) || '';

            const tdTerm = document.createElement('td');
            tdTerm.textContent = getField(t, ['TERMO_BUSCA','termo_busca','TERMO','termo','TERMO_COMPLETO','termo_completo']) || '';

            const tdCat = document.createElement('td');
            tdCat.textContent = getField(t, ['CATEGORIA','categoria','CATEGORY','categ']) || '';

            const tdActions = document.createElement('td');
            const btnDelete = document.createElement('button');
            btnDelete.className = 'btn btn-sm btn-outline-danger';
            btnDelete.style.marginLeft = '8px';
            btnDelete.textContent = 'Remover';
            const btnId = getField(t, ['ID_BASE','id_base','ID','id']) || null;
            if (btnId) btnDelete.dataset.id = String(btnId);
            btnDelete.addEventListener('click', () => {
                const idToDelete = btnDelete.dataset.id ? Number(btnDelete.dataset.id) : null;
                if (!idToDelete) { console.warn('ID do termo inválido. Não foi possível remover.'); return; }
                deleteTerm(idToDelete);
            });

            tdActions.appendChild(btnDelete);

            tr.appendChild(tdId);
            tr.appendChild(tdTerm);
            tr.appendChild(tdCat);
            tr.appendChild(tdActions);

            tbody.appendChild(tr);
        });
    }

    async function loadTerms(reload = false, page = null) {
        try {
            if (reload) {
                offset = 0;
                currentPage = 1;
                const tbody = document.querySelector('#terms-table tbody');
                if (tbody) tbody.innerHTML = '';
            }

            if (page && Number.isInteger(page) && page > 0) {
                offset = (page - 1) * PAGE_SIZE;
            }

            const url = `/api/terms?limit=${PAGE_SIZE}&offset=${offset}`;
            console.debug(`[UI] Fetching terms: page=${page || currentPage}, url=${url}`);
            const res = await fetch(url);
            if (!res.ok) {
                console.error('Falha ao carregar termos', res.status);
                return;
            }
            const json = await res.json();
            console.debug('[DEBUG] /api/terms response:', json);

            if (json && json.pagination) {
                currentPage = json.pagination.current_page;
                totalPages = json.pagination.total_pages;
                const infoEl = document.getElementById('pagination-info');
                if (infoEl) infoEl.textContent = `Página ${currentPage} de ${totalPages}`;
                const prevBtn = document.getElementById('btn-prev-page');
                const nextBtn = document.getElementById('btn-next-page');
                if (prevBtn) prevBtn.disabled = !json.pagination.has_previous;
                if (nextBtn) nextBtn.disabled = !json.pagination.has_next;
                offset = (currentPage - 1) * PAGE_SIZE;
            }

            if (json.terms && Array.isArray(json.terms)) {
                renderTerms(json.terms);
            }
        } catch (e) {
            console.error('Erro loadTerms', e);
        }
    }

    function gotoPage(page) {
        if (!Number.isInteger(page) || page < 1) return;
        if (page > totalPages) return;
        console.debug(`[UI] gotoPage: requesting page ${page}`);
        loadTerms(false, page);
    }

    function showToast(message, type = 'success', title = '') {
        try {
            const container = document.getElementById('toast-container');
            if (!container) return;
            const toastId = 'toast-' + Date.now();
            const bg = type === 'success' ? 'bg-success' : (type === 'warning' ? 'bg-warning' : 'bg-danger');
            const textClass = (type === 'success' || type === 'danger') ? 'text-white' : '';
            const toastHTML = `
                <div id="${toastId}" class="toast ${bg} ${textClass}" role="alert" aria-live="assertive" aria-atomic="true" data-delay="3000">
                    <div class="toast-header ${bg} ${textClass}" style="border-bottom:0">
                        ${title ? `<strong class="mr-auto">${title}</strong>` : ''}
                        <small class="text-muted ml-2"></small>
                        <button type="button" class="ml-2 mb-1 close ${textClass}" data-dismiss="toast" aria-label="Fechar"><span aria-hidden="true">&times;</span></button>
                    </div>
                    <div class="toast-body ${textClass}" style="background:transparent;">
                        ${message}
                    </div>
                </div>`;
            const wrapper = document.createElement('div');
            wrapper.innerHTML = toastHTML;
            const toastEl = wrapper.firstElementChild;
            container.appendChild(toastEl);
            const bsToast = bootstrap.Toast.getOrCreateInstance(toastEl);
            bsToast.show();
            toastEl.addEventListener('hidden.bs.toast', () => { try { toastEl.remove(); } catch (e) {} });
        } catch (e) {
            console.debug('Erro ao exibir toast', e);
        }
    }

    async function proposeTerm(termo) {
        try {
            const res = await fetch('/api/terms', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ termo, proposed_by: 'ui' }) });
            const j = await res.json();
            if (j.success) {
                try { const el = document.getElementById('new-term'); if (el) el.value = ''; } catch (e) {}
                loadTerms(true);
                showToast('Proposta enviada', 'success');
            } else {
                console.error('Erro ao propor termo:', j.message || j);
                showToast('Erro ao propor termo: ' + (j.message || ''), 'danger');
            }
        } catch (e) {
            console.error('Erro proposeTerm', e);
            showToast('Erro ao propor termo', 'danger');
        }
    }

    async function addTermDirect(termo) {
        try {
            const res = await fetch('/api/terms/add', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ termo }) });
            const j = await res.json();
            if (j.success) {
                try { const el = document.getElementById('new-term'); if (el) el.value = ''; } catch(e) {}
                loadTerms(true);
                showToast('Termo adicionado', 'success');
            }
            else {
                console.error('Erro ao adicionar termo:', j.message || j);
                showToast('Erro ao adicionar termo: ' + (j.message || ''), 'danger');
            }
        } catch (e) {
            console.error('Erro addTermDirect', e);
            showToast('Erro ao adicionar termo', 'danger');
        }
    }

    async function deleteTerm(id) {
        try {
            if (!id) return console.warn('ID inválido para exclusão');
            const res = await fetch(`/api/terms/${id}`, { method: 'DELETE' });
            const j = await res.json();
            if (j.success) { loadTerms(true); showToast('Termo removido', 'success'); }
            else console.error('Erro ao remover termo:', j.message || j);
            if (j && j.success === false) showToast('Erro ao remover termo', 'danger');
        } catch (e) {
            console.error('Erro deleteTerm', e);
            showToast('Erro ao remover termo', 'danger');
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        const btnLoad = document.getElementById('btn-load-more');
        if (btnLoad) btnLoad.addEventListener('click', function () { loadTerms(false); });

        const btnAdd = document.getElementById('btn-add-term');
        if (btnAdd) btnAdd.addEventListener('click', function () {
            const termoEl = document.getElementById('new-term');
            const termo = termoEl ? termoEl.value.trim() : '';
            if (!termo) return console.warn('Digite um termo');
            addTermDirect(termo);
        });

        try {
            const select = document.getElementById('page-size-select');
            const stored = window.localStorage ? window.localStorage.getItem('terms_page_size') : null;
            if (stored && Number.isInteger(parseInt(stored))) {
                PAGE_SIZE = parseInt(stored);
            }
            if (select) {
                select.value = String(PAGE_SIZE);
                select.addEventListener('change', function () {
                    const v = parseInt(this.value) || 10;
                    PAGE_SIZE = v;
                    try { if (window.localStorage) window.localStorage.setItem('terms_page_size', String(v)); } catch (e) {}
                    loadTerms(true);
                });
            }
        } catch (e) {
            console.debug('Erro ao inicializar page-size selector', e);
        }

        loadTerms(true);
    });

    document.addEventListener('click', function (e) {
        const prev = document.getElementById('btn-prev-page');
        const next = document.getElementById('btn-next-page');
        // Event delegation for prev/next to ensure listeners exist after DOM updates
        if (e.target === prev && currentPage > 1) gotoPage(currentPage - 1);
        if (e.target === next && currentPage < totalPages) gotoPage(currentPage + 1);
    });

    // Registrar listener somente se existir conexão Socket.IO
    if (socket && typeof socket.on === 'function') {
        socket.on('term_change_applied', (data) => { loadTerms(true); });
    }
})();
