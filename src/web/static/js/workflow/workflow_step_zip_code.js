// workflow_step_zip_code.js - use API to persist reference CEP with confirmation modal
(function(){
  let pendingLookupData = null;

  async function loadCep(){
    try{
      const res = await fetch('/api/config/cep');
      if(!res.ok) return;
      const j = await res.json();
      if(j && j.success){
        const data = j.data || {};
        const cur = document.getElementById('cepCurrent');
        const cidade = document.getElementById('cepCidade');
        const estado = document.getElementById('cepEstado');
        const log = document.getElementById('cepLogradouro');
        if(cur) cur.textContent = data.cep || '(nenhum)';
        const inp = document.getElementById('cepInput');
        if(inp) inp.value = data.cep || '';
        if(cidade) cidade.textContent = data.cidade || '-';
        if(estado) estado.textContent = data.estado || '-';
        if(log) log.textContent = data.logradouro || '-';
        const raioEl = document.getElementById('cepRaioCurrent');
        const raioInput = document.getElementById('cepRaioInput');
        if(raioEl) raioEl.textContent = (data.raio_km !== undefined && data.raio_km !== null) ? String(data.raio_km) : '-';
        if(raioInput) raioInput.value = (data.raio_km !== undefined && data.raio_km !== null) ? String(data.raio_km) : '';
       }
     }catch(e){ console.warn('Erro ao carregar CEP', e); }
   }

  function formatAddress(data){
    // data: { cep, logradouro, bairro, cidade, estado }
    const parts = [];
    if(data.logradouro) parts.push(data.logradouro);
    if(data.bairro) parts.push(data.bairro);
    const cityState = [data.cidade || '', data.estado || ''].filter(Boolean).join('/');
    if(cityState) parts.push(cityState);
    const addr = parts.join(', ');
    return `${addr} (${data.cep || ''})`;
  }

  async function doSaveConfirmed(data){
    try{
      // include raio_km from input if present
      const raioVal = parseInt(document.getElementById('cepRaioInput')?.value || '', 10);
      const payload = { cep: data.cep };
      if(!isNaN(raioVal) && raioVal > 0) payload.raio_km = raioVal;
      const res = await fetch('/api/config/cep', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      const j = await res.json();
      if(res.ok && j.success){
        const d = j.data || {};
        const cur = document.getElementById('cepCurrent');
        const cidade = document.getElementById('cepCidade');
        const estado = document.getElementById('cepEstado');
        const log = document.getElementById('cepLogradouro');
        if(cur) cur.textContent = d.cep || data.cep;
        if(cidade) cidade.textContent = d.cidade || data.cidade || '-';
        if(estado) estado.textContent = d.estado || data.estado || '-';
        if(log) log.textContent = d.logradouro || data.logradouro || '-';
        const raioEl = document.getElementById('cepRaioCurrent');
        const raioInput = document.getElementById('cepRaioInput');
        if(raioEl) raioEl.textContent = (d.raio_km !== undefined && d.raio_km !== null) ? String(d.raio_km) : '-';
        // Keep the input fields populated with the saved values instead of clearing them
        const inp = document.getElementById('cepInput');
        if(inp) inp.value = d.cep || data.cep || inp.value || '';
        if(raioInput) raioInput.value = (d.raio_km !== undefined && d.raio_km !== null) ? String(d.raio_km) : (raioInput.value || '');
       }else{
         alert('Falha ao salvar CEP: ' + (j.message||res.statusText));
       }
     }catch(e){ console.error('Erro ao salvar CEP', e); alert('Erro ao salvar CEP'); }
  }

  async function save(){
    const v = document.getElementById('cepInput')?.value?.trim();
    if(!v){ alert('Informe CEP'); return; }

    // Lookup first
    try{
      const res = await fetch('/api/config/cep/lookup?cep=' + encodeURIComponent(v));
      const j = await res.json();
      if(!res.ok || !j.success){
        alert('Falha ao validar CEP: ' + (j.message || res.statusText));
        return;
      }

      pendingLookupData = j.data || { cep: v };
      const text = formatAddress(pendingLookupData);
      const confirmText = document.getElementById('cepConfirmText');
      if(confirmText) confirmText.textContent = text;

      // Show Bootstrap modal (assumes jQuery + Bootstrap JS present)
      try{
        $('#cepConfirmModal').modal('show');
      }catch(e){
        // fallback: simple confirm
        const ok = window.confirm('Confirmar salvar: ' + text);
        if(ok) doSaveConfirmed(pendingLookupData);
        return;
      }

    }catch(e){ console.error('Erro ao consultar CEP', e); alert('Erro ao validar CEP'); }
  }

  // Hook confirm button
  function setupConfirm(){
    const btn = document.getElementById('cepConfirmBtn');
    if(btn){
      btn.addEventListener('click', function(){
        if(pendingLookupData){
          // Hide modal first
          try{ $('#cepConfirmModal').modal('hide'); }catch(e){}
          doSaveConfirmed(pendingLookupData);
          pendingLookupData = null;
        }
      });
    }
  }

  window.init_define_cep = function(){
    const btn = document.getElementById('saveCep');
    if(btn) btn.addEventListener('click', save);
    setupConfirm();
    loadCep();
  };
 })();
