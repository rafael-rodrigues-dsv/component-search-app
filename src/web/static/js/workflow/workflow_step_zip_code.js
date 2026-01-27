// workflow_step_zip_code.js - use API to persist reference CEP with confirmation modal
(function(){
  let pendingLookupData = null;
  // global buffer for CEP logs (preserve messages until the panel is ready)
  window._cep_log_buffer = window._cep_log_buffer || [];

  // Flush buffered log lines to the CEP log panel (newest first in buffer)
  function flushCepLogBuffer(){
    try{
      if(!window._cep_log_buffer || !window._cep_log_buffer.length) return;
      const el = document.getElementById('cep-logs');
      if(!el) return;
      // Drain buffer (it stores newest-first); we want newest at top
      while(window._cep_log_buffer.length){
        const line = window._cep_log_buffer.shift();
        if(line) el.textContent = line + '\n' + el.textContent;
      }
    }catch(e){ console.warn('flushCepLogBuffer failed', e); }
  }

  // Remove placeholder warning entries previously injected (optional hygiene)
  function removeCepWarningEntries(){
    try{
      const el = document.getElementById('cep-logs');
      if(!el) return;
      // remove lines like 'Socket.IO não disponível' if present
      const filtered = el.textContent.split('\n').filter(l => l.indexOf('Socket.IO não disponível') === -1).join('\n');
      el.textContent = filtered;
    }catch(e){}
  }

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
    if(!data || typeof data !== 'object'){
      return `(sem endereço) (${(data && data.cep) ? data.cep : ''})`;
    }
    const parts = [];
    if(data.logradouro) parts.push(data.logradouro);
    if(data.bairro) parts.push(data.bairro);
    const cityState = [data.cidade || '', data.estado || ''].filter(Boolean).join('/');
    if(cityState) parts.push(cityState);
    const addr = parts.join(', ');
    return `${addr} (${data.cep || ''})`;
  }

  // Vanilla modal helpers (avoid jQuery/Bootstrap dependency)
  function _createBackdrop(){
    const backdrop = document.createElement('div');
    backdrop.className = 'modal-backdrop fade show';
    backdrop.style.zIndex = 1040;
    return backdrop;
  }

  function showDOMModal(modalEl, options){
    if(!modalEl) return;
    options = options || {};
    const titleEl = modalEl.querySelector('.modal-title');
    const bodyEl = modalEl.querySelector('.modal-body');
    const okBtn = modalEl.querySelector('#cepMessageOk') || modalEl.querySelector('.modal-footer .btn-primary');
    const cancelBtn = modalEl.querySelector('#cepMessageCancel') || modalEl.querySelector('.modal-footer .btn-secondary');

    if(options.title && titleEl) titleEl.textContent = options.title;
    if(options.message && bodyEl){
      // if body contains a <p id=...> use it, otherwise set innerHTML
      const p = bodyEl.querySelector('p');
      if(p) p.textContent = options.message; else bodyEl.textContent = options.message;
    }

    // show/hide cancel
    if(cancelBtn){ cancelBtn.style.display = options.showCancel ? '' : 'none'; }

    // attach handlers
    const cleanup = ()=>{
      try{ modalEl.classList.remove('show'); modalEl.style.display = 'none'; modalEl.setAttribute('aria-hidden','true'); }catch(e){}
      try{ const existing = document.querySelector('.modal-backdrop.fade.show'); if(existing) existing.remove(); }catch(e){}
      try{
        if(okBtn && okBtn._cep_ok_handler){
          okBtn.removeEventListener('click', okBtn._cep_ok_handler);
          okBtn._cep_ok_handler = null;
        }
      }catch(e){}
      try{
        if(cancelBtn && cancelBtn._cep_cancel_handler){
          cancelBtn.removeEventListener('click', cancelBtn._cep_cancel_handler);
          cancelBtn._cep_cancel_handler = null;
        }
      }catch(e){}
      // clear pending global callback
      try{ if(window && window._cep_pending_onok) window._cep_pending_onok = null; }catch(e){}
      console.log('[CEP Modal] Cleanup executado');
    };

    const okHandler = function(ev){ 
      console.log('[CEP Modal] OK button clicked');
      try{ 
        if(typeof window !== 'undefined' && window._cep_pending_onok){ 
          console.log('[CEP Modal] Executando callback pendente');
          try{ window._cep_pending_onok(ev); }catch(e){ console.error('[CEP Modal] Erro no callback:', e); } 
        } 
      }finally{ cleanup(); } 
    };
    const cancelHandler = function(ev){ try{ if(typeof options.onCancel === 'function') options.onCancel(ev); }catch(e){} finally{ cleanup(); } };

    // Store the callback in a shared place (window._cep_pending_onok)
    try{ 
      window._cep_pending_onok = (typeof options.onOk === 'function') ? options.onOk : null; 
      console.log('[CEP Modal] Callback armazenado:', window._cep_pending_onok ? 'SIM' : 'NÃO');
    }catch(e){}
    
    // Attach click handler - remover listener antigo antes de anexar novo
    try{
      if(okBtn){
        // Se já tinha um listener, remover antes de anexar novo
        if(okBtn._cep_ok_handler){
          console.log('[CEP Modal] Removendo listener OK antigo');
          okBtn.removeEventListener('click', okBtn._cep_ok_handler);
          okBtn._cep_ok_handler = null;
        }

        // Anexar novo listener e guardar referência
        okBtn._cep_ok_handler = okHandler;
        okBtn.addEventListener('click', okHandler);
        if(okBtn.dataset) okBtn.dataset.cepOkWired = '1';
        console.log('[CEP Modal] Listener OK anexado (novo)');
      }
    }catch(e){ console.error('[CEP Modal] Erro ao anexar listener OK:', e); }

    try{
      if(cancelBtn){
        // Se já tinha um listener, remover antes de anexar novo
        if(cancelBtn._cep_cancel_handler){
          cancelBtn.removeEventListener('click', cancelBtn._cep_cancel_handler);
          cancelBtn._cep_cancel_handler = null;
        }

        // Anexar novo listener e guardar referência
        cancelBtn._cep_cancel_handler = cancelHandler;
        cancelBtn.addEventListener('click', cancelHandler);
        if(cancelBtn.dataset) cancelBtn.dataset.cepCancelWired = '1';
      }
    }catch(e){}

    // show modal
    try{
      modalEl.style.display = 'block';
      modalEl.classList.add('show');
      modalEl.removeAttribute('aria-hidden');
      // backdrop
      const backdrop = _createBackdrop();
      document.body.appendChild(backdrop);
    }catch(e){ /* ignore */ }
  }

  function hideDOMModal(modalEl){
    if(!modalEl) return;
    try{ modalEl.classList.remove('show'); modalEl.style.display = 'none'; modalEl.setAttribute('aria-hidden','true'); }catch(e){}
    try{ const existing = document.querySelector('.modal-backdrop.fade.show'); if(existing) existing.remove(); }catch(e){}
  }

  // Generic modal helpers using DOM
  function showMessage(title, message){
    try{
      let modal = document.getElementById('cepMessageModal');
      if(!modal) {
        // create a temporary modal dynamically
        modal = createTemporaryModal('cepMessageModal_temp', title || 'Mensagem', message || '', false);
        showDOMModal(modal, { title: title || 'Mensagem', message: message || '', showCancel: false, onOk: function(){ modal.remove(); } });
        return;
      }
      showDOMModal(modal, { title: title || 'Mensagem', message: message || '', showCancel: false });
    }catch(e){
      // last-resort: log to console (avoid native alert)
      console.error('showMessage failed:', e, message);
    }
  }

  function showConfirmModal(title, message, onConfirm){
    try{
      let modal = document.getElementById('cepMessageModal');
      if(!modal){
        // create temporary confirm modal and call onConfirm when OK pressed
        modal = createTemporaryModal('cepMessageModal_temp_confirm', title || 'Confirmar', message || '', true);
        showDOMModal(modal, { title: title || 'Confirmar', message: message || '', showCancel: true, onOk: function(){ try{ onConfirm(); } finally{ modal.remove(); } }, onCancel: function(){ modal.remove(); } });
        return;
      }
      showDOMModal(modal, { title: title || 'Confirmar', message: message || '', showCancel: true, onOk: onConfirm });
    }catch(e){
      console.error('showConfirmModal failed:', e);
      // fallback: call onConfirm directly (do not use native confirm)
      try{ onConfirm(); }catch(err){}
    }
  }

  // helper to create a temporary modal in DOM (returns element)
  function createTemporaryModal(id, title, message, includeCancel){
    const wrapper = document.createElement('div');
    wrapper.id = id;
    wrapper.className = 'modal fade';
    wrapper.setAttribute('tabindex','-1');
    wrapper.setAttribute('role','dialog');
    wrapper.innerHTML = `
      <div class="modal-dialog" role="document">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">${title}</h5>
            <button type="button" class="close" aria-label="Fechar"><span aria-hidden="true">&times;</span></button>
          </div>
          <div class="modal-body"><p>${message}</p></div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" ${includeCancel ? '' : 'style="display:none"'}>Cancelar</button>
            <button type="button" class="btn btn-primary">OK</button>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(wrapper);
    // wire close button
    try{ wrapper.querySelector('.close').addEventListener('click', function(){ hideDOMModal(wrapper); wrapper.remove(); }); }catch(e){}
    return wrapper;
  }

  // prepare socket and attach listeners (idempotent)
  function setupCepSocket() {
    const pollInterval = 200; // ms
    const maxWait = 5000; // ms
    let waited = 0;

    function getImmediateSocket() {
      try { if (typeof window !== 'undefined' && window._cep_socket) return window._cep_socket; } catch(e) {}
      try { if (typeof window !== 'undefined' && window.socket) return window.socket; } catch(e) {}
      try { if (typeof io !== 'undefined') { window._cep_socket = window._cep_socket || io(); return window._cep_socket; } } catch(e) {}
      return null;
    }

    function attachListeners(s) {
      if (!s) return;
      try {
        if (window._cep_socket_listening) return;
        window._cep_socket_listening = true;

        try{ s.on('connect', () => { const el = document.getElementById('cep-logs'); if(el) el.textContent = new Date().toLocaleTimeString() + ' [INFO] Socket connected\n' + el.textContent; try{ flushCepLogBuffer(); }catch(e){} }); } catch(e){}
        try{ s.on('disconnect', () => { const el = document.getElementById('cep-logs'); if(el) el.textContent = new Date().toLocaleTimeString() + ' [INFO] Socket disconnected\n' + el.textContent; }); } catch(e){}

        const logHandler = function(evt){
          try{
            let text = '';
            if (!evt) text = '';
            else if (typeof evt === 'string') text = evt;
            else if (evt.message) text = evt.message;
            else if (evt.data) text = (typeof evt.data === 'string') ? evt.data : (evt.data.message || JSON.stringify(evt.data));
            else text = JSON.stringify(evt);

            // Normalize whitespace
            text = (text || '').trim();
            if(!text) return;

            // Determine if this log is relevant to CEP geolocation panel
            const low = text.toLowerCase();
            const isGeo = text.indexOf('[GEO]') !== -1 || low.indexOf('geolocation') !== -1 || low.indexOf('initial_load') !== -1 || low.indexOf('geo') !== -1;
            const isOk = text.indexOf('[OK]') !== -1 || text.indexOf('termos de busca gerados') !== -1;

            // Only show GEO/OK related lines in the CEP panel to reduce noise
            if(!isGeo && !isOk) {
              // keep in buffer for later if needed but do not render
              window._cep_log_buffer = window._cep_log_buffer || [];
              window._cep_log_buffer.unshift(`${new Date().toLocaleTimeString()} ${text}`);
              return;
            }

            // Render relevant line
            const el = document.getElementById('cep-logs');
            const ts = new Date().toLocaleTimeString();
            if (el) el.textContent = `${ts} ${text}\n` + el.textContent;
            else { window._cep_log_buffer = window._cep_log_buffer || []; window._cep_log_buffer.unshift(`${ts} ${text}`); }

            // If line indicates completion, update indicator
            if(isOk){ const indicator = document.getElementById('cep-processing-indicator'); if(indicator){ indicator.textContent = 'Concluído'; indicator.className = 'badge badge-success'; } }
          }catch(e){}
        };

        const statusHandler = function(payload){
          try{
            const running = !!(payload && payload.running);
            try{ setProcessingState(running); }catch(e){}
            try{ const indicator = document.getElementById('cep-processing-indicator'); if(indicator){ indicator.textContent = running ? 'Em execução' : 'Parado'; indicator.className = running ? 'badge badge-warning' : 'badge badge-secondary'; } }catch(e){}
            if(!running){ try{ loadCep(); }catch(e){} }
          }catch(e){}
        };

        try{ s.on('robot_log', logHandler); } catch(e){}
        try{ s.on('robot_status', statusHandler); } catch(e){}
        // Immediately flush any buffered messages now that handlers are attached
        try{ flushCepLogBuffer(); }catch(e){}

        // also attach to global window.socket if different
        try{
          if(typeof window !== 'undefined' && window.socket && window.socket !== s){
            try{ window.socket.on('robot_log', logHandler); window._cep_handler_registered = true; }catch(e){}
            try{ window.socket.on('robot_status', statusHandler); window._cep_status_handler_registered = true; }catch(e){}
          }
        }catch(e){}

      } catch(e) { /* swallow */ }
    }

    let sock = getImmediateSocket();
    if (sock) { attachListeners(sock); return { sock: sock, waitForConnect: Promise.resolve(sock) }; }

    const waitForConnect = new Promise((resolve) => {
      const iv = setInterval(() => {
        waited += pollInterval;
        sock = getImmediateSocket();
        if (sock) { clearInterval(iv); attachListeners(sock); try{ flushCepLogBuffer(); }catch(e){} try{ removeCepWarningEntries(); }catch(e){} return resolve(sock); }
        if (waited >= maxWait) { clearInterval(iv); try{ if (typeof io !== 'undefined') { sock = window._cep_socket = window._cep_socket || io(); } }catch(e){} if(sock){ attachListeners(sock); resolve(sock); } else { console.warn('Socket.IO não disponível no cliente — CEP logs poderão não ser exibidos.'); resolve(null); } }
      }, pollInterval);
    });

    return { sock: sock, waitForConnect: waitForConnect };
  }

  // helper to enable/disable controls and show a small spinner in the Save button
  function setProcessingState(isProcessing){
    try{
      const saveBtn = document.getElementById('saveCep');
      const confirmBtn = document.getElementById('cepConfirmBtn');
      if(saveBtn){
        if(isProcessing){
          saveBtn.setAttribute('disabled','true');
          // add spinner if not present
          if(!saveBtn.querySelector('.spinner-border')){
            const sp = document.createElement('span');
            sp.className = 'spinner-border spinner-border-sm ml-2';
            sp.setAttribute('role','status');
            sp.setAttribute('aria-hidden','true');
            saveBtn.appendChild(sp);
          }
        } else {
          saveBtn.removeAttribute('disabled');
          // remove spinner
          const sp = saveBtn.querySelector('.spinner-border'); if(sp) sp.remove();
        }
      }
      if(confirmBtn){
        if(isProcessing) confirmBtn.setAttribute('disabled','true'); else confirmBtn.removeAttribute('disabled');
      }
      // Also disable generic modal primary buttons to avoid duplicated OK on temporary modals
      try{
        const modalPrimary = document.querySelectorAll('.modal-footer .btn-primary');
        modalPrimary.forEach(function(b){ if(isProcessing) b.setAttribute('disabled','true'); else b.removeAttribute('disabled'); });
      }catch(e){}
    }catch(e){ console.warn('setProcessingState failed', e); }
  }

  async function doSaveConfirmed(data){
    // Prevent re-entrancy / double-submit - ROBUST GUARD
    if(window._cep_processing){
      console.warn('[CEP] doSaveConfirmed: já processando, ignorando chamada duplicada');
      return;
    }
    
    // Set processing flag IMMEDIATELY to block any concurrent calls
    window._cep_processing = true;
    
    // Additional guard to ensure only one network request is sent
    if(window._cep_request_sent){
      console.warn('[CEP] doSaveConfirmed: requisição já enviada, ignorando duplicata');
      window._cep_processing = false;
      return;
    }
    
    // Log entry for debugging
    console.log('[CEP] doSaveConfirmed: iniciando processamento único');
    // set UI processing state
    try{ setProcessingState(true); }catch(e){}
    let serverAccepted = false; // mark if backend accepted request
    try{
      // mark request as sent (pre-network)
      window._cep_request_sent = true;
      // If data is null (possible when confirm handlers fire twice), fallback to reading input
      if(!data || typeof data !== 'object'){
        const v = document.getElementById('cepInput')?.value?.trim();
        if(!v){
          showMessage('Erro', 'Dados do CEP inválidos.');
          window._cep_processing = false;
          window._cep_request_sent = false;
          return;
        }
        data = { cep: v };
      }

      // Extract cep safely
      let cepValue = null;
      try{
        if(data && typeof data === 'object' && data.cep) cepValue = data.cep;
        if(!cepValue) cepValue = document.getElementById('cepInput')?.value?.trim() || null;
      }catch(e){ cepValue = document.getElementById('cepInput')?.value?.trim() || null; }
      console.debug('[CEP] doSaveConfirmed using cepValue=', cepValue, 'data=', data);
      if(!cepValue){ showMessage('Erro', 'CEP inválido.'); window._cep_processing = false; return; }

      // include raio_km from input if present
      const raioVal = parseInt(document.getElementById('cepRaioInput')?.value || '', 10);
      const payload = { cep: cepValue };
      if(!isNaN(raioVal) && raioVal > 0) payload.raio_km = raioVal;

      // clear pending lookup immediately to avoid races from duplicated handlers
      try{ pendingLookupData = null; }catch(e){}

      // Check robot status first: do not allow saving when robot is running
      try{
        const st = await fetch('/api/robot/status');
        if(st && st.ok){
          const js = await st.json();
          if(js && js.running){
            showMessage('Aviso', 'Robô em execução. Não é possível atualizar o CEP enquanto o robô estiver ativo.');
            window._cep_processing = false;
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

      // Save CEP and request a full reprocess (reset + initialize) on the server
      // This will instruct the backend to clear data (preserving CEP config) and run the startup flow
      payload.reset = true;
      console.log('[FETCH] 🚀 Chamando API /api/config/cep com payload:', payload);
      const res = await fetch('/api/config/cep', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      console.log('[FETCH] ✅ API /api/config/cep respondeu com status:', res.status);

      // Safely parse JSON body (backend may return empty body or non-JSON in some cases)
      let j = null;
      try{
        const text = await res.text();
        if(text && text.trim().length > 0){
          try{ j = JSON.parse(text); }catch(e){
            console.warn('Resposta não-JSON ao salvar CEP:', text);
          }
        }
      }catch(e){ console.warn('Falha ao ler corpo da resposta:', e); }

      // If status indicates failure, prefer showing backend message if available
      if(!res.ok){
        const msg = (j && j.message) ? j.message : `Falha ao salvar CEP (status ${res.status})`;
        showMessage('Erro', msg);
        try{ const indicator = document.getElementById('cep-processing-indicator'); if(indicator){ indicator.textContent = 'Erro'; indicator.className = 'badge badge-danger'; } }catch(e){}
        window._cep_processing = false;
        return;
      }

      // mark server accepted
      serverAccepted = true;

      // If res.ok but j exists and indicates success false, show message
      if(j && j.success === false){
        const msg = j.message || 'Falha ao salvar CEP';
        showMessage('Erro', msg);
        try{ const indicator = document.getElementById('cep-processing-indicator'); if(indicator){ indicator.textContent = 'Erro'; indicator.className = 'badge badge-danger'; } }catch(e){}
        window._cep_processing = false;
        return;
      }

      // Success path: prefer data from parsed JSON, fallback to provided data
      const d = (j && typeof j.data === 'object' && j.data !== null) ? j.data : (data || {});

      // Update UI with saved row
      try{
        const cur = document.getElementById('cepCurrent');
        const cidade = document.getElementById('cepCidade');
        const estado = document.getElementById('cepEstado');
        const log = document.getElementById('cepLogradouro');
        if(cur) cur.textContent = (d && d.cep) ? d.cep : (cepValue || '');
        if(cidade) cidade.textContent = (d && d.cidade) ? d.cidade : ((data && data.cidade) ? data.cidade : '-');
        if(estado) estado.textContent = (d && d.estado) ? d.estado : ((data && data.estado) ? data.estado : '-');
        if(log) log.textContent = (d && d.logradouro) ? d.logradouro : ((data && data.logradouro) ? data.logradouro : '-');
        const raioEl = document.getElementById('cepRaioCurrent');
        const raioInput = document.getElementById('cepRaioInput');
        if(raioEl) raioEl.textContent = (d && d.raio_km !== undefined && d.raio_km !== null) ? String(d.raio_km) : ( (data && data.raio_km !== undefined && data.raio_km !== null) ? String(data.raio_km) : '-' );
        // Keep inputs populated
        const inp = document.getElementById('cepInput'); if(inp) inp.value = (d && d.cep) ? d.cep : (cepValue || inp.value || '');
        if(raioInput) raioInput.value = (d && d.raio_km !== undefined && d.raio_km !== null) ? String(d.raio_km) : (raioInput.value || '');
      }catch(uiErr){
        // If server accepted but UI update failed, log and show a non-blocking warning
        console.warn('Erro ao atualizar UI após salvar CEP (UI error):', uiErr);
        if(serverAccepted){
          showMessage('Aviso', 'CEP salvo e reprocessamento iniciado; porém ocorreu um erro ao atualizar a interface. Verifique os logs do navegador.');
          // still mark as concluded visually
          try{ const indicator = document.getElementById('cep-processing-indicator'); if(indicator){ indicator.textContent = 'Concluído'; indicator.className = 'badge badge-success'; } }catch(e){}
          window._cep_processing = false;
          return;
        } else {
          showMessage('Erro', 'Erro ao salvar CEP: ' + (uiErr && uiErr.message ? uiErr.message : String(uiErr)));
          try{ const indicator = document.getElementById('cep-processing-indicator'); if(indicator){ indicator.textContent = 'Erro'; indicator.className = 'badge badge-danger'; } }catch(e){}
          window._cep_processing = false;
          return;
        }
      }

      // The backend performed the reset+initialize; update UI indicator accordingly
      try{ const indicator = document.getElementById('cep-processing-indicator'); if(indicator){ indicator.textContent = 'Concluído'; indicator.className = 'badge badge-success'; } }catch(e){ console.warn('Erro ao marcar indicador concluido', e); }

    }catch(e){
      console.error('Erro ao salvar CEP (caught):', e);
      if(serverAccepted){
        // server already accepted; show warning
        showMessage('Aviso', 'CEP salvo e reprocessamento iniciado; ocorreu um erro não crítico na interface: ' + (e && e.message ? e.message : String(e)));
        try{ const indicator = document.getElementById('cep-processing-indicator'); if(indicator){ indicator.textContent = 'Concluído'; indicator.className = 'badge badge-success'; } }catch(err){}
      } else {
        showMessage('Erro', 'Erro ao salvar CEP: ' + (e && e.message ? e.message : String(e)));
        try{ const indicator = document.getElementById('cep-processing-indicator'); if(indicator){ indicator.textContent = 'Erro'; indicator.className = 'badge badge-danger'; } }catch(err){}
      }
    } finally {
      // clear pendingLookupData and processing flag
      try{ pendingLookupData = null; }catch(e){}
      // reset UI processing state
      try{ setProcessingState(false); }catch(e){}
      window._cep_processing = false;
      // clear request-sent guard
      try{ window._cep_request_sent = false; }catch(e){}
      console.log('[CEP] doSaveConfirmed: processamento finalizado');
    }
  }

  async function save(){
    const v = document.getElementById('cepInput')?.value?.trim();
    if(!v){ showMessage('Aviso', 'Informe CEP'); return; }

    // Lookup first
    try{
      const res = await fetch('/api/config/cep/lookup?cep=' + encodeURIComponent(v));
      const j = await res.json();
      if(!res.ok || !j.success){ showMessage('Erro', 'Falha ao validar CEP: ' + (j.message || res.statusText)); return; }

      pendingLookupData = j.data || { cep: v };
      const text = formatAddress(pendingLookupData);
      const confirmText = document.getElementById('cepConfirmText');
      if(confirmText) confirmText.textContent = text;

      // Show confirmation modal using vanilla DOM helper
      const confirmModal = document.getElementById('cepConfirmModal');
      if(confirmModal){
        showDOMModal(confirmModal, { title: 'Confirme o endereço', message: text, showCancel: true, onOk: function(){ doSaveConfirmed(pendingLookupData); } });
      } else {
        // fallback to generic confirm modal
        showConfirmModal('Confirmar salvar', 'Confirmar salvar: ' + text, function(){ doSaveConfirmed(pendingLookupData); });
      }

    }catch(e){ console.error('Erro ao consultar CEP', e); showMessage('Erro', 'Erro ao validar CEP'); }
  }

  // Hook confirm button
  function setupConfirm(){
    const btn = document.getElementById('cepConfirmBtn');
    if(btn){
      // REMOVIDO: Listener duplicado que causava execução 2x
      // O listener já é anexado por showDOMModal() via window._cep_pending_onok
      // Apenas marcar como wired para evitar re-anexação
      try{
        if(!btn.dataset || !btn.dataset.cepOkWired){
          // Não anexar listener aqui - showDOMModal já faz isso
          if(btn.dataset) btn.dataset.cepOkWired = '1';
        }
      }catch(e){}
    }

    // wire generic message modal OK/Cancel buttons
    const ok = document.getElementById('cepMessageOk');
    const cancel = document.getElementById('cepMessageCancel');
    if(ok){ ok.addEventListener('click', function(){ const modal = document.getElementById('cepMessageModal'); if(modal) hideDOMModal(modal); }); }
    if(cancel){ cancel.addEventListener('click', function(){ const modal = document.getElementById('cepMessageModal'); if(modal) hideDOMModal(modal); }); }
  }

  window.init_define_cep = function(){
    const btn = document.getElementById('saveCep');
    try{
      if(btn && (!btn.dataset || !btn.dataset.cepSaveWired)){
        btn.addEventListener('click', save);
        if(btn.dataset) btn.dataset.cepSaveWired = '1';
      }
    }catch(e){}
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

    // Keep processing state in sync with server while this page is open
    try{
      // initial check
      updateProcessingFromServer();
      // start interval (2s)
      if(!window._cep_status_interval){
        window._cep_status_interval = setInterval(updateProcessingFromServer, 2000);
      }

      // re-sync when tab/page becomes visible again
      if(!window._cep_visibility_handler_registered){
        document.addEventListener('visibilitychange', function(){
          try{
            if(document.visibilityState === 'visible'){
              updateProcessingFromServer();
            }
          }catch(e){}
        });
        window._cep_visibility_handler_registered = true;
      }

      // MutationObserver: if the app uses SPA DOM swaps, re-attach/update when #cep-panel is added back
      if(!window._cep_dom_observer_registered){
        try{
          const mo = new MutationObserver(function(mutations){
            for(const m of mutations){
              for(const node of m.addedNodes){
                try{
                  if(node && node.querySelector && node.querySelector('#cep-panel')){
                    // panel inserted - ensure interval and sync state
                    try{ updateProcessingFromServer(); }catch(e){}
                    if(!window._cep_status_interval){ window._cep_status_interval = setInterval(updateProcessingFromServer, 2000); }
                    return;
                  }
                }catch(e){}
              }
            }
          });
          mo.observe(document.body, { childList: true, subtree: true });
          window._cep_dom_observer = mo;
          window._cep_dom_observer_registered = true;
        }catch(e){}
      }

      // clear interval on page unload
      window.addEventListener('beforeunload', function(){ try{ if(window._cep_status_interval){ clearInterval(window._cep_status_interval); window._cep_status_interval = null; } }catch(e){} });
    }catch(e){}
  };
 })();
