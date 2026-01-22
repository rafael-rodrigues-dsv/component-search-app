// migrated from bairros_grid.js
(function(){
    let PAGE_SIZE = 10;
    let currentPage = 1;
    let data = Array.from({length:28}).map((_,i)=>({id:i+1,name:`Bairro ${i+1}`}));

    function render(){
        const per = parseInt(document.getElementById('bai-page-size').value,10);
        const start = (currentPage-1)*per;
        const items = data.slice(start,start+per);
        const tbody = document.querySelector('#bai-table tbody');
        if(!tbody) return;
        // preserve new-row editor if present
        const newRow = tbody.querySelector('#bai-new-row');
        // clear existing rows
        while(tbody.firstChild) tbody.removeChild(tbody.firstChild);
        if(newRow) tbody.appendChild(newRow);
        // append items
        items.forEach(it=>{
            const tr = document.createElement('tr');
            tr.innerHTML = `<td>${it.id}</td><td>${it.name}</td><td><button class="btn btn-sm btn-outline-danger remove" data-id="${it.id}"><i class="fas fa-trash"></i></button></td>`;
            tbody.appendChild(tr);
        });
        const max = Math.max(1, Math.ceil(data.length/per));
        document.getElementById('pagination-bai-info').textContent = `Página ${currentPage} de ${max}`;
        document.getElementById('btn-prev-bai').disabled = currentPage<=1;
        document.getElementById('btn-next-bai').disabled = currentPage>=max;
        Array.from(document.querySelectorAll('#bai-table .remove')).forEach(b=> b.addEventListener('click', (e)=>{ const id=+e.currentTarget.dataset.id; data = data.filter(x=>x.id!==id); if(currentPage>Math.ceil(data.length/per)) currentPage = Math.max(1, Math.ceil(data.length/per)); render(); showToast('Bairro removido','success'); }));
    }

    function showToast(msg, type='success'){
        const container = document.getElementById('toast-container-bai'); if(!container) return;
        const div = document.createElement('div'); div.className = `toast ${type==='success'?'bg-success text-white':''}`; div.innerHTML = `<div class="toast-body">${msg}</div>`; container.appendChild(div); setTimeout(()=>div.remove(), 2500);
    }

    function addBairroLocal(name){ data.unshift({id:Date.now(), name}); if(currentPage>1) currentPage=1; render(); showToast('Bairro adicionado','success'); }

    function doInit(){
        if(window._bairros_initialized) return; window._bairros_initialized=true;
        const openBtn = document.getElementById('btn-open-bai-editor');
        const newRow = document.getElementById('bai-new-row');
        const cancelBtn = document.getElementById('btn-cancel-bai');
        const okBtn = document.getElementById('btn-add-bai');
        const termInput = document.getElementById('row-new-bai');

        function showEditor(){ if(!newRow) return; newRow.style.display='table-row'; if(termInput) termInput.focus(); }
        function hideEditor(){ if(!newRow) return; newRow.style.display='none'; if(termInput) termInput.value=''; }

        if(openBtn) openBtn.addEventListener('click', (e)=>{ e.preventDefault(); showEditor(); });
        if(cancelBtn) cancelBtn.addEventListener('click', (e)=>{ e.preventDefault(); hideEditor(); });

        if(okBtn) okBtn.addEventListener('click', function(ev){ ev.preventDefault(); if(okBtn.disabled) return; const v = termInput ? termInput.value.trim() : ''; if(!v) return; okBtn.disabled=true; try{ addBairroLocal(v); }finally{ okBtn.disabled=false; hideEditor(); } });

        if(termInput) termInput.addEventListener('keydown', function(e){ if(e.key==='Enter'){ e.preventDefault(); okBtn && okBtn.click(); } else if(e.key==='Escape'){ e.preventDefault(); hideEditor(); } });

        document.getElementById('bai-page-size')?.addEventListener('change', ()=>{ currentPage=1; render(); });
        document.getElementById('btn-prev-bai')?.addEventListener('click', ()=>{ if(currentPage>1) currentPage--; render(); });
        document.getElementById('btn-next-bai')?.addEventListener('click', ()=>{ const per=parseInt(document.getElementById('bai-page-size').value,10); const max=Math.ceil(data.length/per); if(currentPage<max) currentPage++; render(); });

        render();
    }

    window.init_bairros_grid = function(){ try{ doInit(); }catch(e){ console.warn(e); } };
})();
