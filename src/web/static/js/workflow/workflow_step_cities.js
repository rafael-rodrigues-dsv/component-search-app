// migrated from municipios_grid.js
(function(){
    // pagination state (same pattern as termos grid)
    let PAGE_SIZE = 10;
    let offset = 0;
    let currentPage = 1;
    let totalPages = 1;

    // initialize PAGE_SIZE from localStorage or selector
    try{
        const stored = (window.localStorage ? window.localStorage.getItem('mun_page_size') : null);
        if(stored && Number.isInteger(parseInt(stored,10))){
            PAGE_SIZE = parseInt(stored,10);
        } else {
            const sel = document.getElementById('mun-page-size');
            if(sel && sel.value) PAGE_SIZE = parseInt(sel.value,10) || PAGE_SIZE;
        }
    }catch(e){ PAGE_SIZE = PAGE_SIZE || 10; }

    let totalItems = 0;

    function showToast(msg, type='success'){
        const container = document.getElementById('toast-container-mun'); if(!container) return;
        const div = document.createElement('div'); div.className = `toast ${type==='success'?'bg-success text-white':''}`; div.innerHTML = `<div class=\"toast-body\">${msg}</div>`; container.appendChild(div); setTimeout(()=>div.remove(), 2500);
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
            tr.innerHTML = idCell + nameCell;
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
                    try{ if(window.localStorage) window.localStorage.setItem('mun_page_size', String(v)); }catch(e){}
                    currentPage = 1; fetchAndRender();
                });
            }
        }catch(e){ console.debug('mun page-size init', e); }

        document.getElementById('btn-prev-mun')?.addEventListener('click', ()=>{ if(currentPage>1){ currentPage--; fetchAndRender(); } });
        document.getElementById('btn-next-mun')?.addEventListener('click', ()=>{ if(currentPage<totalPages){ currentPage++; fetchAndRender(); } });

        fetchAndRender();
    }

    window.init_municipios_grid = function(){ try{ doInit(); }catch(e){ console.warn(e); } };
})();
