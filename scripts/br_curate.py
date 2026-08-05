#!/usr/bin/env python3
"""
br_curate.py — etapa 2 do pipeline do Trial Matcher: a curadoria propriamente dita.

Lê scripts/_br_discovery.json (saída do br_discover.py) e, para cada estudo novo,
pede a Claude que redija os campos que exigem julgamento clínico — `racional`,
`criterios_principais`, `linha_terapeutica`, `cenario_clinico`, `subtipo`,
`testes_fornecidos` — a partir do texto oficial do registro.

Os campos factuais (nct, fase, status, centros, estados, patrocinador) NÃO passam
por aqui: vêm prontos do br_discover.py. O modelo só escreve o que é interpretação.

Dois modos, mesmo resultado:

  LOCAL (sem custo) — para quem já assina Claude Pro/Max. O script exporta os
  prompts, você cura numa sessão do Claude Code e devolve o JSON. A assinatura
  e a API são faturamentos separados, então este caminho não gera cobrança.

  API (Batch, -50%) — automático, roda sozinho no GitHub Actions uma vez por
  mês. Exige o secret ANTHROPIC_API_KEY e créditos no console.anthropic.com.

⚠️ A saída é RASCUNHO nos dois modos. Vai para um Pull Request, nunca direto
   para produção — todo card precisa de revisão clínica antes de publicar.

Uso — modo LOCAL:
    python3 scripts/br_curate.py --exportar --neoplasia breast
        → grava _br_prompts.json; peça ao Claude Code para curar
    python3 scripts/br_curate.py --importar cards.json
        → anexa os campos factuais e grava _br_curated.json

Uso — modo API:
    python3 scripts/br_curate.py --enviar --neoplasia breast --limite 44
    python3 scripts/br_curate.py --status msgbatch_01ABC
    python3 scripts/br_curate.py --colher msgbatch_01ABC
    python3 scripts/br_curate.py --estimar     # custo, sem enviar nada
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
DISCOVERY = SCRIPTS / "_br_discovery.json"
SAIDA = SCRIPTS / "_br_curated.json"
PROMPTS = SCRIPTS / "_br_prompts.json"
# Registro permanente dos estudos já avaliados e recusados. Sem isto, todo mês
# o pipeline volta a oferecer os mesmos — descartado não entra no trials_br.js,
# então o diff continua vendo o estudo como "novo" indefinidamente.
DESCARTADOS = SCRIPTS / "br_descartados.json"

MODELO = "claude-opus-5"
# Um card curado tem ~26 campos e roda perto de 4.800 caracteres; 4000 tokens
# dão folga confortável sem risco de truncar no meio de um critério.
MAX_TOKENS = 4000

# Preço por milhão de tokens (Batch API = 50% do padrão).
PRECO = {"in": 5.00 * 0.5, "out": 25.00 * 0.5}

# ── Taxonomia canônica ────────────────────────────────────────────────────────
# O modelo precisa escolher DENTRO destas listas — valor fora da lista quebra os
# filtros do Trial Matcher silenciosamente (o card aparece, mas nenhum filtro o
# encontra). A fonte é THERA_TRIALS_BR_META, e é lida daqui em vez de copiada:
# quando era cópia manual, ficou seis valores atrás da META sem ninguém notar
# (llc, lma, lla, gist, solidos, net). Categoria que existe na META mas falta
# aqui some do vocabulário do modelo, que então força o estudo numa categoria
# errada ou o descarta.
TRIALS_JS = SCRIPTS.parent / "assets" / "js" / "trials_br.js"


def meta_ids(bloco: str) -> list[str]:
    """Devolve os `id` de um bloco de THERA_TRIALS_BR_META, na ordem do arquivo."""
    texto = TRIALS_JS.read_text(encoding="utf-8")
    m = re.search(rf"^  {bloco}: \[$(.*?)^  \],$", texto, re.S | re.M)
    if not m:
        raise SystemExit(f"bloco '{bloco}' não encontrado em {TRIALS_JS.name}")
    ids = re.findall(r"^\s*\{ id: '([^']+)'", m.group(1), re.M)
    if not ids:
        raise SystemExit(f"bloco '{bloco}' sem nenhum id em {TRIALS_JS.name}")
    return ids


NEOPLASIAS = meta_ids("neoplasias")
MODALIDADES = meta_ids("modalidades")
LINHAS = meta_ids("linhas")

SCHEMA = {
    "type": "object",
    "properties": {
        "descartar": {
            "type": "boolean",
            "description": "true se o estudo não couber em nenhuma neoplasia da lista "
                           "(ex.: doença hematológica sem categoria própria — SMD, "
                           "mielofibrose, LMC, HPN) ou se o registro não trouxer "
                           "informação suficiente para uma curadoria honesta. Cesta de "
                           "vários sítios ou recrutamento por alteração molecular NÃO "
                           "é motivo de descarte: existe `solidos` para isso.",
        },
        "motivo_descarte": {"type": "string"},
        "nome": {
            "type": "string",
            "description": "Acrônimo do estudo (ex.: 'SUNRAY-02'). Se o registro não "
                           "tiver acrônimo, use o nome do fármaco principal + a fase.",
        },
        "titulo": {
            "type": "string",
            "description": "Uma linha em português descrevendo intervenção e população. "
                           "Não traduza o título oficial literalmente — resuma.",
        },
        "neoplasia": {"type": "string", "enum": NEOPLASIAS},
        "neoplasia_label": {
            "type": "string",
            "description": "Rótulo curto exibido no card, ex.: 'Pulmão · NSCLC', "
                           "'Mama · TNBC'.",
        },
        "subtipo": {
            "type": "string",
            "description": "Subtipo histológico/molecular exigido, ex.: 'NSCLC "
                           "não-escamoso, EGFR mutado'. Vazio se o estudo não restringir.",
        },
        "linha_terapeutica": {"type": "string", "enum": LINHAS},
        "cenario_clinico": {
            "type": "string",
            "description": "Cenário em uma frase, ex.: 'Metastático após progressão "
                           "a inibidor de EGFR de 3ª geração'.",
        },
        "modalidade": {
            "type": "array", "items": {"type": "string", "enum": MODALIDADES},
            "minItems": 1,
        },
        "biomarcadores": {
            "type": "array", "items": {"type": "string"},
            "description": "Só os EXIGIDOS para elegibilidade (ex.: 'EGFR', 'PD-L1', "
                           "'HER2'). Lista vazia se o estudo não exigir biomarcador.",
        },
        "testes_fornecidos": {
            "type": "string",
            "description": "O estudo fornece teste central de biomarcador? Diga apenas "
                           "o que o registro afirmar. Vazio se não mencionar.",
        },
        "intervencao": {
            "type": "string",
            "description": "Braço experimental, com doses se o registro trouxer.",
        },
        "comparador": {
            "type": "string",
            "description": "Braço controle. '— (braço único)' se não houver.",
        },
        "racional": {
            "type": "string",
            "description": "2-3 frases sobre por que este estudo é relevante: mecanismo "
                           "e a lacuna clínica que endereça. Baseie-se APENAS no resumo "
                           "oficial. Não cite resultados de outros estudos, não faça "
                           "prognósticos, não afirme superioridade.",
        },
        "criterios_principais": {
            "type": "array", "items": {"type": "string"}, "minItems": 3, "maxItems": 8,
            "description": "Critérios de INCLUSÃO que mais decidem elegibilidade na "
                           "prática, resumidos em português. Não copie o texto inteiro.",
        },
        # Sem `minItems` o array vazio satisfazia o schema, e 34 dos 102 cards
        # do pipeline saíram sem nenhuma exclusão mesmo com o texto oficial
        # inteiro no prompt. A inclusão, que sempre teve `minItems: 3`, nunca
        # ficou vazia — a assimetria era a causa. O `minItems: 1` aqui é só o
        # primeiro filtro; quem realmente garante é `conferir_exclusao()`, que
        # compara com o texto de origem em vez de confiar na saída do modelo.
        "criterios_exclusao": {
            "type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 6,
            "description": "Critérios de EXCLUSÃO que mais eliminam candidatos na "
                           "prática, resumidos em português: comorbidade que barra, "
                           "tratamento prévio que impede, metástase de SNC, doença "
                           "autoimune, alteração laboratorial. Estão sob 'Exclusion "
                           "Criteria' no texto oficial. Não copie o texto inteiro. "
                           "Se o registro realmente não trouxer exclusões, use "
                           "`exclusao_ausente: true` — nunca devolva lista vazia.",
        },
        "exclusao_ausente": {
            "type": "boolean",
            "description": "true APENAS se o texto de elegibilidade não tiver seção "
                           "de exclusão alguma. Marcar isto com a seção presente é "
                           "falha grave. Se marcar, explique em `notas_revisor`.",
        },
        "confianca": {
            "type": "string", "enum": ["alta", "media", "baixa"],
            "description": "Sua confiança na curadoria. 'baixa' se o registro for vago, "
                           "a população ambígua ou a classificação incerta.",
        },
        "notas_revisor": {
            "type": "string",
            "description": "O que o revisor humano precisa conferir. Seja específico "
                           "sobre o que você NÃO conseguiu determinar pelo registro.",
        },
    },
    "required": [
        "descartar", "motivo_descarte", "nome", "titulo", "neoplasia",
        "neoplasia_label", "subtipo", "linha_terapeutica", "cenario_clinico",
        "modalidade", "biomarcadores", "testes_fornecidos", "intervencao",
        "comparador", "racional", "criterios_principais", "criterios_exclusao",
        "exclusao_ausente", "confianca", "notas_revisor",
    ],
    "additionalProperties": False,
}

SISTEMA = """\
Você prepara rascunhos de curadoria para o Trial Matcher do TheraTrials Oncology \
— uma ferramenta que médicos brasileiros usam para localizar ensaios clínicos \
abertos para seus pacientes.

O que você escreve será revisado por um médico antes de publicar, mas escreva \
como se fosse publicado: é assim que a revisão fica rápida.

REGRAS INVIOLÁVEIS

1. Use APENAS o que está no registro fornecido. Não complete com conhecimento \
   prévio sobre o fármaco, a classe ou estudos parecidos.
2. Se o registro não informa algo, deixe o campo vazio e diga em `notas_revisor`. \
   Campo vazio é correto; campo inventado é falha grave. Isto NÃO vale para \
   `criterios_exclusao`: ver regra 8.
3. Não afirme eficácia, superioridade ou prognóstico. O estudo está em andamento \
   — não há resultado.
4. `neoplasia`, `linha_terapeutica` e `modalidade` só aceitam os valores das listas \
   do schema. Nenhum valor fora delas é válido. Se o estudo não couber em nenhuma \
   neoplasia da lista, marque `descartar: true` e explique.
5. Escreva em português do Brasil, registro clínico, sem marketing. Nomes de \
   fármacos e biomarcadores ficam na grafia internacional (pembrolizumabe é \
   aceitável; KRAS G12C nunca se traduz).
6. `criterios_principais` são os que de fato decidem se o paciente entra — idade, \
   histologia, biomarcador exigido, linha prévia, performance status, função \
   orgânica. Resuma; não transcreva o texto do protocolo.
7. Se ficar em dúvida sobre a classificação, use `confianca: "baixa"` e diga o \
   porquê. Preferimos um card marcado para revisão a um card errado com aparência \
   de certo.

8. `criterios_exclusao` é obrigatório na prática. O texto de elegibilidade que \
   você recebe traz, quase sempre, uma seção "Exclusion Criteria" ou "Key \
   Exclusion Criteria" — ela vem completa no prompt, com orçamento próprio de \
   caracteres, e nunca é cortada antes da inclusão. Extraia dela as exclusões \
   que mais eliminam candidatos: comorbidade que barra, tratamento prévio que \
   impede, metástase de SNC, doença autoimune, alteração laboratorial. \
   Devolver lista vazia com a seção presente é falha grave — tão grave quanto \
   inventar. Só marque `exclusao_ausente: true` se a seção realmente não \
   existir no texto, e nunca alegue que o texto veio truncado: se algo foi \
   cortado, o prompt diz explicitamente onde, com a marca "[… cortada por \
   tamanho …]"."""


# Orçamento de caracteres para cada metade do texto de elegibilidade.
# Um `[:6000]` cru corta o fim, e o fim é justamente onde ficam as exclusões:
# no ADELA o texto tem 12.909 caracteres e a seção de exclusão começa no 5.176,
# então o corte decepava a maior parte dela. Reservar orçamento para as duas
# metades garante que a exclusão sempre chegue ao modelo.
ORCAMENTO_INCLUSAO = 4000
ORCAMENTO_EXCLUSAO = 4000
# O cabeçalho de exclusão não vem num formato só. Casos reais do registro:
#     Exclusion Criteria:
#     Key Exclusion Criteria
#     Phase 1b Exclusion Criteria:          (qualificador antes)
#     Exclusion Criteria Related to NSCLC:  (qualificador depois)
#     Exclusion Criteria: Screening Phase   (qualificador depois dos dois-pontos)
#     2. Key Exclusion Criteria:            (item numerado)
#     Other Exclusions                      (sem a palavra "criteria")
#     Participants who meet any of the following criteria will be disqualified
#       from entering the study:            (sem a palavra "exclusion")
# Um padrão que exigisse a linha exatamente igual a "Exclusion Criteria" perdia
# todos os demais — e aí a conferência acusava, errado, que o card tinha
# inventado exclusões inexistentes. Casa linha curta e isolada, tipo título.
RE_EXCLUSAO = re.compile(
    r"^[ \t]*(?:[*\-–•]|\d+[.)])?[ \t]*"       # marcador de lista, símbolo ou número
    r"(?:"
    r"[\w ./()\-]{0,40}?"                      # qualificador antes ("Key", "Phase 1b")
    r"exclusions?(?:[ \t]+criteria)?"
    r"[\w ,:/()\-]{0,60}"                      # qualificador depois, com ou sem ':'
    r"|"
    r".{0,140}?(?:disqualified from entering|will be excluded from)"
    r"[\w ,/()\-]{0,60}"
    r")"
    r":?[ \t]*$",
    re.I | re.M,
)

# Nem todo registro traz cabeçalho: o SOUNDTRACK-D2 lista as exclusões logo
# depois das inclusões e só as identifica na frase de rodapé. Isto NÃO serve
# para dividir o texto — o rodapé fica no fim da seção, não no começo —, serve
# apenas para conferir que ela existe.
RE_EXCLUSAO_RODAPE = re.compile(r"other exclusion criteria", re.I)


def tem_secao_exclusao(texto: str) -> bool:
    """True se o registro traz exclusões, seja por cabeçalho ou só pelo rodapé."""
    t = texto or ""
    return bool(RE_EXCLUSAO.search(t) or RE_EXCLUSAO_RODAPE.search(t))


def recortar_elegibilidade(texto: str) -> str:
    """Divide inclusão/exclusão e corta cada metade dentro do seu orçamento."""
    if not texto:
        return "(não informados)"
    m = RE_EXCLUSAO.search(texto)
    if not m:
        # Sem cabeçalho de exclusão: pode ser registro que não separa as seções.
        # Manda o texto inteiro dentro do orçamento somado e avisa o modelo.
        corte = texto[: ORCAMENTO_INCLUSAO + ORCAMENTO_EXCLUSAO]
        aviso = "" if len(texto) <= len(corte) else \
            "\n[NOTA: texto acima cortado por tamanho.]"
        return corte + aviso

    inc, exc = texto[: m.start()], texto[m.start():]
    partes = []
    if len(inc) > ORCAMENTO_INCLUSAO:
        partes.append(inc[:ORCAMENTO_INCLUSAO] + "\n[… inclusão cortada por tamanho …]")
    else:
        partes.append(inc)
    if len(exc) > ORCAMENTO_EXCLUSAO:
        partes.append(exc[:ORCAMENTO_EXCLUSAO] + "\n[… exclusão cortada por tamanho …]")
    else:
        partes.append(exc)
    return "".join(partes)


def conferir_exclusao(card: dict, elegibilidade: str) -> str:
    """
    Verifica a exclusão contra o TEXTO DE ORIGEM, não contra a saída do modelo.

    O modelo devolvia `criterios_exclusao: []` e, em 8 dos 34 casos, justificava
    na nota que "o texto de elegibilidade veio truncado no registro consultado".
    Nenhum dos 34 estava truncado — a seção de exclusão começava, na maioria,
    antes do caractere 900, e o corte era em 6000. A justificativa era invenção.

    Por isso a conferência aqui não lê `notas_revisor` nem `exclusao_ausente`:
    procura o cabeçalho no texto oficial e compara. Devolve '' quando está OK.
    """
    tem_secao = tem_secao_exclusao(elegibilidade)
    n = len(card.get("criterios_exclusao") or [])
    ausente = bool(card.get("exclusao_ausente"))

    if tem_secao and n == 0:
        return ("registro TEM seção de exclusão e o card veio sem nenhuma"
                + (" (e marcou exclusao_ausente, o que é falso)" if ausente else ""))
    if not tem_secao and n == 0 and not ausente:
        return "card sem exclusão e sem marcar exclusao_ausente"
    if not tem_secao and n > 0:
        return "card trouxe exclusões que não existem no texto oficial"
    return ""


def prompt(e: dict) -> str:
    linhas = [
        f"NCT: {e['nct']}",
        f"Acrônimo: {e['acronimo'] or '(sem acrônimo)'}",
        f"Título: {e['titulo_breve']}",
        f"Título oficial: {e['titulo_oficial']}",
        f"Fase: {', '.join(e['fases']) or '(não informada)'}",
        f"Status: {e['status_ctgov']}",
        f"Condições: {', '.join(e['condicoes'])}",
        f"Patrocinador: {e['patrocinador']}",
        f"N previsto: {e['n_previsto']}",
        f"Idade: {e['idade_min']} a {e['idade_max']}  |  Sexo: {e['sexo']}",
        f"Centros no Brasil ({e['n_centros_br']}): "
        f"{', '.join(e['cidades_br'])} [{', '.join(e['ufs_br'])}]",
        "",
        "RESUMO OFICIAL:", e["resumo"] or "(sem resumo)", "",
        "BRAÇOS:",
    ]
    for b in e["bracos"]:
        linhas.append(f"  · [{b['tipo']}] {b['rotulo']}: {b['descricao'][:400]}")
    linhas += ["", "INTERVENÇÕES:"]
    for i in e["intervencoes"]:
        linhas.append(f"  · [{i['tipo']}] {i['nome']}: {i['descricao'][:300]}")
    linhas += ["", "CRITÉRIOS DE ELEGIBILIDADE (texto oficial):",
               recortar_elegibilidade(e["elegibilidade"])]
    return "\n".join(linhas)


def montar(estudos: list[dict]):
    """Requests da Batch API. Importa o SDK só aqui — o modo local não precisa dele."""
    import anthropic  # noqa: F401  (validado no chamador)
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request

    return [
        Request(
            custom_id=e["nct"],
            params=MessageCreateParamsNonStreaming(
                model=MODELO,
                max_tokens=MAX_TOKENS,
                system=SISTEMA,
                output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
                messages=[{"role": "user", "content": prompt(e)}],
            ),
        )
        for e in estudos
    ]


def anexar_factual(curado: dict, base: dict) -> dict:
    """Campos factuais vêm da descoberta, nunca do modelo."""
    curado["_factual"] = {
        "nct": base.get("nct", ""),
        "fase": base.get("fases", []),
        "status_ctgov": base.get("status_ctgov", ""),
        "centros": base.get("centros_br", []),
        "locais": base.get("locais_br", []),   # {instituicao, cidade, uf} preservados
        "cidades": base.get("cidades_br", []),
        "estados": base.get("ufs_br", []),
        "patrocinador": base.get("patrocinador", ""),
        "data_atualizacao": base.get("ultima_atualizacao", ""),
    }
    return curado


def ja_descartados() -> dict[str, str]:
    if not DESCARTADOS.exists():
        return {}
    return {d["nct"]: d.get("motivo", "") for d in
            json.loads(DESCARTADOS.read_text(encoding="utf-8"))}


def registrar_descartes(novos: list[dict]) -> None:
    """Acumula no registro permanente, sem duplicar."""
    atuais = json.loads(DESCARTADOS.read_text(encoding="utf-8")) \
        if DESCARTADOS.exists() else []
    vistos = {d["nct"] for d in atuais}
    atuais += [d for d in novos if d["nct"] not in vistos]
    DESCARTADOS.write_text(json.dumps(atuais, ensure_ascii=False, indent=1),
                           encoding="utf-8")


def selecionar(args) -> list[dict]:
    d = json.loads(DISCOVERY.read_text(encoding="utf-8"))
    recusados = ja_descartados()
    novos = [e for e in d["novos"] if e["nct"] not in recusados]
    if recusados:
        print(f"[curate] {len(d['novos']) - len(novos)} estudos pulados "
              f"(já descartados antes)", file=sys.stderr)

    # O Trial Matcher lista recrutamento aberto. Estudo ainda não recrutando
    # fica de fora da curadoria por decisão do autor (2026-08-04) — e sai daqui,
    # não do br_descartados.json: quando o CT.gov virar o status para
    # RECRUITING, ele entra sozinho na descoberta seguinte. Descartá-lo o
    # excluiria para sempre.
    if not args.incluir_nao_abertos:
        abertos = [e for e in novos if e.get("status_ctgov") == "RECRUITING"]
        adiados = len(novos) - len(abertos)
        if adiados:
            print(f"[curate] {adiados} estudos adiados (ainda não recrutando; "
                  f"--incluir-nao-abertos para trazê-los)", file=sys.stderr)
        novos = abertos
    if args.neoplasia:
        alvo = args.neoplasia.lower()
        novos = [e for e in novos
                 if any(alvo in c.lower() for c in e["condicoes"])
                 or alvo in e["titulo_breve"].lower()]
    if args.limite:
        novos = novos[: args.limite]
    return novos


def estimar(estudos: list[dict]) -> None:
    # 4 caracteres por token é a aproximação usual em português; serve para ordem
    # de grandeza. Para o número exato use client.messages.count_tokens().
    entrada = sum(len(SISTEMA) + len(prompt(e)) for e in estudos) / 4
    saida = len(estudos) * 1400
    custo = entrada / 1e6 * PRECO["in"] + saida / 1e6 * PRECO["out"]
    print(f"  estudos ............ {len(estudos)}")
    print(f"  entrada (aprox) .... {entrada/1000:.0f}k tokens")
    print(f"  saída (aprox) ...... {saida/1000:.0f}k tokens")
    print(f"  custo estimado ..... US$ {custo:.2f}  ({MODELO}, Batch API -50%)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--exportar", action="store_true", help="modo local: grava os prompts")
    ap.add_argument("--importar", metavar="CARDS.json", help="modo local: recebe os cards")
    ap.add_argument("--enviar", action="store_true")
    ap.add_argument("--estimar", action="store_true")
    ap.add_argument("--status", metavar="BATCH_ID")
    ap.add_argument("--colher", metavar="BATCH_ID")
    ap.add_argument("--neoplasia", help="filtra o lote por condição (ex.: breast)")
    ap.add_argument("--limite", type=int, default=0)
    ap.add_argument("--incluir-nao-abertos", action="store_true",
                    help="traz também os NOT_YET_RECRUITING (fora por padrão)")
    args = ap.parse_args()

    # ── modo LOCAL ────────────────────────────────────────────────────────────
    if args.exportar:
        estudos = selecionar(args)
        if not estudos:
            print("nenhum estudo selecionado", file=sys.stderr)
            return 1
        PROMPTS.write_text(json.dumps({
            "sistema": SISTEMA,
            "schema": SCHEMA,
            "estudos": [{"nct": e["nct"], "prompt": prompt(e)} for e in estudos],
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{len(estudos)} estudos -> {PROMPTS.name}")
        print("Peça ao Claude Code: cure os estudos de _br_prompts.json seguindo o "
              "schema, e salve os cards num JSON.")
        print("Depois: python3 scripts/br_curate.py --importar <arquivo>")
        return 0

    if args.importar:
        entrada = json.loads(Path(args.importar).read_text(encoding="utf-8"))
        cards_in = entrada["cards"] if isinstance(entrada, dict) else entrada
        d = json.loads(DISCOVERY.read_text(encoding="utf-8"))
        por_nct = {e["nct"]: e for e in d["novos"]}

        cards, descartados, orfaos, sem_exclusao = [], [], [], []
        obrigatorios = set(SCHEMA["required"])
        for c in cards_in:
            nct = c.get("nct") or c.get("_nct", "")
            if nct not in por_nct:
                orfaos.append(nct or "(sem nct)")
                continue
            faltando = obrigatorios - set(c)
            if faltando:
                print(f"  {nct}: campos faltando -> {', '.join(sorted(faltando))}",
                      file=sys.stderr)
                orfaos.append(nct)
                continue
            if c.get("descartar"):
                descartados.append({"nct": nct, "nome": c.get("nome", ""),
                                    "motivo": c.get("motivo_descarte", "")})
                continue
            # Conferência contra o registro, antes de virar card. Rejeita aqui
            # em vez de deixar passar: card sem exclusão chegava ao PR com
            # aparência de completo e ninguém notava que faltava metade.
            erro = conferir_exclusao(c, por_nct[nct].get("elegibilidade", ""))
            if erro:
                print(f"  {nct} ({c.get('nome','?')}): {erro}", file=sys.stderr)
                sem_exclusao.append(nct)
                continue
            cards.append(anexar_factual(c, por_nct[nct]))

        if sem_exclusao:
            print(f"\n⚠ {len(sem_exclusao)} card(s) rejeitados por exclusão ausente/"
                  f"inventada. Recure esses NCTs — o texto oficial tem a seção.",
                  file=sys.stderr)
        if descartados:
            registrar_descartes(descartados)

        SAIDA.write_text(json.dumps(
            {"batch": "local", "cards": cards, "descartados": descartados,
             "falhas": orfaos, "sem_exclusao": sem_exclusao},
            ensure_ascii=False, indent=1), encoding="utf-8")
        baixa = sum(1 for c in cards if c.get("confianca") == "baixa")
        print(f"curados {len(cards)} | descartados {len(descartados)} | rejeitados {len(orfaos)}")
        print(f"  confiança baixa (revisar primeiro): {baixa}")
        print(f"gravado: {SAIDA.name}")
        return 0 if not orfaos else 1

    # ── modo API ──────────────────────────────────────────────────────────────
    if args.estimar or args.enviar:
        estudos = selecionar(args)
        if not estudos:
            print("nenhum estudo selecionado — rode br_discover.py antes", file=sys.stderr)
            return 1
        estimar(estudos)
        if args.estimar:
            return 0

        import anthropic
        cliente = anthropic.Anthropic()
        lote = cliente.messages.batches.create(requests=montar(estudos))
        print(f"\nbatch criado: {lote.id}")
        print(f"acompanhe:  python3 scripts/br_curate.py --status {lote.id}")
        return 0

    if args.status:
        import anthropic
        lote = anthropic.Anthropic().messages.batches.retrieve(args.status)
        c = lote.request_counts
        print(f"{lote.id}: {lote.processing_status}")
        print(f"  processando {c.processing} | ok {c.succeeded} | erro {c.errored} "
              f"| cancelado {c.canceled} | expirado {c.expired}")
        return 0

    if args.colher:
        import anthropic
        cliente = anthropic.Anthropic()
        d = json.loads(DISCOVERY.read_text(encoding="utf-8"))
        por_nct = {e["nct"]: e for e in d["novos"]}
        cards, descartados, falhas = [], [], []

        for r in cliente.messages.batches.results(args.colher):
            if r.result.type != "succeeded":
                falhas.append({"nct": r.custom_id, "tipo": r.result.type})
                continue
            texto = next(b.text for b in r.result.message.content if b.type == "text")
            curado = json.loads(texto)
            base = por_nct.get(r.custom_id, {})
            if curado.get("descartar"):
                descartados.append({"nct": r.custom_id,
                                    "motivo": curado.get("motivo_descarte", "")})
                continue
            # Campos factuais vêm da descoberta; o modelo não os toca.
            curado["_factual"] = {
                "nct": base.get("nct", ""),
                "fase": base.get("fases", []),
                "status_ctgov": base.get("status_ctgov", ""),
                "centros": base.get("centros_br", []),
                "cidades": base.get("cidades_br", []),
                "estados": base.get("ufs_br", []),
                "patrocinador": base.get("patrocinador", ""),
                "data_atualizacao": base.get("ultima_atualizacao", ""),
            }
            cards.append(curado)

        SAIDA.write_text(json.dumps(
            {"batch": args.colher, "cards": cards,
             "descartados": descartados, "falhas": falhas},
            ensure_ascii=False, indent=1), encoding="utf-8")
        baixa = sum(1 for c in cards if c.get("confianca") == "baixa")
        print(f"curados {len(cards)} | descartados {len(descartados)} | falhas {len(falhas)}")
        print(f"  confiança baixa (revisar primeiro): {baixa}")
        print(f"gravado: {SAIDA.name}")
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
