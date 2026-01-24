// workflow_step_zip_code.js - use API to persist reference CEP with confirmation modal
(function(){
  let pendingLookupData = null;
  // global buffer for CEP logs (preserve messages until the panel is ready)
  window._cep_log_buffer = window._cep_log_buffer || [];

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

  // prepare socket and attach listeners (idempotent)
   function setupCepSocket() {
    // Try to acquire socket immediately or within a short polling window
    const pollInterval = 200; // ms
    const maxWait = 5000; // ms
    let waited = 0;

    function getImmediateSocket() {
      try{ if (typeof window !== 'undefined' && window.socket) return window.socket; }catch(e){}
      try{ if (typeof window !== 'undefined' && window._cep_socket) return window._cep_socket; }catch(e){}
      try{ if (typeof io !== 'undefined') { window._cep_socket = window._cep_socket || io(); return window._cep_socket; } }catch(e){}
      return null;
    }

    let sock = getImmediateSocket();
    if (sock && window._cep_socket_listening) return { sock: sock, waitForConnect: Promise.resolve(sock) };

    const waitForConnect = new Promise((resolve) => {
      if (sock) { attachListeners(sock); return resolve(sock); }
      const iv = setInterval(() => {
        waited += pollInterval;
        sock = getImmediateSocket();
        if (sock) { clearInterval(iv); attachListeners(sock); try{ flushCepLogBuffer(); removeCepWarningEntries(); }catch(e){} return resolve(sock); }
        if (waited >= maxWait) { clearInterval(iv); // final fallback
          try{ if (typeof io !== 'undefined') { sock = window._cep_socket = window._cep_socket || io(); } }catch(e){ sock = null; }
          if (sock) { attachListeners(sock); try{ flushCepLogBuffer(); removeCepWarningEntries(); }catch(e){} resolve(sock); } else {
            // do not spam UI logs; log to console once
            console.warn('Socket.IO não disponível no cliente — CEP logs poderão não ser exibidos.');
            resolve(null);
          }
        }
      }, pollInterval);
    });

    return { sock: sock, waitForConnect: waitForConnect };

    function attachListeners(active) {
      try{
        const s = active || window._cep_socket;
        if (!s) return;
        // Attach listeners idempotently. We attach both to the provided socket and to window.socket (global) if present.
        // Use flags to avoid duplicate handlers.
        try{
          if(!window._cep_socket_listening){
            window._cep_socket_listening = true;
            try{ s.on('connect', function(){ const el = document.getElementById('cep-logs'); if(el){ el.textContent = new Date().toLocaleTimeString() + ' [INFO] Socket connected\n' + el.textContent; } }); }catch(e){}
            try{ s.on('disconnect', function(){ const el = document.getElementById('cep-logs'); if(el){ el.textContent = new Date().toLocaleTimeString() + ' [INFO] Socket disconnected\n' + el.textContent; } }); }catch(e){}
            try{
              const handler = function(evt){ try{
                // normalize different event shapes
                let text;
                if (!evt) text = '';
                else if (typeof evt === 'string') text = evt;
                else if (evt.message) text = evt.message;
                else if (evt.data) text = (typeof evt.data === 'string') ? evt.data : (evt.data.message || JSON.stringify(evt.data));
                else if (evt.level && evt.message === undefined) text = JSON.stringify(evt);
                else text = JSON.stringify(evt);
                console.debug('[CEP] robot_log received (normalized):', text, evt);
                const el = document.getElementById('cep-logs');
                const ts = new Date().toLocaleTimeString();
                if (el && text) {
                  el.textContent = `${ts} ${text}\n` + el.textContent;
                } else if (text) {
                  // panel not ready — buffer the message (newest first)
                  window._cep_log_buffer = window._cep_log_buffer || [];
                  window._cep_log_buffer.unshift(`${ts} ${text}`);
                }
                // still change indicator when a clear completion message appears
                if(text.indexOf('[OK]') !== -1 && text.indexOf('termos de busca gerados') !== -1){ const indicator = document.getElementById('cep-processing-indicator'); if(indicator){ indicator.textContent = 'Concluído'; indicator.className = 'badge badge-success'; } }
              }catch(e){} };
              s.on('robot_log', handler);
              // also attach to global window.socket if different
              try{ if(typeof window !== 'undefined' && window.socket && window.socket !== s && !window._cep_handler_registered){ window.socket.on('robot_log', handler); window._cep_handler_registered = true; } }catch(e){}
            }catch(e){}
          }
        }catch(e){}
      }catch(e){ }
    }
   }

  async function doSaveConfirmed(data){
    try{
      // include raio_km from input if present
      const raioVal = parseInt(document.getElementById('cepRaioInput')?.value || '', 10);
      const payload = { cep: data.cep };
      if(!isNaN(raioVal) && raioVal > 0) payload.raio_km = raioVal;

      // Check robot status first: do not allow saving when robot is running
      try{
        const st = await fetch('/api/robot/status');
        if(st && st.ok){
          const js = await st.json();
          if(js && js.running){
            alert('Robô em execução. Não é possível atualizar o CEP enquanto o robô estiver ativo.');
            return;
          }
        }
      }catch(e){ /* ignore errors, proceed to attempt save */ }

      // ensure socket is listening and wait shortly for connect so we can capture logs
      const sockInfo = setupCepSocket();
      try{ await sockInfo.waitForConnect; }catch(e){}

      // clear logs and add starter line
      try{
        const el = document.getElementById('cep-logs'); if(el){ el.textContent = new Date().toLocaleTimeString() + ' [INFO] Salvando CEP e iniciando reprocessamento...\n' + el.textContent; }
      }catch(e){}

      // mark processing indicator
      try{ const indicator = document.getElementById('cep-processing-indicator'); if(indicator){ indicator.textContent = 'Salvando...'; indicator.className = 'badge badge-warning'; } }catch(e){}

      // Save CEP (no automatic destructive reset here)
      const res = await fetch('/api/config/cep', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      const j = await res.json();
      if(!(res && res.ok && j && j.success)){
        alert('Falha ao salvar CEP: ' + (j && j.message ? j.message : (res && res.statusText) || 'Erro'));
        try{ const indicator = document.getElementById('cep-processing-indicator'); if(indicator){ indicator.textContent = 'Erro'; indicator.className = 'badge badge-danger'; } }catch(e){}
        return;
      }

      // Update UI with saved row
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
      // Keep inputs populated
      const inp = document.getElementById('cepInput'); if(inp) inp.value = d.cep || data.cep || inp.value || '';
      if(raioInput) raioInput.value = (d.raio_km !== undefined && d.raio_km !== null) ? String(d.raio_km) : (raioInput.value || '');

      // Start CEP processing job via API so socket events will stream to UI
      try{
        const startResp = await fetch('/api/execute', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ action: 'start', job_type: 'cep' }) });
        const startJson = await startResp.json();
        if(startResp.ok && startJson && startJson.success){
          try{ const indicator = document.getElementById('cep-processing-indicator'); if(indicator){ indicator.textContent = 'Em execução'; indicator.className = 'badge badge-warning'; } }catch(e){}
        } else {
          alert('CEP salvo, mas falha ao iniciar reprocessamento: ' + (startJson && startJson.message ? startJson.message : startResp.statusText));
          try{ const indicator = document.getElementById('cep-processing-indicator'); if(indicator){ indicator.textContent = 'Pronto'; indicator.className = 'badge badge-secondary'; } }catch(e){}
        }
      }catch(e){ console.error('Erro ao iniciar job CEP', e); }
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
    // Ensure socket listeners are registered early so we capture logs
    try{ setupCepSocket(); }catch(e){}
    // If dashboard has already created a global socket, attach a handler immediately as a fallback
    try{
      if (typeof window !== 'undefined' && window.socket && !window._cep_handler_registered) {
        const fallbackHandler = function(evt){
          try{
            const text = (evt && evt.message) ? evt.message : '';
            console.debug('[CEP][fallback] robot_log received:', evt);
            if(text.indexOf('[GEO]') !== -1 || text.indexOf('[OK]') !== -1){
              const el = document.getElementById('cep-logs'); if(el){ const ts = new Date().toLocaleTimeString(); el.textContent = `${ts} ${text}\n` + el.textContent; }
            }
            if(text.indexOf('[OK]') !== -1 && text.indexOf('termos de busca gerados') !== -1){ const indicator = document.getElementById('cep-processing-indicator'); if(indicator){ indicator.textContent = 'Concluído'; indicator.className = 'badge badge-success'; } }
          }catch(e){}
        };
        try{ window.socket.on('robot_log', fallbackHandler); window._cep_handler_registered = true; }catch(e){}
      }
    }catch(e){}
    loadCep();
  };
 })();
