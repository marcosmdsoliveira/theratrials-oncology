/* ============================================================
   Proposta — Portal de Ensaios & Trial Matcher (PROTÓTIPO)
   Dados reais extraídos de listas de "estudos abertos" de 3 centros:
   Personal Oncologia (BH), Oncominas (MG), Oncoclínicas (rede nacional).
   ⚠ Dados ILUSTRATIVOS para demonstração. Contatos marcados "ilustrativo"
   substituem dados reais; atribuição de patrocinador é best-effort.
   ============================================================ */

const UF_CIDADE = {
  MG: 'Belo Horizonte', RJ: 'Rio de Janeiro', SP: 'São Paulo',
  BH: 'Belo Horizonte', BSB: 'Brasília', REC: 'Recife',
  SSA: 'Salvador', SUL_MG: 'Sul de Minas'
};

const CENTROS = {
  oncoclinicas: {
    id: 'oncoclinicas', curto: 'Oncoclínicas',
    nome: 'Oncoclínicas — Pesquisa Clínica (rede nacional)',
    regiao: 'Rede nacional', ufs: ['BH', 'BSB', 'REC', 'RJ', 'SSA', 'SP'],
    cobertura: 'Belo Horizonte · Brasília · Recife · Rio de Janeiro · Salvador · São Paulo',
    site: 'grupooncoclinicas.com', tel: 'Central de recrutamento (ilustrativo)',
    lideres: 'Dr. Fábio Franke (líder nacional de pesquisa) · Dr. Gustavo Gitelman (coord. nacional de recrutamento)',
    verificado: true, destaque: true, cor: '#A855F7'
  },
  personal: {
    id: 'personal', curto: 'Personal Oncologia',
    nome: 'Personal Oncologia — Centro de Pesquisa Clínica',
    regiao: 'Belo Horizonte/MG', ufs: ['MG'],
    cobertura: 'Belo Horizonte/MG · Rua Padre Rolim, 120 — Sta. Efigênia',
    site: 'personaloncologia.com.br', tel: '(31) 3241-3832',
    lideres: 'Dr. André Murad · Dra. Flávia Amaral',
    verificado: true, cor: '#FF8400'
  },
  oncominas: {
    id: 'oncominas', curto: 'Oncominas',
    nome: 'Oncominas — Pesquisa Clínica',
    regiao: 'Sul de Minas/MG', ufs: ['SUL_MG'],
    cobertura: 'Sul de Minas Gerais',
    site: 'oncominas.med.br', tel: '(35) 3429-7035',
    lideres: 'Equipe de Pesquisa Clínica Oncominas',
    verificado: true, cor: '#0EA5B7'
  }
};

const TUMORES = {
  pulmao: 'Pulmão', mama: 'Mama', estomago: 'Estômago / JGE',
  colorretal: 'Colorretal', prostata: 'Próstata', ovario: 'Ovário',
  vias_biliares: 'Vias biliares', hnscc: 'Cabeça e Pescoço', hemato: 'Hematologia'
};

/* Cada ensaio:
   id, nome, fase, tumor, cenario, biomarcadores[], drogas, comparador,
   nct, centro, ufs[], pis[{uf,nome}], contato, status, testeFornecido,
   patrocinador, destaque, inclusao[], exclusao[] */
const ENSAIOS = [
  // ---------- DESTAQUE (slot patrocinado, claramente rotulado) ----------
  { id:'sunray-02', nome:'SUNRAY-02', fase:'Fase 3', tumor:'pulmao',
    cenario:'NSCLC KRAS G12C — adjuvante (EII/IIIB ressecado) ou consolidação (EIII irressecável pós QT+RxT)',
    biomarcadores:['KRAS G12C'], drogas:'Olomorasibe + pembrolizumabe (adjuvante) / + durvalumabe (consolidação)',
    comparador:'Placebo + pembrolizumabe / durvalumabe', nct:'NCT06119581',
    centro:'oncoclinicas', ufs:['RJ','SP','BH'],
    pis:[{uf:'RJ',nome:'Dra. Tatiane Montella'},{uf:'SP',nome:'Dr. William William'},{uf:'BH',nome:'Dra. Flávia Amaral'}],
    contato:'(11) 93756-4589 (ilustrativo)', status:'Recrutando', testeFornecido:true, patrocinador:'Eli Lilly',
    destaque:true,
    inclusao:['NSCLC com KRAS G12C confirmado (teste central fornecido)','EII–IIIB ressecado ou EIII irressecável sem progressão pós QT+RxT','ECOG 0–1'],
    exclusao:['Subtipos escamosos ou de pequenas células','Mutações driver ALK, EGFR ou ROS1','Doença ativa em SNC'] },

  // ---------- PULMÃO ----------
  { id:'sunray-01', nome:'SUNRAY-01', fase:'Fase 3', tumor:'pulmao',
    cenario:'NSCLC KRAS G12C — 1ª linha avançada (TPS ≥ 50%)',
    biomarcadores:['KRAS G12C','PD-L1 ≥ 50%'], drogas:'Pembrolizumabe + olomorasibe (LY3537982)',
    comparador:'Pembrolizumabe + placebo', nct:'', centro:'oncoclinicas', ufs:['RJ','SP'],
    pis:[{uf:'RJ',nome:'Dra. Tatiane Montella'},{uf:'SP',nome:'Dr. William William'}],
    contato:'(11) 93756-4589 (ilustrativo)', status:'Recrutando', testeFornecido:true, patrocinador:'Eli Lilly',
    inclusao:['EIIIb, EIIIc ou IV','KRAS G12C positivo','Doença de SNC controlada permitida'],
    exclusao:['Doença leptomeníngea','Outras mutações driver'] },

  { id:'codebreak-202', nome:'CodeBreaK 202', fase:'Fase 3', tumor:'pulmao',
    cenario:'NSCLC KRAS G12C & TPS < 1% — 1ª linha avançada',
    biomarcadores:['KRAS G12C','PD-L1 < 1%'], drogas:'Platina + sotorasibe',
    comparador:'Platina + pembrolizumabe', nct:'', centro:'oncoclinicas', ufs:['BSB','RJ','SSA'],
    pis:[{uf:'RJ',nome:'Dra. Tatiane Montella'},{uf:'SSA',nome:'Dr. Filipe Visani'},{uf:'BSB',nome:'Dr. Igor Morbeck'}],
    contato:'(11) 93756-4589 (ilustrativo)', status:'Recrutando', testeFornecido:true, patrocinador:'Amgen',
    inclusao:['KRAS G12C positivo','IHQ negativa para PD-L1','Doença de SNC assintomática permitida'],
    exclusao:['Histologia > 50% escamosa','Mutações EGFR ou ALK'] },

  { id:'tropion-lung17', nome:'TROPION-Lung17', fase:'Fase 3', tumor:'pulmao',
    cenario:'NSCLC sem driver — 2ª linha avançada, TROP2+',
    biomarcadores:['TROP2'], drogas:'Datopotamabe deruxtecana (Dato-DXd)', comparador:'Quimioterapia',
    nct:'', centro:'oncoclinicas', ufs:['RJ','SSA'], pis:[{uf:'RJ',nome:'Dra. Tatiane Montella'}],
    contato:'(11) 93756-4589 (ilustrativo)', status:'Recrutando', testeFornecido:false, patrocinador:'AstraZeneca / Daiichi Sankyo',
    inclusao:['NSCLC avançado sem mutação driver','Progressão após 1ª linha'], exclusao:['DPI/pneumonite prévia significativa'] },

  { id:'soho-02', nome:'SOHO-02', fase:'Fase 3', tumor:'pulmao',
    cenario:'NSCLC HER2 mutado (TKD) — 1ª linha avançada',
    biomarcadores:['HER2 mutado (TKD)'], drogas:'BAY 2927088 + doblet (platina + pemetrexede + pembrolizumabe)',
    comparador:'Doblet de platina', nct:'', centro:'oncoclinicas', ufs:['SP'],
    pis:[{uf:'SP',nome:'Dr. Pedro Aguiar'}], contato:'(11) 93756-4589 (ilustrativo)',
    status:'Recrutando', testeFornecido:true, patrocinador:'Bayer',
    inclusao:['Histologia não escamosa, sem tratamento avançado prévio','Mutação de HER2 na região do TKD','Doença de SNC tratada e estável permitida'],
    exclusao:['Terapia anti-HER2 prévia','Outros drivers'] },

  { id:'destiny-lung06', nome:'DESTINY-Lung06', fase:'Fase 3', tumor:'pulmao',
    cenario:'NSCLC HER2 superexpresso & TPS < 50%',
    biomarcadores:['HER2 superexpresso (IHC)'], drogas:'Trastuzumabe deruxtecana (T-DXd)', comparador:'Padrão',
    nct:'', centro:'oncoclinicas', ufs:['RJ'], pis:[{uf:'RJ',nome:'Dra. Tatiane Montella'}],
    contato:'(11) 93756-4589 (ilustrativo)', status:'Recrutando', testeFornecido:false, patrocinador:'AstraZeneca / Daiichi Sankyo',
    inclusao:['NSCLC com superexpressão de HER2','PD-L1 TPS < 50%'], exclusao:['DPI prévia'] },

  { id:'evoke-sclc-04', nome:'EVOKE-SCLC-04', fase:'Fase 2/3', tumor:'pulmao',
    cenario:'SCLC (pequenas células) — 2ª linha, pós-progressão à platina',
    biomarcadores:[], drogas:'Sacituzumabe govitecana', comparador:'Quimioterapia',
    nct:'', centro:'oncoclinicas', ufs:['BH'], pis:[{uf:'BH',nome:'Dra. Marina Xavier Reis'}],
    contato:'(11) 93756-4589 (ilustrativo)', status:'Recrutando', testeFornecido:false, patrocinador:'Gilead',
    inclusao:['SCLC com progressão pós-platina'], exclusao:['SNC sintomático não tratado'] },

  // ---------- CABEÇA E PESCOÇO ----------
  { id:'mcla-03', nome:'MCLA-03', fase:'Fase 3', tumor:'hnscc',
    cenario:'CEC recorrente/avançado — 1ª linha, CPS ≥ 1',
    biomarcadores:['PD-L1 CPS ≥ 1'], drogas:'Petosemtamabe + pembrolizumabe', comparador:'Pembrolizumabe',
    nct:'', centro:'oncoclinicas', ufs:['RJ','SP','BH'],
    pis:[{uf:'RJ',nome:'Dra. Marina Xavier'},{uf:'SP',nome:'Dr. William William'},{uf:'BH',nome:'Dra. Nicole Rossi'}],
    contato:'(11) 93756-4589 (ilustrativo)', status:'Recrutando', testeFornecido:true, patrocinador:'Merus',
    inclusao:['CPS ≥ 1 em avaliação central','Nenhuma terapia sistêmica no cenário avançado/recorrente','Fração de ejeção normal'],
    exclusao:['Doenças autoimunes','Sítio primário nasofaringe ou sinonasal'] },

  { id:'evolve-hnscc', nome:'eVOLVE-HNSCC', fase:'Fase 3', tumor:'hnscc',
    cenario:'CEC localmente avançado — pós QT + RxT (sem progressão)',
    biomarcadores:[], drogas:'Volrustomig', comparador:'Observação',
    nct:'', centro:'oncoclinicas', ufs:['SP'], pis:[{uf:'SP',nome:'Dr. William William'}],
    contato:'(11) 93756-4589 (ilustrativo)', status:'Recrutando', testeFornecido:false, patrocinador:'AstraZeneca',
    inclusao:['EC III / IVA ou IVB (AJCC 8ª)','Faringe, laringe, cavidade oral e orofaringe','Sem progressão pós QT+RxT'],
    exclusao:['Nasofaringe e glândula salivar','Pacientes que receberam apenas RxT'] },

  { id:'bnt113-01', nome:'BNT113-01', fase:'Fase 2', tumor:'hnscc',
    cenario:'CEC recorrente/avançado — 1ª linha, HPV16+ & CPS ≥ 1',
    biomarcadores:['HPV16+','PD-L1 CPS ≥ 1'], drogas:'BNT113 (vacina terapêutica de mRNA anti-HPV16) + pembrolizumabe',
    comparador:'Pembrolizumabe', nct:'', centro:'oncoclinicas', ufs:['BH','SSA'],
    pis:[{uf:'BH',nome:'Dra. Nicole Rossi'},{uf:'SSA',nome:'Dra. Luciana Landeiro'}],
    contato:'(11) 93756-4589 (ilustrativo)', status:'Recrutando', testeFornecido:true, patrocinador:'BioNTech',
    inclusao:['CEC HPV16-positivo confirmado','PD-L1 CPS ≥ 1','1ª linha no cenário avançado'], exclusao:['Doença autoimune ativa'] },

  // ---------- MAMA ----------
  { id:'cherry-pick', nome:'CHERRY-PICK', fase:'Fase 2', tumor:'mama',
    cenario:'HER2+ neoadjuvância — RE < 10% / RP < 1%',
    biomarcadores:['HER2 3+','RE < 10%'], drogas:'PHESGO (pertuzumabe + trastuzumabe SC)', comparador:'—',
    nct:'', centro:'oncoclinicas', ufs:['BH','SP','SSA'],
    pis:[{uf:'BH',nome:'Dra. Nicole Rossi'},{uf:'SP',nome:'Dra. Andrea Moraes Borges'},{uf:'SSA',nome:'Dra. Luciana Landeiro'}],
    contato:'(11) 93756-4589 (ilustrativo)', status:'Recrutando', testeFornecido:false, patrocinador:'Roche',
    inclusao:['Doença inicial T1c–T2, N0–N1','HER2 3+ por IHQ & RE < 10% & RP < 1%','Sem tratamento sistêmico prévio','Lesão ≥ 10 mm'], exclusao:['Doença metastática'] },

  { id:'empowher-303', nome:'EmpowHER-303', fase:'Fase 3', tumor:'mama',
    cenario:'HER2+ — 2ª/3ª linha avançada, após progressão ao T-DXd',
    biomarcadores:['HER2+'], drogas:'Zanidatamabe + quimioterapia', comparador:'Trastuzumabe + quimioterapia',
    nct:'', centro:'oncoclinicas', ufs:['SSA'], pis:[{uf:'SSA',nome:'Dra. Luciana Landeiro'}],
    contato:'(11) 93756-4589 (ilustrativo)', status:'Recrutando', testeFornecido:false, patrocinador:'Jazz / Zymeworks',
    inclusao:['Mama HER2+ avançada','Progressão após trastuzumabe deruxtecana'], exclusao:['ICC sintomática'] },

  { id:'rly-2608', nome:'RLY-2608', fase:'Fase 1/2', tumor:'mama',
    cenario:'Luminal (HR+) — 2ª linha, após inibidor de ciclina; PIK3CA mutado',
    biomarcadores:['PIK3CA mutado','HR+'], drogas:'RLY-2608 (inibidor de PI3Kα mutante-seletivo) + fulvestranto',
    comparador:'—', nct:'', centro:'oncoclinicas', ufs:['BH','RJ','SSA'], pis:[{uf:'BH',nome:'Dra. Marina Xavier Reis'}],
    contato:'(11) 93756-4589 (ilustrativo)', status:'Recrutando', testeFornecido:true, patrocinador:'Relay Therapeutics',
    inclusao:['Mama HR+/HER2− avançada','PIK3CA mutado','Progressão após inibidor de CDK4/6'], exclusao:['Diabetes não controlado'] },

  { id:'ascent-05', nome:'ASCENT-05', fase:'Fase 3', tumor:'mama',
    cenario:'TNBC — doença residual após neoadjuvância + cirurgia',
    biomarcadores:['TNBC'], drogas:'Sacituzumabe govitecana + pembrolizumabe', comparador:'Pembrolizumabe ± capecitabina',
    nct:'', centro:'oncoclinicas', ufs:['SSA'], pis:[{uf:'SSA',nome:'Dra. Luciana Landeiro'}],
    contato:'(11) 93756-4589 (ilustrativo)', status:'Recrutando', testeFornecido:false, patrocinador:'Gilead / MSD',
    inclusao:['TNBC com doença residual pós-neoadjuvância e cirurgia'], exclusao:['Metástase a distância'] },

  { id:'cambria-2', nome:'CAMBRIA-2', fase:'Fase 3', tumor:'mama',
    cenario:'Mama precoce RE+/HER2− — adjuvante, risco intermediário/alto',
    biomarcadores:['RE > 10%','HER2−'], drogas:'Camizestranto (± agonista LHRH)', comparador:'Terapia endócrina padrão por 5 anos',
    nct:'', centro:'oncominas', ufs:['SUL_MG'], pis:[{uf:'SUL_MG',nome:'Equipe Oncominas'}],
    contato:'(35) 3429-7035', status:'Recrutando', testeFornecido:false, patrocinador:'AstraZeneca',
    inclusao:['Câncer de mama invasivo ressecado, estádio inicial, RE > 10% / HER2−','Randomização até 12 meses após cirurgia','Uso de abemaciclibe permitido'],
    exclusao:['Doença metastática'] },

  { id:'cambria-1', nome:'CAMBRIA-1', fase:'Fase 3', tumor:'mama',
    cenario:'Mama precoce RE+/HER2− — após ≥ 2 anos de terapia endócrina adjuvante',
    biomarcadores:['RE > 10%','HER2−'], drogas:'Camizestranto (± agonista LHRH) por 5 anos', comparador:'Terapia endócrina padrão por 5 anos',
    nct:'', centro:'oncominas', ufs:['SUL_MG'], pis:[{uf:'SUL_MG',nome:'Equipe Oncominas'}],
    contato:'(35) 3429-7035', status:'Recrutando', testeFornecido:false, patrocinador:'AstraZeneca',
    inclusao:['Câncer de mama invasivo RE > 10% / HER2−','Completou 2–5 anos de TE adjuvante (± CDK4/6 e iPARP)','Critérios de risco (T4, N≥2, ou T1–5 com G3/Ki67≥20%/Oncotype alto)'],
    exclusao:['Doença metastática'] },

  // ---------- PRÓSTATA / OVÁRIO / TGI / VIAS BILIARES / HEMATO ----------
  { id:'evopar-pr02', nome:'EvoPAR-PR02', fase:'Fase 3', tumor:'prostata',
    cenario:'Próstata — doença localizada de alto risco',
    biomarcadores:['HRR (sub-coorte)'], drogas:'Saruparibe (inibidor de PARP1-seletivo) + terapia padrão', comparador:'Terapia padrão',
    nct:'', centro:'oncoclinicas', ufs:['RJ'], pis:[{uf:'RJ',nome:'Dra. Tatiane Montella'}],
    contato:'(11) 93756-4589 (ilustrativo)', status:'Recrutando', testeFornecido:true, patrocinador:'AstraZeneca',
    inclusao:['Próstata localizada de alto risco'], exclusao:['Doença metastática'] },

  { id:'destiny-ovarian01', nome:'DESTINY-Ovarian01', fase:'Fase 2/3', tumor:'ovario',
    cenario:'Ovário — manutenção em 1ª linha; HER2 (IHC 1/2/3+)',
    biomarcadores:['HER2 IHC 1/2/3+'], drogas:'Trastuzumabe deruxtecana (T-DXd)', comparador:'Padrão de manutenção',
    nct:'', centro:'oncoclinicas', ufs:['BH'], pis:[{uf:'BH',nome:'Dra. Marina Xavier Reis'}],
    contato:'(11) 93756-4589 (ilustrativo)', status:'Recrutando', testeFornecido:true, patrocinador:'AstraZeneca / Daiichi Sankyo',
    inclusao:['Ovário epitelial, expressão de HER2 (IHC 1/2/3+)','Resposta após 1ª linha'], exclusao:['DPI prévia'] },

  { id:'artemide-gastric01', nome:'ARTEMIDE-Gastric01', fase:'Fase 3', tumor:'estomago',
    cenario:'Gástrico/JGE — 1ª linha, HER2+ com CPS ≥ 1',
    biomarcadores:['HER2+','PD-L1 CPS ≥ 1'], drogas:'Rilvegostomig + trastuzumabe + quimioterapia', comparador:'Trastuzumabe + quimioterapia',
    nct:'', centro:'oncoclinicas', ufs:['SSA'], pis:[{uf:'SSA',nome:'Dr. Filipe Visani'}],
    contato:'(11) 93756-4589 (ilustrativo)', status:'Recrutando', testeFornecido:true, patrocinador:'AstraZeneca',
    inclusao:['Adenocarcinoma gástrico/JGE HER2+','PD-L1 CPS ≥ 1','1ª linha'], exclusao:['Doença de SNC ativa'] },

  { id:'codebreak-301', nome:'CodeBreaK 301', fase:'Fase 3', tumor:'colorretal',
    cenario:'mCRC — 1ª linha, KRAS G12C',
    biomarcadores:['KRAS G12C'], drogas:'Sotorasibe + panitumumabe + FOLFIRI', comparador:'FOLFIRI ± bevacizumabe',
    nct:'', centro:'oncoclinicas', ufs:['RJ','BH'], pis:[{uf:'RJ',nome:'Dra. Tatiane Montella'}],
    contato:'(11) 93756-4589 (ilustrativo)', status:'Recrutando', testeFornecido:true, patrocinador:'Amgen',
    inclusao:['mCRC com KRAS G12C','Sem tratamento prévio para doença metastática'], exclusao:['Outras mutações RAS'] },

  { id:'s095031-210', nome:'S095031-210', fase:'Fase 2', tumor:'vias_biliares',
    cenario:'Vias biliares — 1ª linha, IDH1 mutado',
    biomarcadores:['IDH1 mutado'], drogas:'Inibidor de IDH1 (programa Servier) + quimioterapia', comparador:'Quimioterapia',
    nct:'', centro:'oncoclinicas', ufs:['BH'], pis:[{uf:'BH',nome:'Dra. Marina Xavier Reis'}],
    contato:'(11) 93756-4589 (ilustrativo)', status:'Recrutando', testeFornecido:true, patrocinador:'Servier',
    inclusao:['Colangiocarcinoma com IDH1 mutado','1ª linha'], exclusao:['—'] },

  { id:'bgb-16673-302', nome:'BGB-16673-302', fase:'Fase 3', tumor:'hemato',
    cenario:'Leucemia linfocítica crônica — após progressão a inibidores de BTK e BCL2',
    biomarcadores:['LLC'], drogas:'BGB-16673 (degradador de BTK / CDAC)', comparador:'Escolha do investigador',
    nct:'', centro:'oncoclinicas', ufs:['RJ'], pis:[{uf:'RJ',nome:'Dra. Tatiane Montella'}],
    contato:'(11) 93756-4589 (ilustrativo)', status:'Recrutando', testeFornecido:false, patrocinador:'BeiGene',
    inclusao:['LLC com progressão pós-BTKi e BCL2i'], exclusao:['Transformação de Richter'] },

  // ---------- PERSONAL ONCOLOGIA (BH) — NCTs reais ----------
  { id:'hlx22-gc-301', nome:'HLX22-GC-301', fase:'Fase 3', tumor:'estomago',
    cenario:'Gástrico/JGE HER2-positivo — 1ª linha',
    biomarcadores:['HER2+ (IHC 3+ ou 2+/ISH+)'], drogas:'HLX22 (anti-HER2) + trastuzumabe + XELOX ± pembrolizumabe',
    comparador:'Trastuzumabe + XELOX ± pembrolizumabe', nct:'NCT06532006', centro:'personal', ufs:['MG'],
    pis:[{uf:'MG',nome:'Dr. André Murad'}], contato:'(31) 99984-3832 · personaligor1@gmail.com',
    status:'Recrutando', testeFornecido:true, patrocinador:'Henlius',
    inclusao:['Adenocarcinoma gástrico/JGE HER2+ confirmado','Localmente avançado irressecável ou metastático','Sem tratamento prévio'],
    exclusao:['Outros tumores malignos nos 2 anos anteriores'] },

  { id:'lucerna', nome:'LUCERNA (8951-CL-0305)', fase:'Fase 3', tumor:'estomago',
    cenario:'Gástrico/JGE HER2− — 1ª linha; CLDN18.2+ e PD-L1+',
    biomarcadores:['CLDN18.2 ≥ 75%','PD-L1+','HER2−'], drogas:'Zolbetuximabe + pembrolizumabe + quimioterapia (mFOLFOX6/CAPOX)',
    comparador:'Placebo + pembrolizumabe + quimioterapia', nct:'NCT06901531', centro:'personal', ufs:['MG'],
    pis:[{uf:'MG',nome:'Dr. André Murad'}], contato:'(31) 3241-3832 · personaligor1@gmail.com',
    status:'Recrutando', testeFornecido:true, patrocinador:'Astellas',
    inclusao:['Adenocarcinoma gástrico/JGE HER2-negativo','Claudina 18.2 em ≥ 75% das células','PD-L1 positivo'],
    exclusao:['Reação grave prévia a anticorpos monoclonais'] },

  { id:'amivantamab-sc', nome:'Amivantamabe SC (61186372NSC2002)', fase:'Fase 2', tumor:'pulmao',
    cenario:'NSCLC EGFR (exon19del/L858R) — coortes (switch IV→SC; 2ª linha pós amivantamabe+lazertinibe)',
    biomarcadores:['EGFR exon19del/L858R'], drogas:'Amivantamabe SC ± lazertinibe / quimioterapia', comparador:'—',
    nct:'NCT05498428', centro:'personal', ufs:['MG'], pis:[{uf:'MG',nome:'Dra. Flávia Amaral'}],
    contato:'(31) 98804-6940', status:'Recrutando', testeFornecido:false, patrocinador:'Janssen',
    inclusao:['NSCLC EGFR exon19del/L858R confirmado','Localmente avançado/metastático'], exclusao:['—'] },

  { id:'benito', nome:'BENITO', fase:'Fase 3', tumor:'pulmao',
    cenario:'NSCLC não-escamoso IV — 1ª linha (biossimilar de pembrolizumabe)',
    biomarcadores:['sem EGFR/ALK'], drogas:'MB12 (biossimilar proposto de pembrolizumabe) + pemetrexede + platina',
    comparador:'Keytruda + pemetrexede + platina', nct:'NCT06687369', centro:'personal', ufs:['MG'],
    pis:[{uf:'MG',nome:'Dr. André Murad'}], contato:'(31) 99984-3832', status:'Recrutando', testeFornecido:false, patrocinador:'mAbxience',
    inclusao:['CPNPC não escamoso estágio IV','Sem mutação sensibilizante de EGFR ou translocação de ALK','Sem tratamento sistêmico prévio'],
    exclusao:['Histologia predominantemente escamosa'] },

  // ---------- ONCOMINAS (Sul de MG) ----------
  { id:'newpower', nome:'NEWPOWER', fase:'Fase 2', tumor:'pulmao',
    cenario:'NSCLC ressecável EII–IIIB(N2) — perioperatório',
    biomarcadores:[], drogas:'Cemiplimabe + quimioterapia ± outros tratamentos oncológicos', comparador:'Cemiplimabe + quimioterapia',
    nct:'', centro:'oncominas', ufs:['SUL_MG'], pis:[{uf:'SUL_MG',nome:'Equipe Oncominas'}],
    contato:'(35) 3429-7035', status:'Recrutando', testeFornecido:false, patrocinador:'Regeneron',
    inclusao:['CPNPC estágio II–IIIB(N2) ressecável com intenção curativa','Doença mensurável (RECIST 1.1)','ECOG 0–1'],
    exclusao:['Doença metastática a distância','Pneumonite intersticial ativa'] }
];

/* Métricas-mock para o Painel do Parceiro (demonstração) */
const PAINEL_MOCK = {
  periodo: 'últimos 30 dias',
  visualizacoes: 1284, encaminhamentos: 37, taxaConversao: 2.9,
  porEnsaio: [
    { ensaio:'SUNRAY-02', views:312, leads:11 },
    { ensaio:'CodeBreaK 202', views:188, leads:6 },
    { ensaio:'CHERRY-PICK', views:151, leads:5 },
    { ensaio:'TROPION-Lung17', views:134, leads:4 },
    { ensaio:'RLY-2608', views:121, leads:4 },
    { ensaio:'MCLA-03', views:98, leads:3 }
  ],
  porUF: [ {uf:'SP',v:34}, {uf:'RJ',v:23}, {uf:'MG',v:18}, {uf:'BA',v:9}, {uf:'DF',v:7}, {uf:'Outros',v:9} ]
};
