#!/usr/bin/env python3
"""
br_discover.py — descoberta determinística dos ensaios oncológicos com centro no Brasil.

Etapa 1 do pipeline do Trial Matcher. NÃO usa IA: só consulta o ClinicalTrials.gov,
aplica os filtros e faz o diff contra o que já está publicado em trials_br.js.

Substitui o fetch_brazil_trials.py, cuja busca era uma allowlist de fármacos
hardcoded — só encontrava o que já se sabia procurar, então fármaco novo nunca
aparecia. Aqui o corte é "oncologia + Brasil + recrutando", e a filtragem do que
não serve é feita depois, sobre o resultado.

Saída: scripts/_br_discovery.json  (bruto + diff, para as etapas seguintes)

Uso:
    python3 scripts/br_discover.py                    # todas as neoplasias
    python3 scripts/br_discover.py --neoplasia pulmao # um lote só
    python3 scripts/br_discover.py --resumo           # só o relatório, não grava
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://clinicaltrials.gov/api/v2/studies"
SITE = Path(__file__).resolve().parent.parent
TRIALS_JS = SITE / "assets" / "js" / "trials_br.js"
OUT = Path(__file__).resolve().parent / "_br_discovery.json"

# Condições oncológicas. Amplo de propósito — o refinamento é feito depois.
CONDICAO = (
    "cancer OR neoplasm OR carcinoma OR tumor OR leukemia OR lymphoma "
    "OR myeloma OR sarcoma OR melanoma OR glioma OR blastoma"
)

STATUS = ["RECRUITING", "NOT_YET_RECRUITING"]

# `query.cond` do CT.gov faz busca semântica e devolve falsos positivos: um
# estudo de CAR-T anti-CD19 em miastenia gravis entra por "leukemia/lymphoma"
# mesmo sendo doença autoimune. Este segundo filtro roda sobre o campo
# `conditions` do próprio registro — se nenhuma condição declarada for
# oncológica, o estudo cai fora.
# Cobrir as duas ortografias — o CT.gov mistura registros em inglês americano e
# britânico, e um estudo de LMA registrado como "Acute Myeloid Leukaemia" cairia
# fora de um padrão que só aceitasse "leukemi".
ONCOLOGICO = re.compile(
    r"cancer|carcinom|neoplas|tumou?r|sarcom|lymphom|linfom|leuk[ae]{1,2}mi|leucem"
    r"|myelom|mielom|melanom|gliom|glioblastom|blastom|mesotheliom|mesoteliom"
    r"|myelodysplas|mielodisplas|myeloprolifer|mieloprolifer|mastocytos|mastocitos"
    r"|adenocarcinom|cholangiocarcinom|colangiocarcinom|hepatocellular|hepatocarcinom"
    r"|astrocytom|oligodendrogliom|meningiom|seminom|teratom|thymom|timom"
    r"|mycosis fungoides|s[eé]zary|waldenstr|\bgist\b|neuroendocrine|neuroendócrin"
    r"|paraganglio|pheochromocytom|feocromocitom|malign|metasta|metásta"
    r"|myelofibros|mielofibros|polycythemia vera|essential thrombocythemi",
    re.I,
)

# Campos necessários para a curadoria. Pedir só isto em vez do registro
# inteiro (~70 KB/estudo) reduz o payload em cerca de 10x.
CAMPOS = [
    "NCTId", "BriefTitle", "OfficialTitle", "Acronym", "BriefSummary",
    "OverallStatus", "Phase", "StudyType", "LeadSponsorName", "CollaboratorName",
    "Condition", "EligibilityCriteria", "MinimumAge", "MaximumAge", "Sex",
    "ArmGroupLabel", "ArmGroupDescription", "ArmGroupType", "InterventionName",
    "InterventionDescription", "InterventionType",
    "LocationFacility", "LocationCity", "LocationState", "LocationCountry",
    "LocationStatus", "LastUpdatePostDate", "StudyFirstPostDate", "EnrollmentCount",
]

# Teranósticos ficam no database principal (data.js), não no Trial Matcher.
# Mesma lista do curate_trials.py original.
TERANOSTICO = re.compile(
    r"psma-617|lu-?177|177-?lu|225-?ac|ac-?225|actinium|radium-?223|ra-?223"
    r"|radioligand|lutetium|lutécio|dotatate|dotatoc|mibg|y-?90|yttrium|ítrio"
    r"|pluvicto|aaa817|azedra|xofigo|iodine-?131 therapy|holmium",
    re.I,
)

# O campo `city` do CT.gov é texto livre preenchido pelo patrocinador, e vem
# sujo de três formas distintas:
#   1. bairro no lugar da cidade      — "Asa Sul", "Barra da Tijuca", "Bela Vista"
#   2. erro de digitação              — "Porto Algre", "Rio de Janerio", "SJRP"
#   3. estado ou país no lugar da cidade — "Bahia", "Paraná", "Brazil"
# Sem normalizar, cada variação vira uma "cidade" diferente e o card lista o
# mesmo centro várias vezes, ou o perde por não achar a UF.
ALIAS_CIDADE = {
    # bairros → município
    "asa sul": "Brasília", "lago sul": "Brasília",
    "barra da tijuca": "Rio de Janeiro", "curicica": "Rio de Janeiro",
    "bela vista": "São Paulo", "cerqueira cesar": "São Paulo",
    "jardim paulista": "São Paulo", "santa cecilia": "São Paulo",
    # erros de digitação encontrados no registro
    "porto alegre - rs": "Porto Alegre", "porto alegrers": "Porto Alegre",
    "porto alegree": "Porto Alegre", "porto alegrev": "Porto Alegre",
    "porto algre": "Porto Alegre",
    "rio de janerio": "Rio de Janeiro",
    "sjrp": "São José do Rio Preto", "san jose rio preto": "São José do Rio Preto",
    "sao jose rio preto": "São José do Rio Preto",
    "sao jose rio preto ": "São José do Rio Preto",
    "ssanta cruz do sul": "Santa Cruz do Sul",
    "natal/rn": "Natal",
    "curitibapr": "Curitiba", "portalegre": "Porto Alegre",
    "riberao preto": "Ribeirão Preto", "cachoeira de itapemirim": "Cachoeiro de Itapemirim",
    "fortaleza ceara": "Fortaleza", "recife pernambuco": "Recife",
    "sao jose rio": "São José do Rio Preto",
    # bairros de São Paulo
    "liberdade": "São Paulo", "vila mariana": "São Paulo", "vila olimpia": "São Paulo",
}

# Valores que não são município — o centro entra na lista, mas sem cidade/UF.
NAO_CIDADE = {
    "brazil", "brasil", "bahia", "goias", "parana", "minas gerai", "minas gerais",
    "sao paulo state", "rio grande do sul", "ceara", "santa catarina", "sp",
    "rj", "mg", "rs", "pr", "sc", "ba", "pe", "ce",
}


def _chave(cidade: str) -> str:
    """Minúsculas, sem acento e sem espaço duplicado — para casar aliases."""
    import unicodedata
    s = unicodedata.normalize("NFD", cidade.strip().lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return " ".join(s.split())


def normalizar_cidade(bruto: str) -> str:
    """Devolve o município canônico, ou '' se o valor não for uma cidade."""
    k = _chave(bruto)
    if not k or k in NAO_CIDADE:
        return ""
    if k in ALIAS_CIDADE:
        return ALIAS_CIDADE[k]
    # casa contra o mapa oficial ignorando acento/caixa
    for oficial in CIDADE_UF:
        if _chave(oficial) == k:
            return oficial
    return bruto.strip()


# Cidade -> UF. Herdado do curate_trials_v2.py e ampliado.
CIDADE_UF = {
    "São Paulo": "SP", "Sao Paulo": "SP", "Barretos": "SP", "Campinas": "SP",
    "Ribeirão Preto": "SP", "Ribeirao Preto": "SP", "São José do Rio Preto": "SP",
    "Sao Jose do Rio Preto": "SP", "Santo André": "SP", "Sorocaba": "SP",
    "Jaú": "SP", "Jau": "SP", "Presidente Prudente": "SP", "Taubaté": "SP",
    "Rio de Janeiro": "RJ", "Niterói": "RJ", "Niteroi": "RJ",
    "Belo Horizonte": "MG", "Juiz de Fora": "MG", "Uberlândia": "MG", "Muriaé": "MG",
    "Porto Alegre": "RS", "Pelotas": "RS", "Caxias do Sul": "RS", "Ijuí": "RS",
    "Curitiba": "PR", "Londrina": "PR", "Maringá": "PR", "Cascavel": "PR",
    "Florianópolis": "SC", "Florianopolis": "SC", "Joinville": "SC", "Blumenau": "SC",
    "Itajaí": "SC", "Lages": "SC", "Criciúma": "SC",
    "Salvador": "BA", "Feira de Santana": "BA", "Itabuna": "BA",
    "Recife": "PE", "Caruaru": "PE", "Fortaleza": "CE", "Natal": "RN",
    "João Pessoa": "PB", "Maceió": "AL", "Aracaju": "SE", "Teresina": "PI",
    "São Luís": "MA", "Sao Luis": "MA", "Belém": "PA", "Manaus": "AM",
    "Brasília": "DF", "Brasilia": "DF", "Goiânia": "GO", "Goiania": "GO",
    "Campo Grande": "MS", "Cuiabá": "MT", "Cuiaba": "MT", "Vitória": "ES",
    "Vitoria": "ES", "Cachoeiro de Itapemirim": "ES", "Palmas": "TO",
    "Porto Velho": "RO", "Rio Branco": "AC", "Macapá": "AP", "Boa Vista": "RR",
    # acrescentadas em 2026-08 a partir do aviso de cidades sem UF
    "Araçatuba": "SP", "Bauru": "SP", "Botucatu": "SP", "Bragança Paulista": "SP",
    "Jales": "SP", "São Caetano do Sul": "SP", "São Carlos": "SP",
    "São José dos Campos": "SP",
    "Alfenas": "MG", "Betim": "MG", "Divinópolis": "MG", "Ipatinga": "MG",
    "Nova Lima": "MG",
    "Bento Gonçalves": "RS", "Lajeado": "RS", "Passo Fundo": "RS",
    "Rio Grande": "RS", "Santa Cruz do Sul": "RS", "Santa Maria": "RS",
    "Petrópolis": "RJ", "Volta Redonda": "RJ", "São José do Vale do Rio Preto": "RJ",
    "Chapecó": "SC", "Timbó": "SC",
    "Mossoró": "RN", "Bequimão": "MA", "Vitória da Conquista": "BA",
    "Barueri": "SP", "Canoas": "RS", "Piracicaba": "SP", "Pouso Alegre": "MG",
    "Santos": "SP", "Três Lagoas": "MS", "Uberaba": "MG",
}


def http_json(url: str, tentativas: int = 4) -> dict:
    """GET com backoff. A API do CT.gov devolve 429 sob rajada."""
    for n in range(tentativas):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "TheraTrials/1.0 (+https://theratrials.com)"}
            )
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001 — queremos repetir em qualquer falha de rede
            if n == tentativas - 1:
                raise
            espera = 2 ** n
            print(f"[discover] {e} — nova tentativa em {espera}s", file=sys.stderr)
            time.sleep(espera)
    raise RuntimeError("inalcançável")


def buscar() -> list[dict]:
    """Todos os intervencionais oncológicos com centro no Brasil, recrutando."""
    estudos, token, pagina = [], None, 0
    while True:
        params = {
            "query.cond": CONDICAO,
            "query.locn": "Brazil",
            "filter.overallStatus": "|".join(STATUS),
            "filter.advanced": "AREA[StudyType]INTERVENTIONAL",
            "fields": "|".join(CAMPOS),
            "pageSize": "200",
            "countTotal": "true",
        }
        if token:
            params["pageToken"] = token
        d = http_json(f"{API}?{urllib.parse.urlencode(params)}")
        lote = d.get("studies", [])
        estudos.extend(lote)
        pagina += 1
        total = d.get("totalCount")
        print(f"[discover] página {pagina}: +{len(lote)} (acumulado {len(estudos)}"
              f"{f'/{total}' if total else ''})", file=sys.stderr)
        token = d.get("nextPageToken")
        if not token:
            break
        time.sleep(0.5)
    return estudos


def achatar(s: dict) -> dict:
    """Extrai do registro só o que a curadoria precisa, já em formato plano."""
    p = s.get("protocolSection", {})
    ident = p.get("identificationModule", {})
    status = p.get("statusModule", {})
    design = p.get("designModule", {})
    desc = p.get("descriptionModule", {})
    elig = p.get("eligibilityModule", {})
    sponsor = p.get("sponsorCollaboratorsModule", {})
    cond = p.get("conditionsModule", {})
    arms = p.get("armsInterventionsModule", {})
    locs = p.get("contactsLocationsModule", {}).get("locations", [])

    br = [l for l in locs if l.get("country") == "Brazil"]

    # O par cidade→UF precisa andar junto. Guardar duas listas paralelas e
    # reassociá-las depois por posição produz "Salvador / RJ" — as listas são
    # deduplicadas e ordenadas de forma independente, então o índice i de uma
    # não corresponde ao da outra.
    locais = []
    vistos = set()
    for l in br:
        cidade = normalizar_cidade(l.get("city") or "")
        if not cidade or cidade in vistos:
            continue
        vistos.add(cidade)
        # `state` do CT.gov vem por extenso e inconsistente; o mapa local é
        # mais confiável. Sem correspondência, fica vazio e o card mostra só
        # a cidade — melhor do que uma UF errada.
        locais.append({"cidade": cidade, "uf": CIDADE_UF.get(cidade, "")})
    locais.sort(key=lambda x: x["cidade"])

    cidades = [l["cidade"] for l in locais]
    ufs = sorted({l["uf"] for l in locais} - {""})
    centros = sorted({l.get("facility", "").strip() for l in br if l.get("facility")})
    sem_uf = [l["cidade"] for l in locais if not l["uf"]]

    return {
        "nct": ident.get("nctId", ""),
        "acronimo": ident.get("acronym", ""),
        "titulo_breve": ident.get("briefTitle", ""),
        "titulo_oficial": ident.get("officialTitle", ""),
        "resumo": desc.get("briefSummary", ""),
        "status_ctgov": status.get("overallStatus", ""),
        "ultima_atualizacao": status.get("lastUpdatePostDateStruct", {}).get("date", ""),
        "fases": design.get("phases", []),
        "n_previsto": design.get("enrollmentInfo", {}).get("count"),
        "condicoes": cond.get("conditions", []),
        "patrocinador": sponsor.get("leadSponsor", {}).get("name", ""),
        "colaboradores": [c.get("name", "") for c in sponsor.get("collaborators", [])],
        "elegibilidade": elig.get("eligibilityCriteria", ""),
        "idade_min": elig.get("minimumAge", ""),
        "idade_max": elig.get("maximumAge", ""),
        "sexo": elig.get("sex", ""),
        "bracos": [
            {"rotulo": a.get("label", ""), "tipo": a.get("type", ""),
             "descricao": a.get("description", "")}
            for a in arms.get("armGroups", [])
        ],
        "intervencoes": [
            {"tipo": i.get("type", ""), "nome": i.get("name", ""),
             "descricao": i.get("description", "")}
            for i in arms.get("interventions", [])
        ],
        "centros_br": centros,
        "locais_br": locais,      # [{cidade, uf}] — o par preservado
        "cidades_br": cidades,
        "ufs_br": ufs,
        "cidades_sem_uf": sem_uf,  # alimenta o aviso de CIDADE_UF incompleto
        "n_centros_br": len(br),
    }


def eh_teranostico(e: dict) -> bool:
    blob = " ".join([
        e["titulo_breve"], e["titulo_oficial"], e["resumo"],
        " ".join(i["nome"] for i in e["intervencoes"]),
    ])
    return bool(TERANOSTICO.search(blob))


def eh_oncologico(e: dict) -> bool:
    """Alguma das condições declaradas no registro é oncológica?"""
    return any(ONCOLOGICO.search(c) for c in e.get("condicoes", []))


# O Trial Matcher lista ensaios de TRATAMENTO antineoplásico — o que o médico
# pode oferecer ao paciente. A busca por condição também traz estudos de suporte
# e reabilitação (dança, exercício, meditação em VR, wearables, luvas cirúrgicas):
# pesquisa legítima, mas de outra natureza.
# `InterventionType` é um campo estruturado do registro, então o corte é objetivo
# — não depende de interpretar título.
TIPOS_TRATAMENTO = {
    "DRUG", "BIOLOGICAL", "RADIATION", "PROCEDURE", "GENETIC", "COMBINATION_PRODUCT",
}


def eh_tratamento(e: dict) -> bool:
    return any(i.get("tipo") in TIPOS_TRATAMENTO for i in e.get("intervencoes", []))


def publicados() -> dict[str, dict]:
    """Lê os NCTs já publicados direto do trials_br.js, sem executar JS.

    O arquivo é JS escrito à mão — chaves sem aspas e valores em aspas simples
    (`nct: 'NCT06119581',`). Os padrões abaixo aceitam as duas convenções para
    não quebrar se um card vier de um pipeline que serialize como JSON.
    """
    txt = TRIALS_JS.read_text(encoding="utf-8")
    campo = lambda k: rf"""['"]?{k}['"]?\s*:\s*['"]([^'"]*)['"]"""  # noqa: E731
    atual = {}
    for m in re.finditer(campo("nct"), txt):
        nct = re.search(r"NCT\d{8}", m.group(1))
        if not nct:
            continue  # ISRCTN, EudraCT, "Sem NCT" — não dá para casar com o CT.gov
        depois = txt[m.end(): m.end() + 1200]
        antes = txt[max(0, m.start() - 1200): m.start()]
        st = re.search(campo("status"), depois)
        nome = re.findall(campo("nome"), antes)
        atual[nct.group(0)] = {
            "status": st.group(1) if st else "",
            "nome": nome[-1] if nome else "",
        }
    return atual


# CT.gov -> vocabulário de `status` do trials_br.js (ver THERA_TRIALS_BR_META).
STATUS_MAP = {
    "RECRUITING": "Recrutando",
    "NOT_YET_RECRUITING": "Ainda não recrutando",
    "SUSPENDED": "Recrutamento suspenso",
    "ACTIVE_NOT_RECRUITING": "Encerrado",
    "COMPLETED": "Encerrado",
    "TERMINATED": "Encerrado",
    "WITHDRAWN": "Encerrado",
}


def classificar(achatados: list[dict], ja: dict[str, dict]) -> dict:
    novos, mudou_status, inalterados = [], [], []
    teranosticos, nao_onco, suporte = [], [], []
    for e in achatados:
        if not eh_oncologico(e):
            nao_onco.append({"nct": e["nct"], "condicoes": e["condicoes"],
                             "titulo": e["titulo_breve"][:70]})
            continue
        if not eh_tratamento(e):
            suporte.append({"nct": e["nct"], "titulo": e["titulo_breve"][:70],
                            "tipos": sorted({i["tipo"] for i in e["intervencoes"]})})
            continue
        if eh_teranostico(e):
            teranosticos.append(e)
            continue
        if e["nct"] not in ja:
            novos.append(e)
            continue
        esperado = STATUS_MAP.get(e["status_ctgov"], "")
        atual = ja[e["nct"]]["status"]
        if esperado and atual and esperado != atual:
            mudou_status.append({
                "nct": e["nct"], "nome": ja[e["nct"]]["nome"],
                "de": atual, "para": esperado,
            })
        else:
            inalterados.append(e["nct"])

    # Publicados que sumiram do resultado = provavelmente encerraram o recrutamento.
    vistos = {e["nct"] for e in achatados}
    sumiram = [
        {"nct": n, "nome": v["nome"], "status_publicado": v["status"]}
        for n, v in ja.items() if n not in vistos and n.startswith("NCT")
    ]
    return {
        "novos": novos, "mudou_status": mudou_status,
        "inalterados": inalterados, "teranosticos": teranosticos,
        "sumiram": sumiram, "nao_oncologicos": nao_onco, "suporte": suporte,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--resumo", action="store_true", help="só relata, não grava o JSON")
    ap.add_argument("--limite", type=int, default=0, help="corta a lista (para testes)")
    args = ap.parse_args()

    print("[discover] consultando ClinicalTrials.gov…", file=sys.stderr)
    brutos = buscar()
    achatados = [achatar(s) for s in brutos]
    achatados = [e for e in achatados if e["nct"] and e["n_centros_br"] > 0]
    if args.limite:
        achatados = achatados[: args.limite]

    ja = publicados()
    d = classificar(achatados, ja)

    print()
    print("=" * 62)
    print(f"  ENCONTRADOS no CT.gov ...... {len(achatados)}")
    print(f"  já publicados .............. {len(ja)}")
    print("-" * 62)
    print(f"  NOVOS (curar) .............. {len(d['novos'])}")
    print(f"  status mudou ............... {len(d['mudou_status'])}")
    print(f"  inalterados ................ {len(d['inalterados'])}")
    print(f"  teranósticos (-> data.js) .. {len(d['teranosticos'])}")
    print(f"  publicados que sumiram ..... {len(d['sumiram'])}")
    print(f"  descartados: não-oncológico  {len(d['nao_oncologicos'])}")
    print(f"  descartados: não é tratamento {len(d['suporte'])}")
    print("=" * 62)

    if d["nao_oncologicos"]:
        print("\nDESCARTADOS — condição não é oncológica:")
        for x in d["nao_oncologicos"][:8]:
            print(f"   {x['nct']}  {', '.join(x['condicoes'])[:52]}")
    faltando = sorted({c for e in d["novos"] for c in e.get("cidades_sem_uf", [])})
    if faltando:
        print(f"\n⚠ CIDADES SEM UF no mapa CIDADE_UF ({len(faltando)}) — "
              f"os cards sairão só com a cidade:")
        for c in faltando[:20]:
            print(f"   {c}")

    if d["suporte"]:
        print("\nDESCARTADOS — suporte/reabilitação, não tratamento antineoplásico:")
        for x in d["suporte"][:8]:
            print(f"   {x['nct']}  [{','.join(x['tipos'])[:22]:24s}] {x['titulo'][:42]}")

    if d["mudou_status"]:
        print("\nMUDANÇA DE STATUS:")
        for m in d["mudou_status"][:20]:
            print(f"   {m['nct']}  {m['nome'][:34]:36s} {m['de']} -> {m['para']}")

    # Distribuição por condição, para escolher a ordem dos lotes.
    from collections import Counter
    c = Counter()
    for e in d["novos"]:
        c[(e["condicoes"] or ["(sem condição)"])[0][:40]] += 1
    print(f"\nNOVOS por condição (top 18 de {len(c)}):")
    for cond, n in c.most_common(18):
        print(f"   {n:4d}  {cond}")

    if not args.resumo:
        OUT.write_text(json.dumps({
            "gerado_em": datetime.now(timezone.utc).isoformat(),
            "total_ctgov": len(achatados),
            "ja_publicados": len(ja),
            **d,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\n[discover] gravado: {OUT.relative_to(SITE)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
