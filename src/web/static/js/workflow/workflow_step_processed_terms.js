// migrated from termos_processados_grid.js
(function(){
    let PAGE_SIZE = 10;
    let currentPage = 1;
    let data = Array.from({length:83}).map((_,i)=>({id:i+1, termo:`Processado ${i+1}`, status: i%3===0 ? 'OK' : 'IGNORADO'}));

    function render(){
        const per = parseInt(document.getElementById('tp-page-size').value,10);
        const start = (currentPage-1)*per;
        const items = data.slice(start,start+per);
        const tbody = document.querySelector('#tp-table tbody');
        if(!tbody) return;
        tbody.innerHTML = items.map(it=>`<tr><td>${it.id}</td><td>${it.termo}</td><td><span class="badge badge-${it.status==='OK'?'success':'secondary'}">${it.status}</span></td></tr>`).join('');
        const max = Math.max(1, Math.ceil(data.length/per));
        document.getElementById('pagination-tp-info').textContent = `Página ${currentPage} de ${max}`;
        document.getElementById('btn-prev-tp').disabled = currentPage<=1;
        document.getElementById('btn-next-tp').disabled = currentPage>=max;
    }

    function attach(){
        document.getElementById('tp-page-size')?.addEventListener('change', ()=>{ currentPage=1; render(); });
        document.getElementById('btn-prev-tp')?.addEventListener('click', ()=>{ if(currentPage>1) currentPage--; render(); });
        document.getElementById('btn-next-tp')?.addEventListener('click', ()=>{ const per=parseInt(document.getElementById('tp-page-size').value,10); const max=Math.ceil(data.length/per); if(currentPage<max) currentPage++; render(); });
    }

    window.init_termos_processados_grid = function(){ attach(); render(); };
})();
