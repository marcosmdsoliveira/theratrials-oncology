#!/usr/bin/env python3
"""
db_migracao_integridade_2026_09b.py — correção de integridade de ASPEN e TROPION-Lung01.

Origem: candidatos confirmados no piloto v2.1, reauditados contra a fonte primária e aprovados pelo editor em
2026-09-29 (ASPEN com `basal` reescrito só com números da publicação).

    python3 scripts/db_migracao_integridade_2026_09b.py            # gera a CÓPIA scripts/_db_copia/data.js
    python3 scripts/db_migracao_integridade_2026_09b.py --aplicar  # promove a cópia validada a assets/js/data.js

Disciplina (a mesma de db_migracao_p0_2026_09.py): o banco de origem tem de ter exatamente o SHA-256 esperado
(outro arquivo é recusado); cada troca confere o valor ATUAL exato (se divergir, nada é gravado); só estes dois
cards podem mudar; nenhum uid muda; serialização idêntica; cada troca gera proveniência com trecho literal da fonte.
Idempotente: com o banco já corrigido, não faz nada. `--aplicar` só copia se a cópia tiver o SHA final esperado.
Depois de aplicar: `node scripts/export_app_data.mjs` regenera app-data/.

Saídas: scripts/_db_copia/data.js, scripts/_db_proveniencia_integridade.jsonl, scripts/_db_diff_integridade.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import db_registro as R  # noqa: E402

COPIA_DIR = SCRIPTS / "_db_copia"
COPIA = COPIA_DIR / "data.js"
PROV = SCRIPTS / "_db_proveniencia_integridade.jsonl"
DIFF = SCRIPTS / "_db_diff_integridade.md"
DECISAO = "aprovado pelo editor em 2026-09-29 (ASPEN: basal só com números da publicação; TROPION integral)"
CARDS = {"rcc_adjuvante_naocc_9", "tropion-lung01-dato-dxd-vs-docetaxel-nsclc"}
SHA_ORIGEM = "cd4bd842ae1c617dd0587a5bf1d61ea873a6aac20232585b28826d2d043ec769"
SHA_FINAL = "e542ba1f73daef63faa683463bf4ce08a21b6fd14bc33b621beef5f691b51b99"

# (uid, campo, anterior EXATO, novo, identificador, locator, evidência literal, motivo, confiança, natureza, derivado)
MUDANCAS = [('rcc_adjuvante_naocc_9',
  'comparador',
  'Everolimus (vs sunitinibe)',
  'Sunitinibe 50 mg/d VO, 4 semanas com / 2 sem tratamento (grupo de referência do HR; a hipótese testada era a '
  'superioridade do everolimus)',
  'PMID 26794930 · PMC6863151',
  'Methods (Statistical analysis)',
  'the alternative hypothesis was that everolimus would cause a 60% improvement in median progression-free survival '
  'from 6 ⋅ 0 months to 9⋅6 months in the sunitinib and everolimus groups, respectively, compared with sunitinib (HR '
  '0⋅625) … In all multivariable analyses, the reference group was sunitinib',
  'o card trazia o everolimus como comparador; pela hipótese e pela análise, o sunitinibe é a referência',
  'alta',
  'clínica',
  False),
 ('rcc_adjuvante_naocc_9',
  'estatistica',
  'Primário PFS. Poder 80% para HR 0,67.',
  'Primário: PFS (ITT; log-rank bilateral estratificado). Hipótese: superioridade do everolimus (HR 0,625; mediana '
  '6,0 → 9,6 m). α bilateral 0,20 (fase 2), poder 83% para 90 eventos; análise final com 87 eventos (poder 82%). α '
  'dos secundários de eficácia: 0,05.',
  'PMID 26794930 · PMC6863151',
  'Methods (Statistical analysis)',
  'Using a two-sided type I error rate of 0⋅20, we estimated that 90 progression-free survival events would allow us '
  'to detect this difference in progression with 83% power … the final analysis was done once 87 events were '
  'recorded because of funding issues … (82%) … The prespecified type I error rate for secondary efficacy analyses '
  'was 0⋅05',
  "card dizia 'Poder 80% para HR 0,67'; o plano era HR 0,625, poder 83% e α bilateral 0,20",
  'alta',
  'clínica',
  False),
 ('rcc_adjuvante_naocc_9',
  'primario',
  'mPFS sunitinibe 8,3 vs everolimus 5,6 m (HR 1,41 a favor de sunitinibe; IC 80% 1,03-1,92; p=0,16 — NS, mas '
  'tendência clara). ORR suni 18% vs everol 9%.',
  'PFS mediana (investigador, ITT): sunitinibe 8,3 m (IC 80% 5,8–11,4) vs everolimus 5,6 m (IC 80% 5,5–6,0); HR 1,41 '
  '(IC 80% 1,03–1,92; sunitinibe como referência); p=0,16 — atingiu o nível de significância pré-especificado (α '
  'bilateral 0,20), a favor do sunitinibe, no sentido oposto ao da hipótese.',
  'PMID 26794930 · PMC6863151',
  'Results',
  'Median progression-free survival was 8⋅3 months (80% CI 5⋅8–11⋅4) for sunitinib and 5⋅6 months (5⋅5–6⋅0) for '
  'everolimus (HR 1⋅41 [80% CI 1⋅03–1⋅92]; p=0⋅16; figure 2; table 2), meeting the prespecified level of statistical '
  'significance for the study (two-sided type I error rate of 0⋅20)',
  "o card dizia 'p=0,16 — NS, mas tendência clara'; com α bilateral 0,20 pré-especificado, p=0,16 é significativo (a "
  'publicação o declara)',
  'alta',
  'clínica',
  False),
 ('rcc_adjuvante_naocc_9',
  'secundario',
  'mOS sunitinibe 31,5 vs everolimus 13,2 m (HR 1,12; NS no longo prazo). Papilar: PFS sunitinibe melhor; '
  'chromophobe: sem diferença.',
  'OS mediana: sunitinibe 31,5 m (IC 95% 14,8–não atingido) vs everolimus 13,2 m (IC 95% 9,7–37,9); HR 1,12 (IC 95% '
  '0,7–2,1); p=0,60 — sem diferença (α 0,05 para secundários). ORR (RECIST 1.1, investigador): sunitinibe 18% (9/51) '
  'vs everolimus 9% (5/57; a publicação lista 2 RC + 4 RP para o everolimus — inconsistência interna).',
  'PMID 26794930 · PMC6863151',
  'Results',
  'Overall survival was not different between the two treatment groups (HR 1⋅12 [95% CI 0⋅7–2⋅1]; p=0⋅60 … Median '
  'overall survival was 13⋅2 months (95% CI 9⋅7–37⋅9) in the everolimus group and 31⋅5 months (14⋅8-not reached) in '
  'the sunitinib group … in five (9% [1–16]) of 57 evaluable patients who were treated with everolimus (two patients '
  'had a complete response and four patients had a partial response',
  "'NS no longo prazo' sem fonte (não há análise de longo prazo); afirmações de subgrupo movidas para 'subgrupo'; "
  'ORR sai do primário',
  'alta',
  'clínica',
  False),
 ('rcc_adjuvante_naocc_9',
  'subgrupo',
  'Sunitinibe superior em papilar e indiferenciado; sem diferença em chromophobe (subgrupo pequeno).',
  'Descritivo, sem teste de interação (baixo poder): PFS mediana mais longa com sunitinibe nos subtipos papilífero e '
  'não classificado e mais longa com everolimus no cromófobo; por risco MSKCC, sunitinibe favorável nos riscos '
  'favorável/intermediário e everolimus no risco desfavorável.',
  'PMID 26794930 · PMC6863151',
  'Results / Discussion',
  'two subtypes in which sunitinib was associated with a longer median progression-free survival than that '
  'associated with everolimus (papillary and unclassified) and one subtype (chromophobe) in which everolimus was '
  'associated with a longer median progression-free survival than that of sunitinib … median progression-free '
  'survival was longer with first-line sunitinib than with everolimus in patients with non-clear-cell renal cell '
  'carcinoma who had been rated as good or intermediate risk according to MSKCC criteria, whereas median '
  'progression-free survival was longer for patients rated as poor risk treated with everolimus',
  "o card dizia 'sem diferença em chromophobe'; a fonte relata PFS mais longa com everolimus no cromófobo",
  'alta',
  'clínica',
  False),
 ('rcc_adjuvante_naocc_9',
  'tox_g3',
  'TRAEs ≥G3: sunitinibe 63%, everolimus 47%. Suni: HFS, fadiga, hipertensão; everolimus: hiperglicemia, mucosite, '
  'anemia.',
  'EA grau ≥3 relacionados: sunitinibe 78% (40/51) vs everolimus 60% (34/57); sem óbitos relacionados. Sunitinibe: '
  'hipertensão G3-4 24%, diarreia G3 10%, síndrome mão-pé G3-4 8%, fadiga G3 4%. Everolimus: pneumonite G3-4 9%, '
  'fadiga G3 7%.',
  'PMID 26794930 · PMC6863151',
  'Results (Toxic effects)',
  'Overall, 40 (78%) patients receiving sunitinib had grade 3 or worse treatment-related adverse event compared with '
  '34 (60%) patients receiving everolimus … Among the 51 patients who were treated with sunitinib, 12 (24%) had '
  'grade 3 or 4 hypertension, five (10%) patients had grade 3 diarrhoea, four (8%) patients had grade 3 or 4 '
  'hand-foot syndrome, and two (4%) patients had grade 3 fatigue. Among the 57 patients who were treated with '
  'everolimus, five (9%) patients had grade 3 or 4 pneumonitis, and four (7%) patients had grade 3 fatigue … We did '
  'not record any treatment-related deaths',
  "o card dizia 'TRAEs ≥G3: sunitinibe 63%, everolimus 47%'; a fonte dá 78% vs 60%",
  'alta',
  'clínica',
  False),
 ('rcc_adjuvante_naocc_9',
  'tox_interesse',
  'Pneumonite everolimus 7% qualquer grau. Descontinuação por TRAE: suni 22%, everol 25%.',
  'Pneumonite com everolimus: grau 3-4 em 9% (5/57). Descontinuação por toxicidade: sunitinibe 14% (7/51) vs '
  'everolimus 23% (13/57); redução de dose: 53% vs 16%.',
  'PMID 26794930 · PMC6863151',
  'Results (Toxic effects)',
  '27 (53%) of 51 patients treated with sunitinib needed dose reductions, and seven (14%) patients discontinued '
  'treatment because of toxic effects. Nine (16%) of 57 patients who received everolimus needed dose reductions, and '
  '13 (23%) participants discontinued treatment because of toxic effects',
  "o card dizia 'Pneumonite everolimus 7% qualquer grau' (sem fonte no texto) e descontinuação 22% vs 25% (fonte: "
  '14% vs 23%)',
  'alta',
  'clínica',
  False),
 ('rcc_adjuvante_naocc_9',
  'incl',
  '≥18a; ECOG 0-2; nccRCC; doença mensurável; sem tratamento sistêmico prévio.',
  '≥18 anos; KPS ≥60; nccRCC com histologia predominante (≥50%) papilífera, cromófoba ou não classificada; doença '
  'mensurável (RECIST 1.1); sem tratamento sistêmico prévio; expectativa de vida ≥3 meses.',
  'PMID 26794930 · PMC6863151',
  'Methods (Patients)',
  'Additional eligibility criteria included baseline Karnofsky performance status of 60 or higher, life expectancy '
  'of at least 3 months, presence of measurable metastatic disease as per RECIST 1.1 criteria',
  "o card dizia 'ECOG 0-2'; o critério era KPS ≥60",
  'alta',
  'clínica',
  False),
 ('rcc_adjuvante_naocc_9',
  'excl',
  'Sarcomatoid puro; mets SNC.',
  'Metástases no SNC (atuais ou prévias); tratamento sistêmico prévio para RCC. Histologia sarcomatoide era '
  'permitida quando a histologia não-células-claras predominava.',
  'NCT01108445 · PMID 26794930 · PMC6863151',
  'Registro (Exclusion) + Methods',
  'Subjects with a history of or active central nervous system (CNS) metastases … Translocation carcinomas (if '
  'known) and sarcomatoid histologies were allowed irrespective of the histological mixture, provided that '
  'non-clear-cell histology was predominant',
  "o card excluía 'sarcomatoide puro' — a fonte permite sarcomatoide",
  'alta',
  'clínica',
  False),
 ('rcc_adjuvante_naocc_9',
  'basal',
  'Mediana 64a; ECOG 0-1 ~85%; papilar 70%, chromophobe 16%, outros 14%; MSKCC int 64%, poor 22%.',
  '108 randomizados (sunitinibe 51, everolimus 57). Histologia (revisão patológica local): papilífera 65% (70/108), '
  'não classificada 20% (22/108); cromófoba ou não classificada 35% (38/108). Risco MSKCC desfavorável 14% (15/108).',
  'PMID 26794930 · PMC6863151',
  'Abstract (Findings) + Methods (Participants) + Results',
  '108 patients were randomly assigned to receive either sunitinib (n=51) or everolimus (n=57) … as assessed through '
  'pathological examination by a local site review … only one (7%) of the 15 patients who were rated as having poor '
  'risk had chromophobe histology, whereas nine (13%) of 70 patients with papillary renal cell carcinoma and five '
  '(23%) of 22 patients with unclassified renal cell carcinoma … 20 (53%) of 38 patients with chromophobe or '
  'unclassified renal cell carcinoma',
  "o card lia contagens como porcentagem ('papilar 70%', 'poor 22%'); 'mediana 64a', 'ECOG 0-1 ~85%', 'chromophobe "
  "16%', 'outros 14%' e 'MSKCC int 64%' não têm número direto na publicação (Tabela 1 fora do texto) e foram "
  'removidos, sem substituição por inferência ou pelo registro. Porcentagens = contagem publicada / 108, '
  'arredondadas',
  'alta',
  'clínica',
  True),
 ('rcc_adjuvante_naocc_9',
  'limit',
  'Fase 2 com pequena amostra. Heterogeneidade histológica. Era pré-IO. Não evita conclusões fortes em chromophobe '
  '(subgrupo subamostrado).',
  'Fase 2 (108 pacientes) com α bilateral 0,20 — maior tolerância a falso-positivo; aberto, PFS e resposta pelo '
  'investigador, sem revisão central de imagem nem de patologia; análise final com 87 de 90 eventos planejados; '
  'subgrupos histológicos pequenos e sem teste de interação; era pré-imunoterapia.',
  'PMID 26794930 · PMC6863151',
  'Methods / Discussion',
  'This type I error rate was selected because we were willing to accept a higher false-positive rate in this phase '
  '2 trial setting … Central review of imaging was not done … we have relied on individual clinical pathology '
  'assessments rather than a central pathology interpretation',
  'limitações reais do desenho (α 0,20, sem revisão central) ausentes do card',
  'alta',
  'clínica',
  False),
 ('rcc_adjuvante_naocc_9',
  'resultado_chave',
  'mPFS suni 8,3 vs everolimus 5,6 m · HR 1,41 (p=0,16) · ORR 18% vs 9% — NS, tendência pró-sunitinibe',
  'mPFS sunitinibe 8,3 vs everolimus 5,6 m · HR 1,41 (IC 80% 1,03–1,92; p=0,16) — significativo pelo α bilateral '
  '0,20 pré-especificado, a favor do sunitinibe',
  'PMID 26794930 · PMC6863151',
  'Results',
  'meeting the prespecified level of statistical significance for the study (two-sided type I error rate of 0⋅20)',
  "o card dizia 'NS, tendência pró-sunitinibe'; a ORR (secundário descritivo) sai do resumo, que destaca o desfecho "
  'primário',
  'alta',
  'clínica',
  False),
 ('tropion-lung01-dato-dxd-vs-docetaxel-nsclc',
  'tox_interesse',
  'Toxicidade de classe do ADC: estomatite/mucosite (~7%), doença pulmonar intersticial/pneumonite adjudicada (~4%, '
  'com casos fatais G5 relatados), toxicidade ocular (ceratite/superfície ocular), náusea, alopecia',
  'Conjunto de segurança: Dato-DXd n=297, docetaxel n=290. DPI/pneumonite adjudicada como relacionada ao fármaco — '
  'Dato-DXd: qualquer grau 8,8% (26/297), grau ≥3 3,7%, grau 5 2,4% (7); docetaxel: qualquer grau 4,1% (12/290), '
  'grau ≥3 1,4%, grau 5 0,3% (1). Estomatite como EA relacionado ao tratamento: qualquer grau 47,5% vs 15,5%; grau '
  '≥3 6,7% vs 1,0%. Mucosite oral/estomatite como EA de interesse especial (termo agrupado, EA emergente): 55,2% vs '
  '20,7%. Ceratite com Dato-DXd: qualquer grau 4,0%, grau ≥3 1,3%. EAs relacionados, qualquer grau: náusea 34,0% vs '
  '16,6%; alopecia 32,0% vs 34,8%.',
  'PMID 39250535 · PMC11771353',
  'Results (Safety) + Table 4',
  'The safety analysis set included 297 and 290 treated patients … Adjudicated drug-related ILD or pneumonitis | e | 26 '
  '(8.8) | 11 (3.7) | 12 (4.1) | 4 (1.4) … seven (2.4%) had grade 5 events … one (0.3%) had a grade 5 event … '
  'Stomatitis | 141 (47.5) | 20 (6.7) | 45 (15.5) | 3 (1.0) … Oral mucositis/stomatitis occurred in 164 patients '
  '(55.2%) receiving Dato-DXd versus 60 (20.7%) … any-grade and grade ≥3 keratitis occurred in 12 (4.0%) and 4 '
  '(1.3%) … Nausea | 101 (34.0) | 7 (2.4) | 48 (16.6) … Alopecia | 95 (32.0) | 0 | 101 (34.8)',
  "o card atribuía ao Dato-DXd a taxa de DPI do docetaxel (~4%) e chamava de '~7%' a estomatite (é o grau ≥3); a "
  'redação nova separa braço, grau e definição (TRAE × termo agrupado de interesse especial)',
  'alta',
  'clínica',
  False),
 ('tropion-lung01-dato-dxd-vs-docetaxel-nsclc',
  'tox_g3',
  'EAs relacionados ao tratamento ≥G3: 26% (Dato-DXd) vs 42% (docetaxel)',
  'EAs relacionados ao tratamento ≥G3: 25,6% (Dato-DXd) vs 42,1% (docetaxel); óbitos por EA relacionado '
  '(investigador): 3 (1,0%) vs 2 (0,7%), incluindo DPI/pneumonite em 2 e 1.',
  'PMID 39250535 · PMC11771353',
  'Abstract + Results (Safety)',
  'Grade ≥3 treatment-related adverse events occurred in 25.6% and 42.1% of patients … Three patients (1.0%) treated '
  'with Dato-DXd and 2 (0.7%) with docetaxel had investigator-assessed TRAEs associated with death: two cases of '
  'ILD/pneumonitis and one of sepsis (Dato-DXd) and one case of ILD/pneumonitis and one of septic shock (docetaxel)',
  'precisão (26% → 25,6%; 42% → 42,1%) e óbitos por DPI, que o card não trazia',
  'alta',
  'clínica',
  False)]


def carregar(caminho: Path):
    t = caminho.read_text(encoding="utf-8")
    i, j = t.index("{"), t.rindex("}") + 1
    return t[:i], json.loads(t[i:j]), t[j:]


def serializar(prefixo, dados, fim):
    return prefixo + json.dumps(dados, ensure_ascii=False, separators=(",", ":")) + fim


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def aplicar() -> int:
    atual = sha(R.DATA_JS)
    if atual == SHA_FINAL:
        print("já aplicado: assets/js/data.js tem o SHA final; nada a fazer")
        return 0
    if atual != SHA_ORIGEM:
        print(f"recusado: assets/js/data.js inesperado ({atual[:16]}), esperado {SHA_ORIGEM[:16]}", file=sys.stderr)
        return 2
    if not COPIA.exists() or sha(COPIA) != SHA_FINAL:
        print("recusado: a cópia não existe ou não tem o SHA final esperado; gere e valide a cópia antes", file=sys.stderr)
        return 2
    shutil.copyfile(COPIA, R.DATA_JS)
    print(f"aplicado: assets/js/data.js {SHA_ORIGEM[:16]} → {SHA_FINAL[:16]}")
    return 0


def main(argv=None) -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--aplicar", action="store_true", help="promove a cópia validada a assets/js/data.js")
    if a.parse_args(argv).aplicar:
        return aplicar()
    if COPIA.resolve() == R.DATA_JS.resolve():
        print("recusado: o alvo é o banco publicado", file=sys.stderr)
        return 2
    origem = sha(R.DATA_JS)
    if origem == SHA_FINAL:
        print("já aplicado: assets/js/data.js tem o SHA final; nada a fazer")
        return 0
    if origem != SHA_ORIGEM:
        print(f"recusado: assets/js/data.js inesperado ({origem[:16]}), esperado {SHA_ORIGEM[:16]}", file=sys.stderr)
        return 2
    COPIA_DIR.mkdir(exist_ok=True)
    shutil.copyfile(R.DATA_JS, COPIA)
    prefixo, dados, fim = carregar(COPIA)
    assert serializar(prefixo, dados, fim) == COPIA.read_text(encoding="utf-8"), "serialização não é idêntica"
    uids_antes = [s["uid"] for s in dados["studies"]]
    por_uid = {s["uid"]: s for s in dados["studies"]}
    erros, prov, aplicadas = [], [], []
    for uid, campo, antes, depois, ident, loc, evid, motivo, conf, nat, der in MUDANCAS:
        card = por_uid.get(uid)
        if card is None:
            erros.append(f"{uid}: card inexistente"); continue
        atual = card.get(campo)
        if atual == depois:
            continue
        if atual != antes:
            erros.append(f"{uid}.{campo}: valor atual diferente do esperado — {str(atual)[:80]!r}"); continue
        card[campo] = depois
        aplicadas.append((uid, campo, antes, depois))
        prov.append({"uid": uid, "campo": campo, "anterior": antes, "novo": depois, "identificador": ident,
                     "locator": loc, "evidencia": evid, "motivo": motivo, "evidence_confidence": conf,
                     "natureza": nat, "derivado": der, "decisao_humana": DECISAO,
                     "arquivo": "cópia (scripts/_db_copia/data.js)"})
    if erros:
        print("NADA GRAVADO:\n  " + "\n  ".join(erros), file=sys.stderr)
        COPIA.unlink()
        return 1
    assert [s["uid"] for s in dados["studies"]] == uids_antes, "uid mudou"
    _, orig, _ = carregar(R.DATA_JS)
    mudaram = {s["uid"] for s, o in zip(dados["studies"], orig["studies"]) if s != o}
    assert mudaram == CARDS, f"cards alterados fora do escopo: {sorted(mudaram ^ CARDS)}"
    assert {k: v for k, v in dados.items() if k != "studies"} == {k: v for k, v in orig.items() if k != "studies"}
    COPIA.write_text(serializar(prefixo, dados, fim), encoding="utf-8")
    R.gravar(PROV, "\n".join(json.dumps(p, ensure_ascii=False) for p in prov) + "\n")
    L = ["# Diff campo a campo — cópia scripts/_db_copia/data.js", "",
         f"{len(aplicadas)} campos em {len({a[0] for a in aplicadas})} cards. Nenhum uid mudou. "
         f"SHA da cópia: {sha(COPIA)}.", ""]
    for uid in dict.fromkeys(a[0] for a in aplicadas):
        L += [f"## `{uid}` — {por_uid[uid]['estudo']}", ""]
        for u, campo, antes, depois in aplicadas:
            if u == uid:
                p = next(x for x in prov if x["uid"] == u and x["campo"] == campo)
                L += [f"**{campo}** · confiança {p['evidence_confidence']} · {p['identificador']} · {p['locator']}"
                      + (" · DERIVADO" if p["derivado"] else ""),
                      f"- antes: {antes!r}", f"- depois: {depois!r}", f"- motivo: {p['motivo']}",
                      f"- trecho: {p['evidencia']}", ""]
    DIFF.write_text("\n".join(L), encoding="utf-8")
    print(json.dumps({"campos": len(aplicadas), "cards": sorted({a[0] for a in aplicadas}),
                      "proveniencia": len(prov)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
