#!/usr/bin/env python3
"""
write_gl_batch_c.py
Appends 6 deeply expanded guideline objects to guidelines-data.js:
  - 3 x Metastases osseas (bone-snmmi-eanm-palliative-2023, bone-eanm-beta-2018, bone-acr-ra223-2020)
  - 2 x MIBG (mibg-eanm-procedure-2008, mibg-dosimetry-sop-2020)
  - 1 x RSO (rso-eanm-2022)
"""

import os

target = r"C:\Users\marco\Desktop\TheraTrials Oncology\site\assets\js\guidelines-data.js"

content = r'''
  // ===============================================
  //  5. Metastases osseas
  // ===============================================
  {
    id: "bone-snmmi-eanm-palliative-2023",
    title: "SNMMI Procedure Standard/EANM Practice Guideline for Palliative Nuclear Medicine Therapies of Bone Metastases",
    year: "2023",
    society: "SNMMI · EANM",
    type: "Procedure standard / Practice guideline",
    badges: ["essential"],
    category: "osseas",
    categoryName: "Metástases ósseas",
    categoryColor: "#94A3B8",
    scope: "Guideline procedimental consolidado e multissociedade que abrange todas as modalidades de terapia paliativa com radionuclideos direcionada a metastases osseas, incluindo o alfa-emissor 223Ra-Dicloreto e os beta-emissores classicos 89Sr e 153Sm-EDTMP. O documento integra evidencias do estudo ALSYMPCA, que demonstrou beneficio de sobrevida global com 223Ra em mCRPC, e os dados de alerta do ERA 223, que contraindicaram a combinacao de 223Ra com abiraterona/prednisona por aumento de fraturas e mortalidade. Contextualiza o papel de cada agente no cenario atual de mCRPC, onde terapias como 177Lu-PSMA-617 expandiram as opcoes de tratamento. Aborda o mecanismo de acao distinto dos alfa-emissores (alto LET, curto alcance, dano irreparavel ao DNA) versus beta-emissores (menor LET, maior alcance, paliacao da dor). Posiciona a terapia com radionuclideos osseos como complementar a radioterapia externa e a terapia analgesica sistemica, especialmente em doenca difusa. O guideline serve como referencia para selecao de pacientes, protocolos de administracao e monitoramento de toxicidade em centros de medicina nuclear.",
    indications: [
      "mCRPC com metastases osseas sintomaticas e cintilografia ossea demonstrando padrao osteoblastico multifocal, sem metastase visceral conhecida (criterio ALSYMPCA para 223Ra)",
      "Pacientes com mCRPC pos-docetaxel ou nao candidatos/que recusam quimioterapia citotoxica, com ECOG 0-2",
      "Hemoglobina >= 10 g/dL, plaquetas >= 100.000/mm3, neutrofilos >= 1.500/mm3 para elegibilidade a 223Ra",
      "Dor ossea refrataria a analgesicos convencionais (escada da OMS) em metastases osteoblasticas de cancer de prostata, mama ou pulmao (89Sr e 153Sm)",
      "Doenca ossea difusa onde radioterapia externa de campo estendido nao e viavel ou pratica",
      "Lesoes osteoblasticas com captacao confirmada em cintilografia ossea com 99mTc-MDP/HDP como pre-requisito para todos os agentes",
      "ALP serica elevada como marcador de atividade osteoblastica, especialmente para monitoramento de resposta ao 223Ra",
      "Complemento a radioterapia externa localizada em pacientes com doenca ossea disseminada e dor multifocal",
      "Ausencia de compressao medular iminente (contraindicacao relativa — requer avaliacao neurocirurgica/RT de urgencia primeiro)",
      "Funcao renal preservada (CrCl >= 30 mL/min) para todos os agentes; sem insuficiencia hepatica grave"
    ],
    keyPoints: [
      "223Ra-Dicloreto (Xofigo): 55 kBq/kg de peso corporal IV a cada 4 semanas, por 6 ciclos; unico agente com beneficio de sobrevida global demonstrado em estudo fase III (ALSYMPCA: mediana OS 14,9 vs 11,3 meses; HR 0,70)",
      "223Ra e um alfa-emissor com alcance de <100 micrometros no tecido osseo, gerando dano irreparavel de dupla fita de DNA nas celulas tumorais adjacentes a superficie ossea remodelada",
      "ERA 223: combinacao de 223Ra com abiraterona/prednisona resultou em aumento de fraturas e tendencia a maior mortalidade — esta combinacao e CONTRAINDICADA; dados observacionais sugerem seguranca com enzalutamida",
      "89Sr-Cloreto (Metastron): 148 MBq (4 mCi) ou 1,5-2,2 MBq/kg IV em dose unica; meia-vida fisica de 50,5 dias; beta-emissor puro (Emax 1,46 MeV); resposta paliativa em 60-80% dos pacientes em 2-4 semanas",
      "153Sm-EDTMP (Quadramet): 37 MBq/kg IV em dose unica; meia-vida de 1,9 dias; beta-emissor (Emax 0,81 MeV) com emissao gama que permite cintilografia pos-dose; inicio de efeito mais rapido (1-2 semanas) mas duracao mais curta que 89Sr",
      "Flare pain (piora transitoria da dor nas primeiras 24-72h pos-administracao) ocorre em 10-15% dos pacientes e pode ser preditor de boa resposta — manejar com analgesicos sem suspender o tratamento",
      "Nadir hematologico com 223Ra: plaquetas em 2-3 semanas, tipicamente grau 1-2; com 89Sr e 153Sm: nadir de plaquetas em 4-6 semanas, mais profundo (grau 2-3 em ate 30% dos pacientes)",
      "Monitoramento hematologico obrigatorio: hemograma completo a cada 2 semanas nos 3 primeiros ciclos de 223Ra; antes de cada administracao de 89Sr/153Sm e semanalmente por 8 semanas apos",
      "ALP serica como marcador farmacodinamico de 223Ra: queda >= 30% em 12 semanas correlaciona-se com beneficio de OS; monitorar a cada ciclo junto com PSA",
      "Criterios de suspensao de 223Ra: plaquetas < 50.000/mm3, neutrofilos < 1.000/mm3, aparecimento de nova metastase visceral, deterioracao clinica com ECOG >= 3",
      "Intervalo minimo entre 153Sm e quimioterapia subsequente: 6-8 semanas para permitir recuperacao hematologica adequada; para 89Sr o intervalo e maior (10-12 semanas) devido a meia-vida longa",
      "Radioterapia externa pode ser combinada com 223Ra sem comprometimento significativo da eficacia, desde que nao haja sobreposicao de campos em medula ossea ja irradiada",
      "Radioproteao para 223Ra: sem necessidade de isolamento hospitalar (alfa-emissor com radiacao externa minima); orientar descarte adequado de excretas por 7 dias",
      "Radioproteao para 89Sr e 153Sm: pode requerer internacao de 24-48h conforme regulacao local; orientar cuidados com fluidos corporais por 3-7 dias",
      "Avaliacao de resposta: escala de dor (VAS ou BPI) em 4, 8 e 12 semanas; cintilografia ossea a cada 3-6 meses (atencao ao flare cintilografico que nao deve ser confundido com progressao)",
      "Sequenciamento com 177Lu-PSMA-617: nao ha dados prospectivos robustos; evitar uso concomitante pelo risco de mielotoxicidade aditiva; respeitar intervalo de pelo menos 6 semanas entre tratamentos"
    ],
    radiopharmaceuticals: "223Ra-Dicloreto (Xofigo, Bayer) e um alfa-emissor (T1/2 = 11,4 dias) que emite particulas alfa de alto LET com alcance tecidual < 100 micrometros, mimetizando o calcio na superficie ossea remodelada. 89Sr-Cloreto (Metastron, GE Healthcare) e um beta-emissor puro (T1/2 = 50,5 dias; Emax 1,46 MeV; alcance maximo ~8 mm no tecido) fornecido em solucao pronta para uso. 153Sm-EDTMP (Quadramet, Lantheus) e um beta-emissor (T1/2 = 1,9 dias; Emax 0,81 MeV; alcance maximo ~3 mm) com emissao gama de 103 keV que permite imagem pos-terapeutica para verificacao de biodistribuicao. Todos concentram-se preferencialmente em areas de remodelacao ossea aumentada.",
    practicalAspects: "Avaliacao pre-tratamento inclui cintilografia ossea com 99mTc-MDP/HDP para confirmar padrao osteoblastico multifocal e hemograma completo com perfil hepatico e renal. Para 223Ra, verificar ausencia de metastases viscerais por TC de torax/abdome/pelve. Administracao de 223Ra: IV lento em bolus (aproximadamente 1 minuto) por acesso venoso periferico calibroso, seguido de flush com soro fisiologico; procedimento ambulatorial. Nao combinar com abiraterona/prednisona; enzalutamida pode ser mantida conforme avaliacao multidisciplinar. Para 89Sr e 153Sm, administracao IV em bolus lento (1-2 minutos) com acesso exclusivo. Cintilografia pos-dose com 153Sm (emissao gama de 103 keV) permite verificar distribuicao do radiofarmaco nas lesoes e detectar captacao extra-ossea inesperada. Monitoramento de hemograma: a cada 2 semanas nos primeiros 3 ciclos de 223Ra, depois a cada 4 semanas; para beta-emissores, semanal por 8 semanas. Avaliacao de resposta de dor com escalas validadas (VAS, BPI) nos retornos ambulatoriais. Criterios de retratamento com 153Sm: intervalo minimo de 8-12 semanas e recuperacao hematologica documentada (plaquetas > 100.000, neutrofilos > 1.500). ALP e PSA devem ser dosados antes de cada ciclo de 223Ra para avaliacao farmacodinamica e de progressao bioquimica.",
    limitations: "223Ra e limitado exclusivamente a metastases osseas sintomaticas em mCRPC — nao trata doenca visceral, linfonodal ou de partes moles. A combinacao com abiraterona/prednisona e contraindicada com base nos dados do estudo ERA 223, que demonstraram aumento de fraturas patologicas e tendencia a maior mortalidade. Dados de combinacao com 177Lu-PSMA-617 sao anecdoticos e nao ha protocolo de sequenciamento validado. Beta-emissores (89Sr, 153Sm) nao demonstraram beneficio de sobrevida global — sao estritamente paliativos para controle de dor. Mielossupressao e a principal toxicidade dose-limitante de todos os agentes, sendo mais pronunciada e prolongada com 89Sr devido a sua meia-vida longa. Eficacia limitada em lesoes puramente liticas (sem componente osteoblastico) — estes pacientes nao sao bons candidatos. A populacao elegivel para 223Ra e restrita pela exigencia de ausencia de metastases viscerais, o que exclui uma parcela significativa de pacientes com mCRPC avancado. Lesoes osseas de componente misto (litico-blastico) podem ter captacao variavel e resposta imprevisivel.",
    reference: "Silberstein EB, et al. SNMMI Procedure Standard/EANM Practice Guideline for Palliative Nuclear Medicine Therapies of Bone Metastases. J Nucl Med. 2023."
  },
  {
    id: "bone-eanm-beta-2018",
    title: "EANM guidelines for radionuclide therapy of bone metastases with beta-emitting radionuclides",
    year: "2018",
    society: "EANM",
    type: "Guideline",
    badges: [],
    category: "osseas",
    categoryName: "Metástases ósseas",
    categoryColor: "#94A3B8",
    scope: "Guideline europeu dedicado exclusivamente a beta-emissores para paliacao de dor em metastases osseas, detalhando mecanismos de acao, farmacocinetica, selecao de pacientes e protocolos de administracao para 89Sr-Cloreto, 153Sm-EDTMP e 186Re-HEDP. Publicado antes da consolidacao do 223Ra como padrao em mCRPC, este documento foca no papel especifico dos beta-emissores na paliacao de dor ossea refrataria em multiplos tumores primarios, incluindo cancer de prostata, mama e pulmao. A base de evidencia consiste em estudos randomizados duplo-cegos (para 89Sr e 153Sm versus placebo) e series clinicas que demonstraram taxas de resposta de dor de 60-80%. O guideline posiciona estes agentes como complementares a radioterapia externa e analgesicos sistemicos, nao como alternativa curativa. O mecanismo de acao baseia-se na concentracao preferencial de compostos osteotropicos em areas de remodelacao ossea aumentada (lesoes osteoblasticas), onde a emissao beta causa dano celular local.",
    indications: [
      "Dor ossea metastatica multifocal refrataria a analgesicos de escada 1-2 da OMS, com padrao osteoblastico confirmado em cintilografia ossea",
      "Cancer de prostata com metastases osseas difusas e dor nao controlada com radioterapia externa localizada",
      "Cancer de mama com metastases osteoblasticas ou mistas (componente blastico predominante) e dor refrataria",
      "Cancer de pulmao e outros tumores solidos com metastases osseas osteoblasticas sintomaticas multifocais",
      "Pacientes com ECOG 0-2, expectativa de vida superior a 3 meses e reserva medular adequada",
      "Hemoglobina >= 9 g/dL, plaquetas >= 80.000/mm3, leucocitos >= 3.000/mm3 como criterios minimos de elegibilidade",
      "Ausencia de quimioterapia nas ultimas 4-6 semanas (para garantir recuperacao medular pre-tratamento)",
      "Lesoes com captacao confirmada em cintilografia ossea com 99mTc-MDP ou 99mTc-HDP (padrao osteoblastico)",
      "Paliacao complementar quando radioterapia de hemicorpo nao esta disponivel ou ja foi utilizada",
      "Retratamento com 153Sm apos resposta inicial e recorrencia de dor, desde que haja recuperacao hematologica documentada"
    ],
    keyPoints: [
      "Beta-emissores osteotropicos concentram-se em areas de turnover osseo aumentado (matriz de hidroxiapatita em formacao nas lesoes osteoblasticas), com relacao de captacao lesao/osso normal de 2:1 a 10:1",
      "89Sr-Cloreto: meia-vida fisica de 50,5 dias, Emax 1,46 MeV, alcance maximo no tecido de 8 mm — efeito paliativo prolongado (duracao media de resposta de 3-6 meses), mas recuperacao hematologica mais lenta",
      "153Sm-EDTMP: meia-vida fisica de 1,9 dias, Emax 0,81 MeV, alcance maximo de 3 mm — inicio de efeito mais rapido (7-14 dias), menor mielotoxicidade acumulada e possibilidade de retratamento mais precoce",
      "186Re-HEDP: meia-vida de 3,7 dias, Emax 1,07 MeV — disponibilidade limitada e menos dados clinicos que 89Sr e 153Sm; emissao gama de 137 keV permite imagem pos-dose",
      "Taxas de resposta de dor: 60-80% para todos os agentes, com resposta completa em 15-30% dos pacientes; inicio variavel (7-28 dias conforme agente)",
      "Flare pain (exacerbacao paradoxal da dor nas primeiras 48-72h) ocorre em 10-15% dos pacientes — e potencial preditor de boa resposta e deve ser manejado com analgesicos, sem suspensao do tratamento",
      "Nadir hematologico com 89Sr: plaquetas em 6-8 semanas, com recuperacao em 10-12 semanas; com 153Sm: nadir em 3-4 semanas com recuperacao em 6-8 semanas",
      "Monitoramento hematologico: hemograma completo semanal por 8-12 semanas apos 89Sr; semanal por 6-8 semanas apos 153Sm; incluir contagem de reticulocitos para avaliar regeneracao medular",
      "Retratamento com 153Sm e possivel apos 8-12 semanas se plaquetas > 100.000 e neutrofilos > 1.500 — a curta meia-vida permite repetibilidade sem acumulo excessivo de dose medular",
      "Interacao com quimioterapia: evitar administracao concomitante; intervalo minimo de 4-6 semanas apos QT e 6-8 semanas antes de nova QT; a mielotoxicidade e aditiva e pode ser severa",
      "Avaliacao de resposta com escalas validadas de dor (VAS, BPI) e consumo de analgesicos nos retornos de 2, 4 e 8 semanas pos-tratamento",
      "Cintilografia ossea de controle em 3-6 meses — nao confundir flare cintilografico precoce (aumento transitorio de captacao) com progressao; SPECT/CT pode auxiliar na diferenciacao",
      "Orientacoes de radioproteao: beta-emissores tem radiacao externa limitada, mas contaminacao por excretas (urina) requer cuidados por 3-7 dias; internacao pode ser requerida conforme regulacao local",
      "Em metastases de cancer de mama, selecionar pacientes com componente osteoblastico predominante — lesoes puramente liticas nao captam os radiofarmacos osteotropicos",
      "Papel complementar, nao substitutivo, da radioterapia externa e dos bifosfonatos/denosumab na abordagem multimodal da dor ossea metastatica"
    ],
    radiopharmaceuticals: "89Sr-Cloreto (Metastron, GE Healthcare) e um analogo do calcio e beta-emissor puro (T1/2 = 50,5 dias; Emax 1,46 MeV; alcance maximo ~8 mm), fornecido em solucao IV pronta. 153Sm-EDTMP (Quadramet, Lantheus) e um beta-emissor (T1/2 = 1,9 dias; Emax 0,81 MeV; alcance ~3 mm) quelado a etilendiaminotetrametilenfosfonato que se liga a hidroxiapatita; possui emissao gama de 103 keV para imagem pos-dose. 186Re-HEDP (meia-vida 3,7 dias; Emax 1,07 MeV; emissao gama 137 keV) tem disponibilidade regional limitada. Todos requerem controle de qualidade com verificacao de pureza radioquimica e atividade antes da administracao.",
    practicalAspects: "Avaliacao pre-tratamento obrigatoria: cintilografia ossea com 99mTc-MDP/HDP confirmando padrao osteoblastico multifocal com captacao nas lesoes sintomaticas. Hemograma completo com diferencial, funcao renal (creatinina, CrCl) e funcao hepatica devem ser obtidos ate 2 semanas antes do tratamento. Revisar medicacoes concomitantes que possam afetar funcao medular. Administracao: 89Sr-Cloreto 148 MBq (4 mCi) IV em bolus lento (1-2 min); 153Sm-EDTMP 37 MBq/kg IV em bolus lento (1-2 min); 186Re-HEDP 1.295 MBq (35 mCi) IV. Acesso venoso periferico calibroso com flush de SF antes e apos a injecao. Cintilografia pos-dose com 153Sm (gama 103 keV) em 4-24h para verificar biodistribuicao e captacao tumoral. Resposta de dor avaliada em consultas de retorno em 2, 4 e 8 semanas com escalas VAS ou BPI e registro de consumo de analgesicos opiaceos e nao-opiaceos. Hemograma semanal por 8-12 semanas pos-89Sr e 6-8 semanas pos-153Sm. Em caso de trombocitopenia grau 3 (plaquetas < 50.000), considerar suporte transfusional e suspender retratamento. Repetir cintilografia ossea em 3-6 meses para reavaliacao de carga tumoral. Orientar pacientes sobre cuidados com urina e excretas por 3-7 dias pos-administracao.",
    limitations: "Beta-emissores osseos NAO demonstraram beneficio de sobrevida global em nenhum estudo randomizado — seu papel e estritamente paliativo para controle de dor. Eficacia limitada ou nula em lesoes puramente liticas, que nao captam radiofarmacos osteotropicos — estes pacientes devem ser encaminhados para outras modalidades (RT externa, bifosfonatos). Mielossupressao e a principal toxicidade dose-limitante, especialmente com 89Sr (nadir prolongado em 6-8 semanas, recuperacao lenta), o que pode comprometer quimioterapia subsequente. Retratamento com 89Sr raramente e viavel pelo risco de mielotoxicidade cumulativa; 153Sm e preferivel quando multiplas administracoes sao necessarias. 186Re-HEDP tem disponibilidade limitada em muitos paises e menos evidencia robusta que 89Sr e 153Sm. Com a aprovacao do 223Ra (alfa-emissor com beneficio de OS) e do 177Lu-PSMA-617 em mCRPC, o papel dos beta-emissores ficou mais restrito nesta indicacao especifica. Pacientes com mets osseas de histologia neuroendocrina ou small cell nao se beneficiam desta abordagem.",
    reference: "EANM guidelines for radionuclide therapy of bone metastases with beta-emitting radionuclides. Eur J Nucl Med Mol Imaging. 2018."
  },
  {
    id: "bone-acr-ra223-2020",
    title: "ACR–ACNM–ARS–SNMMI Practice Parameter for Therapy with Radium-223 Dichloride",
    year: "2020",
    society: "ACR · ACNM · ARS · SNMMI",
    type: "Practice parameter",
    badges: [],
    category: "osseas",
    categoryName: "Metástases ósseas",
    categoryColor: "#94A3B8",
    scope: "Parametro de pratica multissociedade norte-americano que estabelece padroes detalhados para terapia com 223Ra-Dicloreto (Xofigo) em cancer de prostata metastatico resistente a castracao (mCRPC) com metastases osseas sintomaticas. O documento baseia-se nos resultados do estudo fase III ALSYMPCA, que demonstrou melhora de sobrevida global (HR 0,70; mediana 14,9 vs 11,3 meses), alem de reducao de eventos esqueleticos sintomaticos. Aborda qualificacoes profissionais, infraestrutura necessaria, criterios de selecao do paciente, protocolo de administracao e manejo de toxicidade. Incorpora os dados de seguranca do estudo ERA 223, que contraindicam formalmente a combinacao de 223Ra com abiraterona/prednisona. Define o 223Ra como o unico agente emissor de particulas alfa aprovado para tratamento de metastases osseas, com mecanismo de acao baseado na mimetizacao do calcio na superficie ossea e inducao de quebras de dupla fita de DNA irreparaveis. Posiciona o 223Ra no algoritmo terapeutico do mCRPC apos ou como alternativa ao docetaxel.",
    indications: [
      "mCRPC com pelo menos 2 metastases osseas sintomaticas detectadas em cintilografia ossea com 99mTc-MDP/HDP",
      "Ausencia de metastase visceral conhecida (pulmonar, hepatica, cerebral) — criterio mandatorio do estudo ALSYMPCA",
      "Linfadenopatia metastatica ate 3 cm no eixo curto e aceitavel (nao configura doenca visceral)",
      "Pacientes pos-docetaxel ou nao candidatos/recusam quimioterapia citotoxica",
      "ECOG 0-2 com expectativa de vida superior a 6 meses",
      "Hemoglobina >= 10 g/dL, plaquetas >= 100.000/mm3, neutrofilos >= 1.500/mm3, ANC >= 1.000/mm3",
      "Funcao renal preservada (sem insuficiencia renal grave que impeca tratamento)",
      "Ausencia de compressao medular ou fratura patologica iminente que requeira intervencao ortopedica ou RT de urgencia",
      "Nao estar em uso concomitante de abiraterona/prednisona (contraindicacao baseada em ERA 223)"
    ],
    keyPoints: [
      "Dose padrao: 55 kBq/kg de peso corporal IV a cada 4 semanas, por 6 ciclos consecutivos, conforme protocolo ALSYMPCA aprovado pela FDA/EMA",
      "ALSYMPCA: beneficio de OS robusto (HR 0,70; p < 0,001), alem de reducao de 30% em eventos esqueleticos sintomaticos e melhora de qualidade de vida",
      "Mecanismo: 223Ra e um mimético do calcio que se incorpora a matriz ossea em areas de remodelacao osteoblastica; emissao alfa (quatro particulas na cadeia de decaimento) com alto LET e alcance < 100 micrometros",
      "ERA 223: combinacao de 223Ra + abiraterona/prednisona resultou em aumento estatisticamente significativo de fraturas patologicas e tendencia a maior mortalidade — esta combinacao e CONTRAINDICADA pelas agencias regulatorias",
      "Monitoramento entre ciclos: hemograma completo antes de cada administracao (a cada 4 semanas); ALP serica como biomarcador farmacodinamico de atividade osteoblastica; PSA a cada ciclo",
      "Queda de ALP >= 30% em relacao ao basal dentro de 12 semanas e marcador de beneficio clinico e correlaciona com melhora de sobrevida global",
      "Criterios de suspensao de ciclo: plaquetas < 50.000/mm3, neutrofilos < 1.000/mm3 (adiar ate recuperacao); suspensao definitiva se nova metastase visceral, deterioracao clinica ECOG >= 3 ou toxicidade grau 4 persistente",
      "Qualificacoes do medico administrador: treinamento em terapia com radionuclideos, certificacao em radioprotecao, licenciamento para manipulacao de fontes radioativas (NRC nos EUA; CNEN no Brasil)",
      "Infraestrutura requerida: calibrador de dose para alfa-emissores, equipamento de radioprotecao, protocolo de descarte de residuos, sistema de registro de doses administradas",
      "Efeitos adversos mais comuns: diarreia (grau 1-2 em 25%), nausea (15%), trombocitopenia (12%), anemia, fadiga; mielotoxicidade geralmente leve comparada a beta-emissores",
      "Nadir hematologico com 223Ra: plaquetas em 2-3 semanas pos-administracao, tipicamente grau 1-2, com recuperacao espontanea antes do proximo ciclo",
      "Sem necessidade de internacao hospitalar: alfa-emissores tem radiacao externa minima; orientar cuidados com excretas por 7 dias (toilete, limpeza)",
      "Contraindicacoes adicionais: doenca de Crohn ou retocolite ulcerativa ativa (risco de acumulo intestinal), fistula urinaria ou colostomia sem protocolo de manejo de residuos",
      "Sequenciamento com 177Lu-PSMA-617: nao estabelecido prospectivamente; respeitar intervalo minimo de 6 semanas e garantir recuperacao hematologica entre terapias",
      "Imagem pos-dose nao e rotina (223Ra nao emite gama util para cintilografia convencional), mas bone scan de seguimento em 3-6 meses para avaliacao de resposta"
    ],
    radiopharmaceuticals: "223Ra-Dicloreto (Xofigo, Bayer) e um mimético do calcio e alfa-emissor (T1/2 = 11,4 dias) que gera quatro particulas alfa ao longo de sua cadeia de decaimento ate chumbo-207 estavel. O alto LET (transferencia linear de energia) das particulas alfa (~80 keV/micrometro) causa dano de dupla fita de DNA irreparavel nas celulas tumorais adjacentes a superficie ossea. O alcance tecidual extremamente curto (< 100 micrometros) limita a irradiacao a poucos diametros celulares, poupando medula ossea circundante. Fornecido em solucao IV pronta para uso, com calibracao de atividade na data de referencia.",
    practicalAspects: "Avaliacao pre-tratamento: cintilografia ossea com 99mTc-MDP confirmando pelo menos 2 lesoes osteoblasticas; TC de torax/abdome/pelve para excluir metastases viscerais; hemograma completo, PSA, ALP, creatinina, funcao hepatica. Verificar ausencia de uso concomitante de abiraterona/prednisona. Administracao: IV em bolus lento (aproximadamente 1 minuto) por acesso venoso periferico, seguido de flush com 10-20 mL de soro fisiologico. O procedimento e totalmente ambulatorial, sem necessidade de internacao ou isolamento (radiacao externa do 223Ra e minima). Posologia: 55 kBq/kg, recalcular se peso corporal variar mais de 10% entre ciclos. Hemograma antes de cada ciclo; ALP e PSA a cada 4 semanas. Se plaquetas entre 50.000-100.000, considerar adiamento de 2 semanas e reavaliar. Avaliacao de resposta de dor com VAS/BPI a cada ciclo. Prevencao de fraturas patologicas: manter suplementacao de calcio e vitamina D; considerar agente antirreabsortivo (denosumab ou acido zoledronico) conforme avaliacao oncologica. Efeitos colaterais gastrointestinais (diarreia, nausea) manejados com antidiarreicos e antieméticos conforme necessidade. Documentar todas as doses em prontuario de radioprotecao do paciente.",
    limitations: "O 223Ra e restrito a mCRPC com metastases osseas sintomaticas — nao ha indicacao aprovada para outros tumores primarios (mama, pulmao) apesar do racional teorico. A exigencia de ausencia de metastases viscerais reduz significativamente a populacao elegivel, pois muitos pacientes com mCRPC avancado apresentam doenca visceral concomitante. A contraindicacao formal de combinacao com abiraterona/prednisona (ERA 223) limita as opcoes de terapia concomitante. Nao ha dados prospectivos de sequenciamento otimo com 177Lu-PSMA-617, enzalutamida ou novos agentes hormonais. O 223Ra nao emite radiacao gama util para imagem, dificultando verificacao direta de biodistribuicao pos-dose. Custos elevados e necessidade de infraestrutura especifica para manipulacao de alfa-emissores podem limitar a disponibilidade em centros menores. Eficacia limitada em lesoes liticas ou mistas com componente litico predominante. Dados de retratamento (segundo curso de 6 ciclos) sao limitados a pequenas series retrospectivas.",
    reference: "ACR–ACNM–ARS–SNMMI Practice Parameter for the Performance of Therapy with Radium-223 Dichloride. 2020."
  },

  // ===============================================
  //  6. MIBG
  // ===============================================
  {
    id: "mibg-eanm-procedure-2008",
    title: "EANM procedure guidelines for 131I-meta-iodobenzylguanidine (131I-mIBG) therapy",
    year: "2008",
    society: "EANM",
    type: "Procedure guideline",
    badges: ["essential"],
    category: "mibg",
    categoryName: "Tumores neuroectodérmicos / 131I-MIBG",
    categoryColor: "#FB923C",
    scope: "Guideline procedimental europeu de referencia para terapia com 131I-MIBG (metaiodobenzilguanidina) em tumores neuroectodermicos e neuroendocrinos que demonstram captacao de MIBG. A MIBG e um analogo da norepinefrina que utiliza o mecanismo de captacao-1 (transportador de norepinefrina, NET) para acumular-se seletivamente em celulas de origem simpatica. O documento aborda o espectro completo de indicacoes terapeuticas: neuroblastoma de alto risco em pediatria (principal indicacao por volume), feocromocitoma/paraganglioma metastatico ou irressecavel, carcinoide MIBG-avido e, raramente, carcinoma medular de tireoide. A publicacao em 2008 precedeu o desenvolvimento do 131I-MIBG de alta atividade especifica (Azedra/iobenguano I-131), que posteriormente recebeu aprovacao da FDA para feocromocitoma/paraganglioma. O guideline permanece como referencia fundamental para protocolos de administracao, preparo do paciente e manejo de complicacoes especificas deste radiofarmaco.",
    indications: [
      "Neuroblastoma de alto risco (estagio 4/M, amplificacao de MYCN, idade > 18 meses) refratario a quimioterapia de inducao ou em protocolo de primeira linha multimodal",
      "Neuroblastoma recidivado ou progressivo apos quimioterapia e/ou cirurgia, com captacao MIBG confirmada em cintilografia diagnostica",
      "Feocromocitoma maligno/metastatico irressecavel com captacao MIBG confirmada e doenca progressiva ou sintomatica (hipertensao refrataria, crises adrenergicas)",
      "Paraganglioma metastatico ou localmente avancado MIBG-avido, incluindo paragangliomas de cabeca e pescoco com disseminacao regional",
      "Tumores carcinoides MIBG-avidos refratarios a terapias sistemicas (especialmente quando nao candidatos a PRRT por baixa expressao SSTR)",
      "Carcinoma medular de tireoide metastatico com captacao MIBG demonstrada (indicacao rara, < 5% dos casos sao MIBG-avidos)",
      "ECOG 0-2, expectativa de vida > 3 meses em adultos; status Lansky/Karnofsky adequado em pediatria",
      "Funcao renal preservada (CrCl >= 50 mL/min) e funcao hepatica adequada (bilirrubinas e transaminases < 3x LSN)",
      "Plaquetas >= 80.000/mm3, neutrofilos >= 1.000/mm3, hemoglobina >= 8 g/dL (limiares mais baixos podem ser aceitos em neuroblastoma com suporte transfusional)",
      "Captacao tumoral confirmada em cintilografia diagnostica com 123I-MIBG (preferido) ou 131I-MIBG em dose tracadora"
    ],
    keyPoints: [
      "Avaliacao pre-terapia obrigatoria: cintilografia diagnostica com 123I-MIBG (74-185 MBq IV em adultos; 5,2 MBq/kg em criancas, maximo 370 MBq) ou 131I-MIBG em dose tracadora (37-74 MBq) para confirmar captacao tumoral",
      "Bloqueio tireoidiano MANDATORIO: solucao de Lugol (3-5 gotas, 3x/dia) ou iodeto de potassio (SSKI; 130 mg/dia em adultos, 65 mg em criancas), iniciar 24-48h ANTES da administracao e manter por 10-14 dias apos para prevenir captacao tireoidiana de 131I livre",
      "Atividades terapeuticas em adultos: 3,7-11,2 GBq (100-300 mCi) por ciclo; em neuroblastoma pediatrico, doses calculadas por peso (444 MBq/kg em protocolos mieloablativos) ou atividade fixa conforme protocolo institucional",
      "Infusao IV lenta obrigatoria: diluir em 50-100 mL de SF e infundir em 1-4 horas; velocidade lenta e essencial para minimizar risco de liberacao de catecolaminas em feocromocitoma e evitar hipertensao aguda",
      "Pre-medicacao em feocromocitoma/paraganglioma: bloqueio alfa-adrenergico com fenoxibenzamina (20-40 mg/dia) ou doxazosina (4-16 mg/dia), iniciado 10-14 dias antes do tratamento; bloqueio beta (propranolol/atenolol) apenas APOS bloqueio alfa adequado, nunca isoladamente",
      "Monitoramento hemodinamico durante infusao: PA e FC a cada 15 min em feocromocitoma; acesso a nitroprussiato de sodio IV, fentolamina ou labetalol para crise hipertensiva aguda; equipe de anestesia disponivel",
      "Medicamentos que INTERFEREM com captacao de MIBG e devem ser SUSPENSOS: labetalol (4-7 dias), antidepressivos triciclicos (6 semanas), simpaticomimeticos (descongestionantes, efedrina — 3 dias), reserpina (2 semanas), cocaina; fenilefrina topica nasal tambem interfere",
      "Internacao em quarto plumbifero dedicado por 48-96 horas conforme atividade administrada e taxa de dose medida a 1 metro; criterio de liberacao: < 25 microSv/h a 1 metro (variavel por regulacao local)",
      "Mielossupressao: principal toxicidade dose-limitante; nadir de plaquetas em 4-6 semanas, neutrofilos em 3-5 semanas; recuperacao em 6-8 semanas em doses convencionais",
      "Em protocolos mieloablativos (neuroblastoma): doses de 444-666 MBq/kg com resgate de celulas-tronco hematopoeticas autologas (ASCT); coleta de CTH ANTES da administracao de MIBG",
      "Hipotireoidismo pos-tratamento em 10-20% dos pacientes APESAR do bloqueio com iodo estavel — monitorar TSH a cada 3 meses no primeiro ano e iniciar levotiroxina quando indicado",
      "Nausea e vomito em 30-50% dos pacientes nas primeiras 24-48h — antieméticos profilaticos (ondansetrona 8 mg IV/VO pre-infusao)",
      "Xerostomia transitoria e disfuncao salivar em < 10% dos pacientes — geralmente autolimitada; sialagogia com pastilhas citricas pode auxiliar",
      "Cintilografia pos-dose com 131I (imagem planar de corpo inteiro ± SPECT/CT) em 48-72h para verificacao de biodistribuicao e dosimetria simplificada",
      "Ciclos subsequentes: intervalo minimo de 8-12 semanas entre tratamentos; indicacao de retratamento baseada em resposta clinica/bioquimica e recuperacao hematologica; tipicamente ate 3-4 ciclos em doses convencionais",
      "Seguimento pos-terapia: cintilografia MIBG + TC/RM em 3-6 meses; marcadores bioquimicos (catecolaminas/metanefrinas urinarias ou plasmaticas para feocromocitoma; ferritina, LDH, NSE, VMA/HVA para neuroblastoma)"
    ],
    radiopharmaceuticals: "131I-MIBG (metaiodobenzilguanidina marcada com iodo-131) e um analogo da norepinefrina que e captado pelo transportador de norepinefrina (NET/uptake-1) nas celulas de origem neuroendocrina simpatica. 131I e um emissor beta (Emax 0,61 MeV; alcance maximo ~2 mm no tecido) e gama (364 keV — permite imagem cintilografica pos-dose). Meia-vida fisica de 8,02 dias. Preparacao convencional: atividade especifica padrao, com ligacao inespecifica a albumina e outros componentes. Iobenguano I-131 de alta atividade especifica (Azedra, Progenics/Lantheus) foi desenvolvido posteriormente com maior pureza e menor massa quimica de MIBG fria, resultando em maior captacao tumoral por dose administrada. 123I-MIBG (T1/2 = 13,2h; gama 159 keV) e utilizado exclusivamente para fins diagnosticos por sua melhor qualidade de imagem e menor dose ao paciente.",
    practicalAspects: "Avaliacao pre-terapia completa: cintilografia diagnostica com 123I-MIBG (imagem planar de corpo inteiro + SPECT/CT em 24h) ou 131I-MIBG em dose tracadora; TC/RM de estadiamento; hemograma completo, funcao renal (creatinina, CrCl), funcao hepatica, TSH, catecolaminas/metanefrinas plasmaticas ou urinarias. Para feocromocitoma: iniciar bloqueio alfa-adrenergico 10-14 dias antes com titulacao gradual; garantir PA controlada (< 140/90 mmHg) antes de prosseguir. Revisar medicacoes e suspender farmacos que interferem com captacao MIBG (lista detalhada nos keyPoints). Jejum de 4h antes da administracao; antieméticos profilaticos. Acesso venoso periferico calibroso (18-20G) com verificacao de perviedade antes da infusao — EXTRAVASAMENTO de 131I-MIBG causa necrose tecidual local e requer intervencao imediata (aspiracao, irrigacao, compressao). Infusao IV em 1-4 horas com bomba de infusao ou gotejamento controlado em sala dedicada. Monitoramento hemodinamico contínuo durante e ate 2h apos infusao em pacientes com feocromocitoma. Internacao em quarto plumbifero com banheiro exclusivo; monitoramento diario de taxa de dose para liberacao. Coleta de urina em recipiente blindado para decaimento quando requerido por regulacao local. Imagem pos-dose: planar corpo inteiro ± SPECT/CT em 48-72h para documentacao de biodistribuicao e planejamento dosimetrico.",
    limitations: "Mielotoxicidade e a principal toxicidade dose-limitante, especialmente em doses altas e mieloablativas, podendo requerer suporte com G-CSF ou transplante autologo de celulas-tronco hematopoeticas. Hipotireoidismo pos-tratamento ocorre em 10-20% dos pacientes apesar do bloqueio adequado com iodo estavel, requerendo monitoramento prolongado. Captacao de MIBG e heterogenea entre tumores e lesoes individuais — tumores MIBG-negativos (10-15% dos neuroblastomas, proporcao maior de feocromocitomas de variante succinato desidrogenase) nao sao candidatos e devem ser encaminhados para alternativas como PRRT (se SSTR-positivos) ou quimioterapia. A energia gama alta do 131I (364 keV) gera significativa exposicao radiologica a equipe de saude e familiares, exigindo internacao prolongada e infraestrutura blindada dedicada. Risco de crise hipertensiva grave em feocromocitoma durante a infusao, mesmo com bloqueio farmacologico adequado — necessidade de equipe treinada e medicacoes de emergencia disponiveis. Disponibilidade limitada de 131I-MIBG de alta atividade especifica (Azedra) a nivel global. Menos eficaz em doenca rapidamente progressiva e em tumores com baixa expressao de NET/uptake-1.",
    reference: "Giammarile F, et al. EANM procedure guidelines for 131I-meta-iodobenzylguanidine (131I-mIBG) therapy. Eur J Nucl Med Mol Imaging. 2008;35(5):1039-1047."
  },
  {
    id: "mibg-dosimetry-sop-2020",
    title: "EANM Dosimetry Committee SOP: dosimetry for 131I-mIBG treatment of neuroendocrine tumours",
    year: "2020",
    society: "EANM — Dosimetry Committee",
    type: "Standard operating procedure",
    badges: ["dosimetry"],
    category: "mibg",
    categoryName: "Tumores neuroectodérmicos / 131I-MIBG",
    categoryColor: "#FB923C",
    scope: "Procedimento operacional padrao do Comite de Dosimetria da EANM para dosimetria clinica de 131I-MIBG em tumores neuroendocrinos. O documento estabelece uma metodologia unificada para aquisicao de imagens seriadas, calculo de tempo de residencia e determinacao de dose absorvida em tumores e orgaos criticos (medula ossea, figado, coracao, tireoide, rins). A dosimetria e particularmente importante para MIBG por duas razoes: a mielotoxicidade e dose-limitante e a variabilidade farmacocinetica inter-paciente e significativa. O SOP abrange tanto a dosimetria pre-terapeutica (usando dose tracadora para estimar farmacocinetica e planejar atividade terapeutica otima) quanto a dosimetria peri-terapeutica (verificacao pos-dose para correlacao dose-resposta e predicao de toxicidade). E especialmente indicado em cenarios de doses altas/mieloablativas, retratamento e populacoes pediatricas, onde a otimizacao de atividade pode minimizar toxicidade sem comprometer eficacia.",
    indications: [
      "Dosimetria pre-terapeutica com dose tracadora de 131I-MIBG para individualizacao de atividade antes do ciclo terapeutico",
      "Dosimetria peri-terapeutica com imagens pos-dose terapeutica para calculo de dose absorvida real em tumores e orgaos",
      "Planejamento de doses mieloablativas em neuroblastoma pediatrico: calculo de atividade maxima toleravel pela medula ossea antes de transplante autologo",
      "Retratamento com MIBG: avaliacao de dose acumulada em orgaos criticos (medula, figado, coracao) para determinar seguranca de ciclos adicionais",
      "Correlacao dose-resposta em estudos clinicos e protocolos de pesquisa para otimizacao de esquemas terapeuticos",
      "Pacientes com funcao renal ou hepatica reduzida, onde a farmacocinetica pode diferir significativamente do padrao"
    ],
    keyPoints: [
      "Aquisicao de imagens planares de corpo inteiro em 3-5 timepoints pos-injecao: idealmente 4h, 24h, 48h, 72h (e opcionalmente 96-120h para curvas com clearance lento)",
      "SPECT/CT complementar em pelo menos 1-2 timepoints para quantificacao volumetrica de lesoes individuais e correcao de sobreposicao de estruturas em imagem planar",
      "Calibracao da gama-camara para 131I: fotopico 364 keV (janela 15-20%), colimador de alta energia, correcao de scatter e septal penetration obrigatorias para quantificacao acurada",
      "Calculo de tempo de residencia tumoral: definicao de ROIs sobre tumores identificaveis em cada timepoint, geracao de curvas atividade-tempo e ajuste por funcao mono ou bi-exponencial",
      "Dose absorvida em corpo inteiro: limite conservador de 2 Gy para tratamento convencional sem suporte medular; acima de 2 Gy, considerar resgate com celulas-tronco hematopoeticas",
      "Dosimetria de medula ossea: metodo de amostragem sanguinea (4 amostras em timepoints padronizados) com calculo de dose a sangue como proxy de dose medular; complementar com imagem de corpo inteiro para componente cross-dose",
      "Dosimetria hepatica e cardiaca: relevante em pacientes com doenca hepatica metastatica volumosa (risco de hepatotoxicidade por irradiacao) e em feocromocitoma (captacao miocardica de MIBG)",
      "Dosimetria tireoidiana: mesmo com bloqueio de iodo estavel, verificar captacao tireoidiana residual que possa causar hipotireoidismo; dose tireoidiana < 50 Gy como alvo com bloqueio adequado",
      "Integracao com dosimetria baseada em voxel: software dedicado (OLINDA/EXM 2.0, PLANET Dose, IDAC-Dose) para mapas de dose 3D quando SPECT/CT quantitativo esta disponivel",
      "Em pediatria: ajuste de fatores S por phantoms pediatricos especificos (ICRP), pois a extrapolacao de modelos adultos subestima significativamente a dose em orgaos menores"
    ],
    radiopharmaceuticals: "131I-MIBG em dose tracadora para dosimetria pre-terapeutica (37-185 MBq em adultos; 3,7-5,2 MBq/kg em criancas) e dose terapeutica para dosimetria peri-terapeutica (3,7-11,2 GBq conforme protocolo). A dosimetria requer que o mesmo radiofarmaco (mesma formulacao e atividade especifica) seja utilizado na fase diagnostica/dosimetrica e na fase terapeutica para garantir farmacocinetica comparavel. Quando disponivel, 131I-MIBG de alta atividade especifica (Azedra) pode ter biodistribuicao diferente da formulacao convencional, exigindo dosimetria especifica.",
    practicalAspects: "Protocolo de imagem: posicionar paciente em decubito dorsal, bracos ao lado do corpo (ou acima da cabeca para SPECT toracico); imagem planar de corpo inteiro em velocidade de varredura padronizada (10-15 cm/min) com calibracao de sensibilidade em cada sessao. SPECT/CT com 60-120 projecoes, 20-30 s por projecao, matriz 128x128 para 131I. Correcao de atenuacao obrigatoria (TC componente do SPECT/CT). ROIs desenhadas sobre: tumores identificaveis, figado, coracao, tireoide, corpo inteiro, fundo (background). Curvas atividade-tempo geradas para cada VOI (volume of interest) com ajuste de funcao exponencial. Software dosimetrico: OLINDA/EXM para calculo de dose absorvida por orgao (S-values); dosimetria voxelizada com PLANET Dose, MIM ou HERMES para mapas de dose 3D. Amostragem sanguinea: coleta em 4 timepoints (1h, 4-6h, 24h, 48h pos-injecao) em tubos heparinizados, pesagem precisa e contagem em poco gama calibrado para 131I (364 keV). Relatorio dosimetrico deve incluir: atividade administrada, timepoints de imagem, tempo de residencia por orgao/tumor, dose absorvida por orgao (Gy), dose a sangue/corpo inteiro, e recomendacao de atividade para ciclo terapeutico.",
    limitations: "A dosimetria com 131I-MIBG e intrinsecamente mais desafiadora que com 177Lu devido a alta energia gama do 131I (364 keV), que gera significativo scatter, penetracao septal e contaminacao de imagem, reduzindo a acuracia quantitativa. Imagens planares subestimam a atividade em lesoes profundas ou sobrepostas — SPECT/CT melhora a precisao mas requer tempo adicional de aquisicao e processamento. O metodo de sangue como proxy de dose medular tem incerteza significativa (tipicamente 20-30%) devido a simplificacoes do modelo. A dosimetria pre-terapeutica com dose tracadora pode nao refletir perfeitamente a farmacocinetica da dose terapeutica (efeito de dose sobre farmacocinetica, especialmente em tumores grandes com necrose central). Poucos centros realizam dosimetria de rotina para MIBG — a maioria utiliza doses empiricas fixas ou baseadas em peso. Em pediatria, a falta de phantoms especificos para todas as faixas etarias adiciona incerteza aos calculos dosimetricos. O investimento em tempo, equipamento (poco gama calibrado, software dosimetrico) e expertise limita a implementacao ampla.",
    reference: "Gear J, et al. EANM Dosimetry Committee SOP: dosimetry for 131I-mIBG treatment. Eur J Nucl Med Mol Imaging. 2020."
  },

  // ===============================================
  //  7. Radiossinoviortese
  // ===============================================
  {
    id: "rso-eanm-2022",
    title: "The EANM guideline for radiosynoviorthesis",
    year: "2022",
    society: "EANM",
    type: "Guideline",
    badges: ["essential"],
    category: "rso",
    categoryName: "Radiossinoviortese",
    categoryColor: "#06B6D4",
    scope: "Guideline europeu abrangente e atualizado para radiosinoviortese (RSO), terapia intra-articular com coloides radioativos para tratamento de sinovite cronica refrataria. A RSO e uma tecnica estabelecida ha mais de 60 anos que utiliza a fagocitose de particulas coloidais radiomarcadas pelos sinoviocitos inflamados, resultando em ablacao seletiva da membrana sinovial hiperplasica com preservacao da cartilagem articular subjacente. O documento cobre o espectro completo de indicacoes, desde a artrite reumatoide refrataria ate a artropatia hemofilica, passando pela sinovite vilonodular pigmentada recorrente e artrite psoriatica. A selecao do radionuclideo e baseada no tamanho articular: beta-emissores de alta energia e maior penetracao para articulacoes grandes, e emissores de menor energia e penetracao para articulacoes pequenas. O guideline integra evidencias de ensaios controlados, meta-analises e experiencia clinica acumulada na Europa, onde a RSO e amplamente praticada, diferentemente dos EUA e America Latina onde a disponibilidade e mais limitada.",
    indications: [
      "Artrite reumatoide com sinovite persistente em 1-3 articulacoes apesar de terapia sistemica otimizada (DMARDs convencionais e biologicos) e pelo menos 2 infiltracoes com corticoide intra-articular sem resposta duravel",
      "Artropatia hemofilica cronica com sinovite de repeticao e hemartrose recorrente — RSO como alternativa a sinovectomia cirurgica com menor risco de sangramento em pacientes com coagulopatia",
      "Sinovite vilonodular pigmentada (SVNP) recorrente apos sinovectomia cirurgica ou artroscopica, como tratamento adjuvante para reduzir recidiva",
      "Osteoartrite com componente sinovitico ativo demonstrado por US com Power Doppler (hipervascularidade sinovial grau 2-3) ou por fase de pool sanguineo em cintilografia ossea trifasica",
      "Artrite psoriatica com sinovite persistente localizada refrataria a tratamento sistemico",
      "Artrite reativa ou enteropatica com sinovite cronica monoarticular ou oligoarticular",
      "Condromatose sinovial como tratamento complementar pos-artroscopia",
      "Joelho: a articulacao mais frequentemente tratada (90Y); ombro, cotovelo, quadril e tornozelo (186Re); articulacoes metacarpofalangeanas, interfalangeanas e metatarsofalangeanas (169Er)",
      "Confirmacao de sinovite ativa: US com Power Doppler demonstrando hipervascularidade sinovial, ou cintilografia ossea trifasica com hipercaptacao na fase de pool sanguineo, ou RM com gadolinio mostrando realce sinovial"
    ],
    keyPoints: [
      "Selecao de radionuclideo por tamanho articular: 90Y (ítrio-90, beta puro, Emax 2,27 MeV, alcance maximo 11 mm, T1/2 2,7 dias) para articulacoes grandes (joelho); 186Re (renio-186, Emax 1,07 MeV, alcance maximo 3,6 mm, T1/2 3,7 dias) para articulacoes medias (ombro, cotovelo, quadril, punho, tornozelo); 169Er (erbio-169, Emax 0,34 MeV, alcance maximo 1,0 mm, T1/2 9,4 dias) para articulacoes pequenas (MCF, IFP, MTF)",
      "Atividades padrao recomendadas: 185 MBq (5 mCi) de 90Y para joelho; 74 MBq (2 mCi) de 186Re para articulacoes medias; 37 MBq (1 mCi) de 169Er para articulacoes pequenas (ajustar em criancas e adolescentes)",
      "Radiocoloides utilizados: 90Y-Citrato coloidal ou 90Y-Silicato, 186Re-Sulfeto coloidal, 169Er-Citrato coloidal; tamanho medio de particula 2-10 micrometros para garantir fagocitose pelos sinoviocitos e retencao intra-articular",
      "Confirmacao de posicionamento intra-articular: fluoroscopia com contraste iodado (artrograma previo a injecao) ou guia por ultrassonografia em tempo real; a verificacao e ESSENCIAL para evitar deposicao peri-articular ou em tecidos moles",
      "Tecnica de injecao: aspiracao de derrame articular previamente (quando presente), seguida de injecao do radiocoloide diluido em 0,5-2 mL de solucao, com flush de 0,5 mL de corticoide intra-articular (triancinolona 20-40 mg) e/ou SF para lavar a agulha e reduzir refluxo pelo trajeto",
      "Imobilizacao pos-injecao: manter a articulacao imobilizada (tala, ortese ou repouso funcional) por 48-72 horas para maximizar a retencao intra-articular e minimizar leak linfatico para linfonodos regionais",
      "Cintilografia de controle em 24h (imagem estatica da articulacao e linfonodos regionais) para verificar retencao intra-articular adequada (> 90%) e detectar leak extra-articular ou linfatico",
      "Leak extra-articular para linfonodos regionais (inguinais para joelho, axilares para ombro) ocorre em 3-5% dos procedimentos; geralmente sem consequencia clinica significativa, mas e indicador de tecnica subotima",
      "Eficacia: 60-80% de melhora clinica sustentada (reducao de dor e derrame) por 1-5 anos; resultados melhores quando a articulacao tem sinovite ativa predominante sem destruicao articular avancada (classificacao Larsen 0-III)",
      "Preditores de boa resposta: sinovite ativa ao US com Power Doppler, ausencia de destruicao articular radiografica avancada, duracao de doenca articular < 2 anos, ausencia de instabilidade ligamentar significativa",
      "Repeticao possivel apos 6 meses se resposta parcial ou recidiva de sinovite; ate 3 procedimentos na mesma articulacao sao aceitos; apos 2 RSO sem resposta, considerar sinovectomia cirurgica",
      "Dose de radiacao a cartilagem articular: estudos dosimetricos demonstram que com 185 MBq de 90Y no joelho, a dose a cartilagem e inferior a 1 Gy — considerada segura para cartilagem em condicao basal adequada",
      "Combinacao com corticoide intra-articular (triancinolona hexacetonida 20-40 mg) e pratica comum e pode potencializar o efeito anti-inflamatorio inicial enquanto o efeito da RSO se instala (2-6 semanas)",
      "Em artropatia hemofilica: administracao de fator de coagulacao deficiente ANTES do procedimento (manter nivel de fator > 50% por 48h); RSO e preferida sobre sinovectomia cirurgica pelo menor risco hemorragico",
      "Avaliacao de resposta em 3 e 6 meses pos-RSO: exame clinico (dor VAS, frequencia de derrame, amplitude de movimento), US articular com Power Doppler, e opcionalmente cintilografia ossea trifasica para documentar reducao de hiperemia sinovial",
      "Nao ha interacao medicamentosa com DMARDs biologicos (anti-TNF, anti-IL6, anti-CD20) — RSO pode ser realizada durante uso de terapia biologica sistemica sem necessidade de interrupcao"
    ],
    radiopharmaceuticals: "90Y-Citrato coloidal ou 90Y-Silicato: beta-emissor puro de alta energia (Emax 2,27 MeV; alcance maximo no tecido ~11 mm; T1/2 = 2,7 dias); ideal para joelho devido ao maior volume sinovial. 186Re-Sulfeto coloidal: beta-emissor de energia intermediaria (Emax 1,07 MeV; alcance ~3,6 mm; T1/2 = 3,7 dias) com emissao gama de 137 keV que permite imagem pos-dose para verificacao de retencao; adequado para articulacoes medias. 169Er-Citrato coloidal: beta-emissor de baixa energia (Emax 0,34 MeV; alcance ~1,0 mm; T1/2 = 9,4 dias); alcance muito curto minimiza irradiacao de cartilagem em articulacoes pequenas. Todos os radiocoloides tem tamanho de particula de 2-10 micrometros, otimizado para fagocitose pelos sinoviocitos tipo A (macrofagos sinoviais) com retencao na membrana sinovial.",
    practicalAspects: "Procedimento ambulatorial realizado em sala dedicada de medicina nuclear, com duracao tipica de 15-30 minutos. Avaliacao pre-procedimento: exame clinico articular, US com Power Doppler para confirmar sinovite ativa e mapear a articulacao, radiografia simples para avaliar grau de destruicao articular (classificacao de Larsen). Quando presente, aspirar derrame articular ANTES da injecao (reduz diluicao do radiocoloide e melhora retencao). Acesso articular guiado por fluoroscopia (com injecao previa de 0,5-1 mL de contraste iodado nao-ionico para confirmar posicao) ou por ultrassonografia em tempo real (preferido em muitos centros pela ausencia de radiacao e melhor visualizacao de tecidos moles). Agulha: 21-22G para joelho; 22-25G para articulacoes menores. Sequencia de injecao: radiocoloide (volume de 0,5-2 mL conforme articulacao), seguido de flush com 0,5-1 mL de corticoide (triancinolona hexacetonida 20-40 mg) e/ou SF para limpar a agulha. Movimentacao passiva suave da articulacao imediatamente apos para distribuicao uniforme do coloide na cavidade sinovial. Imobilizacao: tala gessada, ortese funcional ou repouso absoluto por 48-72 horas; deambulacao com auxiliar de marcha (muletas) para joelho. Cintilografia de controle em 24h com gama-camara (para 186Re — gama 137 keV) ou Bremsstrahlung (para 90Y); 169Er nao permite imagem de controle pratica. Avaliacao de resposta: 3 meses (precoce) e 6 meses (tardia) pos-procedimento com exame clinico e US articular. Orientacoes de radioprotecao: cuidados minimos necessarios (emissores beta de curto alcance), evitar contato intimo da articulacao tratada com gestantes/criancas por 48h.",
    limitations: "Contraindicado em gestacao e lactacao; em mulheres em idade fertil, realizar teste de gravidez e garantir contracepcao por 4-6 meses apos RSO com 90Y. Contraindicado em infeccao articular ativa (artrite septica) — excluir por aspiracao e cultura sinovial quando houver duvida. Ruptura de cisto popliteo (Baker) no joelho e contraindicacao relativa — risco de leak do radiocoloide para panturrilha. Leak extra-articular para linfonodos regionais ocorre em 3-5% dos procedimentos, geralmente sem consequencia clinica, mas indica tecnica subotima e pode reduzir eficacia. Disponibilidade de radiofarmacos para RSO varia significativamente entre paises — 90Y-Citrato e amplamente disponivel na Europa, mas acesso limitado nas Americas e em partes da Asia. Resultados dependem criticamente da selecao adequada do paciente: articulacoes com destruicao avancada (Larsen IV-V), instabilidade ligamentar grave ou anquilose parcial tem beneficio minimo. O procedimento nao reverte dano estrutural ja estabelecido (erosoes, perda de espaco articular) — seu papel e controlar a sinovite ativa e prevenir progressao. Em articulacoes profundas (quadril), o posicionamento intra-articular e mais desafiador e requer guia de imagem preciso (fluoroscopia preferida). A radiacao a epifises de crescimento em criancas e adolescentes deve ser cuidadosamente considerada, embora doses terapeuticas sejam consideradas seguras em pacientes com artropatia hemofilica.",
    reference: "Defined by EANM Committee. The EANM guideline for radiosynoviorthesis. Eur J Nucl Med Mol Imaging. 2022."
  },
'''

with open(target, 'a', encoding='utf-8') as f:
    f.write(content)

print("Batch C written: 6 guidelines (Osseas + MIBG + RSO)")
