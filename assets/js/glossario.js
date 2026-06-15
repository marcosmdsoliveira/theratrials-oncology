/* ============================================================
   TheraTrials Oncology — Glossário de siglas
   Fonte ÚNICA da verdade para siglas/métricas de ensaios clínicos.
   Alimenta (1) o modal "Legenda de siglas" e (2) os tooltips
   contextuais nos cards e no modal de detalhe do estudo.
   Bilíngue (pt-br / en); a definição é resolvida no momento da
   exibição via window.getLang(), então alternar idioma é instantâneo.
   NENHUMA definição inventada — siglas-padrão de oncologia clínica.
   ============================================================ */
(function () {
  'use strict';

  // Grupos didáticos. Cada termo: a = sigla; pt/en = expansão curta.
  var GLOSSARY = [
    {
      id: 'desfechos', icon: 'target', pt: 'Desfechos de eficácia', en: 'Efficacy endpoints',
      terms: [
        { a: 'OS',    pt: 'Sobrevida global',                                en: 'Overall survival' },
        { a: 'mOS',   pt: 'Sobrevida global mediana',                        en: 'Median overall survival' },
        { a: 'PFS',   pt: 'Sobrevida livre de progressão',                   en: 'Progression-free survival' },
        { a: 'mPFS',  pt: 'Sobrevida livre de progressão mediana',           en: 'Median progression-free survival' },
        { a: 'rPFS',  pt: 'Sobrevida livre de progressão radiográfica',      en: 'Radiographic progression-free survival' },
        { a: 'DFS',   pt: 'Sobrevida livre de doença',                       en: 'Disease-free survival' },
        { a: 'EFS',   pt: 'Sobrevida livre de eventos',                      en: 'Event-free survival' },
        { a: 'RFS',   pt: 'Sobrevida livre de recidiva',                     en: 'Recurrence-free survival' },
        { a: 'MFS',   pt: 'Sobrevida livre de metástases',                   en: 'Metastasis-free survival' },
        { a: 'TTP',   pt: 'Tempo até a progressão',                          en: 'Time to progression' },
        { a: 'DOR',   pt: 'Duração da resposta',                             en: 'Duration of response' },
        { a: 'mDOR',  pt: 'Duração mediana da resposta',                     en: 'Median duration of response' },
        { a: 'QoL',   pt: 'Qualidade de vida',                               en: 'Quality of life' }
      ]
    },
    {
      id: 'resposta', icon: 'activity', pt: 'Resposta e critérios de imagem', en: 'Response & imaging criteria',
      terms: [
        { a: 'ORR',     pt: 'Taxa de resposta objetiva (RC + RP)',          en: 'Objective response rate (CR + PR)' },
        { a: 'CR',      pt: 'Resposta completa',                            en: 'Complete response' },
        { a: 'PR',      pt: 'Resposta parcial',                             en: 'Partial response' },
        { a: 'SD',      pt: 'Doença estável',                               en: 'Stable disease' },
        { a: 'PD',      pt: 'Doença em progressão',                         en: 'Progressive disease' },
        { a: 'DCR',     pt: 'Taxa de controle da doença (RC + RP + DE)',    en: 'Disease control rate (CR + PR + SD)' },
        { a: 'CBR',     pt: 'Taxa de benefício clínico',                    en: 'Clinical benefit rate' },
        { a: 'pCR',     pt: 'Resposta patológica completa',                 en: 'Pathological complete response' },
        { a: 'PSA50',   pt: 'Queda de PSA ≥ 50%',                           en: 'PSA decline ≥ 50%' },
        { a: 'RANO',    pt: 'Critérios de resposta em neuro-oncologia',     en: 'Response Assessment in Neuro-Oncology' },
        { a: 'DoR',     pt: 'Duração da resposta',                          en: 'Duration of response' },
        { a: 'NED',     pt: 'Sem evidência de doença',                      en: 'No evidence of disease' }
      ]
    },
    {
      id: 'estatistica', icon: 'sigma', pt: 'Estatística', en: 'Statistics',
      terms: [
        { a: 'HR',   pt: 'Razão de risco (hazard ratio) — < 1 favorece o braço experimental', en: 'Hazard ratio — < 1 favours the experimental arm' },
        { a: 'OR',   pt: 'Razão de chances (odds ratio)',                   en: 'Odds ratio' },
        { a: 'RR',   pt: 'Risco relativo',                                  en: 'Relative risk' },
        { a: 'IC',   pt: 'Intervalo de confiança (ex.: IC 95%)',            en: 'Confidence interval (e.g., 95% CI)' },
        { a: 'CI',   pt: 'Intervalo de confiança',                          en: 'Confidence interval' },
        { a: 'ITT',  pt: 'Análise por intenção de tratar',                  en: 'Intention-to-treat analysis' },
        { a: 'PP',   pt: 'Análise por protocolo',                           en: 'Per-protocol analysis' },
        { a: 'NR',   pt: 'Não atingido (mediana não alcançada)',            en: 'Not reached (median)' },
        { a: 'NS',   pt: 'Diferença não significativa',                     en: 'Not statistically significant' },
        { a: 'BICR', pt: 'Revisão central independente e cega',             en: 'Blinded independent central review' },
        { a: 'IC95', pt: 'Intervalo de confiança de 95%',                  en: '95% confidence interval' }
      ]
    },
    {
      id: 'biomarcadores', icon: 'dna', pt: 'Biomarcadores e molecular', en: 'Biomarkers & molecular',
      terms: [
        { a: 'SSTR',  pt: 'Receptor de somatostatina',                      en: 'Somatostatin receptor' },
        { a: 'HER2',  pt: 'Receptor 2 do fator de crescimento epidérmico',  en: 'Human epidermal growth factor receptor 2' },
        { a: 'HR+',   pt: 'Receptor hormonal positivo (RE e/ou RP) — mama',  en: 'Hormone receptor-positive (ER and/or PR) — breast' },
        { a: 'HR-',   pt: 'Receptor hormonal negativo — mama',               en: 'Hormone receptor-negative — breast' },
        { a: 'HR−', hidden: true, pt: 'Receptor hormonal negativo — mama', en: 'Hormone receptor-negative — breast' },
        { a: 'HR–', hidden: true, pt: 'Receptor hormonal negativo — mama', en: 'Hormone receptor-negative — breast' },
        { a: 'EGFR',  pt: 'Receptor do fator de crescimento epidérmico',    en: 'Epidermal growth factor receptor' },
        { a: 'ALK',   pt: 'Quinase do linfoma anaplásico (gene/proteína)',  en: 'Anaplastic lymphoma kinase' },
        { a: 'BRAF',  pt: 'Gene/proteína BRAF',                             en: 'BRAF gene/protein' },
        { a: 'PD-L1', pt: 'Ligante 1 de morte programada',                  en: 'Programmed death-ligand 1' },
        { a: 'CPS',   pt: 'Escore combinado de positividade (PD-L1)',       en: 'Combined positive score (PD-L1)' },
        { a: 'TPS',   pt: 'Escore de proporção tumoral (PD-L1)',            en: 'Tumour proportion score (PD-L1)' },
        { a: 'TMB',   pt: 'Carga mutacional tumoral',                       en: 'Tumour mutational burden' },
        { a: 'MSI',   pt: 'Instabilidade de microssatélites',              en: 'Microsatellite instability' },
        { a: 'MSI-H', pt: 'Instabilidade de microssatélites alta',         en: 'Microsatellite instability-high' },
        { a: 'dMMR',  pt: 'Deficiência de reparo de malpareamento',         en: 'Mismatch repair deficiency' },
        { a: 'pMMR',  pt: 'Reparo de malpareamento proficiente',           en: 'Mismatch repair proficient' },
        { a: 'HRD',   pt: 'Deficiência de recombinação homóloga',           en: 'Homologous recombination deficiency' },
        { a: 'HRR',   pt: 'Reparo por recombinação homóloga',               en: 'Homologous recombination repair' },
        { a: 'IHC',   pt: 'Imuno-histoquímica',                            en: 'Immunohistochemistry' },
        { a: 'NGS',   pt: 'Sequenciamento de nova geração',                en: 'Next-generation sequencing' },
        { a: 'ctDNA', pt: 'DNA tumoral circulante',                        en: 'Circulating tumour DNA' },
        { a: 'MRD',   pt: 'Doença residual mínima / mensurável',           en: 'Minimal / measurable residual disease' },
        { a: 'PARP',  pt: 'Enzima poli(ADP-ribose) polimerase',            en: 'Poly(ADP-ribose) polymerase' },
        { a: 'PARPi', pt: 'Inibidor de PARP',                              en: 'PARP inhibitor' }
      ]
    },
    {
      id: 'doenca', icon: 'stethoscope', pt: 'Tipos e contextos de doença', en: 'Disease types & contexts',
      terms: [
        { a: 'NSCLC',  pt: 'Câncer de pulmão de células não pequenas',      en: 'Non-small cell lung cancer' },
        { a: 'SCLC',   pt: 'Câncer de pulmão de pequenas células',          en: 'Small cell lung cancer' },
        { a: 'mCRPC',  pt: 'Câncer de próstata resistente à castração, metastático', en: 'Metastatic castration-resistant prostate cancer' },
        { a: 'nmCRPC', pt: 'Câncer de próstata resistente à castração, não metastático', en: 'Non-metastatic castration-resistant prostate cancer' },
        { a: 'mHSPC',  pt: 'Câncer de próstata hormônio-sensível, metastático', en: 'Metastatic hormone-sensitive prostate cancer' },
        { a: 'mCRC',   pt: 'Câncer colorretal metastático',                 en: 'Metastatic colorectal cancer' },
        { a: 'ccRCC',  pt: 'Carcinoma de células renais de células claras', en: 'Clear cell renal cell carcinoma' },
        { a: 'RCC',    pt: 'Carcinoma de células renais',                   en: 'Renal cell carcinoma' },
        { a: 'HCC',    pt: 'Carcinoma hepatocelular',                       en: 'Hepatocellular carcinoma' },
        { a: 'CHC',    pt: 'Carcinoma hepatocelular',                       en: 'Hepatocellular carcinoma' },
        { a: 'NET',    pt: 'Tumor neuroendócrino',                          en: 'Neuroendocrine tumour' },
        { a: 'PPGL',   pt: 'Feocromocitoma / paraganglioma',                en: 'Pheochromocytoma / paraganglioma' },
        { a: 'TNBC',   pt: 'Câncer de mama triplo-negativo',                en: 'Triple-negative breast cancer' },
        { a: 'DTC',    pt: 'Câncer de tireoide diferenciado',               en: 'Differentiated thyroid cancer' },
        { a: 'MTC',    pt: 'Câncer medular de tireoide',                    en: 'Medullary thyroid cancer' },
        { a: 'PDAC',   pt: 'Adenocarcinoma ductal de pâncreas',            en: 'Pancreatic ductal adenocarcinoma' },
        { a: 'HNSCC',  pt: 'Carcinoma espinocelular de cabeça e pescoço',  en: 'Head and neck squamous cell carcinoma' },
        { a: 'NMIBC',  pt: 'Câncer de bexiga não músculo-invasivo',        en: 'Non-muscle-invasive bladder cancer' },
        { a: 'MIBC',   pt: 'Câncer de bexiga músculo-invasivo',            en: 'Muscle-invasive bladder cancer' },
        { a: 'CIS',    pt: 'Carcinoma in situ',                            en: 'Carcinoma in situ' },
        { a: 'SNC',    pt: 'Sistema nervoso central',                      en: 'Central nervous system' },
        { a: 'HBV',    pt: 'Vírus da hepatite B',                          en: 'Hepatitis B virus' },
        { a: 'HCV',    pt: 'Vírus da hepatite C',                          en: 'Hepatitis C virus' }
      ]
    },
    {
      id: 'tratamento', icon: 'syringe', pt: 'Modalidades de tratamento', en: 'Treatment modalities',
      terms: [
        { a: 'ADT',   pt: 'Terapia de privação androgênica',                en: 'Androgen deprivation therapy' },
        { a: 'ARPi',  pt: 'Inibidor da via do receptor androgênico',        en: 'Androgen receptor pathway inhibitor' },
        { a: 'ARSI',  pt: 'Inibidor da sinalização do receptor androgênico', en: 'Androgen receptor signaling inhibitor' },
        { a: 'TKI',   pt: 'Inibidor de tirosina quinase',                   en: 'Tyrosine kinase inhibitor' },
        { a: 'ICI',   pt: 'Inibidor de checkpoint imune',                   en: 'Immune checkpoint inhibitor' },
        { a: 'IO',    pt: 'Imuno-oncologia / imunoterapia',                 en: 'Immuno-oncology / immunotherapy' },
        { a: 'ADC',   pt: 'Conjugado anticorpo-fármaco',                    en: 'Antibody-drug conjugate' },
        { a: 'mAb',   pt: 'Anticorpo monoclonal',                           en: 'Monoclonal antibody' },
        { a: 'BsAb',  pt: 'Anticorpo biespecífico',                         en: 'Bispecific antibody' },
        { a: 'CAR-T', pt: 'Linfócito T com receptor de antígeno quimérico', en: 'Chimeric antigen receptor T-cell' },
        { a: 'RLT',   pt: 'Terapia com radioligante',                       en: 'Radioligand therapy' },
        { a: 'PRRT',  pt: 'Terapia com radionuclídeo ligado a peptídeo',    en: 'Peptide receptor radionuclide therapy' },
        { a: 'SBRT',  pt: 'Radioterapia estereotáxica corpórea',           en: 'Stereotactic body radiotherapy' },
        { a: 'SABR',  pt: 'Radioterapia ablativa estereotáxica (= SBRT)',  en: 'Stereotactic ablative radiotherapy (= SBRT)' },
        { a: 'CRT',   pt: 'Quimiorradioterapia',                           en: 'Chemoradiotherapy' },
        { a: 'QRT',   pt: 'Quimiorradioterapia',                           en: 'Chemoradiotherapy' },
        { a: 'ASCT',  pt: 'Transplante autólogo de células-tronco',        en: 'Autologous stem-cell transplant' },
        { a: 'BCG',   pt: 'BCG intravesical (imunoterapia da bexiga)',     en: 'Intravesical BCG (bladder immunotherapy)' },
        { a: 'GBq',   pt: 'Gigabecquerel (unidade de atividade radioativa)', en: 'Gigabecquerel (unit of radioactivity)' },
        { a: 'MBq',   pt: 'Megabecquerel (unidade de atividade radioativa)', en: 'Megabecquerel (unit of radioactivity)' },
        { a: 'VO',    pt: 'Via oral',                                      en: 'Oral route' }
      ]
    },
    {
      id: 'orgaos', icon: 'landmark', pt: 'Sociedades e agências', en: 'Societies & agencies',
      terms: [
        { a: 'ESMO',   pt: 'Sociedade Europeia de Oncologia Clínica',       en: 'European Society for Medical Oncology' },
        { a: 'ASCO',   pt: 'Sociedade Americana de Oncologia Clínica',      en: 'American Society of Clinical Oncology' },
        { a: 'NCCN',   pt: 'Rede Nacional Abrangente do Câncer (EUA)',      en: 'National Comprehensive Cancer Network' },
        { a: 'FDA',    pt: 'Agência reguladora de medicamentos dos EUA',    en: 'US Food and Drug Administration' },
        { a: 'EMA',    pt: 'Agência Europeia de Medicamentos',              en: 'European Medicines Agency' },
        { a: 'ANVISA', pt: 'Agência Nacional de Vigilância Sanitária (Brasil)', en: 'Brazilian Health Regulatory Agency' },
        { a: 'AJCC',   pt: 'Comitê Americano Conjunto sobre Câncer (estadiamento)', en: 'American Joint Committee on Cancer (staging)' },
        { a: 'OMS',    pt: 'Organização Mundial da Saúde',                  en: 'World Health Organization (WHO)' },
        { a: 'WHO',    pt: 'Organização Mundial da Saúde',                  en: 'World Health Organization' },
        { a: 'ATA',    pt: 'Associação Americana de Tireoide',             en: 'American Thyroid Association' },
        { a: 'ENETS',  pt: 'Sociedade Europeia de Tumores Neuroendócrinos', en: 'European Neuroendocrine Tumor Society' },
        { a: 'NANETS', pt: 'Sociedade Norte-Americana de Tumores Neuroendócrinos', en: 'North American Neuroendocrine Tumor Society' }
      ]
    },
    {
      id: 'avaliacao', icon: 'clipboard-list', pt: 'Avaliação clínica e segurança', en: 'Clinical assessment & safety',
      terms: [
        { a: 'ECOG',  pt: 'Escala de capacidade funcional ECOG (0 = ativo a 5 = óbito)', en: 'ECOG performance status (0 active – 5 dead)' },
        { a: 'PS',    pt: 'Estado funcional (performance status)',          en: 'Performance status' },
        { a: 'KPS',   pt: 'Índice de desempenho de Karnofsky (0–100)',      en: 'Karnofsky performance status (0–100)' },
        { a: 'TRAE',  pt: 'Evento adverso relacionado ao tratamento',       en: 'Treatment-related adverse event' },
        { a: 'TRAEs', pt: 'Eventos adversos relacionados ao tratamento',    en: 'Treatment-related adverse events' },
        { a: 'irAE',  pt: 'Evento adverso imunorrelacionado',               en: 'Immune-related adverse event' },
        { a: 'irAEs', pt: 'Eventos adversos imunorrelacionados',            en: 'Immune-related adverse events' },
        { a: 'HFS',   pt: 'Síndrome mão-pé (eritrodisestesia palmoplantar)', en: 'Hand-foot syndrome' },
        { a: 'SoC',   pt: 'Tratamento padrão (standard of care)',           en: 'Standard of care' },
        { a: 'PK/PD', pt: 'Perfil farmacocinético/farmacodinâmico',         en: 'Pharmacokinetic/pharmacodynamic profile' },
        { a: 'PK',    pt: 'Farmacocinética',                                en: 'Pharmacokinetics' },
        { a: 'R/R',   pt: 'Recidivante / refratário',                       en: 'Relapsed / refractory' },
        { a: 'R/M',   pt: 'Recidivante / metastático',                      en: 'Recurrent / metastatic' }
      ]
    },
    {
      id: 'exames', icon: 'flask-conical', pt: 'Exames, escores e estadiamento', en: 'Labs, scores & staging',
      terms: [
        { a: 'AFP',        pt: 'Alfafetoproteína (marcador tumoral)',       en: 'Alpha-fetoprotein (tumour marker)' },
        { a: 'CEA',        pt: 'Antígeno carcinoembrionário',               en: 'Carcinoembryonic antigen' },
        { a: 'TSH',        pt: 'Hormônio tireoestimulante',                 en: 'Thyroid-stimulating hormone' },
        { a: 'rhTSH',      pt: 'TSH humano recombinante',                   en: 'Recombinant human TSH' },
        { a: 'LVEF',       pt: 'Fração de ejeção do ventrículo esquerdo',   en: 'Left ventricular ejection fraction' },
        { a: 'FEVE',       pt: 'Fração de ejeção do ventrículo esquerdo',   en: 'Left ventricular ejection fraction' },
        { a: 'QTc',        pt: 'Intervalo QT corrigido (eletrocardiograma)', en: 'Corrected QT interval (electrocardiogram)' },
        { a: 'ULN',        pt: 'Limite superior da normalidade',            en: 'Upper limit of normal' },
        { a: 'FIGO',       pt: 'Estadiamento ginecológico FIGO',            en: 'FIGO gynaecologic staging' },
        { a: 'IMDC',       pt: 'Escore prognóstico IMDC (RCC metastático)', en: 'IMDC prognostic score (metastatic RCC)' }
      ]
    }
  ];

  // ---- Mapa plano sigla -> {pt,en} + lista de termos para o regex ----
  var DEF = Object.create(null);
  var TERMS = [];
  GLOSSARY.forEach(function (g) {
    g.terms.forEach(function (t) {
      if (!DEF[t.a]) { DEF[t.a] = t; TERMS.push(t.a); }
    });
  });
  // Mais longos primeiro: garante que "mPFS" vença "PFS", "PET/CT" vença "PET" etc.
  TERMS.sort(function (a, b) { return b.length - a.length; });

  function escRe(s) { return s.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&'); }
  // (^|não-alfanum) (TERMO) seguido de não-alfanum — sem lookbehind (compat. ampla).
  var RE = new RegExp('(^|[^A-Za-z0-9])(' + TERMS.map(escRe).join('|') + ')(?![A-Za-z0-9])', 'g');

  function escHtml(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  window.TheraTrials = window.TheraTrials || {};

  // Resolve a definição de uma sigla no idioma atual.
  TheraTrials.glossaryDef = function (term) {
    var d = DEF[term];
    if (!d) return null;
    return (window.getLang && window.getLang() === 'en') ? d.en : d.pt;
  };

  // Grupos resolvidos no idioma pedido — alimenta o modal de legenda.
  TheraTrials.glossaryGroups = function (lang) {
    var en = (lang || (window.getLang && window.getLang()) || 'pt-br') === 'en';
    return GLOSSARY.map(function (g) {
      return {
        id: g.id, icon: g.icon, label: en ? g.en : g.pt,
        items: g.terms.filter(function (t) { return !t.hidden; })
          .map(function (t) { return { abbr: t.a, def: en ? t.en : t.pt }; })
      };
    });
  };

  // Envolve siglas conhecidas em <abbr class="gloss-term">. Faz escape do HTML
  // ANTES de injetar — seguro para texto livre vindo do database.
  TheraTrials.annotateAbbr = function (text) {
    if (text == null || text === '') return '';
    var safe = escHtml(String(text));
    return safe.replace(RE, function (m, pre, term) {
      return pre + '<abbr class="gloss-term" tabindex="0" data-term="' + term + '">' + term + '</abbr>';
    });
  };

  // ---------- Anotação direta no DOM (conteúdo estático / gerado por innerHTML) ----------
  // Varre os nós de TEXTO sob `root`, sem tocar em tags/atributos, e envolve as
  // siglas em <abbr>. Pula elementos interativos, títulos, links e nós ligados a
  // Alpine (x-text/x-html) ou i18n (data-i18n) para não brigar com re-renders.
  var BLOCK_TAGS = {
    SCRIPT: 1, STYLE: 1, A: 1, ABBR: 1, BUTTON: 1, CODE: 1, KBD: 1, PRE: 1,
    TEXTAREA: 1, INPUT: 1, SELECT: 1, OPTION: 1, H1: 1, H2: 1, H3: 1, H4: 1,
    NAV: 1, TEMPLATE: 1, SVG: 1
  };
  function shouldSkip(el) {
    if (!el || el.nodeType !== 1) return false;
    var tag = el.tagName ? el.tagName.toUpperCase() : '';
    if (BLOCK_TAGS[tag]) return true;
    if (el.classList && el.classList.contains('gloss-term')) return true;
    if (el.hasAttribute) {
      if (el.hasAttribute('data-no-gloss')) return true;
      if (el.hasAttribute('x-text') || el.hasAttribute('x-html') || el.hasAttribute('data-i18n')) return true;
    }
    return false;
  }
  function annotateTextNode(node) {
    var s = node.nodeValue;
    if (!s || s.length < 2 || !/[A-Za-z]/.test(s)) return;
    RE.lastIndex = 0;
    var m, last = 0, frag = null;
    while ((m = RE.exec(s))) {
      var term = m[2];
      var termStart = m.index + m[1].length;
      if (!frag) frag = document.createDocumentFragment();
      if (termStart > last) frag.appendChild(document.createTextNode(s.slice(last, termStart)));
      var ab = document.createElement('abbr');
      ab.className = 'gloss-term';
      ab.setAttribute('tabindex', '0');
      ab.setAttribute('data-term', term);
      ab.textContent = term;
      frag.appendChild(ab);
      last = RE.lastIndex;
    }
    if (frag) {
      if (last < s.length) frag.appendChild(document.createTextNode(s.slice(last)));
      node.parentNode.replaceChild(frag, node);
    }
  }
  function walk(node) {
    var child = node.firstChild;
    while (child) {
      var next = child.nextSibling;
      if (child.nodeType === 3) annotateTextNode(child);
      else if (child.nodeType === 1 && !shouldSkip(child)) walk(child);
      child = next;
    }
  }
  TheraTrials.annotateDOM = function (root) {
    if (typeof root === 'string') root = document.querySelector(root);
    if (root) walk(root);
  };

  // ---------- Modal de legenda reutilizável (JS puro; serve páginas Alpine e vanilla) ----------
  TheraTrials.openGlossaryModal = function () {
    var en = !!(window.getLang && window.getLang() === 'en');
    var groups = TheraTrials.glossaryGroups(window.getLang ? window.getLang() : 'pt-br');
    var o = document.getElementById('tgloss-overlay');
    if (!o) {
      o = document.createElement('div');
      o.id = 'tgloss-overlay';
      o.className = 'tgloss-overlay';
      document.body.appendChild(o);
      o.addEventListener('click', function (e) { if (e.target === o) TheraTrials.closeGlossaryModal(); });
    }
    var html = '<div class="tgloss-modal" role="dialog" aria-modal="true" aria-label="'
      + (en ? 'Glossary' : 'Legenda de siglas') + '">'
      + '<button class="tgloss-close" aria-label="' + (en ? 'Close' : 'Fechar') + '">&times;</button>'
      + '<div class="tgloss-head"><h2>' + (en ? 'Abbreviation &amp; metric glossary' : 'Legenda de siglas e métricas') + '</h2>'
      + '<p>' + (en
        ? 'Hover or tap an underlined abbreviation in the text to see its meaning. Educational definitions; always check the primary publication.'
        : 'Passe o mouse ou toque numa sigla sublinhada no texto para ver o significado. Definições didáticas; sempre confira a publicação primária.')
      + '</p></div><div class="tgloss-body">';
    groups.forEach(function (g) {
      html += '<div class="tgloss-group"><h3>' + escHtml(g.label) + '</h3><dl class="tgloss-grid">';
      g.items.forEach(function (it) {
        html += '<div class="tgloss-item"><dt>' + escHtml(it.abbr) + '</dt><dd>' + escHtml(it.def) + '</dd></div>';
      });
      html += '</dl></div>';
    });
    html += '</div></div>';
    o.innerHTML = html;
    o.querySelector('.tgloss-close').addEventListener('click', TheraTrials.closeGlossaryModal);
    o.classList.add('on');
    document.body.style.overflow = 'hidden';
  };
  TheraTrials.closeGlossaryModal = function () {
    var o = document.getElementById('tgloss-overlay');
    if (o) { o.classList.remove('on'); document.body.style.overflow = ''; }
  };

  // ---------- Controlador de tooltip (hover desktop + toque mobile) ----------
  document.addEventListener('DOMContentLoaded', function () {
    var tip = null, current = null;

    function ensureTip() {
      if (tip) return tip;
      tip = document.createElement('div');
      tip.className = 'gloss-tip';
      tip.setAttribute('role', 'tooltip');
      document.body.appendChild(tip);
      return tip;
    }

    function show(el) {
      var term = el.getAttribute('data-term');
      var def = TheraTrials.glossaryDef(term);
      if (!def) return;
      var t = ensureTip();
      t.innerHTML = '<strong>' + escHtml(term) + '</strong> ' + escHtml(def);
      t.classList.add('on');
      current = el;
      position(el, t);
    }

    function position(el, t) {
      var r = el.getBoundingClientRect();
      t.style.maxWidth = Math.min(300, window.innerWidth - 24) + 'px';
      // medir
      t.style.left = '0px'; t.style.top = '0px';
      var tw = t.offsetWidth, th = t.offsetHeight;
      var left = r.left + r.width / 2 - tw / 2;
      left = Math.max(12, Math.min(left, window.innerWidth - tw - 12));
      var top = r.top - th - 8;
      var below = false;
      if (top < 8) { top = r.bottom + 8; below = true; }
      t.classList.toggle('below', below);
      t.style.left = left + 'px';
      t.style.top = top + 'px';
    }

    function hide() {
      if (tip) tip.classList.remove('on');
      current = null;
    }

    // Hover (dispositivos com mouse)
    document.addEventListener('mouseover', function (e) {
      var el = e.target.closest && e.target.closest('.gloss-term');
      if (el) show(el);
    });
    document.addEventListener('mouseout', function (e) {
      var el = e.target.closest && e.target.closest('.gloss-term');
      if (el && el === current) hide();
    });

    // Foco por teclado
    document.addEventListener('focusin', function (e) {
      var el = e.target.closest && e.target.closest('.gloss-term');
      if (el) show(el);
    });
    document.addEventListener('focusout', function (e) {
      var el = e.target.closest && e.target.closest('.gloss-term');
      if (el && el === current) hide();
    });

    // Toque/clique: captura ANTES do @click do card (impede abrir o modal do estudo)
    document.addEventListener('click', function (e) {
      var el = e.target.closest && e.target.closest('.gloss-term');
      if (el) {
        e.stopPropagation();
        e.preventDefault();
        if (current === el) { hide(); } else { show(el); }
        return;
      }
      hide();
    }, true);

    window.addEventListener('scroll', hide, true);
    window.addEventListener('resize', hide);
    window.addEventListener('langchange', hide);
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { hide(); TheraTrials.closeGlossaryModal(); }
    });

    // Auto-anota containers marcados com data-gloss-auto (conteúdo estático)
    var autos = document.querySelectorAll('[data-gloss-auto]');
    for (var i = 0; i < autos.length; i++) TheraTrials.annotateDOM(autos[i]);
  });
})();
