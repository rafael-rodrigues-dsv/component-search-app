// migrated from workflow/termos_grid.js
// This file implements the grid behavior for the workflow 'Define os Termos' step
(function () {
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
        // preserve the new-row if present
        const newRow = tbody.querySelector('#terms-new-row');
        // remove all children
        while (tbody.firstChild) tbody.removeChild(tbody.firstChild);
        if (newRow) tbody.appendChild(newRow);
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

        // Attach handlers for open / ok / cancel and input keydown so editor works after re-render
        try{
            const openBtn = document.getElementById('btn-open-term-editor');
            const newRowEl = document.getElementById('terms-new-row');
            const okBtn = document.getElementById('btn-add-term');
            const cancelBtn = document.getElementById('btn-cancel-term');
            const termInputEl = document.getElementById('row-new-term');
            const catInputEl = document.getElementById('row-new-term-category');

            const showRow = ()=>{ if(newRowEl) { newRowEl.style.display='table-row'; termInputEl && termInputEl.focus(); } };
            const hideRow = ()=>{ if(newRowEl) { newRowEl.style.display='none'; } if(termInputEl) termInputEl.value=''; if(catInputEl) catInputEl.value=''; };

            if(openBtn){ openBtn.onclick = (e)=>{ e.preventDefault(); showRow(); }; }
            if(cancelBtn){ cancelBtn.onclick = (e)=>{ e.preventDefault(); hideRow(); }; }
            if(okBtn){ okBtn.onclick = async (e)=>{ e.preventDefault(); if(okBtn.disabled) return; const termo = termInputEl ? termInputEl.value.trim() : ''; if(!termo) return; const categoria = catInputEl ? (catInputEl.value || 'base') : 'base'; okBtn.disabled = true; try{ await addTermDirect(termo, categoria); }finally{ okBtn.disabled = false; hideRow(); } }; }
            if(termInputEl){ termInputEl.onkeydown = (e)=>{ if(e.key === 'Enter'){ e.preventDefault(); okBtn && okBtn.click(); } else if(e.key === 'Escape'){ e.preventDefault(); hideRow(); } }; }
            if(catInputEl){ catInputEl.onkeydown = (e)=>{ if(e.key === 'Enter'){ e.preventDefault(); okBtn && okBtn.click(); } else if(e.key === 'Escape'){ e.preventDefault(); hideRow(); } }; }
        }catch(e){ /* non-fatal */ }
    }

    async function loadTerms(reload = false, page = null) {
        try {
            if (reload) {
                offset = 0;
                currentPage = 1;
            }

            if (page && Number.isInteger(page) && page > 0) {
                offset = (page - 1) * PAGE_SIZE;
            }

            const url = `/api/terms?limit=${PAGE_SIZE}&offset=${offset}`;
            const res = await fetch(url);
            if (!res.ok) {
                console.error('Falha ao carregar termos', res.status);
                return;
            }
            const json = await res.json();

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
        loadTerms(false, page);
    }

    async function addTermDirect(termo, categoria='base') {
        try {
            categoria = (typeof categoria === 'string') ? categoria.trim() : categoria;
            const res = await fetch('/api/terms/add', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ termo, categoria }) });
            const j = await res.json();
            if (j.success) {
                try { const el = document.getElementById('new-term'); if (el) el.value = ''; const cat = document.getElementById('new-term-category'); if (cat) cat.value = ''; } catch(e) {}
                loadTerms(true);
            }
            else {
                console.error('Erro ao adicionar termo:', j.message || j);
            }
        } catch (e) {
            console.error('Erro addTermDirect', e);
        }
    }

    async function deleteTerm(id) {
        try {
            if (!id) return console.warn('ID inválido para exclusão');
            const res = await fetch(`/api/terms/${id}`, { method: 'DELETE' });
            const j = await res.json();
            if (j.success) { loadTerms(true); }
            else console.error('Erro ao remover termo:', j.message || j);
        } catch (e) {
            console.error('Erro deleteTerm', e);
        }
    }

    function doInit(){
        if (window._workflow_terms_initialized) return; // guard against double initialization
        window._workflow_terms_initialized = true;

        const btnLoad = document.getElementById('btn-load-more');
        if (btnLoad) btnLoad.addEventListener('click', function () { loadTerms(false); });

        // Use event delegation to handle open/ok/cancel so handlers survive re-renders
        function showEditorRow(){ const newRow = document.getElementById('terms-new-row'); const termInput = document.getElementById('row-new-term'); if(!newRow) return; newRow.style.display='table-row'; if(termInput) termInput.focus(); }
        function hideEditorRow(){ const newRow = document.getElementById('terms-new-row'); const termInput = document.getElementById('row-new-term'); const catInput = document.getElementById('row-new-term-category'); if(!newRow) return; newRow.style.display='none'; if(termInput) termInput.value=''; if(catInput) catInput.value=''; }

        document.addEventListener('click', function delegatedClick(e){
            const target = e.target;
            // open editor
            if(target && (target.id === 'btn-open-term-editor' || target.closest && target.closest('#btn-open-term-editor'))){
                e.preventDefault(); showEditorRow(); return;
            }
            // cancel
            if(target && (target.id === 'btn-cancel-term' || target.closest && target.closest('#btn-cancel-term'))){
                e.preventDefault(); hideEditorRow(); return;
            }
            // ok (add)
            if(target && (target.id === 'btn-add-term' || target.closest && target.closest('#btn-add-term'))){
                e.preventDefault();
                const okBtn = document.getElementById('btn-add-term');
                if(!okBtn || okBtn.disabled) return;
                const termInput = document.getElementById('row-new-term');
                const catInput = document.getElementById('row-new-term-category');
                const termo = termInput ? termInput.value.trim() : '';
                if(!termo) return console.warn('Digite um termo');
                const categoria = catInput ? (catInput.value || 'base') : 'base';
                okBtn.disabled = true;
                addTermDirect(termo, categoria).finally(()=>{ okBtn.disabled = false; hideEditorRow(); });
                return;
            }
        });

        // Key handling for Enter/Escape inside the row inputs
        document.addEventListener('keydown', function delegatedKey(e){
            const row = document.getElementById('terms-new-row');
            if(!row || row.style.display === 'none') return;
            const active = document.activeElement;
            if(!active) return;
            if(active.id === 'row-new-term' || active.id === 'row-new-term-category'){
                if(e.key === 'Enter'){
                    e.preventDefault(); const okBtn = document.getElementById('btn-add-term'); okBtn && okBtn.click();
                } else if(e.key === 'Escape'){
                    e.preventDefault(); hideEditorRow();
                }
            }
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
    }

    window.init_define_terms = function(){ try{ doInit(); }catch(e){ console.warn('init_define_terms error', e); } };

    document.addEventListener('click', function (e) {
        const prev = document.getElementById('btn-prev-page');
        const next = document.getElementById('btn-next-page');
        if (e.target === prev && currentPage > 1) gotoPage(currentPage - 1);
        if (e.target === next && currentPage < totalPages) gotoPage(currentPage + 1);
    });

    if (socket && typeof socket.on === 'function') {
        socket.on('term_change_applied', (_) => { loadTerms(true); });
    }
})();
