/* ============================================================================
 * ferramentas/renal.js — Função renal: CKD-EPI 2021, Cockcroft-Gault, MDRD e estágio KDIGO.
 *
 * Extraído LITERALMENTE de ferramentas.html (26/set/2026), sem nenhuma linha
 * reescrita. A indentação herdada do HTML foi mantida de propósito: os corpos
 * de modal são template strings, e preservá-los byte a byte é o que permite
 * provar a equivalência contra a versão inline (ver o harness de snapshot).
 *
 * Carregado como script CLÁSSICO e SÍNCRONO, na mesma posição em que o bloco
 * inline estava — mesma ordem de execução, mesmo escopo global compartilhado
 * (`const` de topo e `function` continuam visíveis aos handlers inline).
 * Expõe window.calcRenal.
 * ==========================================================================*/

(function(){
  "use strict";

  function calcRenal(){
    var age = parseFloat(document.getElementById('renal-age').value);
    var sex = document.getElementById('renal-sex').value;
    var wt  = parseFloat(document.getElementById('renal-weight').value);
    var ht  = parseFloat(document.getElementById('renal-height').value);
    var scr = parseFloat(document.getElementById('renal-cr').value);

    if(!age||!wt||!ht||!scr||age<18||scr<=0){
      document.getElementById('ckdepi-val').textContent='--';
      document.getElementById('cg-val').textContent='--';
      document.getElementById('mdrd-val').textContent='--';
      document.getElementById('ckdepi-stage').textContent='';
      document.getElementById('cg-bsa').textContent='';
      document.getElementById('mdrd-stage').textContent='';
      resetBar();
      return;
    }

    var isFemale = (sex==='F');
    var kappa = isFemale ? 0.7 : 0.9;
    var alpha = isFemale ? -0.241 : -0.302;
    var sexMul = isFemale ? 1.012 : 1.0;
    var scrK = scr / kappa;
    var ckdepi = 142 * Math.pow(Math.min(scrK,1), alpha) * Math.pow(Math.max(scrK,1), -1.200) * Math.pow(0.9938, age) * sexMul;

    var cg = ((140 - age) * wt) / (72 * scr);
    if(isFemale) cg *= 0.85;

    var mdrd = 175 * Math.pow(scr, -1.154) * Math.pow(age, -0.203);
    if(isFemale) mdrd *= 0.742;

    var bsa = 0.007184 * Math.pow(ht, 0.725) * Math.pow(wt, 0.425);
    var cgNorm = cg * (1.73 / bsa);

    document.getElementById('ckdepi-val').textContent = ckdepi.toFixed(1);
    document.getElementById('cg-val').textContent = cg.toFixed(1);
    document.getElementById('mdrd-val').textContent = mdrd.toFixed(1);

    document.getElementById('ckdepi-stage').textContent = stageLabel(ckdepi);
    document.getElementById('cg-bsa').textContent = 'Corrigido BSA: ' + cgNorm.toFixed(1) + ' mL/min/1,73 m² · BSA: ' + bsa.toFixed(2) + ' m²';
    document.getElementById('mdrd-stage').textContent = stageLabel(mdrd);

    highlightBar(ckdepi);
  }

  function stageLabel(gfr){
    if(gfr>=90) return 'G1 — Normal ou alto';
    if(gfr>=60) return 'G2 — Levemente diminuído';
    if(gfr>=45) return 'G3a — Leve a moderadamente diminuído';
    if(gfr>=30) return 'G3b — Moderada a severamente diminuído';
    if(gfr>=15) return 'G4 — Severamente diminuído';
    return 'G5 — Falência renal';
  }

  function resetBar(){
    var ids=['ckd-g1','ckd-g2','ckd-g3a','ckd-g3b','ckd-g4','ckd-g5'];
    for(var i=0;i<ids.length;i++){
      document.getElementById(ids[i]).style.outline='none';
      document.getElementById(ids[i]).style.zIndex='0';
      document.getElementById(ids[i]).style.transform='none';
    }
  }

  function highlightBar(gfr){
    resetBar();
    var active='';
    if(gfr>=90) active='ckd-g1';
    else if(gfr>=60) active='ckd-g2';
    else if(gfr>=45) active='ckd-g3a';
    else if(gfr>=30) active='ckd-g3b';
    else if(gfr>=15) active='ckd-g4';
    else active='ckd-g5';
    var el=document.getElementById(active);
    el.style.outline='2px solid currentColor';
    el.style.zIndex='1';
    el.style.transform='scaleY(1.25)';
  }

  window.calcRenal = calcRenal;
  document.addEventListener('DOMContentLoaded', calcRenal);
})();
