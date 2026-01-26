(function(){
  window.init_define_terms = window.init_define_terms || function(){ try{ if(window['loadTerms']){ /* termos_ativos.js uses loadTerms on DOMContentLoaded; attempt to call loadTerms */ } }catch(e){} };
  window.init_define_cep = window.init_define_cep || function(){ if(window.init_define_cep){ try{ window.init_define_cep(); }catch(e){} } };
  window.init_municipios = window.init_municipios || function(){ if(window.init_municipios_grid) try{ window.init_municipios_grid(); }catch(e){} };
  window.init_bairros = window.init_bairros || function(){ if(window.init_bairros_grid) try{ window.init_bairros_grid(); }catch(e){} };
  window.init_termos_processados = window.init_termos_processados || function(){ if(window.init_termos_processados_grid) try{ window.init_termos_processados_grid(); }catch(e){} };

  // Ensure global socket exists (created by other modules) and register a reprocess_complete handler
  try{
    const socket = (typeof window !== 'undefined' && window.socket) ? window.socket : (typeof io !== 'undefined' ? io() : null);
    if(typeof window !== 'undefined' && !window.socket && socket) window.socket = socket;

    // internal reference for polling cancellation
    window._reset_polling = window._reset_polling || { timer: null, active: false };

    function _trigger_refreshes(){
        try{ if(window.refreshProcessedTerms) window.refreshProcessedTerms(); }catch(e){}
        try{ if(window.refreshBaseTerms) window.refreshBaseTerms(); }catch(e){}
        try{ if(window.refreshCitiesGrid) window.refreshCitiesGrid(); }catch(e){}
        try{ if(window.refreshNeighborhoodsGrid) window.refreshNeighborhoodsGrid(); }catch(e){}
        try{ if(window.refreshCepConfig) window.refreshCepConfig(); }catch(e){}
        try{ if(window.updateDashboardStats) window.updateDashboardStats(); }catch(e){}
    }

    if(socket && !window._reprocess_listener_registered){
        socket.on('reprocess_complete', (payload)=>{
            // cancel any polling in progress
            try{ if(window._reset_polling && window._reset_polling.timer){ clearInterval(window._reset_polling.timer); window._reset_polling.timer = null; window._reset_polling.active = false; } }catch(e){}
            // Trigger refresh functions if present (non-blocking)
            _trigger_refreshes();
        });
        window._reprocess_listener_registered = true;
    }

    // Polling function: polls /api/admin/reset-status?task_id=... every 2s until status done/failed
    window.pollResetTask = async function(taskId, intervalMs){
        if(!taskId) return;
        intervalMs = intervalMs || 2000;
        try{
            // prevent double polling
            if(window._reset_polling && window._reset_polling.active){ return; }
            window._reset_polling.active = true;
            window._reset_polling.timer = setInterval(async function(){
                try{
                    const res = await fetch(`/api/admin/reset-status?task_id=${encodeURIComponent(taskId)}`);
                    if(!res.ok){ return; }
                    const j = await res.json();
                    if(j && j.task && j.task.status){
                        const st = j.task.status;
                        if(st === 'done' || st === 'failed'){
                            // stop polling
                            try{ clearInterval(window._reset_polling.timer); }catch(e){}
                            window._reset_polling.timer = null;
                            window._reset_polling.active = false;
                            // trigger UI refreshes
                            _trigger_refreshes();
                        }
                    }
                }catch(e){ /* ignore transient errors */ }
            }, intervalMs);
        }catch(e){ window._reset_polling.active = false; }
    };

    // Helper to start admin reset and automatically poll for completion (fallback if socket not connected)
    window.startAdminReset = async function(){
        try{
            const res = await fetch('/api/admin/reset-and-initialize', { method: 'POST' });
            if(res.status === 202){
                const j = await res.json();
                const tid = j.task_id;
                // start polling as fallback; socket listener will cancel if available
                window.pollResetTask(tid, 2000);
                return { status: 'accepted', task_id: tid };
            }
            const j = await res.json();
            if(res.ok){
                // synchronous completion (server returned result) - trigger refreshes immediately
                _trigger_refreshes();
                return { status: 'done', result: j };
            }
            return { status: 'error', error: j };
        }catch(e){ return { status: 'exception', error: String(e) }; }
    };

  }catch(e){}
})();
