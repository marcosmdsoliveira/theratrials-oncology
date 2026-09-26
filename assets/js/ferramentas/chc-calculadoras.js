/* ============================================================================
 * ferramentas/chc-calculadoras.js — Calculadoras embutidas nos modais de CHC: ALBI, MELD (clássico, Na, 3.0) e Child-Pugh.
 *
 * Extraído LITERALMENTE de ferramentas.html (26/set/2026), sem nenhuma linha
 * reescrita. A indentação herdada do HTML foi mantida de propósito: os corpos
 * de modal são template strings, e preservá-los byte a byte é o que permite
 * provar a equivalência contra a versão inline (ver o harness de snapshot).
 *
 * Carregado como script CLÁSSICO e SÍNCRONO, na mesma posição em que o bloco
 * inline estava — mesma ordem de execução, mesmo escopo global compartilhado
 * (`const` de topo e `function` continuam visíveis aos handlers inline).
 * Chamadas pelos oninput/onchange que vivem DENTRO das strings de CRIT_DATA.
 * ==========================================================================*/
      // ── Calculadoras embutidas (ALBI / MELD) ──
      function _ccPf(id){ var el = document.getElementById(id); if(!el) return NaN; return parseFloat(String(el.value).replace(',', '.')); }
      function _ccFmt(n, d){ return n.toFixed(d).replace('.', ','); }
      function _ccClamp(x, lo, hi){ return Math.min(Math.max(x, lo), hi); }

      function calcAlbi(){
        var res = document.getElementById('albi-result'); if(!res) return;
        var b = _ccPf('albi-bili'), a = _ccPf('albi-alb');
        var bu = (document.getElementById('albi-bili-u') || {}).value;
        var au = (document.getElementById('albi-alb-u') || {}).value;
        if(!(b > 0) || !(a > 0)){
          res.className = 'cc-result cc-empty';
          res.innerHTML = 'Informe bilirrubina e albumina para calcular o ALBI score.';
          return;
        }
        var biliUmol = (bu === 'mgdl') ? b * 17.1 : b;   // 1 mg/dL = 17,1 µmol/L
        var albGL = (au === 'gdl') ? a * 10 : a;          // 1 g/dL = 10 g/L
        var albi = Math.log10(biliUmol) * 0.66 + albGL * (-0.085);
        var grade, desc;
        if(albi <= -2.60){ grade = 'Grade 1'; desc = 'melhor reserva hepática (≈ Child-Pugh A robusto; melhor prognóstico em Y-90 e sistêmica)'; }
        else if(albi <= -1.39){ grade = 'Grade 2'; desc = 'reserva intermediária (CP A frágil a CP B)'; }
        else { grade = 'Grade 3'; desc = 'reserva pior (≈ Child-Pugh C)'; }
        res.className = 'cc-result';
        res.innerHTML = '<span class="cc-score">' + _ccFmt(albi, 2) + '</span> &nbsp; <span class="cc-grade">' + grade + '</span>'
          + '<div class="cc-hint">' + desc + '.<br>Cortes: Grade 1 &le; &minus;2,60 &middot; Grade 2 de &minus;2,60 a &minus;1,39 &middot; Grade 3 &gt; &minus;1,39.</div>';
      }

      function calcMeld(){
        var res = document.getElementById('meld-result'); if(!res) return;
        var bili = _ccPf('meld-bili'), cr = _ccPf('meld-cr'), inr = _ccPf('meld-inr');
        var na = _ccPf('meld-na'), alb = _ccPf('meld-alb');
        var sex = (document.getElementById('meld-sex') || {}).value;
        var dial = !!(document.getElementById('meld-dialysis') || {}).checked;
        if(!(bili > 0) || !(cr > 0) || !(inr > 0)){
          res.className = 'cc-result cc-empty';
          res.innerHTML = 'Informe ao menos bilirrubina, creatinina e INR para o MELD clássico. Sódio habilita o MELD-Na; sódio + albumina + sexo habilitam o MELD 3.0.';
          return;
        }
        var ln = Math.log;
        // MELD clássico (Kamath/UNOS): labs mínimos 1,0; creatinina máx 4,0; diálise → 4,0
        var bC = Math.max(bili, 1), iC = Math.max(inr, 1), crC = Math.max(cr, 1);
        crC = dial ? 4.0 : Math.min(crC, 4.0);
        var meldClassic = _ccClamp(Math.round(9.57 * ln(crC) + 3.78 * ln(bC) + 11.2 * ln(iC) + 6.43), 6, 40);
        // MELD-Na (OPTN 2016): Na 125–137; ajuste só se MELD > 11
        var meldNa = null;
        if(na > 0){
          var naC = _ccClamp(na, 125, 137);
          var m = meldClassic;
          if(meldClassic > 11){ m = meldClassic + 1.32 * (137 - naC) - 0.033 * meldClassic * (137 - naC); }
          meldNa = _ccClamp(Math.round(m), 6, 40);
        }
        // MELD 3.0 (OPTN 2023, Kim 2021): sexo, albumina 1,5–3,5; creatinina máx 3,0; Na 125–137
        var meld3 = null;
        if(na > 0 && alb > 0){
          var naC2 = _ccClamp(na, 125, 137), albC = _ccClamp(alb, 1.5, 3.5);
          var cr3 = dial ? 3.0 : Math.min(Math.max(cr, 1), 3.0);
          var b3 = Math.max(bili, 1), i3 = Math.max(inr, 1);
          var fem = (sex === 'F') ? 1 : 0;
          var m3 = 1.33 * fem + 4.56 * ln(b3) + 0.82 * (137 - naC2) - 0.24 * (137 - naC2) * ln(b3)
            + 9.09 * ln(i3) + 11.14 * ln(cr3) + 1.85 * (3.5 - albC) - 1.83 * (3.5 - albC) * ln(cr3) + 6;
          meld3 = _ccClamp(Math.round(m3), 6, 40);
        }
        function surv(x){ if(x < 10) return '~97%'; if(x <= 19) return '~76%'; if(x <= 29) return '~50%'; if(x <= 39) return '~30%'; return '~7%'; }
        var h = '';
        h += '<div class="cc-meld-row"><span class="cc-mlabel">MELD clássico</span><span class="cc-score">' + meldClassic + '</span></div>';
        h += '<div class="cc-meld-row"><span class="cc-mlabel">MELD-Na</span>' + (meldNa != null ? ('<span class="cc-score">' + meldNa + '</span>') : '<span class="cc-na">informe Na&#8314;</span>') + '</div>';
        h += '<div class="cc-meld-row"><span class="cc-mlabel">MELD 3.0</span>' + (meld3 != null ? ('<span class="cc-score">' + meld3 + '</span>') : '<span class="cc-na">informe Na&#8314;, albumina e sexo</span>') + '</div>';
        h += '<div class="cc-hint">Sobrevida estimada em 3 meses (cirrose, pelo MELD clássico): ' + surv(meldClassic) + '.';
        if(dial){ h += ' Diálise considerada &rarr; creatinina fixada (4,0 no clássico/Na; 3,0 no MELD 3.0).'; }
        h += ' Labs &lt; 1,0 são ajustados para 1,0; faixa final 6&ndash;40. O MELD 3.0 limita creatinina a 3,0, albumina a 1,5&ndash;3,5 e Na a 125&ndash;137.</div>';
        res.className = 'cc-result';
        res.innerHTML = h;
      }

      function calcChildPugh(){
        var res = document.getElementById('cp-result'); if(!res) return;
        var bili = _ccPf('cp-bili'), alb = _ccPf('cp-alb'), inr = _ccPf('cp-inr');
        var asc = parseInt((document.getElementById('cp-ascites') || {}).value, 10) || 1;
        var enc = parseInt((document.getElementById('cp-enceph') || {}).value, 10) || 1;
        if(!(bili > 0) || !(alb > 0) || !(inr > 0)){
          res.className = 'cc-result cc-empty';
          res.innerHTML = 'Informe bilirrubina, albumina e INR (e ajuste ascite/encefalopatia) para calcular o Child-Pugh.';
          return;
        }
        var pBili = (bili < 2) ? 1 : ((bili <= 3) ? 2 : 3);   // <2 / 2-3 / >3 mg/dL
        var pAlb  = (alb > 3.5) ? 1 : ((alb >= 2.8) ? 2 : 3);  // >3,5 / 2,8-3,5 / <2,8 g/dL
        var pInr  = (inr < 1.7) ? 1 : ((inr <= 2.3) ? 2 : 3);  // <1,7 / 1,7-2,3 / >2,3
        var total = pBili + pAlb + pInr + asc + enc;
        var cls, surv, desc;
        if(total <= 6){ cls = 'A'; surv = '~100%'; desc = 'cirrose compensada, boa reserva hepática'; }
        else if(total <= 9){ cls = 'B'; surv = '~80%'; desc = 'comprometimento funcional significativo'; }
        else { cls = 'C'; surv = '~45%'; desc = 'doença descompensada'; }
        res.className = 'cc-result';
        res.innerHTML = '<span class="cc-score">' + total + ' pts</span> &nbsp; <span class="cc-grade">Classe ' + cls + '</span>'
          + '<div class="cc-hint">' + desc + '. Sobrevida ~1 ano: ' + surv + '.<br>'
          + 'Pontos &rarr; bilirrubina ' + pBili + ' &middot; albumina ' + pAlb + ' &middot; INR ' + pInr + ' &middot; ascite ' + asc + ' &middot; encefalopatia ' + enc + '. '
          + 'Classes: A 5&ndash;6 &middot; B 7&ndash;9 &middot; C 10&ndash;15.</div>';
      }

