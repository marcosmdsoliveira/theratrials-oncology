/* ============================================================
   TheraTrials Oncology — JavaScript comum
   Helpers, navegação e utilitários compartilhados
   ============================================================ */

(function() {
  'use strict';

  // Marcar link ativo no menu
  document.addEventListener('DOMContentLoaded', function() {
    // Toggle do menu mobile agora eh feito via onclick inline na tag <button>
    const path = window.location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.nav a').forEach(a => {
      const href = a.getAttribute('href') || '';
      if (href === path || (path === '' && href === 'index.html')) {
        a.classList.add('active');
      }
    });

    // Inicializa Lucide icons se disponível
    if (window.lucide) lucide.createIcons();
  });

  // ---------- Helpers de dados ----------
  window.TheraTrials = window.TheraTrials || {};

  // Categorias cuja intervencao principal eh um radiofarmaco/teranostico.
  // Define os labels do modal: estudos radio mostram "Intervencao e radiofarmacia" /
  // "Criterios moleculares e imagem"; estudos nao-radio mostram versoes neutras.
  TheraTrials.RADIO_CATEGORIES = new Set([
    'lupsma_prostata', 'ra223_prostata', 'net_gep', 'lupsma_ccrcc',
    'hepatobiliar', 'novos_psma', 'ppgl', 'neuroblastoma',
    'lung_radio_dev', 'breast_radio_dev',
    'teranostico_emergente'
  ]);

  // Modalidades teranósticas/radiofármacos — usadas para detectar estudo "radio" via tags
  TheraTrials.RADIO_MODALITIES = new Set([
    'teranostico_psma', 'teranostico_prrt', 'teranostico_alfa',
    'tare_y90', 'mibg', 'iodo_131', 'teranostico_emergente'
  ]);

  TheraTrials.isRadioStudy = function(study) {
    if (!study) return false;
    // Prioridade: array modalities[] (taxonomia canônica)
    if (Array.isArray(study.modalities) && study.modalities.length) {
      return study.modalities.some(m => TheraTrials.RADIO_MODALITIES.has(m));
    }
    // Decisão POR ESTUDO: radio sse o badge de modalidade for teranóstico (radiofármaco, #FF8400).
    // Antes era por category_id, mas categorias mistas (hepatobiliar, neuroblastoma, ppgl) marcavam
    // estudos de imuno/alvo/QT/ADC como radio → modal exibia rótulos de radiofarmácia indevidos.
    if (typeof TheraTrials.studyModality === 'function') {
      var m = TheraTrials.studyModality(study);
      return !!(m && m.color === '#FF8400');
    }
    // Fallback final: category_id legado
    return TheraTrials.RADIO_CATEGORIES.has(study.category_id);
  };

  // Campo "tem conteúdo real"? (para esconder campos vazios/placeholder em cards não-radio)
  TheraTrials.fieldMeaningful = function(v) {
    if (v === undefined || v === null) return false;
    var t = String(v).trim().toLowerCase();
    if (!t || t === '—' || t === '-' || t === '–' || t === 'n/a' || t === 'na') return false;
    if (/^sem\s+crit[ée]rio/.test(t)) return false;            // "Sem critério molecular."
    if (/^n[ãa]o[-\s]?radiof[áa]rmaco\b/.test(t)) return false; // placeholder "Não-radiofármaco; ..."
    return true;
  };

  TheraTrials.studyTitle = function(estudo) {
    if (!estudo) return '';
    return estudo.split('\n')[0].split('(')[0].trim();
  };

  TheraTrials.cleanText = function(t) {
    if (!t) return '';
    return String(t).replace(/\n+/g, ' · ');
  };

  TheraTrials.extractN = function(n) {
    if (!n) return '—';
    const m = String(n).match(/(\d{1,3}(?:\.\d{3})*|\d{2,4})/);
    return m ? `n=${m[0]}` : '—';
  };

  TheraTrials.extractYear = function(estudo) {
    if (!estudo) return 0;
    const m = String(estudo).match(/\((?:[^()]*?)(\d{4})/);
    return m ? parseInt(m[1]) : 0;
  };

  TheraTrials.phaseClass = function(fase) {
    const f = String(fase || '').toLowerCase();
    if (f.includes('fase 3') || f.includes('plataforma')) return 'phase-3';
    if (f.includes('fase 2')) return 'phase-2';
    if (f.includes('fase 1')) return 'phase-1';
    return 'phase-other';
  };

  // ============================================================
  // CLASSIFICAÇÃO DE MODALIDADE TERAPÊUTICA
  // Retorna { label, html, color, icon } para exibição em badge nos cards.
  // ============================================================
  TheraTrials.studyModality = function(s) {
    if (!s) return { label: '—', color: '#8E949C', icon: 'circle' };

    const fase = String(s.fase || '').toLowerCase();
    const rfa  = String(s.radiofarmaco || '').toLowerCase();
    const est  = String(s.estudo || '').toLowerCase();
    const cat  = s.category_id || '';
    // blob amplo só para detecção de cirurgia/RT (último recurso); para imuno/alvo/QT/teranóstico, usar rfa + est + acron (mais específico)
    const blobNarrow = rfa + ' ' + est + ' ' + String(s.acron || '').toLowerCase();
    const blobWide = blobNarrow + ' ' + String(s.esquema || '').toLowerCase() + ' ' + String(s.indicacao || '').toLowerCase();

    // 1) DIRETRIZ / GUIDELINE
    if (/diretriz|guideline|consensus|consenso/.test(fase) || /\b(guidelines?|diretriz|consensus|consenso)\b/i.test(s.estudo || '')) {
      return { label: 'Diretriz', color: '#A78BFA', icon: 'book-open' };
    }

    // 2) META-ANÁLISE
    if (/meta-?an[aá]lise|systematic review/.test(fase)) {
      return { label: 'Meta-análise', color: '#A78BFA', icon: 'layers' };
    }

    // 3) TERANÓSTICO — depende de padrão concreto no radiofarmaco
    // (NÃO usar category_id sozinho — categorias como 'hepatobiliar' são mistas)
    // Categorias 100%-teranósticas (todos os estudos são radio): usar como atalho
    const PURE_RADIO_CATS = new Set([
      'lupsma_prostata', 'ra223_prostata', 'lupsma_ccrcc', 'novos_psma',
      'lung_radio_dev', 'breast_radio_dev', 'teranostico_emergente'
    ]);
    const isPureRadio = PURE_RADIO_CATS.has(cat);

    // Marcador explícito no banco: campo radiofarmaco com sufixo "(não-radiofármaco)"
    // indica que o esquema descrito ali é não-radio (apenas convenção editorial).
    const isExplicitNonRadio = /\(\s*n[aã]o-?radio[^)]*\)/i.test(rfa);

    // Isótopos relevantes em medicina nuclear (terapêuticos e diagnósticos teranósticos).
    // O símbolo precisa estar grudado ou hifenado ao número e NÃO seguido de unidade
    // de dose ("mg", "g", "mL", "kg" etc.) — evita match em "600 mg", "200 mg".
    const ISOTOPE_NUMERIC = /\b(?:(?:177|176)\s*Lu|Lu[-\s]?17[67]|225\s*Ac|Ac[-\s]?225|223\s*Ra|Ra[-\s]?223|90\s*Y|Y[-\s]?90|13[12]\s*I|I[-\s]?13[12]|123\s*I|I[-\s]?123|161\s*Tb|Tb[-\s]?161|67\s*Cu|Cu[-\s]?67|64\s*Cu|Cu[-\s]?64|166\s*Ho|Ho[-\s]?166|188\s*Re|Re[-\s]?188|186\s*Re|Re[-\s]?186|153\s*Sm|Sm[-\s]?153|89\s*Sr|Sr[-\s]?89|212\s*Pb|Pb[-\s]?212|213\s*Bi|Bi[-\s]?213|211\s*At|At[-\s]?211|227\s*Th|Th[-\s]?227|68\s*Ga|Ga[-\s]?68|18\s*F|F[-\s]?18|99m?\s*Tc|Tc[-\s]?99m?|89\s*Zr|Zr[-\s]?89|44\s*Sc|Sc[-\s]?44|111\s*In|In[-\s]?111|201\s*Tl|Tl[-\s]?201)\b(?!\s*(?:mg|mcg|ug|g|ml|mL|L|kg|UI|UFC))/i;
    // Plataformas de radiofármaco identificáveis pelo nome (sem nº de isótopo).
    const RADIO_PLATFORM = /\b(tare|sirt|radioembol\w*|microesferas?|sir-?spheres|therasphere|quirem|holmium\s+microsph|mibg|iobenguano|iobenguane|psma-617|psma-i&t|psma-i-t|dotatate|dotatoc|dotanoc|dotamtate|sartate|pentixather|girentuximab.*lu|girentuximab.*y|fapi-46|fap-2286|pnt2002|pnt2003)\b/i;
    const RADIO_BRAND = /\b(lutathera|pluvicto|xofigo|azedra|metastron|quadramet|zevalin|bexxar|locametz|netspot|illuccix|posluma|theraspheres?|sir-?spheres?|quiremspheres?)\b/i;

    const hasIsotopePattern = !isExplicitNonRadio && (
      ISOTOPE_NUMERIC.test(rfa) || RADIO_PLATFORM.test(rfa) || RADIO_BRAND.test(rfa)
    );

    if ((isPureRadio && !isExplicitNonRadio) || hasIsotopePattern) {
      const label = TheraTrials._formatTheranosticLabel(s);
      return { label: label, html: true, color: '#FF8400', icon: 'atom' };
    }

    // 4) IMUNOTERAPIA (ICIs, vacinas, BiTE, CAR-T, ADCs imuno, anti-GD2)
    // Terminação flexível (\w* ao final) para aceitar variantes pt-BR (-mab/-mabe, -nib/-nibe)
    const RE_IMMUNO = /\b(pembrolizumab|pembro|keytruda|nivolumab|nivo|opdivo|ipilimumab|yervoy|atezolizumab|atezo|tecentriq|durvalumab|durva|imfinzi|tremelimumab|treme|imjudo|avelumab|bavencio|cemiplimab|libtayo|tislelizumab|tevimbra|sintilimab|tyvyt|camrelizumab|toripalimab|loqtorzi|dostarlimab|jemperli|spartalizumab|relatlimab|opdualag|sipuleucel|provenge|dinutuximab|unituxin|naxitamab|danyelza|hu3f8|3f8|car-t|cilta|carvykti|abecma|yescarta|teclistamab|tecvayli|elranatamab|talvey|talquetamab|epcoritamab|glofitamab|columvi|mosunetuzumab|lunsumio|blinatumomab|blincyto|amivantamab|rybrevant|n-803|nogapendekin|anktiva|tarlatamab|imdelltra|lifileucel|amtagvi|ivonescimab|nadofaragene|firadenovec|adstiladrin|imc-f106c|brenetafusp|ima203|interferon|interleukin|il-2|gm-csf)\w*/i;
    if (RE_IMMUNO.test(blobNarrow) || /\bipi\b/i.test(blobNarrow)) {
      return { label: 'Imunoterapia', color: '#34D399', icon: 'shield-plus' };
    }

    // 4.3) ADC — conjugados anticorpo-fármaco. ACIMA do alvo genérico: num combo o ADC
    // costuma ser o agente novo. Detecta por payload (-deruxtecana/-vedotina/-govitecana/
    // -emtansina/-brengitecano) + nomes específicos. Não casa mAb "nu" (trastuzumabe/
    // pertuzumabe isolados → seguem Terapia-alvo). ADC+IO já saiu como Imunoterapia acima.
    const RE_ADC = /\b(t-?dxd|t-?dm1|deruxteca\w*|vedotin\w*|goviteca\w*|emtansin\w*|entansin\w*|brengiteca\w*|tirumoteca\w*|sacituzumab\w*|trodelvy|datopotamab\w*|datroway|enfortumab\w*|padcev|enhertu|kadcyla|mirvetuximab\w*|elahere|tisotumab\w*|tivdak|polatuzumab\w*|polivy|loncastuximab\w*|zynlonta|brentuximab\w*|adcetris|gemtuzumab\w*|mylotarg|inotuzumab\w*|besponsa|belantamab\w*|blenrep|telisotuzumab\w*|patritumab\w*|izalontamab\w*|iza-bren)/i;
    if (RE_ADC.test(blobNarrow)) {
      return { label: 'ADC', color: '#2563EB', icon: 'link-2' };
    }

    // 4.6) PARP — inibidores de PARP. ACIMA do alvo genérico: em combos ARPi+PARP
    // (PROpel, TALAPRO, MAGNITUDE) o agente novo testado é o PARP.
    const RE_PARP = /\b(olaparib|lynparza|rucaparib|rubraca|niraparib|zejula|talazoparib|talzenna|veliparib|pamiparib|fluzoparib|senaparib)\w*/i;
    if (RE_PARP.test(blobNarrow)) {
      return { label: 'PARP', color: '#E11D48', icon: 'dna' };
    }

    // 5) TERAPIA-ALVO (TKIs, PI3K/AKT/mTOR, anti-HER2 mAb, BRAF/MEK, KRAS, RET, NTRK, ALK, MET, EGFR, VEGF)
    // ARPi, SERD, CDK4/6, PARP e ADC foram extraídos p/ tags próprias (checados acima/abaixo).
    // Terminação flexível para tolerar variantes pt-BR
    const RE_TARGETED = /\b(olaparib|lynparza|rucaparib|rubraca|niraparib|zejula|talazoparib|talzenna|veliparib|relugolix|alpelisib|piqray|capivasertib|truqap|inavolisib|trastuzumab|herceptin|pertuzumab|perjeta|t-dxd|enhertu|t-dm1|kadcyla|tucatinib|tukysa|lapatinib|tykerb|sotorasib|lumakras|adagrasib|krazati|encorafenib|braftovi|vemurafenib|zelboraf|dabrafenib|tafinlar|trametinib|mekinist|cobimetinib|cotellic|binimetinib|mektovi|selumetinib|koselugo|selpercatinib|retsevmo|pralsetinib|gavreto|larotrectinib|vitrakvi|entrectinib|rozlytrek|repotrectinib|augtyro|crizotinib|xalkori|lorlatinib|lorbrena|alectinib|alecensa|brigatinib|alunbrig|ceritinib|zykadia|gefitinib|iressa|erlotinib|tarceva|afatinib|giotrif|gilotrif|osimertinib|tagrisso|lazertinib|lazcluze|cetuximab|erbitux|panitumumab|vectibix|sunitinib|sutent|sorafenib|nexavar|regorafenib|stivarga|lenvatinib|lenvima|cabozantinib|cabometyx|cometriq|axitinib|inlyta|pazopanib|votrient|fruquintinib|fruzaqla|surufatinib|sulanda|everolimus|afinitor|temsirolimus|torisel|venetoclax|venclexta|ivosidenib|tibsovo|enasidenib|idhifa|pemigatinib|pemazyre|infigratinib|truseltiq|futibatinib|lytgobi|zanidatamab|ziihera|nirogacestat|ogsiveo|belzutifan|welireg|ramucirumab|cyramza|bevacizumab|avastin|aflibercept|zaltrap|tivozanib|fotivda|ponatinib|iclusig|dasatinib|sprycel|nilotinib|tasigna|imatinib|gleevec|bosutinib|bosulif|ruxolitinib|jakafi|fedratinib|inrebic|pacritinib|vonjo|momelotinib|ojjaara|idelalisib|zydelig|duvelisib|copiktra|copanlisib|aliqopa|umbralisib|ukoniq|ibrutinib|imbruvica|acalabrutinib|calquence|zanubrutinib|brukinsa|pirtobrutinib|jaypirca|midostaurin|rydapt|gilteritinib|xospata|quizartinib|vanflyta|olutasidenib|rezlidhia|trilaciclib|cosela|mirvetuximab|elahere|tisotumab|tivdak|tafasitamab|monjuvi|polatuzumab|polivy|loncastuximab|zynlonta|brentuximab|adcetris|gemtuzumab|mylotarg|inotuzumab|besponsa|moxetumomab|lumoxiti|belantamab|blenrep|lenalidomida|revlimid|pomalidomida|pomalyst|talidomida|thalomid|iberdomida|mezigdomida|bortezomib|velcade|carfilzomib|kyprolis|ixazomib|ninlaro|daratumumab|darzalex|isatuximab|sarclisa|elotuzumab|empliciti|tazemetostat|tazverik|rivoceranib|apatinib|telisotuzumab|octreotid|sandostatin|lanreotid|somatuline|pasireotid|signifor|surufatinib|orteronel|asciminib|scemblix|capmatinib|tabrecta|erdafitinib|balversa|vandetanib|caprelsa|zolbetuximab|vyloy|patritumab|revumenib|revuforj|selinexor|xpovio|everolimo|izalontamab|sunvozertinib|zegfrovy|neladalkib|daraxonrasib)\w*/i;
    if (RE_TARGETED.test(blobNarrow)) {
      return { label: 'Terapia-alvo', color: '#0EA5B7', icon: 'target' };
    }

    // 5.3) CDK4/6 — ABAIXO do alvo genérico: assim INAVO120 (inavolisibe=PI3K novo + palbo
    // backbone) fica Terapia-alvo, e combos SERD+CDK4/6 (PALOMA-3) ficam CDK4/6 (agente novo).
    const RE_CDK = /\b(palbociclib|ibrance|ribociclib|kisqali|abemaciclib|verzenio|dalpiciclib|lerociclib)\w*/i;
    if (RE_CDK.test(blobNarrow)) {
      return { label: 'CDK4/6', color: '#0D9488', icon: 'timer' };
    }

    // 5.6) ARPi — inibidores da via do receptor de andrógeno (próstata). Backbone em combos:
    // ARPi+PARP já saiu como PARP acima; só ARPi "definidor" chega aqui (LATITUDE, PREVAIL…).
    const RE_ARPI = /\b(abirateron\w*|zytiga|enzalutamid\w*|xtandi|apalutamid\w*|erleada|darolutamid\w*|nubeqa)/i;
    if (RE_ARPI.test(blobNarrow)) {
      return { label: 'ARPi', color: '#0E7490', icon: 'mars' };
    }

    // 5.8) SERD — degradadores seletivos do receptor de estrógeno (mama HR+). Backbone em
    // combos: SERD+CDK4/6→CDK4/6, SERD+PI3K/AKT→Terapia-alvo; só SERD puro (EMERALD, lidERA).
    const RE_SERD = /\b(fulvestrant\w*|faslodex|elacestrant\w*|orserdu|giredestrant\w*|camizestrant\w*|imlunestrant\w*|amcenestrant\w*|rintodestrant\w*)/i;
    if (RE_SERD.test(blobNarrow)) {
      return { label: 'SERD', color: '#DB2777', icon: 'venus' };
    }

    // 6) QUIMIOTERAPIA (citotóxicos clássicos) — terminação flexível
    const RE_CHEMO = /\b(folfox|folfiri|capox|xelox|folfoxiri|capem|cape\+tem|capecitabin|xeloda|cisplatin|carboplatin|oxaliplatin|eloxatin|irinotecan|camptosar|paclitaxel|taxol|docetaxel|taxotere|cabazitaxel|jevtana|nab-?paclitaxel|abraxane|gemcitabin|gemzar|etoposid|vp-16|trifluridin|tas-?102|lonsurf|5-?fu|fluoruracil|temozolomid|temodal|temodar|dacarbazin|dtic|ciclofosfamid|cyclophosphamid|cytoxan|ifosfamid|holoxan|vincristin|oncovin|vinblastin|vinorelbin|navelbine|doxorrubicin|doxorubicin|adriamic|epirubicin|ellence|daunorubicin|daunoxome|melfalan|melphalan|alkeran|busulfan|myleran|busulfex|fludarabin|fludara|citarabin|cytarabin|ara-c|metotrexato|methotrexate|trexall|otrexup|pemetrexed|alimta|hidroxiureia|hydrea|topotecan|hycamtin|mitoxantron|novantrone|bendamustin|treanda|treosulfan|trabectedin|yondelis|lurbinectedin|zepzelca|nelarabin|arranon|raltitrexed|tomudex|mitomicin|streptozocin|zanosar|carmustin|bcnu|gliadel|tegafur|teysuno|s-?1|nimustin|liposomal|cpx-?351|vyxeos|asparaginase|elspar|erwinaze|fluorouracil|6-?mp|6-?tg|lomustin|fluoropirimidin|fluoro|gencitabin|azacitidin|azacytidin|vidaza|cc-486|onureg|decitabin|dacogen)\w*/i;
    if (RE_CHEMO.test(blobNarrow)) {
      return { label: 'Quimioterapia', color: '#FBBF24', icon: 'flask-conical' };
    }

    // 6.5) RT/SBRT — categorias dedicadas (MDT, consolidação, próstata localizada)
    if (['rt_sbrt_oligo', 'rt_prostata_local', 'rt_consolidacao'].includes(cat)) {
      return { label: 'Cirurgia/RT', color: '#F472B6', icon: 'scissors' };
    }

    // 7) CIRURGIA / RADIOTERAPIA / NEOADJUVANTE puro — usa blob amplo (busca também em esquema e indicacao)
    if (/\b(tireoidectomia|lobectomia|colectomia|gastrectomia|tme|cirurgia\s+(?:radical|inicial|prim)|surgery|resection|ressec[áa]vel|nefrectomia|prostatectomia|mastectomia|histerectomia|hepatectomia|radioterapia|qrt|imrt|sbrt|braquiterapia|radiocirurgia|ablação|ablation|tace|deb-tace|crioablação|microwave|rfa|watch-?and-?wait|órgão-?preservação|total\s+neoadjuvant|tnt|vigilância\s+ativa)\b/i.test(blobWide)) {
      return { label: 'Cirurgia/RT', color: '#F472B6', icon: 'scissors' };
    }

    // 7.5) FALLBACK — regime descrito apenas no campo `esquema` (ex.: protocolos
    // pediátricos de QT multiagente, em que o acrônimo não nomeia os fármacos).
    // Só roda quando nada acima casou; pula categorias de contexto/plataforma
    // (multi-braço por design → manter rótulo neutro, não forçar um braço).
    if (cat !== 'prostata_contexto') {
      const esq = String(s.esquema || '').toLowerCase();
      if (RE_IMMUNO.test(esq) || /\bipi\b/i.test(esq)) return { label: 'Imunoterapia', color: '#34D399', icon: 'shield-plus' };
      if (RE_ADC.test(esq)) return { label: 'ADC', color: '#2563EB', icon: 'link-2' };
      if (RE_PARP.test(esq)) return { label: 'PARP', color: '#E11D48', icon: 'dna' };
      if (RE_TARGETED.test(esq)) return { label: 'Terapia-alvo', color: '#0EA5B7', icon: 'target' };
      if (RE_CDK.test(esq)) return { label: 'CDK4/6', color: '#0D9488', icon: 'timer' };
      if (RE_ARPI.test(esq)) return { label: 'ARPi', color: '#0E7490', icon: 'mars' };
      if (RE_SERD.test(esq)) return { label: 'SERD', color: '#DB2777', icon: 'venus' };
      if (RE_CHEMO.test(esq)) return { label: 'Quimioterapia', color: '#FBBF24', icon: 'flask-conical' };
    }

    // 7.7) HORMONIOTERAPIA — endócrino "puro" (mama HR+ adjuvante/avançada, supressão
    // ovariana). Prioridade BAIXA de propósito: combos CDK4/6+endócrino, PI3K+fulvestranto,
    // ARPi de próstata e SERDs orais já saíram acima como Terapia-alvo (agente definidor).
    const RE_HORMONE = /\b(tamoxifen|toremifen|raloxifen|fulvestrant|anastrozol|letrozol|exemestan|aromatase|megestrol|medroxiprogest|goserelin|leuprorrel|triptorrel|triptorelin|busserel|ooforectom|oophorectom|supress[aã]o ovariana|abla[cç][aã]o ovariana|hormonioterapia|endocrinoterapia|endocrine therapy|inibidor de aromatase)\w*/i;
    if (RE_HORMONE.test(blobNarrow) || RE_HORMONE.test(String(s.esquema || '').toLowerCase())) {
      return { label: 'Hormonioterapia', color: '#D946EF', icon: 'pill' };
    }

    // 7.8) PLATAFORMA — entradas de overview multibraço (não um braço/fármaco específico).
    // Baixa prioridade: um braço concreto (ex.: STAMPEDE-2 = ¹⁷⁷Lu-PSMA) já saiu como sua
    // modalidade própria; só o resumo-plataforma chega aqui.
    if (/\b(plataforma|platform|multi-?arm multi-?stage|mams)\b/i.test((s.estudo || '') + ' ' + (s.acron || ''))) {
      return { label: 'Plataforma', color: '#818CF8', icon: 'git-branch' };
    }

    // 8) Default
    return { label: 'Sistêmica', color: '#8E949C', icon: 'circle' };
  };

  // Formatador para teranóstico: retorna nome completo do radiotraçador (ex: ²²⁵Ac-PSMA-617)
  TheraTrials._formatTheranosticLabel = function(s) {
    let rfa = s.radiofarmaco || '';
    // Normalizar superscripts unicode → dígitos comuns
    rfa = rfa.replace(/[⁰¹²³⁴⁵⁶⁷⁸⁹]/g, (m) => '⁰¹²³⁴⁵⁶⁷⁸⁹'.indexOf(m).toString());

    // Padrão típico: "[177Lu]Lu-PSMA-617", "225Ac-PSMA-617", "[131I]MIBG", "223Ra-dicloreto", "90Y-microsferas"
    // Captura: massa atômica + elemento + opcional ligante completo
    const m = rfa.match(/\[?(\d{2,3})\]?\s*([A-Z][a-z]?)[\s\-\]]*([A-Za-z0-9\-\&]+(?:[\s\-][A-Za-z0-9\&]+)*)?/);
    if (m) {
      const mass = m[1];
      const elem = m[2];
      let ligand = (m[3] || '').trim();
      // Limpar: cortar no primeiro parêntese, vírgula, ou espaço seguido de palavra descritiva
      ligand = ligand.split(/\s*[\(,\/]/)[0].trim();
      // Ligandos não têm espaços internos (ex.: PSMA-617, MIBG, DOTATATE, FAP-2286, PSMA-I&T)
      // Cortar tudo a partir do primeiro espaço
      ligand = ligand.split(/\s+/)[0];
      // Se o ligando começa com a sigla do elemento (caso [177Lu]Lu-PSMA-617), descartar essa repetição
      const elemRe = new RegExp('^' + elem + '[\\s\\-]+', 'i');
      ligand = ligand.replace(elemRe, '');
      // Simplificações de nomes longos
      const ll = ligand.toLowerCase();
      if (/dota-?tyr3?-?octreotate|tyr3?-?octreotate/.test(ll)) ligand = 'DOTATATE';
      else if (/dota-?(tyr3?-?)?octreotide/.test(ll)) ligand = 'DOTATOC';
      else if (/dota-?nal3?-?octreotide/.test(ll)) ligand = 'DOTANOC';
      else if (/dota-?mtate|dotam-?tate/.test(ll)) ligand = 'DOTAMTATE';
      else if (/microsferas?|micro.?esferas?|sir-?spheres|therasphere/.test(ll)) ligand = 'microesferas';
      else if (/dicloreto|chloride/.test(ll)) ligand = '';  // ²²³Ra puro
      else if (/iodeto|sodium\s*iodide|^nai$/.test(ll)) ligand = '';  // ¹³¹I puro
      else if (/iobenguan/.test(ll)) ligand = 'MIBG';
      // Renderizar
      const eleStr = elem;
      return ligand ? `<sup>${mass}</sup>${eleStr}-${ligand}` : `<sup>${mass}</sup>${eleStr}`;
    }

    // Fallback por categoria
    if (s.category_id === 'hepatobiliar' && /sarah|sirvenib|dosisphere|legacy|premiere|trace|raser|sirflox|foxfire|epoch|tare/i.test(s.estudo || '')) {
      return '<sup>90</sup>Y-microesferas';
    }
    const fbMap = {
      'lupsma_prostata': '<sup>177</sup>Lu-PSMA-617',
      'ra223_prostata': '<sup>223</sup>Ra',
      'net_gep': '<sup>177</sup>Lu-DOTATATE',
      'lupsma_ccrcc': '<sup>177</sup>Lu-PSMA-617',
      'novos_psma': '<sup>225</sup>Ac-PSMA',
      'ppgl': '<sup>131</sup>I-MIBG',
      'neuroblastoma': '<sup>131</sup>I-MIBG',
      'teranostico_emergente': 'Teranóstico',
      'lung_radio_dev': 'Radioexp',
      'breast_radio_dev': 'Radioexp',
    };
    return fbMap[s.category_id] || 'Teranóstico';
  };

  // ============================================================
  // CENÁRIOS CLÍNICOS DE PRÓSTATA
  // ============================================================
  TheraTrials._studyLineProstate = function(s) {
    const fase = String(s.fase || '').toLowerCase();
    const txt = (String(s.indicacao || '') + ' ' + String(s.acron || '') + ' ' + String(s.estudo || '')).toLowerCase();

    // 1) Diretriz / consenso / meta-análise
    if (/diretriz|guideline|consensus|consenso|meta-?an[aá]lise|systematic review/.test(fase) ||
        /\b(guidelines?|diretriz)\b/i.test(s.estudo || '')) {
      return { key: 'diretriz', label: 'Diretriz / Consenso', order: 99 };
    }

    // 2) Neoadjuvante / pré-tratamento curativo (LUTECTOMY, pré-prostatectomia)
    if (/neoadjuvante|neoadjuvant|pr[ée]-?prostatectomia|pr[ée]-?ressec|lutectomy|pre.?surgery/.test(txt)) {
      return { key: 'neoadj', label: 'Pré-tratamento curativo · neoadjuvante', order: 1 };
    }

    // 3) Recidiva bioquímica · oligometastático HSPC (Bullseye, oligo-rt)
    if (/oligometast[áa]tic|recidiva\s+bioqu[íi]mic|biochemical\s+recurr|\bbcr\b|psa.?recidiv|hspc\s+oligo|bullseye/.test(txt)) {
      return { key: 'bcr', label: 'Recidiva bioquímica · oligometastático', order: 2 };
    }

    // 4) mHSPC (hormônio-sensível metastático)
    if (/\bmhspc\b|hormone-?sensit|hormon[iô]nio-?sens|metast[áa]tic\s+hormone-?sensit|hsensit/.test(txt)) {
      return { key: 'mhspc', label: 'mHSPC (hormônio-sensível metastático)', order: 3 };
    }

    // 5) nmCRPC (não-metastático castração-resistente)
    if (/\bnmcrpc\b|non-?metastatic\s+crpc|n[ãa]o-?metast[áa]tic.*castr|m0\s+crpc|psa-?dt\s*≤?\s*10/.test(txt)) {
      return { key: 'nmcrpc', label: 'nmCRPC (não-metastático CR)', order: 4 };
    }

    // 6) mCRPC HRR-mut / PARP (PROfound, MAGNITUDE, TALAPRO-2)
    const isHRR = /\b(hrr|brca[12]?|atm|cdk12|chek2|palb2)\b/.test(txt) ||
                  /\b(olaparib|talazoparib|niraparib|rucaparib)\w*/.test(txt);
    if (isHRR && /mcrpc|castr.*resist/.test(txt)) {
      return { key: 'mcrpc_hrr', label: 'mCRPC HRR-mut (PARPi)', order: 5 };
    }

    // 7) mCRPC pós-ARPi E pós-taxano (multi-tratado — VISION, CARD)
    const posArpi = /(p[óo]s.?(?:≥?\s*\d+\s*)?(?:arpi|abirat|enzalu|apalu|darolu))/i.test(txt);
    const posTax  = /p[óo]s.?(?:≥?\s*\d+\s*)?(?:taxano|docetaxel|cabazitaxel|quimio|chemo)\b/i.test(txt) &&
                    !/com\s+ou\s+sem\s+(?:qt|quimio)/.test(txt);
    if (posArpi && posTax) {
      return { key: 'mcrpc_multi', label: 'mCRPC pós-ARPi + pós-taxano', order: 8 };
    }

    // 8) mCRPC pós-ARPi · pré-taxano (PSMAfore, SPLASH, TheraP—wait, TheraP é pós-doce; só pré-taxano se explícito)
    if (posArpi && /pr[ée]-?taxano|sem\s+quimio|chemo-?naive|taxano-?naive|sem\s+chemo\s+pr[ée]vi/.test(txt)) {
      return { key: 'mcrpc_posarpi_pretax', label: 'mCRPC pós-ARPi · pré-taxano', order: 6 };
    }

    // 9) mCRPC pós-taxano / pós-quimio (AFFIRM, COU-AA-301, TheraP, CARD)
    if (posTax && /crpc|castr.*resist/.test(txt)) {
      return { key: 'mcrpc_posqt', label: 'mCRPC pós-quimio (taxano)', order: 7 };
    }

    // 10) mCRPC 1L · pré-quimio (PREVAIL, COU-AA-302)
    if (/(?:pr[ée]-?qt|pr[ée]-?quimio|pr[ée]-?docetaxel|chemo-?naive|sem\s+quimio|min\s+sintom).*(crpc|castr)/.test(txt) ||
        /(crpc|castr.*resist).*?(?:pr[ée]-?qt|pr[ée]-?quimio|chemo-?naive)/.test(txt) ||
        /\bmcrpc\s+1[ªa]\s*linha\b|1l\s+mcrpc/.test(txt)) {
      return { key: 'mcrpc_1L', label: 'mCRPC 1L · pré-quimio', order: 5 };
    }

    // 11) mCRPC ósseo sintomático (α-emissor — ALSYMPCA)
    if (/mcrpc.*[óo]sse|metast.*[óo]sse.*castr|sintom[áa]tico\s+sem\s+mets?\s+visc|\b[óo]sseo\s+sintom[áa]tico\b/.test(txt)) {
      return { key: 'mcrpc_osseo', label: 'mCRPC ósseo sintomático', order: 9 };
    }

    // 12) mCRPC genérico
    if (/mcrpc|castration-?resistant|castr.*resist/.test(txt)) {
      return { key: 'mcrpc', label: 'mCRPC (cenário geral)', order: 10 };
    }

    // Fallback
    return { key: 'av', label: 'Câncer de próstata · geral', order: 50 };
  };

  // ============================================================
  // CLASSIFICAÇÃO DE LINHA DE TRATAMENTO
  // Retorna { key, label, order } para agrupar dentro de modalidade
  // Aceita tumorId opcional para usar regras tumor-específicas
  // ============================================================
  TheraTrials.studyLine = function(s, tumorId) {
    if (!s) return { key: 'geral', label: 'Geral', order: 10 };
    // Regras tumor-específicas (cenários clínicos próprios)
    if (tumorId === 'prostata') return TheraTrials._studyLineProstate(s);
    // — Genérica abaixo —
    const fase  = String(s.fase || '').toLowerCase();
    const ind   = String(s.indicacao || '').toLowerCase();
    const acron = String(s.acron || '').toLowerCase();
    const est   = String(s.estudo || '').toLowerCase();
    const txt   = ind + ' ' + acron + ' ' + est;

    // Diretriz / Meta-análise (não-trial)
    if (/diretriz|guideline|consensus|consenso|meta-?an[aá]lise|systematic review/i.test(fase) ||
        /\b(guidelines?|diretriz)\b/i.test(s.estudo || '')) {
      return { key: 'diretriz', label: 'Diretriz / Consenso', order: 99 };
    }

    // Adjuvante / Neoadjuvante / Perioperatório / Locorregional curativo
    if (/\b(adjuvante|adjuvant|perioperat[óo]ri|neoadjuvante|neoadjuvant|p[óo]s-?cirurgia|p[óo]s-?ressec|consolida[çc][ãa]o\s+(?:p[óo]s-?asct|imunoter|asct)|consolidation|watch.?and.?wait|órg[ãa]o-?preserv|vigil[âa]ncia\s+ativa|abla[çc][ãa]o|m[óo]rgan-?preserv|tnt\b|total\s+neoadjuvant|risco\s+(?:baixo|intermedi[áa]rio|alto)\s+(?:cdt|p[óo]s)|hr-?nbl|asct\b)\b/i.test(txt)) {
      return { key: 'adj', label: 'Adjuvante · Perioperatório · Locorregional', order: 1 };
    }

    // Localmente avançado / Estágio II-III (pré-metastático mas não-adjuvante puro)
    if (/\b(localmente\s+avan[çc]ado|locally\s+advanced|est[áa]gio\s+(?:ii|iii)\b|stage\s+(?:ii|iii)\b)\b/i.test(txt) &&
        !/refrat|metast|avan[çc]ado\/met|m1\b/i.test(txt)) {
      return { key: 'loc_adv', label: 'Localmente avançado', order: 2 };
    }

    // Refratário / 3L+ / pós-múltiplas linhas
    if (/refrat[áa]rio|recidivad|relapsed|3.?ª?\s*linha|terceira\s+linha|third.?line|p[óo]s.?gemcis|p[óo]s.?(?:lu-?dotatate|prrt)|p[óo]s.?sorafenib|p[óo]s.?2\s*linhas|fourth.?line|p[óo]s.?(?:sunitinib|pazopanib|cabozan)|sotorasib.*pani|sotorasib\s+\+\s+panitumumab|adagrasib.*cetuximab|pos.?asct.*recidiv|altamente\s+refrat/i.test(txt)) {
      return { key: '3L', label: '3ª linha+ · Refratário', order: 5 };
    }

    // 2ª linha / pós-1L
    if (/\b(2.?ª?\s*linha|segunda\s+linha|\b2l\b|second.?line|p[óo]s.?1l\b|p[óo]s.?primeira\s+linha|p[óo]s.?progress[ãa]o\s+a\s+\w+|after\s+(?:sorafenib|gemcis|chemo)|pos.?fluoro\/oxa|p[óo]s.?fluoro)\b/i.test(txt)) {
      return { key: '2L', label: '2ª linha', order: 4 };
    }

    // 1ª linha
    if (/\b(1.?ª?\s*linha|primeira\s+linha|\b1l\b|first.?line|n[ãa]o.?tratad|untreated|treatment.?naive|sem\s+sist[eê]mica|sem\s+tratamento\s+pr[ée]vio|chemo.?naive|consolida[çc][ãa]o\s+inicial)\b/i.test(txt)) {
      return { key: '1L', label: '1ª linha', order: 3 };
    }

    // Avançado/Metastático geral (sem linha explícita)
    return { key: 'av', label: 'Avançado / Metastático', order: 10 };
  };

  TheraTrials.phaseShort = function(fase) {
    const f = String(fase || '').toLowerCase();
    if (f.includes('fase 3') && f.includes('plataforma')) return 'Fase 3 Plat.';
    if (f.includes('fase 3')) return 'Fase 3';
    if (f.includes('1/2')) return 'Fase 1/2';
    if (f.includes('fase 2')) return 'Fase 2';
    if (f.includes('fase 1')) return 'Fase 1';
    if (f.includes('coorte')) return 'Coorte';
    if (f.includes('retrospect')) return 'Retro';
    return fase || '—';
  };

  TheraTrials.isOngoing = function(s) {
    return s.status === 'Em andamento';
  };

  // ============================================================
  // FILTROS HIERÁRQUICOS — usados pelo database.html
  // ============================================================

  // Helper: estudo cobre tumor X? Prioriza array tumors[] (taxonomia canônica),
  // cai no category_id legado se ausente.
  function hasTumor(s, ...ids) {
    if (Array.isArray(s.tumors) && s.tumors.length) {
      return s.tumors.some(t => ids.includes(t));
    }
    return false;
  }
  TheraTrials.hasTumor = hasTumor;

  // Tipos tumorais (multi-select) — prioriza s.tumors[]; fallback para category_id legado
  TheraTrials.tumorTypes = [
    { id: 'prostata', name: 'Próstata', short: 'Próstata',
      match: (s) => hasTumor(s, 'prostata') || ['lupsma_prostata', 'ra223_prostata', 'novos_psma', 'prostata_contexto', 'rt_prostata_local'].includes(s.category_id) || (s.category_id === 'rt_sbrt_oligo' && /(prostat|mCRPC|mHSPC|STOMP|ORIOLE|STAMPEDE)/i.test((s.indicacao||'') + ' ' + (s.estudo||''))) },
    { id: 'pulmao', name: 'Pulmão (NSCLC + SCLC)', short: 'Pulmão',
      match: (s) => hasTumor(s, 'nsclc', 'nsclc_egfr', 'nsclc_alk', 'nsclc_kras', 'nsclc_outros_drivers', 'nsclc_imuno', 'nsclc_periop', 'sclc') || ['nsclc_imuno', 'nsclc_alvo', 'nsclc_periop', 'sclc', 'lung_radio_dev'].includes(s.category_id) || (['rt_sbrt_oligo', 'rt_consolidacao'].includes(s.category_id) && /(NSCLC|SCLC|pulmão|lung|PACIFIC|LAURA|KEYNOTE-799|SINDAS|ADRIATIC|STARS|ROSEL)/i.test((s.indicacao||'') + ' ' + (s.estudo||''))) },
    { id: 'mama', name: 'Mama (HER2+, HR+, TNBC)', short: 'Mama',
      match: (s) => hasTumor(s, 'mama_her2pos', 'mama_hrpos', 'mama_tnbc') || ['breast_her2', 'breast_hrpos', 'breast_tnbc_brca', 'breast_radio_dev'].includes(s.category_id) || (s.category_id === 'rt_sbrt_oligo' && /(mama|breast|NRG-BR)/i.test((s.indicacao||'') + ' ' + (s.estudo||''))) },
    { id: 'net', name: 'Tumores neuroendócrinos (GEP + brônquicos)', short: 'Neuroendócrinos',
      match: (s) => hasTumor(s, 'net_gep') || s.category_id === 'net_gep' },
    { id: 'pheo_pgl', name: 'Feocromocitoma e Paraganglioma (PPGL)', short: 'Feocromocitoma',
      match: (s) => hasTumor(s, 'ppgl') || s.category_id === 'ppgl' },
    { id: 'neuroblastoma', name: 'Neuroblastoma', short: 'Neuroblastoma',
      match: (s) => hasTumor(s, 'neuroblastoma') || s.category_id === 'neuroblastoma' },
    { id: 'hcc', name: 'Hepatocelular (CHC)', short: 'CHC',
      match: (s) => hasTumor(s, 'hcc') || /(hcc|hepatocelular)/i.test(s.indicacao || '') },
    { id: 'colangiocarcinoma', name: 'Colangiocarcinoma (intra/extra-hep + vesícula)', short: 'Colangio',
      match: (s) => hasTumor(s, 'colangiocarcinoma', 'vesicula') },
    { id: 'mcrc', name: 'Colorretal', short: 'Colorretal',
      match: (s) => hasTumor(s, 'colorretal') || /(mcrc|colorretal)/i.test(s.indicacao || '') },
    { id: 'ccrcc', name: 'Renal (ccRCC e não-clear)', short: 'Rim',
      match: (s) => hasTumor(s, 'ccrcc', 'rcc_naoclear') || ['lupsma_ccrcc', 'rcc_avancado', 'rcc_adjuvante_naocc'].includes(s.category_id) },
    { id: 'urotelial', name: 'Urotelial (bexiga · trato superior · NMIBC)', short: 'Bexiga',
      match: (s) => hasTumor(s, 'urotelial_avancado', 'urotelial_periop') || ['urotelial_avancado', 'urotelial_periop_nmibc'].includes(s.category_id) },
    { id: 'tireoide', name: 'Tireoide (CDT / MTC / ATC)', short: 'Tireoide',
      match: (s) => hasTumor(s, 'tireoide_cdt', 'tireoide_mtc', 'tireoide_atc') || s.category_id === 'tireoide_avancado' },
    { id: 'esofago_egj', name: 'Esôfago e EGJ (ESCC + EAC + gástrico)', short: 'Esôfago e estômago',
      match: (s) => hasTumor(s, 'esofago_escc', 'esofago_eac', 'gastrico') || s.category_id === 'esofago_egj' },
    { id: 'pancreas', name: 'Pâncreas (adenocarcinoma)', short: 'Pâncreas',
      match: (s) => hasTumor(s, 'pancreas_ductal') || s.category_id === 'pancreas' },
    // 'teranostico_emergente' saiu daqui em 2026-08-09: é modalidade, não tipo tumoral.
    // Continua como categoria e como sub-filtro dentro da modalidade Teranóstico.
    // Os dois cards da categoria ganharam `tumors[]` e aparecem no órgão certo.
    { id: 'hnscc', name: 'Cabeça e Pescoço (HNSCC)', short: 'Cabeça e pescoço',
      match: (s) => hasTumor(s, 'hnscc') || s.category_id === 'hnscc' },
    { id: 'melanoma', name: 'Melanoma (cutâneo + uveal)', short: 'Melanoma',
      match: (s) => hasTumor(s, 'melanoma_cutaneo', 'melanoma_uveal') || ['melanoma_avancado', 'melanoma_adjuvante'].includes(s.category_id) },
    { id: 'mieloma', name: 'Mieloma múltiplo (NDMM + RRMM)', short: 'Mieloma',
      match: (s) => hasTumor(s, 'mieloma') || s.category_id === 'mieloma' },
    { id: 'linfoma', name: 'Linfoma B agressivo (DLBCL · Hodgkin · PTCL)', short: 'Linfoma',
      match: (s) => hasTumor(s, 'dlbcl', 'hodgkin', 'follicular') || s.category_id === 'linfoma_dlbcl' },
    { id: 'lma', name: 'Leucemia mieloide aguda (LMA)', short: 'Leucemia',
      match: (s) => hasTumor(s, 'lma', 'lla') || s.category_id === 'lma' },
    { id: 'ovario', name: 'Ovário (epitelial avançado/recidivado)', short: 'Ovário',
      match: (s) => hasTumor(s, 'ovario') || s.category_id === 'ovario' },
    { id: 'endometrio', name: 'Endométrio (avançado/recidivado)', short: 'Endométrio',
      match: (s) => hasTumor(s, 'endometrio') || s.category_id === 'endometrio' },
    { id: 'cervix', name: 'Cérvix (LACC + recurrente/metastático)', short: 'Colo do útero',
      match: (s) => hasTumor(s, 'cervix') || s.category_id === 'cervix' },
  ];

  TheraTrials.tumorTypesUpcoming = [
    { id: 'tgi', name: 'Trato gastrointestinal (cólon, reto, hepatobiliar)' },
    { id: 'ginecologico', name: 'Ginecológico (ovário, endométrio, cérvix)' },
    { id: 'hematologico', name: 'Hematológico (mieloma, linfoma, leucemias)' },
  ];

  // Modalidades terapêuticas (multi-select com subníveis)
  TheraTrials.modalities = [
    { id: 'teranostico', name: 'Teranóstico', short: 'Teranóstico',
      match: (s) => ['lupsma_prostata', 'ra223_prostata', 'net_gep', 'lupsma_ccrcc', 'hepatobiliar', 'novos_psma', 'ppgl', 'neuroblastoma', 'lung_radio_dev', 'breast_radio_dev', 'teranostico_emergente'].includes(s.category_id),
      subs: [
        { id: 'lupsma_prostata', name: '177Lu-PSMA · Próstata', short: 'Lu-PSMA' },
        { id: 'ra223_prostata', name: '223Ra · Próstata', short: 'Ra-223' },
        { id: 'net_gep', name: 'NETs · GEP e brônquicos (PRRT)', short: 'NETs' },
        { id: 'lupsma_ccrcc', name: '177Lu-PSMA · ccRCC', short: 'Lu-PSMA-RCC' },
        { id: 'hepatobiliar', name: 'Hepatobiliar (CHC, colangio · inclui TARE Y-90)', short: 'Hepatobiliar' },
        { id: 'novos_psma', name: 'Novos PSMA (α / 161Tb / RIT)', short: 'α-PSMA' },
        { id: 'ppgl', name: 'PPGL · 131I-MIBG e 177Lu-DOTATATE', short: 'PPGL' },
        { id: 'neuroblastoma', name: 'Neuroblastoma · pediátrico', short: 'NB' },
        { id: 'lung_radio_dev', name: 'Pulmão · radio-exp (DLL3, FAPI)', short: 'Lung-radio' },
        { id: 'breast_radio_dev', name: 'Mama · 89Zr-trastu, FES, FAPI', short: 'Mama-radio' },
        { id: 'teranostico_emergente', name: 'Pipeline emergente (FAPI pan-tumor, 64Cu/67Cu-PSMA)', short: 'Pipeline exp' },
      ]},
    { id: 'imunoterapia', name: 'Imunoterapia (ICIs · vacinas · BiTE)', short: 'Imuno',
      match: (s) => {
        const r = (s.radiofarmaco || '').toLowerCase();
        if (/(sipuleucel|vacina)/i.test(r)) return true;
        if (['nsclc_imuno', 'sclc'].includes(s.category_id)) return true;
        if (s.category_id === 'nsclc_periop' && !/osi|alect/i.test(r)) return true;
        if (s.category_id === 'breast_tnbc_brca' && /pembro|nivo|atezo|durva/i.test(r)) return true;
        // Uro-oncologia: regimes IO ou IO+TKI/QT/ADC nas 4 categorias novas
        const uroCats = ['rcc_avancado', 'rcc_adjuvante_naocc', 'urotelial_avancado', 'urotelial_periop_nmibc'];
        if (uroCats.includes(s.category_id) && /(pembro|nivo|atezo|durva|avelumab|tremelimumab|ipilimumab|n-803|nogapendekin|anktiva)/i.test(r)) return true;
        return false;
      },
      subs: [
        { id: 'nsclc_imuno', name: 'NSCLC · ICI 1L', short: 'NSCLC IO' },
        { id: 'nsclc_periop', name: 'NSCLC · perioperatório IO', short: 'NSCLC periop IO' },
        { id: 'sclc', name: 'SCLC · imuno + QT, BiTE', short: 'SCLC' },
        { id: 'breast_tnbc_brca', name: 'Mama · TNBC neoadj/1L (KEYNOTE-522/-355)', short: 'Mama TNBC IO' },
        { id: 'prostata_contexto', name: 'Próstata · vacinas (Sipuleucel-T)', short: 'Próstata' },
        { id: 'rcc_avancado', name: 'ccRCC · IO+TKI / IO+IO 1L (CM-214, KN-426, CM-9ER, CLEAR)', short: 'ccRCC IO' },
        { id: 'rcc_adjuvante_naocc', name: 'RCC · IO adjuvante (KN-564, CM-914, IMmotion010)', short: 'RCC adj IO' },
        { id: 'urotelial_avancado', name: 'Urotelial · IO+ADC/QT 1L e 2L+ (EV-302, CM-901, KN-045)', short: 'Uro IO' },
        { id: 'urotelial_periop_nmibc', name: 'Urotelial · IO periop e NMIBC (NIAGARA, CM-274, KN-057)', short: 'Uro periop IO' },
      ]},
    { id: 'terapia_alvo', name: 'Terapia-alvo (TKIs · ARPi · CDK4/6 · PI3K · VEGFR · FGFR · HIF-2α)', short: 'Alvo',
      match: (s) => {
        const r = (s.radiofarmaco || '').toLowerCase();
        const isProstateARPi = s.category_id === 'prostata_contexto' && /(abiraterona|enzalutamida|apalutamida|darolutamida)/i.test(r) && !/(olaparib|rucaparib|niraparib|talazoparib)/i.test(r);
        const isLungAlvo = s.category_id === 'nsclc_alvo';
        const isLungAdjAlvo = s.category_id === 'nsclc_periop' && /osi|alect/i.test(r);
        const isBreastAlvo = s.category_id === 'breast_hrpos' || (s.category_id === 'breast_her2' && /(tucatinib|neratinib|lapatinib)/i.test(r));
        // Uro-oncologia: TKIs VEGFR (sunitinibe/cabo/axi/pazo/lenva/tivo), FGFRi (erdafitinibe), HIF-2α (belzutifan), MET (savolitinibe/crizo)
        const uroCats = ['rcc_avancado', 'rcc_adjuvante_naocc', 'urotelial_avancado'];
        const isUroAlvo = uroCats.includes(s.category_id) && /(sunitinib|cabozantinib|axitinib|pazopanib|lenvatinib|tivozanib|sorafenib|everolimus|belzutifan|erdafitinib|savolitinib|crizotinib)/i.test(r);
        return isProstateARPi || isLungAlvo || isLungAdjAlvo || isBreastAlvo || isUroAlvo;
      },
      subs: [
        { id: 'arpi', name: 'ARPi · próstata', short: 'ARPi' },
        { id: 'egfr', name: 'NSCLC · EGFR (FLAURA, MARIPOSA, ADAURA)', short: 'EGFR' },
        { id: 'alk', name: 'NSCLC · ALK (ALEX, CROWN, ALINA)', short: 'ALK' },
        { id: 'kras', name: 'NSCLC · KRAS G12C (CodeBreaK)', short: 'KRAS' },
        { id: 'ret_met_her2_ros1', name: 'NSCLC · RET / MET / HER2 / ROS1-NTRK', short: 'Outros drivers' },
        { id: 'cdk46', name: 'Mama · CDK4/6i (palbo, ribo, abema)', short: 'CDK4/6' },
        { id: 'pi3k_akt', name: 'Mama · PI3K/AKT (alpelisib, inavolisib, capivasertib)', short: 'PI3K/AKT' },
        { id: 'serd_her2tki', name: 'Mama · SERDs orais e HER2-TKI (elacestrant, tucatinib)', short: 'SERD/HER2-TKI' },
        { id: 'vegfr_tki_rcc', name: 'RCC · VEGFR-TKI (sunitinibe, cabo, axi, lenva, pazo, tivo)', short: 'VEGFR-TKI' },
        { id: 'hif2a', name: 'RCC · HIF-2α (belzutifan)', short: 'HIF-2α' },
        { id: 'fgfr_uro', name: 'Urotelial · FGFR (erdafitinibe)', short: 'FGFR' },
        { id: 'met_papRCC', name: 'papRCC · MET (savolitinibe, crizotinibe)', short: 'MET' },
      ]},
    { id: 'adc', name: 'ADC · conjugados anticorpo-droga', short: 'ADC',
      match: (s) => /(trastuzumab emtansine|t-dm1|trastuzumab deruxtecan|t-dxd|sacituzumab|datopotamab|enfortumab vedotin|enfortumabe vedotina)/i.test(s.radiofarmaco || ''),
      subs: [
        { id: 'tdm1', name: 'T-DM1 (HER2+)', short: 'T-DM1' },
        { id: 'tdxd', name: 'T-DXd (HER2+ e HER2-low · pan-tumor IHC 3+)', short: 'T-DXd' },
        { id: 'sacituzumab', name: 'Sacituzumab govitecan (TNBC, Trop-2)', short: 'Sacituzumab' },
        { id: 'ev_uro', name: 'Enfortumab vedotin (Nectin-4 · UC)', short: 'EV' },
      ]},
    { id: 'parp', name: 'PARP inibidores', short: 'PARP',
      match: (s) => /(olaparib|rucaparib|niraparib|talazoparib)/i.test(s.radiofarmaco || ''),
      subs: [
        { id: 'parp_prostata', name: 'Próstata HRR+ (PROfound, TRITON, PROpel, MAGNITUDE, TALAPRO)', short: 'Próstata' },
        { id: 'parp_mama', name: 'Mama BRCA+ (OlympiAD, EMBRACA, OlympiA)', short: 'Mama BRCA+' },
      ]},
    { id: 'qt', name: 'Quimioterapia citotóxica', short: 'QT',
      match: (s) => {
        const r = (s.radiofarmaco || '').toLowerCase();
        return /(docetaxel|cabazitaxel)/i.test(r) && !/(psma|lu-?psma|ra-?223|177lu)/.test(r);
      }},
    { id: 'rt_sbrt', name: 'Radioterapia / SBRT', short: 'RT/SBRT',
      match: (s) => ['rt_sbrt_oligo', 'rt_prostata_local', 'rt_consolidacao'].includes(s.category_id),
      subs: [
        { id: 'rt_sbrt_oligo', name: 'RT/SBRT · Doença oligometastática (STOMP, ORIOLE, SABR-COMET)', short: 'Oligomet' },
        { id: 'rt_prostata_local', name: 'RT · Próstata localizada e pós-operatória (PACE-B, FLAME, RADICALS)', short: 'Próstata local' },
        { id: 'rt_consolidacao', name: 'RT · Consolidação e combinação IO/TKI (PACIFIC, LAURA, ADRIATIC)', short: 'Consolid. IO/TKI' },
      ]},
  ];

  TheraTrials.modalitiesUpcoming = [
    { id: 'cart', name: 'CAR-T' },
    { id: 'anti_angio', name: 'Anti-angiogênico' },
    { id: 'biteother', name: 'BiTE/anticorpos bispecíficos (não DLL3)' },
  ];

  // Linhas de tratamento
  TheraTrials.treatmentLines = [
    { id: '1L', name: '1ª linha',
      match: (s) => {
        const t = ((s.indicacao || '') + ' ' + (s.estudo || '') + ' ' + (s.fase || '')).toLowerCase();
        return /\b(1ª linha|1l|first-line|pré-qt|mhspc|recém-diagnost|de novo)\b/i.test(t);
      }},
    { id: '2L', name: '2ª linha',
      match: (s) => {
        const t = ((s.indicacao || '') + ' ' + (s.estudo || '')).toLowerCase();
        return /(pós-1|pos-1|pós-arpi|pós-doce|pós-docetaxel|2ª linha|2l|second-line|after.*progression)/i.test(t);
      }},
    { id: '3L', name: '3ª linha+',
      match: (s) => {
        const t = ((s.indicacao || '') + ' ' + (s.estudo || '')).toLowerCase();
        return /(pós-≥2|pós-2|pós-doce.*pós-arpi|3ª linha|3l|multi.*linha|fortemente pré-trat|heavily pretreat)/i.test(t);
      }},
    { id: 'adjuvante', name: 'Adjuvante',
      match: (s) => /(adjuvante|adjuvant)/i.test((s.indicacao || '') + ' ' + (s.estudo || '')) || (s.category_id === 'nsclc_periop') },
    { id: 'neoadjuvante', name: 'Neoadjuvante',
      match: (s) => /(neoadjuvante|neoadjuvant|pré-rpt|pre-rpt|pré-prostatec|pre-prostatec|neoadj|perioperat)/i.test((s.indicacao || '') + ' ' + (s.estudo || '') + ' ' + (s.desenho || '')) },
    { id: 'localizado', name: 'Localizado',
      match: (s) => /(localizado|hrlpc|localized)/i.test((s.indicacao || '') + ' ' + (s.estudo || '')) },
  ];


  // Mapeamentos por modalidade terapêutica (para a página Modalidades)
  TheraTrials.modalityMap = {
    teranostico: {
      name: 'Teranóstico',
      tagline: 'Imagem molecular + radiofármaco terapêutico no mesmo alvo',
      icon: 'atom',
      color: '#FF8400',
      categorias: ['lupsma_prostata', 'ra223_prostata', 'net_gep', 'lupsma_ccrcc', 'hepatobiliar', 'novos_psma', 'ppgl', 'neuroblastoma']
    },
    terapia_alvo: {
      name: 'Terapias-alvo molecular',
      tagline: 'Inibidores específicos guiados por biomarcador (HRR, BRCA, ARPi)',
      icon: 'target',
      color: '#0EA5B7',
      keywords: ['olaparib', 'rucaparib', 'niraparib', 'talazoparib', 'abiraterona', 'enzalutamida', 'apalutamida', 'darolutamida']
    },
    quimio: {
      name: 'Quimioterapia citotóxica',
      tagline: 'Esquemas com taxanos em mHSPC e mCRPC',
      icon: 'flask-conical',
      color: '#FBBF24',
      keywords: ['docetaxel', 'cabazitaxel']
    },
    imunoterapia: {
      name: 'Imunoterapia',
      tagline: 'Vacinas autólogas (escopo atual em próstata)',
      icon: 'shield-plus',
      color: '#34D399',
      keywords: ['sipuleucel-t', 'vacina']
    }
  };

  // Mapa de tumores → categorias e palavras-chave
  TheraTrials.tumorMap = {
    prostata: {
      name: 'Câncer de próstata',
      tagline: 'mHSPC, mCRPC, nmCRPC, oligometastático',
      icon: 'circle-dot',
      color: '#FF8400',
      categorias: ['lupsma_prostata', 'ra223_prostata', 'novos_psma', 'prostata_contexto']
    },
    net: {
      name: 'Tumores neuroendócrinos',
      tagline: 'GEP-NET, midgut, pancreático, brônquico/pulmonar',
      icon: 'activity',
      color: '#10B981',
      categorias: ['net_gep']
    },
    pheo_pgl: {
      name: 'Feocromocitoma e paraganglioma',
      tagline: 'PPGL maligno · 131I-MIBG e 177Lu-DOTATATE',
      icon: 'heart-pulse',
      color: '#EC4899',
      categorias: ['ppgl']
    },
    neuroblastoma: {
      name: 'Neuroblastoma (pediatria)',
      tagline: 'Alto risco refratário/recidivado · 131I-MIBG e PRRT pediátrica',
      icon: 'baby',
      color: '#8B5CF6',
      categorias: ['neuroblastoma']
    },
    hcc: {
      name: 'Carcinoma hepatocelular (CHC)',
      tagline: 'BCLC A/B/C · IO+anti-VEGF, TKIs, IO duplo, radioembolização ⁹⁰Y',
      icon: 'droplet',
      color: '#FBBF24',
      categorias: ['hepatobiliar'],
      filter: function(s) { return (Array.isArray(s.tumors) && s.tumors.includes('hcc')) || /(hcc|hepatocelular)/i.test(s.indicacao||''); }
    },
    colangiocarcinoma: {
      name: 'Colangiocarcinoma e vesícula biliar',
      tagline: 'Intra-hep, extra-hep e vesícula · gem/cis ± durva, alvos moleculares (FGFR2, IDH1, HER2)',
      icon: 'droplet',
      color: '#F59E0B',
      categorias: ['hepatobiliar'],
      filter: function(s) { return Array.isArray(s.tumors) && (s.tumors.includes('colangiocarcinoma') || s.tumors.includes('vesicula')); }
    },
    mcrc: {
      name: 'Câncer colorretal',
      tagline: 'Sistêmico e direcionado a mets hepáticas (TARE ⁹⁰Y)',
      icon: 'activity-square',
      color: '#F87171',
      categorias: ['hepatobiliar'],
      filter: function(s) { return (Array.isArray(s.tumors) && s.tumors.includes('colorretal')) || /(mcrc|colorretal)/i.test(s.indicacao||''); }
    },
    ccrcc: {
      name: 'Carcinoma renal (ccRCC e não-clear)',
      tagline: '1L IO+TKI/IO+IO · adjuvante · 2L+ HIF-2α · não-clear · teranóstico Lu-PSMA exploratório',
      icon: 'bean',
      color: '#38BDF8',
      categorias: ['lupsma_ccrcc', 'rcc_avancado', 'rcc_adjuvante_naocc']
    },
    urotelial: {
      name: 'Carcinoma urotelial',
      tagline: 'mUC 1L EV+pembro/IO-quimio · adjuvante · perioperatório (NIAGARA, VOLGA) · NMIBC BCG-unresponsive',
      icon: 'flask-conical',
      color: '#EAB308',
      categorias: ['urotelial_avancado', 'urotelial_periop_nmibc']
    },
    pulmao: {
      name: 'Câncer de pulmão',
      tagline: 'NSCLC drivers (EGFR/ALK/KRAS/etc), IO 1L, perioperatório, SCLC, radiofármacos exp',
      icon: 'wind',
      color: '#22d3ee',
      categorias: ['nsclc_imuno', 'nsclc_alvo', 'nsclc_periop', 'sclc', 'lung_radio_dev']
    },
    mama: {
      name: 'Câncer de mama',
      tagline: 'HER2+ (T-DXd, T-DM1), HR+/HER2- (CDK4/6, PI3K, AKT, SERD), TNBC (pembro, sacituzumab), BRCA-mut (PARPi), imagem molecular',
      icon: 'flower-2',
      color: '#ec4899',
      categorias: ['breast_her2', 'breast_hrpos', 'breast_tnbc_brca', 'breast_radio_dev']
    }
  };

})();
