// migrated from termos_processados_grid.js
(function(){
    // pagination state
    // default standardized to 5 to align with other grids
    let PAGE_SIZE = 5;
    let currentPage = 1;
    let totalPages = 1;

    try{
        const stored = (window.localStorage ? window.localStorage.getItem('tp_page_size') : null);
        const userSet = (window.localStorage ? window.localStorage.getItem('tp_page_size_user_set') : null);
        if(userSet === '1' && stored && Number.isInteger(parseInt(stored,10))){ PAGE_SIZE = parseInt(stored,10); }
        else { const sel = document.getElementById('tp-page-size'); if(sel && sel.value) PAGE_SIZE = parseInt(sel.value,10) || PAGE_SIZE; }
    }catch(e){ PAGE_SIZE = PAGE_SIZE || 5; }

    function showToast(msg){ const c = document.getElementById('toast-container-tp'); if(!c) return; const d = document.createElement('div'); d.className='toast'; d.innerHTML = `<div class="toast-body">${msg}</div>`; c.appendChild(d); setTimeout(()=>d.remove(),2500); }

    async function fetchAndRender(){
        const offset = (currentPage-1)*PAGE_SIZE;
        const params = new URLSearchParams({ limit: PAGE_SIZE, offset: offset });
        try{
            const res = await fetch(`/api/workflow/processed_terms?${params.toString()}`);
            const payload = await res.json();
            if(!res.ok){ showToast(payload.message||'Erro ao carregar termos'); return; }
            const items = payload.terms || [];
            const pagination = payload.pagination || { total: items.length, limit: PAGE_SIZE, offset: offset, total_pages:1, current_page:1 };
            totalPages = pagination.total_pages || 1;
            renderTable(items, pagination);
        }catch(e){ console.error(e); showToast('Erro ao carregar termos'); }
    }

    function renderTable(items, pagination){
        const tbody = document.querySelector('#tp-table tbody'); if(!tbody) return; while(tbody.firstChild) tbody.removeChild(tbody.firstChild);
        items.forEach(it=>{
            const tr = document.createElement('tr');
            const idCell = `<td>${it.id !== undefined && it.id !== null ? it.id : ''}</td>`;
            const termoCell = `<td>${(it.termo_completo||'').replace(/</g,'&lt;')}</td>`;
            const tipoCell = `<td>${(it.tipo_localidade||'').replace(/</g,'&lt;')}</td>`;
            const statusCell = `<td>${(it.status||'').replace(/</g,'&lt;')}</td>`;
            tr.innerHTML = idCell + termoCell + tipoCell + statusCell;
            tbody.appendChild(tr);
        });
        const info = document.getElementById('pagination-tp-info'); if(info) info.textContent = `Página ${pagination.current_page} de ${pagination.total_pages}`;
        document.getElementById('btn-prev-tp').disabled = !pagination.has_previous;
        document.getElementById('btn-next-tp').disabled = !pagination.has_next;
    }

    function doInit(){ if(window._tp_initialized) return; window._tp_initialized=true;

        try{
            fetch('/api/ui/reset').then(r=>r.json()).then(j=>{
                if(j && j.reset){
                    try{ localStorage.removeItem('tp_page_size'); localStorage.removeItem('tp_page_size_user_set'); }catch(e){}
                    PAGE_SIZE = 5;
                }
            }).catch(()=>{});
        }catch(e){}

         try{ const sel=document.getElementById('tp-page-size'); const stored=(window.localStorage?window.localStorage.getItem('tp_page_size'):null); if(stored&&Number.isInteger(parseInt(stored,10))) PAGE_SIZE=parseInt(stored,10); if(sel){ sel.value=String(PAGE_SIZE); sel.addEventListener('change',function(){ const v=parseInt(this.value,10)||10; PAGE_SIZE=v; try{ if(window.localStorage){ window.localStorage.setItem('tp_page_size',String(v)); window.localStorage.setItem('tp_page_size_user_set','1'); } }catch(e){} currentPage=1; fetchAndRender(); }); } }catch(e){ console.debug('tp page-size init',e); }
        document.getElementById('btn-prev-tp')?.addEventListener('click', ()=>{ if(currentPage>1){ currentPage--; fetchAndRender(); } });
        document.getElementById('btn-next-tp')?.addEventListener('click', ()=>{ if(currentPage<totalPages){ currentPage++; fetchAndRender(); } });
        fetchAndRender();
    }

    // Expose a refresh wrapper so external events can trigger a reload without reinitializing the grid state
    window.refreshProcessedTerms = function(){ try{ currentPage = 1; fetchAndRender(); }catch(e){ console.warn(e); } };

    // init name used by shims
    window.init_termos_processados_grid = function(){ try{ doInit(); }catch(e){ console.warn(e); } };
})();
