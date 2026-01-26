// migrated from bairros_grid.js
(function(){
    // pagination state (same pattern as other grids)
    // default standardized to 5 to align with other grids
    let PAGE_SIZE = 5;
    let currentPage = 1;
    let totalPages = 1;

    // initialize PAGE_SIZE from localStorage or selector
    try{
        const stored = (window.localStorage ? window.localStorage.getItem('bai_page_size') : null);
        const userSet = (window.localStorage ? window.localStorage.getItem('bai_page_size_user_set') : null);
        if(userSet === '1' && stored && Number.isInteger(parseInt(stored,10))){
            PAGE_SIZE = parseInt(stored,10);
        } else {
            const sel = document.getElementById('bai-page-size');
            if(sel && sel.value) PAGE_SIZE = parseInt(sel.value,10) || PAGE_SIZE;
        }
    }catch(e){ PAGE_SIZE = PAGE_SIZE || 5; }

    function showToast(msg, type='success'){
        const container = document.getElementById('toast-container-bai'); if(!container) return;
        const div = document.createElement('div'); div.className = `toast ${type==='success'?'bg-success text-white':''}`; div.innerHTML = `<div class=\"toast-body\">${msg}</div>`; container.appendChild(div); setTimeout(()=>div.remove(), 2500);
    }

    async function fetchAndRender(){
        const offset = (currentPage-1)*PAGE_SIZE;
        const params = new URLSearchParams({ limit: PAGE_SIZE, offset: offset });
        try{
            const res = await fetch(`/api/workflow/neighborhoods?${params.toString()}`);
            const payload = await res.json();
            if(!res.ok){ showToast(payload.message||'Erro ao carregar bairros','error'); return; }
            const items = payload.neighborhoods || [];
            const pagination = payload.pagination || { total: items.length, limit: PAGE_SIZE, offset: offset, total_pages:1, current_page:1 };
            totalPages = pagination.total_pages || 1;
            renderTable(items, pagination);
        }catch(e){ console.error(e); showToast('Erro ao carregar bairros','error'); }
    }

    function renderTable(items, pagination){
        const tbody = document.querySelector('#bai-table tbody');
        if(!tbody) return;
        while(tbody.firstChild) tbody.removeChild(tbody.firstChild);
        items.forEach(it=>{
            const tr = document.createElement('tr');
            const idCell = `<td>${it.id !== undefined && it.id !== null ? it.id : ''}</td>`;
            const nameCell = `<td>${(it.name||'').replace(/</g,'&lt;')}</td>`;
            const cityCell = `<td>${(it.city||'').replace(/</g,'&lt;')}</td>`;
            const ufCell = `<td>${(it.uf||'').replace(/</g,'&lt;')}</td>`;
            tr.innerHTML = idCell + nameCell + cityCell + ufCell;
            tbody.appendChild(tr);
        });

        const infoEl = document.getElementById('pagination-bai-info');
        if(infoEl) infoEl.textContent = `Página ${pagination.current_page} de ${pagination.total_pages}`;
        const prev = document.getElementById('btn-prev-bai');
        const next = document.getElementById('btn-next-bai');
        if(prev) prev.disabled = !pagination.has_previous;
        if(next) next.disabled = !pagination.has_next;
    }

    function doInit(){
        if(window._bai_initialized) return; window._bai_initialized = true;

        // consult server to see if UI prefs should be reset after server restart
        try{
            fetch('/api/ui/reset').then(r=>r.json()).then(j=>{
                if(j && j.reset){
                    try{ localStorage.removeItem('bai_page_size'); localStorage.removeItem('bai_page_size_user_set'); }catch(e){}
                    PAGE_SIZE = 5;
                }
            }).catch(()=>{});
        }catch(e){}

        try{
            const sel = document.getElementById('bai-page-size');
            const stored = (window.localStorage ? window.localStorage.getItem('bai_page_size') : null);
            if(stored && Number.isInteger(parseInt(stored,10))) PAGE_SIZE = parseInt(stored,10);
            if(sel){
                sel.value = String(PAGE_SIZE);
                sel.addEventListener('change', function(){
                    const v = parseInt(this.value,10) || 10;
                    PAGE_SIZE = v;
                    try{ if(window.localStorage){ window.localStorage.setItem('bai_page_size', String(v)); window.localStorage.setItem('bai_page_size_user_set','1'); } }catch(e){}
                    currentPage = 1; fetchAndRender();
                });
            }
        }catch(e){ console.debug('bai page-size init', e); }

        document.getElementById('btn-prev-bai')?.addEventListener('click', ()=>{ if(currentPage>1){ currentPage--; fetchAndRender(); } });
        document.getElementById('btn-next-bai')?.addEventListener('click', ()=>{ if(currentPage<totalPages){ currentPage++; fetchAndRender(); } });

        fetchAndRender();
    }

    // Expose refresh wrapper for neighborhoods grid to be triggered by reprocess event.
    window.refreshNeighborhoodsGrid = function(){ try{ currentPage = 1; fetchAndRender(); }catch(e){ console.warn(e); } };

    // Keep same init name used by shims: window.init_bairros_grid
    window.init_bairros_grid = function(){ try{ doInit(); }catch(e){ console.warn(e); } };
})();
