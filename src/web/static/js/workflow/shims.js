(function(){
  window.init_define_terms = window.init_define_terms || function(){ try{ if(window['loadTerms']){ /* termos_ativos.js uses loadTerms on DOMContentLoaded; attempt to call loadTerms */ } }catch(e){} };
  window.init_define_cep = window.init_define_cep || function(){ if(window.init_define_cep){ try{ window.init_define_cep(); }catch(e){} } };
  window.init_municipios = window.init_municipios || function(){ if(window.init_municipios_grid) try{ window.init_municipios_grid(); }catch(e){} };
  window.init_bairros = window.init_bairros || function(){ if(window.init_bairros_grid) try{ window.init_bairros_grid(); }catch(e){} };
  window.init_termos_processados = window.init_termos_processados || function(){ if(window.init_termos_processados_grid) try{ window.init_termos_processados_grid(); }catch(e){} };
})();
