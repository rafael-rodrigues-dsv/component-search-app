// migrated from municipios_grid.js
(function(){
    // pagination state (same pattern as termos grid)
    // default standardized to 5 to align with other grids
    let PAGE_SIZE = 5;
    let currentPage = 1;
    let totalPages = 1;

    // initialize PAGE_SIZE from localStorage or selector
    try{
        // Only honor stored page size if user explicitly changed it before.
        const stored = (window.localStorage ? window.localStorage.getItem('mun_page_size') : null);
        const userSet = (window.localStorage ? window.localStorage.getItem('mun_page_size_user_set') : null);
        if(userSet === '1' && stored && Number.isInteger(parseInt(stored,10))){
            PAGE_SIZE = parseInt(stored,10);
        } else {
            const sel = document.getElementById('mun-page-size');
            if(sel && sel.value) PAGE_SIZE = parseInt(sel.value,10) || PAGE_SIZE;
        }
    }catch(e){ PAGE_SIZE = PAGE_SIZE || 5; }

    let totalItems = 0;

    function showToast(msg, type='success'){
        const container = document.getElementById('toast-container-mun'); if(!container) return;
        const div = document.createElement('div'); div.className = `toast ${type==='success'?'bg-success text-white':''}`; div.innerHTML = `<div class="toast-body">${msg}</div>`; container.appendChild(div); setTimeout(()=>div.remove(), 2500);
    }

    async function fetchAndRender(){
        const offs = (currentPage-1)*PAGE_SIZE;
        const params = new URLSearchParams({ limit: PAGE_SIZE, offset: offs });
        try{
            const res = await fetch(`/api/workflow/cities?${params.toString()}`);
            const payload = await res.json();
            if(!res.ok){ showToast(payload.message||'Erro ao carregar municípios','error'); return; }
            const cities = payload.cities||[];
            const pagination = payload.pagination||{ total: (cities||[]).length, limit: PAGE_SIZE, offset: offs, total_pages:1, current_page:1 };
            totalPages = pagination.total_pages || 1;
            totalItems = pagination.total || (cities||[]).length;
            renderTable(cities, pagination);
        }catch(e){ console.error(e); showToast('Erro ao carregar municípios','error'); }
    }

    function renderTable(items, pagination){
        const tbody = document.querySelector('#mun-table tbody');
        if(!tbody) return;
        while(tbody.firstChild) tbody.removeChild(tbody.firstChild);
        items.forEach(it=>{
            const tr = document.createElement('tr');
            const idCell = `<td>${it.id !== undefined && it.id !== null ? it.id : ''}</td>`;
            const nameCell = `<td>${(it.name||'').replace(/</g,'&lt;')}</td>`;
            const ufCell = `<td>${(it.uf||'').replace(/</g,'&lt;')}</td>`;
            tr.innerHTML = idCell + nameCell + ufCell;
            tbody.appendChild(tr);
        });

        document.getElementById('pagination-mun-info').textContent = `Página ${pagination.current_page} de ${pagination.total_pages}`;
        document.getElementById('btn-prev-mun').disabled = !pagination.has_previous;
        document.getElementById('btn-next-mun').disabled = !pagination.has_next;
    }

    function gotoPage(page){
        if(!Number.isInteger(page) || page < 1) return;
        if(page > totalPages) return;
        currentPage = page;
        fetchAndRender();
    }

    function doInit(){
        if(window._mun_initialized) return; window._mun_initialized=true;

        // check server-driven UI reset (Option A): server returns reset=true once after startup
        try{
            fetch('/api/ui/reset').then(r=>r.json()).then(j=>{
                if(j && j.reset){
                    try{ localStorage.removeItem('mun_page_size'); localStorage.removeItem('mun_page_size_user_set'); }catch(e){}
                    PAGE_SIZE = 5;
                }
            }).catch(()=>{});
        }catch(e){}

        // wire page size selector and persist choice
        try{
            const sel = document.getElementById('mun-page-size');
            const stored = (window.localStorage ? window.localStorage.getItem('mun_page_size') : null);
            if(stored && Number.isInteger(parseInt(stored,10))) PAGE_SIZE = parseInt(stored,10);
            if(sel){
                sel.value = String(PAGE_SIZE);
                sel.addEventListener('change', function(){
                    const v = parseInt(this.value,10) || 10;
                    PAGE_SIZE = v;
                    try{ if(window.localStorage){ window.localStorage.setItem('mun_page_size', String(v)); window.localStorage.setItem('mun_page_size_user_set','1'); } }catch(e){}
                    currentPage = 1; fetchAndRender();
                });
            }
        }catch(e){ console.debug('mun page-size init', e); }

        document.getElementById('btn-prev-mun')?.addEventListener('click', ()=>{ if(currentPage>1){ currentPage--; fetchAndRender(); } });
        document.getElementById('btn-next-mun')?.addEventListener('click', ()=>{ if(currentPage<totalPages){ currentPage++; fetchAndRender(); } });

        fetchAndRender();
    }

    window.refreshCitiesGrid = function(){ try{ currentPage = 1; fetchAndRender(); }catch(e){ console.warn(e); } };

    window.init_municipios_grid = function(){ try{ doInit(); }catch(e){ console.warn(e); } };
})();
