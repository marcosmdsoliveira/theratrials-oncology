#!/usr/bin/env python3
"""
db_migracao_p0_2026_09.py — aplica os reparos P0 APROVADOS numa CÓPIA do Database.

Decisões humanas de 2026-09-28 (ASPEN, TROPION-Lung01, ANBL1531, KEYNOTE-158
endométrio, SINDAS). O ppgl_8 recebe a quarentena editorial por NEUTRALIZAÇÃO (opção B,
aprovada): mesmo uid, mesma categoria, conteúdo clínico trocado por um aviso;
só se aplica se o card publicado for exatamente o auditado (hash).

Disciplina (a mesma das migrações br_*):
  • trabalha em scripts/_db_copia/data.js, refeita a partir do publicado a cada
    execução; recusa escrever em assets/js/data.js;
  • cada troca confere o valor ATUAL exato; se divergir, nada é gravado;
  • idempotente (valor já novo = sem mudança);
  • serialização idêntica à do publicado (JSON compacto, UTF-8), diff mínimo;
  • nenhum uid muda; nenhum card entra ou sai;
  • cada troca gera uma linha de proveniência.

Saídas: scripts/_db_copia/data.js, scripts/_db_proveniencia_p0.jsonl,
scripts/_db_diff_p0.md.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import db_registro as R  # noqa: E402

COPIA_DIR = SCRIPTS / "_db_copia"
COPIA = COPIA_DIR / "data.js"
PROV = SCRIPTS / "_db_proveniencia_p0.jsonl"
DIFF = SCRIPTS / "_db_diff_p0.md"
DECISAO = "aprovada pelo usuário em 2026-09-28 (fechamento dos P0 conhecidos)"

PMC_ASPEN = "PMC6863151"
PMC_SINDAS = "PMC10248839"
PMC_ANBL09P1 = "PMC9150928"
SINDAS = f"PMID 35094066 · {PMC_SINDAS}"

# (uid, campo, anterior, novo, identificador, fonte, evidência, motivo, evidence_confidence, natureza)
MUDANCAS = [
    # ── ASPEN ────────────────────────────────────────────────────────────
    ("rcc_adjuvante_naocc_9", "nct", "NCT01185366", "NCT01108445", "NCT01108445 · PMID 26794930",
     "PubMed DataBank + abstract + CT.gov",
     "abstract: 'This study is registered with ClinicalTrials.gov, number NCT01108445'; DataBank do PMID "
     "26794930 = NCT01108445; CT.gov NCT01108445 tem a sigla ASPEN e cita o PMID; NCT01185366 é outro "
     "estudo (MD Anderson, TERMINATED, 73 participantes)",
     "NCT de outro estudo", "alta", "bibliográfica/factual"),
    ("rcc_adjuvante_naocc_9", "nct_url", "https://clinicaltrials.gov/study/NCT01185366",
     "https://clinicaltrials.gov/study/NCT01108445", "NCT01108445", "CT.gov", "segue o NCT",
     "NCT de outro estudo", "alta", "bibliográfica/factual"),
    ("rcc_adjuvante_naocc_9", "centros", "16 centros, 5 países", "17 centros (EUA, Canadá e Reino Unido)",
     f"PMID 26794930 · {PMC_ASPEN}", "publicação primária (texto completo, PMC)",
     "'We did this open-label, randomised trial at 17 centres in the USA, Canada, and the UK'",
     "valor do card sem fonte; a publicação dá 17 centros em 3 países (o registro lista 18 locais, não usado)",
     "alta", "bibliográfica/factual"),
    # ── TROPION-Lung01 ───────────────────────────────────────────────────
    ("tropion-lung01-dato-dxd-vs-docetaxel-nsclc", "nct", "NCT05215340", "NCT04656652",
     "NCT04656652 · PMID 39250535", "PubMed DataBank + CT.gov",
     "DataBank do PMID 39250535 = NCT04656652; NCT04656652[si] devolve o PMID; CT.gov NCT04656652 "
     "(TROPION-LUNG01) cita o PMID; NCT05215340 é o TROPION-Lung08",
     "NCT de outro estudo", "alta", "bibliográfica/factual"),
    ("tropion-lung01-dato-dxd-vs-docetaxel-nsclc", "nct_url", "https://clinicaltrials.gov/study/NCT05215340",
     "https://clinicaltrials.gov/study/NCT04656652", "NCT04656652", "CT.gov", "segue o NCT",
     "NCT de outro estudo", "alta", "bibliográfica/factual"),
    ("tropion-lung01-dato-dxd-vs-docetaxel-nsclc", "periodo", "Início 2022; análise primária 2023-2024",
     "Início dez/2020; análise primária 2023-2024", "NCT04656652", "CT.gov (registro correto)",
     "startDate 2020-12-21 no NCT04656652; o '2022' do card é o início do NCT05215340 (TROPION-Lung08)",
     "ano de início vindo do registro errado", "alta", "bibliográfica/factual"),
    # ── ANBL1531 ─────────────────────────────────────────────────────────
    ("neuroblastoma_3", "pubmed_url", "https://pubmed.ncbi.nlm.nih.gov/34028986/", "", "PMID 34028986",
     "convenção do banco para ensaio sem publicação de resultado",
     "34028986 é o relato do piloto ANBL09P1 (NCT01175356), card neuroblastoma_2; NCT03126916 está "
     "RECRUITING, sem resultados", "PMID emprestado de outro estudo", "alta", "bibliográfica/factual"),
    ("neuroblastoma_3", "titulo_full",
     "A safety and feasibility trial of (131) I-MIBG in newly diagnosed high-risk neuroblastoma: A Children's "
     "Oncology Group study",
     "A Phase 3 Study of 131I-Metaiodobenzylguanidine (131I-MIBG) or ALK Inhibitor Therapy Added to Intensive "
     "Therapy for Children With Newly Diagnosed High-Risk Neuroblastoma (NBL)", "NCT03126916",
     "CT.gov officialTitle", "card de desenho usa o título oficial do registro",
     "título copiado do artigo de outro estudo", "alta", "bibliográfica/factual"),
    ("neuroblastoma_3", "periodo", "2017 - em recrutamento ativo", "2018 - em recrutamento ativo", "NCT03126916",
     "CT.gov", "startDate 2018-05-14", "início divergente do registro", "alta", "bibliográfica/factual"),
    ("neuroblastoma_3", "limit", "Recrutamento longo (>9 anos); resultados aguardados.",
     "Recrutamento longo (desde mai/2018); resultados aguardados.", "NCT03126916", "CT.gov",
     "de mai/2018 a set/2026 são ~8 anos; '>9 anos' partia do início 2017",
     "consequência direta da correção do início", "alta", "bibliográfica/factual"),
    ("neuroblastoma_3", "impacto_reg",
     "Estudo registracional para avaliar papel do 131I-MIBG em primeira linha em NB de alto risco. Resultado "
     "esperado em 2026-2027 pode mudar prática global.",
     "Estudo registracional para avaliar papel do 131I-MIBG em primeira linha em NB de alto risco. Conclusão "
     "primária estimada no registro: 30/09/2030.", "NCT03126916", "CT.gov",
     "primaryCompletionDate 2030-09-30 (ESTIMATED)", "previsão de resultado sem fonte, contrária ao registro",
     "alta", "clínica"),
    ("neuroblastoma_3", "takehome",
     "Estudo registracional do papel do 131I-MIBG em 1ª linha; resultado esperado em 2026-2027 pode mudar a "
     "prática global.",
     "Estudo registracional do papel do 131I-MIBG em 1ª linha; conclusão primária estimada no registro para "
     "30/09/2030.", "NCT03126916", "CT.gov", "primaryCompletionDate 2030-09-30 (ESTIMATED)",
     "mesma previsão sem fonte do impacto_reg, repetida no takehome", "alta", "clínica"),
    # ── KEYNOTE-158 endométrio: passa a representar a atualização 2025 ─────
    ("endometrio_6", "pubmed_url", "https://pubmed.ncbi.nlm.nih.gov/34843401/",
     "https://pubmed.ncbi.nlm.nih.gov/39847999/", "PMID 39847999 · DOI 10.1016/j.ygyno.2024.12.020",
     "PubMed", "34843401 é o ZENITH20-2 (poziotinib, NSCLC, NCT03318939). O card representa a atualização "
     "39847999 (Gynecol Oncol 2025;193:130-135), fonte de n=94, ORR 50%, CR 16%, DOR 4 anos 66%",
     "PMID de outro estudo; representação decidida: atualização 2025", "alta", "bibliográfica/factual"),
    ("endometrio_6", "titulo_full",
     "Poziotinib in Non-Small-Cell Lung Cancer Harboring HER2 Exon 20 Insertion Mutations After Prior Therapies: "
     "ZENITH20-2 Trial",
     "Pembrolizumab in microsatellite instability-high/mismatch repair deficient (MSI-H/dMMR) and "
     "non-MSI-H/non-dMMR advanced endometrial cancer: Phase 2 KEYNOTE-158 study results",
     "PMID 39847999", "PubMed", "título do PubMed", "título copiado do artigo errado", "alta",
     "bibliográfica/factual"),
    ("endometrio_6", "ano_pub", 2022, 2025, "PMID 39847999", "PubMed", "Gynecol Oncol 2025;193:130-135",
     "ano da publicação representada", "alta", "bibliográfica/factual"),
    ("endometrio_6", "ref",
     "O'Malley DM et al. J Clin Oncol 2022;40:752-761; atualização: Gynecol Oncol 2024 (PMID 39847999), ORR "
     "50%/CR 16% (n=94).",
     "O'Malley DM, Bariani GM, Cassier PA, Marabelle A, et al. Gynecol Oncol 2025;193:130-135 (atualização; "
     "PMID 39847999). Publicação primária anterior: O'Malley DM, et al. J Clin Oncol 2022;40:752-761 "
     "(PMID 34990208).", "PMID 39847999 · PMID 34990208", "PubMed",
     "citações conferidas no PubMed; o ano da atualização é 2025, não 2024",
     "representação decidida: atualização 2025; a primária de 2022 fica registrada", "alta",
     "bibliográfica/factual"),
    ("endometrio_6", "primario",
     "dMMR/MSI-H: ORR 50% (CR 16%); mDOR não atingida (JCO 2022); DOR em 4 anos 66% (atualização 2024). "
     "Pembrolizumabe monoterapia em endométrio dMMR avançado.",
     "MSI-H/dMMR (n=94): ORR 50% (IC95% 40%-61%); CR 16%; DOR estimada em 4 anos 66%. Pembrolizumabe "
     "monoterapia em endométrio dMMR avançado.", "PMID 39847999", "abstract da atualização",
     "'The ORR (95 % CI) was 50 % (40 %-61 %) in the MSI-H/dMMR group; 15 patients (16 %) experienced a "
     "complete response … The estimated 4-year DOR rates were 66 %'",
     "misturava a mDOR de 2022 com os números de 2025; a atualização não informa mediana de DOR",
     "alta", "clínica"),
    ("endometrio_6", "resultado_chave", "dMMR/MSI-H: ORR 50% (CR 16%) · mDOR não atingida · DOR em 4 anos 66%",
     "MSI-H/dMMR: ORR 50% (CR 16%) · DOR estimada em 4 anos 66%", "PMID 39847999", "abstract da atualização",
     "números do primario", "misturava 2022 e 2025", "alta", "clínica"),
    # ── SINDAS (versão final após a microauditoria do texto completo) ──
    ("rt_sbrt_oligo_5", "esquema",
     "SBRT: 25-50 Gy em 5 frações a todas as lesões. TKI (gefitinib, erlotinib ou icotinib) contínuo.",
     "RT: 25-40 Gy em 5 frações (conforme tamanho e localização) a todas as metástases e ao tumor primário/"
     "linfonodos regionais acometidos. TKI de 1ª geração (gefitinib, erlotinib ou icotinib) contínuo.",
     SINDAS, "publicação primária",
     "'randomization was between no RT vs RT (25-40 Gy in 5 fractions depending on tumor size and location) to "
     "all metastases and the primary tumor/involved regional lymphatics'; 'All patients received a "
     "first-generation TKI'", "dose do card (25-50 Gy) diverge da publicação", "alta", "clínica"),
    ("rt_sbrt_oligo_5", "primario",
     "PFS: 20,2 m (SBRT + TKI) vs 12,5 m (TKI); HR 0,618 (IC 95% 0,395-0,970; p<0,001). OS: 25,5 m (SBRT + "
     "TKI) vs 17,4 m (TKI); p<0,001.",
     "Desfecho primário: PFS. Comparação planejada da PFS em 6 meses: 95,2% (TKI) vs 99,1% (TKI + RT); P>0,05. "
     "PFS mediana: 12,5 m (TKI) vs 20,2 m (TKI + RT); P<0,001.",
     SINDAS, "abstract + texto (Endpoints, Results)",
     "'The primary endpoint was PFS'; 'the protocol-specified analysis was a comparison of the 6-month PFS rates'; 'The "
     "respective 6-month PFS was 95.2% … vs 99.1% … (P > .05)'; 'median PFS was 12.5 months vs 20.2 months "
     "(P < .001)' (TKI only vs TKI with RT). HR 0,618/IC 0,395-0,970 não aparece na publicação (o texto traz "
     "HR 0,22 para a PFS): removido, sem reconciliar. OS passa para secundario (desfecho secundário na publicação)",
     "HR sem fonte; OS registrada como primária", "alta", "clínica"),
    ("rt_sbrt_oligo_5", "resultado_chave", "mPFS 20,2 vs 12,5 m · HR 0,618 (p<0,001) · mOS 25,5 vs 17,4 m (p<0,001)",
     "mPFS 20,2 m (TKI + RT) vs 12,5 m (TKI); p<0,001 · PFS em 6 meses sem diferença (P>0,05)", SINDAS, "abstract + texto (Results)",
     "resumo do desfecho primário (PFS): 'median PFS was 12.5 months vs 20.2 months (P < .001)'; 'The "
     "respective 6-month PFS was 95.2% … vs 99.1% … (P > .05)'. OS é secundária (e o braço só-TKI está em "
     "WITHIN_SOURCE_CONFLICT): fica em secundario, não no resumo",
     "HR sem fonte; resumo destacava desfecho secundário", "alta", "clínica"),
    ("rt_sbrt_oligo_5", "tox_g3", "Esofagite G3: 3%; pneumonite G2-3: 4,5%. Sem G4/G5.",
     "Pneumonite sintomática grau 3-4: 4/68 (5,9%; 6% no resumo) no braço TKI + RT; incluindo a "
     "assintomática, pneumonite grau 3-4 em 5/68 (7,4%). Nenhum evento grau 5.", SINDAS,
     "abstract + Tabela 3 + texto",
     "Tabela 3 (toxicidades relacionadas ao tratamento), TKI + RT: pneumonite sintomática grau 3 = 3 (4,4%), "
     "grau 4 = 1 (1,5%) → 4/68; assintomática grau 3 = 1 (1,5%) → total 5/68 = '5 of 68 (7.4%) experienced "
     "grade 3-4 pneumonitis'; abstract '6% rate of symptomatic grade 3-4'; 'No patient experienced grade 5 "
     "events'. Divergência EXPLICADA (conflito:rt_sbrt_oligo_5:pneumonite_g34): medidas diferentes",
     "toxicidade do card diverge da publicação ('Sem G4' era falso)", "alta", "clínica"),
    ("rt_sbrt_oligo_5", "tox_interesse",
     "Toxicidade aceitável. Pneumonite por radiação G2 em ~7,5%, mas manejável. Sem interrupção prolongada de TKI.",
     "Pneumonite no braço TKI + RT (detalhes em tox_g3); nenhum evento grau 5.", SINDAS, "texto",
     "'~7,5%' de pneumonite G2 e 'sem interrupção prolongada de TKI' não aparecem na publicação",
     "números sem fonte", "alta", "clínica"),
    # adicionais: afirmações contraditas ou ausentes na publicação
    ("rt_sbrt_oligo_5", "desenho",
     "Randomização 1:1 a TKI EGFR (1ª ou 2ª geração) + SBRT a todas as mets vs TKI isolado em pacientes com "
     "NSCLC EGFR+ oligometastático (≤5 mets).",
     "Randomização 1:1, aberta, a TKI de 1ª geração + RT a todas as lesões vs TKI isolado em NSCLC "
     "EGFR-mutante oligometastático síncrono (≤5 metástases; ≤2 por órgão), sem metástases cerebrais.",
     SINDAS, "texto (Methods)", "'All patients received a first-generation TKI'; '≤5 metastases; ≤2 lesions in any "
     "one organ … without brain metastases'; 'the randomization was not masked'",
     "a publicação usa só TKI de 1ª geração", "alta", "clínica"),
    ("rt_sbrt_oligo_5", "comparador", "TKI EGFR isolado (1ª/2ª geração) — gefitinib/erlotinib/icotinib.",
     "TKI de 1ª geração isolado — gefitinib, erlotinib ou icotinib.", SINDAS, "texto (Methods)",
     "'All patients received a first-generation TKI (gefitinib …, erlotinib …, or icotinib …)'",
     "a publicação usa só TKI de 1ª geração", "alta", "clínica"),
    ("rt_sbrt_oligo_5", "incl",
     "NSCLC histologicamente confirmado; mutação EGFR (del19 ou L858R); ≤5 mets extracraniais; ECOG 0-1; não "
     "tratado previamente para doença metastática.",
     "Adenocarcinoma EGFR-mutante (deleção do éxon 19 ou mutação do éxon 21) comprovado por biópsia; "
     "oligometástases síncronas (≤5; ≤2 por órgão), sem metástases cerebrais; Zubrod 0-2; 18-75 anos; sem "
     "tratamento prévio.", SINDAS, "texto (Patients)",
     "'aged 18 years and older and 75 years or younger with a Zubrod performance status of 0-2'; 'biopsy-proven "
     "EGFRm adenocarcinoma (defined as any deletion in exon 19 or any mutation in exon 21…)'",
     "ECOG 0-1 do card contradiz a publicação (Zubrod 0-2)", "alta", "clínica"),
    ("rt_sbrt_oligo_5", "estrat", "Tipo de mutação EGFR (del19 vs L858R); número de mets (1-2 vs 3-5).",
     "Minimização (Pocock e Simon) por 7 covariáveis: idade ≤63 vs >63 anos, sexo, Zubrod 0 vs 1-2, nº de "
     "metástases 1-2 vs 3-5, T1-2 vs T3-4, N1 vs N2-3, éxon 19 vs 21.", SINDAS, "texto (Randomization)",
     "'methods of Pocock and Simon (8) to dynamically balance for 7 prognostic covariates (…)'",
     "card listava 2 dos 7 fatores", "alta", "clínica"),
    ("rt_sbrt_oligo_5", "basal", "Mediana 57a; 62% feminino; del19 em 55%; adenocarcinoma em 100%; mediana de 3 mets.",
     "Idade média 63 (TKI) e 67 anos (TKI + RT); sexo feminino 60% e 63%; EGFR éxon 19 em 69% (92/133); "
     "adenocarcinoma em todos (critério de inclusão).", SINDAS, "Tabela 1 + texto",
     "Tabela 1: 'Age, y Mean (SD) 63 (11) 67 (10)'; 'Female 39 (60.0) 43 (63.2)'; texto: 'The most common EGFR "
     "abnormality was in exon 19 (92 of 133 [69.2%])'",
     "idade ('mediana 57a') e del19 (55%) contraditos pela Tabela 1; 'mediana de 3 mets' não relatada",
     "alta", "clínica"),
    ("rt_sbrt_oligo_5", "estatistica", "Endpoint primário: PFS. Poder 80%, HR alvo 0,60. α 0,05.",
     "Desfecho primário: PFS. Planejados 200 pacientes (poder de 80%, α bilateral de 0,05) para detectar aumento "
     "da PFS em 6 meses de 75% para 90%. Análise interina pré-especificada a 68% do recrutamento.", SINDAS,
     "texto (Endpoints)", "'increase the 6-month PFS from 75% with TKI only (5) to 90%. … 200 patients to achieve "
     "a power of 80% with a 2-sided α of .05. The protocol prespecified an interim analysis when 68% of accrual'",
     "'HR alvo 0,60' não existe na publicação", "alta", "clínica"),
    ("rt_sbrt_oligo_5", "secundario",
     "ORR: 90% vs 74%. DCR: 97% vs 91%. Tempo até novo sítio de progressão: significativamente mais longo com SBRT.",
     "Desfechos secundários: OS e segurança/toxicidade (ver tox_g3). OS mediana: 25,5 m (TKI + RT); braço TKI: "
     "17,4 m no resumo vs 17,6 m (IC 95% 15,4-19,8) no texto de resultados — divergência dentro da própria "
     "publicação, sem valor único; P<0,001. Taxa de resposta não relatada.",
     SINDAS, "abstract + texto (Endpoints, Results)",
     "'secondary endpoints were OS … and safety'; OS: abstract '17.4 months vs 25.5 months'; Results '17.6 months "
     "(95% CI = 15.4 to 19.8 months) vs 25.5 months' — mesma população (TKI only, n=65), endpoint, timepoint e "
     "método: WITHIN_SOURCE_CONFLICT (conflito:rt_sbrt_oligo_5:os_tki); nenhum dos dois é apresentado como "
     "fato. ORR/DCR não aparecem na publicação",
     "ORR, DCR e 'tempo até novo sítio' sem fonte; conflito interno na OS do braço só-TKI", "alta", "clínica"),
    ("rt_sbrt_oligo_5", "subgrupo",
     "Benefício consistente em del19 e L858R. Pacientes com ≤3 mets tiveram maior benefício numérico.",
     "Sem análise de subgrupo relatada; os autores declaram que o estudo não tinha poder para análise "
     "estratificada pelo tipo de mutação EGFR.", SINDAS, "texto (Discussion)",
     "'nor was it powered for a stratified analysis based on the particular type of EGFR mutation'",
     "afirmações de subgrupo sem fonte", "alta", "clínica"),
    ("rt_sbrt_oligo_5", "cumul", "BED10 37,5-100 Gy conforme dose e sítio",
     "—", SINDAS, "decisão editorial",
     "a publicação não relata BED; um BED10 derivado depende de α/β e não tem semântica própria no campo. A "
     "dose real (25-40 Gy em 5 frações) fica em esquema. O limite de 100 Gy vinha da dose de 50 Gy, que a "
     "publicação não usa", "BED sem fonte", "alta", "clínica"),
    ("rt_sbrt_oligo_5", "limit",
     "TKI 1ª/2ª geração (não osimertinib). Monocêntrico dominante. Definição de oligometastático sem PET-FDG "
     "mandatório. Sem dados com IO ou 3ª geração TKI.",
     "Análise interina pré-especificada (68% do recrutamento: 133 de 200 pacientes planejados); por resultados "
     "positivos de eficácia, o comitê de ética recomendou encerrar o recrutamento; seguimento mediano de 23,6 "
     "meses. A PFS em 6 meses, base do cálculo amostral e citada na discussão como desfecho primário, não "
     "diferiu (P>0,05); a conclusão apoia-se nas medianas de PFS e OS. TKI de 1ª geração (sem osimertinib). PET "
     "não obrigatório para definir oligometástase. Sem dados com IO ou TKI de 3ª geração.", SINDAS, "texto",
     "'prespecified an interim analysis when 68% of accrual'; 'the ethics committee did not recommend further "
     "recruitment'; 'The median follow-up was 23.6 months'; 'The primary endpoint of this trial was 6-month "
     "PFS, but there were too few progression or death events'; '6-month PFS … P > .05'; 'PET was "
     "encouraged'; '5 participating centers' (o 'monocêntrico dominante' não tem fonte)",
     "maturidade e encerramento antecipado ausentes; geração de TKI errada", "alta", "clínica"),
]


# ── ppgl_8: quarentena editorial por neutralização (opção B) ────────────────
PPGL8_SHA = "9fc27a988e11f39f832066a2eceb22f79aba3473b0c814b449697fe17d8e427a"   # card auditado
AVISO = "Em revisão editorial — conteúdo temporariamente retirado até verificação das fontes primárias."
NEUTRALIZAR = {
    "estudo": "MGMT em PPGL — em revisão editorial",
    "acron": "MGMT em PPGL — em revisão editorial",
    "titulo_full": "", "pubmed_url": "", "ano_pub": 0, "status": "Em revisão editorial",
    "ref": "Em revisão editorial — referências em verificação.",
    "indicacao": AVISO, "desenho": AVISO, "primario": AVISO,
    **{c: "—" for c in ("nct", "sponsor", "fase", "centros", "periodo", "incl", "excl", "estrat", "basal", "n",
                        "molecular", "biomarc", "radiofarmaco", "esquema", "cumul", "comparador", "estatistica",
                        "analises", "secundario", "subgrupo", "tox_g3", "tox_interesse", "impacto_reg", "limit")},
}
PRESERVAR = ("uid", "category_id", "category_name", "category_short", "category_color", "nct_url", "preparo")


def neutralizar_ppgl8(card: dict) -> list[tuple]:
    import hashlib
    sha = hashlib.sha256(json.dumps(card, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    if sha != PPGL8_SHA:
        raise ValueError("ppgl_8 publicado difere do card auditado — nada gravado")
    trocas = []
    for campo, novo in NEUTRALIZAR.items():
        if card.get(campo) != novo:
            trocas.append((campo, card.get(campo), novo))
            card[campo] = novo
    return trocas


def carregar(caminho: Path) -> tuple[str, dict, str]:
    texto = caminho.read_text(encoding="utf-8")
    m = re.search(r"window\.THERA_DATA\s*=\s*", texto)
    corpo = texto[m.end():].rstrip()
    fim = texto[m.end() + len(corpo):]
    if corpo.endswith(";"):
        corpo, fim = corpo[:-1], ";" + fim
    return texto[:m.end()], json.loads(corpo), fim


def serializar(prefixo: str, dados: dict, fim: str) -> str:
    return prefixo + json.dumps(dados, ensure_ascii=False, separators=(",", ":")) + fim


def main() -> int:
    if COPIA.resolve() == R.DATA_JS.resolve():
        print("recusado: o alvo é o banco publicado", file=sys.stderr)
        return 2
    COPIA_DIR.mkdir(exist_ok=True)
    shutil.copyfile(R.DATA_JS, COPIA)                       # cópia fresca a cada execução
    prefixo, dados, fim = carregar(COPIA)
    assert serializar(prefixo, dados, fim) == COPIA.read_text(encoding="utf-8"), "serialização não é idêntica"
    uids_antes = [s["uid"] for s in dados["studies"]]
    por_uid = {s["uid"]: s for s in dados["studies"]}
    erros, prov, aplicadas = [], [], []
    for uid, campo, antes, depois, ident, fonte, evid, motivo, conf, nat in MUDANCAS:
        card = por_uid.get(uid)
        if card is None:
            erros.append(f"{uid}: card inexistente")
            continue
        atual = card.get(campo)
        if atual == depois:
            continue
        if atual != antes:
            erros.append(f"{uid}.{campo}: valor atual diferente do esperado — {str(atual)[:80]!r}")
            continue
        card[campo] = depois
        aplicadas.append((uid, campo, antes, depois))
        prov.append({"uid": uid, "campo": campo, "anterior": antes, "novo": depois, "identificador": ident,
                     "fonte": fonte, "evidencia": evid, "motivo": motivo, "evidence_confidence": conf,
                     "natureza": nat, "decisao_humana": DECISAO, "arquivo": "cópia (scripts/_db_copia/data.js)"})
    q = por_uid.get("ppgl_8")
    if q is not None and q.get("status") != NEUTRALIZAR["status"]:
        try:
            for campo, antes, depois in neutralizar_ppgl8(q):
                aplicadas.append(("ppgl_8", campo, antes, depois))
                prov.append({"uid": "ppgl_8", "campo": campo, "anterior": antes, "novo": depois,
                             "identificador": "quarentena:ppgl_8", "fonte": "decisão editorial",
                             "evidencia": "referências do card não sustentam o conteúdo: PMID 24752622 é o Hadoux "
                                          "2014 (card ppgl_7); 'Int J Mol Sci 2020;21(4):1273' resolve para artigo "
                                          "de meningioma (PMID 32070062); Niemeijer 2014 é meta-análise de CVD "
                                          "sem MGMT",
                             "motivo": "quarentena editorial (opção B): conteúdo clínico sem fonte primária "
                                       "verificável; uid e categoria preservados",
                             "evidence_confidence": "alta", "natureza": "editorial",
                             "decisao_humana": DECISAO, "arquivo": "cópia (scripts/_db_copia/data.js)"})
        except ValueError as e:
            erros.append(str(e))
    if erros:
        print("NADA GRAVADO:\n  " + "\n  ".join(erros), file=sys.stderr)
        COPIA.unlink()
        return 1
    # Registro bibliográfico: a primária anterior do KEYNOTE-158 fica na história.
    prov.append({"uid": "endometrio_6", "campo": "(registro bibliográfico)", "anterior": None,
                 "novo": {"publicacao_representada": "39847999", "relacao": "follow_up",
                          "publicacao_primaria_anterior": "34990208"},
                 "identificador": "PMID 39847999 · PMID 34990208 · NCT02628067", "fonte": "PubMed",
                 "evidencia": "34990208 (J Clin Oncol 2022;40:752-761) permanece ligada ao NCT02628067 no "
                              "registro de identidade como primary_publication", "motivo": "preservar a história "
                 "bibliográfica", "evidence_confidence": "alta", "natureza": "bibliográfica/factual",
                 "decisao_humana": DECISAO, "arquivo": "registro (db_decisoes.json)"})
    assert [s["uid"] for s in dados["studies"]] == uids_antes, "uid mudou"
    COPIA.write_text(serializar(prefixo, dados, fim), encoding="utf-8")
    R.gravar(PROV, "\n".join(json.dumps(p, ensure_ascii=False) for p in prov) + "\n")
    L = ["# Diff campo a campo — cópia do Database (scripts/_db_copia/data.js)", "",
         f"{len(aplicadas)} campos em {len({a[0] for a in aplicadas})} cards. Nenhum uid mudou; nenhum card "
         "entrou ou saiu. Nada aplicado a assets/js/data.js.", ""]
    for uid in dict.fromkeys(a[0] for a in aplicadas):
        L += [f"## `{uid}` — {por_uid[uid]['estudo']}", ""]
        for u, campo, antes, depois in aplicadas:
            if u == uid:
                p = next(x for x in prov if x["uid"] == u and x["campo"] == campo)
                L += [f"**{campo}** · {p['natureza']} · confiança {p['evidence_confidence']} · {p['identificador']}",
                      f"- antes: {antes!r}", f"- depois: {depois!r}", f"- evidência: {p['evidencia']}", ""]
    DIFF.write_text("\n".join(L), encoding="utf-8")
    print(json.dumps({"campos": len(aplicadas), "cards": sorted({a[0] for a in aplicadas}),
                      "proveniencia": len(prov)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
