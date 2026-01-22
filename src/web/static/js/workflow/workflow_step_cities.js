// migrated from municipios_grid.js
(function(){
    let PAGE_SIZE = 10;
    let currentPage = 1;
    let data = Array.from({length:16}).map((_,i)=>({id:i+1,name:`Município ${i+1}`}));

    function render(){
        const per = parseInt(document.getElementById('mun-page-size').value,10);
        const start = (currentPage-1)*per;
        const items = data.slice(start,start+per);
        const tbody = document.querySelector('#mun-table tbody');
        if(!tbody) return;
        // preserve new-row editor if present
        const newRow = tbody.querySelector('#mun-new-row');
        // clear existing rows
        while(tbody.firstChild) tbody.removeChild(tbody.firstChild);
        if(newRow) tbody.appendChild(newRow);
        // append items
        items.forEach(it => {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td>${it.id}</td><td>${it.name}</td><td><button class="btn btn-sm btn-outline-danger remove" data-id="${it.id}"><i class="fas fa-trash"></i></button></td>`;
            tbody.appendChild(tr);
        });
        const max = Math.max(1, Math.ceil(data.length/per));
        document.getElementById('pagination-mun-info').textContent = `Página ${currentPage} de ${max}`;
        document.getElementById('btn-prev-mun').disabled = currentPage<=1;
        document.getElementById('btn-next-mun').disabled = currentPage>=max;
        Array.from(document.querySelectorAll('#mun-table .remove')).forEach(b=> b.addEventListener('click', (e)=>{ const id=+e.currentTarget.dataset.id; data = data.filter(x=>x.id!==id); if(currentPage>Math.ceil(data.length/per)) currentPage = Math.max(1, Math.ceil(data.length/per)); render(); showToast('Município removido','success'); }));
    }

    function showToast(msg, type='success'){
        const container = document.getElementById('toast-container-mun'); if(!container) return;
        const div = document.createElement('div'); div.className = `toast ${type==='success'?'bg-success text-white':''}`; div.innerHTML = `<div class="toast-body">${msg}</div>`; container.appendChild(div); setTimeout(()=>div.remove(), 2500);
    }

    function addMunLocal(name){ data.unshift({id:Date.now(), name}); if(currentPage>1) currentPage=1; render(); showToast('Município adicionado','success'); }

    function doInit(){
        if(window._mun_initialized) return; window._mun_initialized=true;
        const openBtn = document.getElementById('btn-open-mun-editor');
        const newRow = document.getElementById('mun-new-row');
        const cancelBtn = document.getElementById('btn-cancel-mun');
        const okBtn = document.getElementById('btn-add-mun');
        const termInput = document.getElementById('row-new-mun');

        function showEditor(){ if(!newRow) return; newRow.style.display='table-row'; if(termInput) termInput.focus(); }
        function hideEditor(){ if(!newRow) return; newRow.style.display='none'; if(termInput) termInput.value=''; }

        if(openBtn) openBtn.addEventListener('click', (e)=>{ e.preventDefault(); showEditor(); });
        if(cancelBtn) cancelBtn.addEventListener('click', (e)=>{ e.preventDefault(); hideEditor(); });

        if(okBtn) okBtn.addEventListener('click', function(ev){ ev.preventDefault(); if(okBtn.disabled) return; const v = termInput ? termInput.value.trim() : ''; if(!v) return; okBtn.disabled=true; try{ addMunLocal(v); }finally{ okBtn.disabled=false; hideEditor(); } });

        if(termInput) termInput.addEventListener('keydown', function(e){ if(e.key==='Enter'){ e.preventDefault(); okBtn && okBtn.click(); } else if(e.key==='Escape'){ e.preventDefault(); hideEditor(); } });

        document.getElementById('mun-page-size')?.addEventListener('change', ()=>{ currentPage=1; render(); });
        document.getElementById('btn-prev-mun')?.addEventListener('click', ()=>{ if(currentPage>1) currentPage--; render(); });
        document.getElementById('btn-next-mun')?.addEventListener('click', ()=>{ const per=parseInt(document.getElementById('mun-page-size').value,10); const max=Math.ceil(data.length/per); if(currentPage<max) currentPage++; render(); });

        render();
    }

    window.init_municipios_grid = function(){ try{ doInit(); }catch(e){ console.warn(e); } };
})();
