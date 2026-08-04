#!/usr/bin/env python3
"""
br_instituicoes.py — resolve o nome da instituição recrutadora.

O campo `facility` do ClinicalTrials.gov é texto livre, preenchido por cada
patrocinador, e a mesma casa aparece de até vinte formas diferentes:

    Fundacao Antonio Prudente
    Fundacao Antonio Prudente - AC Camargo Cancer Center /ID# 260827
    A. C. Camargo Cancer Center ( Site 0310)
    A.C.Camargo Cancer Center - Centro Internacional de Pesquisa (CIPE)

São quatro registros de um único hospital. Contar `facility` cru multiplica o
número de centros por dois. Este módulo devolve um nome canônico por
instituição, para que a contagem e a exibição batam com a realidade.

Três coisas que NÃO são nome de instituição e precisam sair da contagem:

  1. placeholder anônimo — "Research Site", "Novartis Investigative Site",
     "Local Institution - 0165", "Site 134". O patrocinador optou por não
     revelar o centro. Existe um centro ali, mas não dá para nomeá-lo.
  2. endereço no lugar do nome — "Av. Ipiranga 6690", "Rua Professor Annes
     Dias, 295 - Centro Histórico".
  3. nome do próprio patrocinador — "MSD Brasil".

Nesses casos `resolver()` devolve (None, motivo): o centro continua contando
como um local naquela cidade, mas entra como "centro não identificado".

Regra de agregação: unidades da mesma marca na mesma cidade contam como UMA.
Duas unidades da Rede D'Or em São Paulo viram um centro. É deliberado e
conservador — erra para menos, nunca para mais, e é reprodutível. O número
publicado é, portanto, um piso.

Uso:
    from br_instituicoes import resolver
    nome, motivo = resolver("A. C. Camargo Cancer Center ( Site 0310)", "São Paulo")
"""
from __future__ import annotations

import re
import unicodedata


def _dea(s: str) -> str:
    """Minúsculas, sem acento — base para casar padrão."""
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


# ── 1. o que não é instituição ────────────────────────────────────────────
PLACEHOLDER = re.compile(
    r"^\s*("
    r"research site|clinical (trial|research) site|investigational site|"
    r"local institution\b.*|site\s*[0-9]+|"
    r"[a-z]{2,14} (investigational|investigative|clinical) site|"
    r"msd brasil|"
    r"centro de pesquisa clinica - area administrativa"
    r")\s*$",
    re.I,
)

# Começa com tipo de logradouro, ou é só "palavra + número". Brasília usa
# setor/quadra em vez de rua ("St. de Habitações Individuais Sul QI 15").
#
# O ponto abreviativo é opcional e o separador tem de ser espaço explícito:
# escrever `st\.` seguido de `\b` NÃO casa "St. de Habitações" — entre o "."
# e o espaço não existe fronteira de palavra, então a alternativa nunca
# dispara e o endereço passava como se fosse nome de hospital.
ENDERECO = re.compile(
    # `setor` fica de fora de propósito: não aparece em nenhum registro real e
    # "Setor de Oncologia do Hospital X" seria nome legítimo de centro.
    r"^\s*(av|avenida|rua|r|travessa|alameda|praca|rodovia|estrada|"
    r"st|quadra|sqn|sqs|shis|qi)\.?\s"
    r"|^\s*[a-z\s]+\s+\d{2,5}\s*$",
    re.I,
)


# ── 2. instituições com muitas grafias ────────────────────────────────────
# (cidade normalizada | None p/ qualquer, padrão no nome sem acento, canônico)
# A primeira regra que casar vence, então o mais específico vem antes.
CANONICOS: list[tuple[str | None, str, str]] = [
    # ---- São Paulo
    ("sao paulo", r"antonio prudente|a\.?\s?c\.?\s?camargo|\bcipe\b", "A.C.Camargo Cancer Center"),
    ("sao paulo", r"icesp|cancer do estado de sao paulo|octavio frias", "ICESP – Instituto do Câncer do Estado de São Paulo"),
    ("sao paulo", r"beneficencia portuguesa|beneficancia portuguesa|beneficiencia portuguesa|"
                  r"real e benemerita associacao portuguesa|hospital bp\b|^bp\b",
     "BP – A Beneficência Portuguesa de São Paulo"),
    ("sao paulo", r"\bibcc\b|brasileiro de controle|brazilian institute for cancer control", "IBCC Oncologia"),
    ("sao paulo", r"albert einstein|israelita brasileira", "Hospital Israelita Albert Einstein"),
    ("sao paulo", r"sirio.?libanes|senhoras hospital sirio", "Hospital Sírio-Libanês"),
    ("sao paulo", r"onco.?star", "Onco Star (Rede D'Or)"),
    ("sao paulo", r"\bd.?or\b|\bidor\b|oncologia rede d", "Instituto D'Or de Pesquisa e Ensino (IDOR)"),
    # O HC-FMUSP aparece com oito grafias diferentes no CT.gov — inclusive
    # traduzido para o inglês e nomeado pelo serviço em vez do hospital. Sem
    # todas aqui, a mesma casa entrava oito vezes na contagem de centros.
    # A USP crua ("University of Sao Paulo") fica DE FORA de propósito: o ICESP
    # também é USP, e o NCT05996367 usa exatamente essa grafia sendo do ICESP.
    ("sao paulo", r"clinicas da faculdade de medicina|clinicas d[ae] fmusp|clinicas fmusp|"
                  r"\bhcfmusp\b|faculdade de medicina da usp|clinicas de sao paulo|"
                  r"clinicas da universidade de sao paulo|clinical hospital of medicine school",
     "Hospital das Clínicas da FMUSP"),
    ("sao paulo", r"santa marcelina", "Hospital Santa Marcelina"),
    ("sao paulo", r"(9|nove) de julho", "Hospital 9 de Julho"),
    ("sao paulo", r"oncoclinicas|centro paulista de oncologia", "Oncoclínicas São Paulo"),
    ("sao paulo", r"perola byington", "Hospital Pérola Byington"),
    ("sao paulo", r"samaritano", "Hospital Samaritano"),
    ("sao paulo", r"alemao oswaldo cruz", "Hospital Alemão Oswaldo Cruz"),
    ("sao paulo", r"servidor publico estadual|iamspe", "IAMSPE"),
    ("sao paulo", r"graacc", "GRAACC"),
    ("sao paulo", r"unifesp|universidade federal de sao paulo", "Hospital São Paulo (UNIFESP)"),
    ("sao paulo", r"santa casa de misericordia de sao paulo", "Santa Casa de Misericórdia de São Paulo"),
    ("sao paulo", r"santa catarina", "Hospital Santa Catarina"),
    ("sao paulo", r"paulistano", "Hospital Paulistano"),
    ("sao paulo", r"hospital do coracao|\bhcor\b", "Hospital do Coração (HCor)"),
    ("sao paulo", r"arnaldo vieira", "Instituto do Câncer Arnaldo Vieira de Carvalho"),
    ("sao paulo", r"hemomed", "Instituto Hemomed"),
    ("sao paulo", r"sao germano", "Clínica Médica São Germano"),
    ("sao paulo", r"sao camilo", "Rede São Camilo"),
    ("sao paulo", r"sao lucas", "Instituto de Ensino e Pesquisas São Lucas"),

    # ---- Porto Alegre
    ("porto alegre", r"clinicas de porto alegre|\bhcpa\b|\bupco\b", "Hospital de Clínicas de Porto Alegre (HCPA)"),
    ("porto alegre", r"sao lucas|pucrs|pontificia universidade catolica do rio grande|"
                     r"uniao brasileira de educacao", "Hospital São Lucas da PUCRS"),
    ("porto alegre", r"santa casa", "Santa Casa de Misericórdia de Porto Alegre"),
    ("porto alegre", r"mae de deus|gaucho integrado", "Hospital Mãe de Deus"),
    ("porto alegre", r"moinhos de vento", "Hospital Moinhos de Vento"),
    ("porto alegre", r"nossa senhora da conceicao", "Hospital Nossa Senhora da Conceição"),
    ("porto alegre", r"ernesto dornelles", "Hospital Ernesto Dornelles"),
    ("porto alegre", r"futtura", "FUTTURA Oncologia"),
    ("porto alegre", r"medplex", "MedPlex Eixo Norte"),
    ("porto alegre", r"crianca santo antonio", "Hospital da Criança Santo Antônio"),

    # ---- Rio de Janeiro
    ("rio de janeiro", r"\binca\b|instituto nacional de cancer|instituto nacional do cancer|"
                       r"national cancer institute|jose de alencar", "INCA – Instituto Nacional de Câncer"),
    ("rio de janeiro", r"americas|educacao, pesquisa e gestao em saude|educacao pesquisa e gestao", "Américas Centro de Oncologia Integrado"),
    ("rio de janeiro", r"\bd.?or\b|\bidor\b|\bdaor\b", "Instituto D'Or de Pesquisa e Ensino (IDOR)"),
    ("rio de janeiro", r"oncoclinicas|botafogo", "Oncoclínicas Rio de Janeiro"),
    ("rio de janeiro", r"\bcoi\b", "Instituto COI"),
    ("rio de janeiro", r"sao lucas", "Hospital São Lucas Dasa"),

    # ---- Salvador
    ("salvador", r"\bamo\b|clinica amo|etica", "AMO – Assistência Multidisciplinar em Oncologia"),
    ("salvador", r"nucleo de oncologia da bahia|\bnob\b", "Núcleo de Oncologia da Bahia (NOB)"),
    ("salvador", r"sao rafael", "Hospital São Rafael"),
    ("salvador", r"irma dulce", "Obras Sociais Irmã Dulce"),
    ("salvador", r"santa izabel", "Hospital Santa Izabel"),
    ("salvador", r"\bhba\b|hospital da bahia", "Hospital da Bahia"),
    ("salvador", r"\bd.?or\b|\bidor\b", "Instituto D'Or de Pesquisa e Ensino (IDOR)"),

    # ---- demais capitais e polos
    # Hemocentro e Hospital de Clínicas são unidades distintas da UNICAMP, mas
    # a fusão aqui é por marca + cidade: para quem encaminha um paciente, o
    # destino é a UNICAMP. Cinco grafias viravam cinco centros.
    ("campinas", r"\bunicamp\b|universidade estadual de campinas|universidade de campinas",
     "UNICAMP – Universidade Estadual de Campinas"),
    ("natal", r"liga norte", "Liga Norte-Riograndense Contra o Câncer"),
    ("barretos", r"pio xii|hospital de amor|hospital de cancer de barretos", "Hospital de Amor (Fundação Pio XII)"),
    ("sao jose do rio preto", r"faculdade regional de medicina|famerp|hospital de base|\bhb onco\b",
     "Hospital de Base / FAMERP"),
    ("fortaleza", r"\bcrio\b|regional integrado de oncologia", "CRIO – Centro Regional Integrado de Oncologia"),
    ("fortaleza", r"instituto do cancer do ceara|\bicc\b", "Instituto do Câncer do Ceará"),
    ("goiania", r"araujo jorge", "Hospital Araújo Jorge"),
    ("belo horizonte", r"mario penna", "Hospital Mário Penna"),
    ("belo horizonte", r"\bcetus\b", "Cetus Oncologia"),
    ("curitiba", r"erasto gaertner|liga paranaense", "Hospital Erasto Gaertner"),
    ("curitiba", r"\bcionc\b|centro integrado (de )?oncologia", "CIONC – Centro Integrado de Oncologia de Curitiba"),
    ("curitiba", r"evangelico mackenzie|\bhuem\b", "Hospital Universitário Evangélico Mackenzie"),
    ("curitiba", r"\bictr\b|ictrials|cancer e transplante", "ICTR – Instituto do Câncer e Transplante de Curitiba"),
    ("curitiba", r"\biop\b|oncologia do parana", "IOP – Instituto de Oncologia do Paraná"),
    ("curitiba", r"santa cruz", "Hospital Santa Cruz"),
    # HCP e IMIP são casas diferentes: o primeiro é o Hospital de Câncer de
    # Pernambuco, o segundo o Instituto de Medicina Integral Fernando Figueira.
    ("recife", r"cancer de pernambuco|\bhcp\b", "Hospital de Câncer de Pernambuco"),
    ("recife", r"medicina integral|fernando figueira|\bimip\b", "IMIP – Instituto de Medicina Integral Prof. Fernando Figueira"),
    ("recife", r"real hospital portugues|beneficencia portuguesa|beneficiencia", "Real Hospital Português de Beneficência"),
    ("recife", r"santa joana", "Hospital Santa Joana Recife"),
    ("recife", r"oswaldo cruz|unipeclin", "Hospital Universitário Oswaldo Cruz (UNIPECLIN)"),
    ("brasilia", r"sirio.?libanes", "Hospital Sírio-Libanês (Brasília)"),
    ("brasilia", r"hospital brasilia|dasa|impar servicos", "Hospital Brasília (DASA)"),
    ("brasilia", r"df star", "DF Star"),
    ("brasilia", r"onco.?vida", "Onco-Vida"),
    ("belo horizonte", r"oncocentro|oncolinicas|oncoclinicas", "Oncocentro (Oncoclínicas)"),
    ("belo horizonte", r"personal oncologia", "PERSONAL Oncologia de Precisão e Personalizada"),
    ("belo horizonte", r"cenantron", "Cenantron – Centro Avançado de Tratamento Oncológico"),
    ("belo horizonte", r"felicio rocho", "Hospital Felício Rocho"),
    ("belo horizonte", r"santa casa", "Santa Casa de Misericórdia de Belo Horizonte"),
    # CEPON e CEPEN são instituições distintas em Florianópolis — o primeiro é
    # o centro estadual de oncologia, o segundo um centro de ensino/pesquisa.
    ("florianopolis", r"\bcepon\b|pesquisas oncologicas", "CEPON – Centro de Pesquisas Oncológicas"),
    ("florianopolis", r"\bcepen\b|ensino em oncologia", "CEPEN – Centro de Pesquisa e Ensino em Oncologia de SC"),
    ("fortaleza", r"oncocentro|sao carlos", "Oncocentro – Hospital São Carlos"),
    ("fortaleza", r"pronutrir|suporte nutricional", "Pronutrir Oncologia"),
    ("londrina", r"londrina", "Instituto de Câncer de Londrina"),
    ("santa cruz do sul", r"saint gallen", "Instituto de Oncologia Saint Gallen"),
    ("ijui", r"oncosite", "ONCOSITE – Centro de Pesquisa Clínica em Oncologia"),
    ("blumenau", r"reichow", "Clínica de Oncologia Reichow"),
    ("jau", r"amaral carvalho", "Hospital Amaral Carvalho"),
    ("vitoria", r"afecc|santa rita", "Hospital Santa Rita de Cássia (AFECC)"),
    ("teresina", r"vencer", "Vencer Centro de Pesquisa Clínica"),
    ("passo fundo", r"sao vicente de paulo", "Hospital São Vicente de Paulo"),
    ("lages", r"animi", "ANIMI – Unidade de Tratamento Oncológico"),
    ("ribeirao preto", r"ribeirao preto|fmrp", "Hospital das Clínicas da FMRP-USP"),
    ("santo andre", r"\bcepho\b|hematologia e oncologia", "CEPHO – Centro de Estudos e Pesquisas em Hematologia e Oncologia"),
    ("santo andre", r"\babc\b|fmabc", "Faculdade de Medicina do ABC"),
    ("sao caetano do sul", r"ceon", "CEON+ – Centro de Oncologia do ABC"),
    ("vitoria", r"cedoes", "CEDOES – Diagnóstico e Pesquisa"),
    ("sorocaba", r"unimed|\biepe\b", "IEPE – Unimed Sorocaba"),
    ("itajai", r"neoplasias litoral|catarina pesquisa", "Clínica de Neoplasias Litoral"),
    ("belem", r"\bcto\b|tratamento oncologico", "CTO – Centro de Tratamento Oncológico"),
    ("belem", r"cpam|amazonia", "CPAM – Centro de Pesquisas da Amazônia"),
    ("cachoeiro de itapemirim", r"evangelico|cachoeiro|pesquisas clinicas em oncologia",
     "Hospital Evangélico de Cachoeiro de Itapemirim"),
    ("bauru", r"\bnaic\b", "NAIC – Instituto do Câncer"),
    ("bento goncalves", r"tacchini", "Hospital Tacchini"),
    ("braganca paulista", r"sao francisco", "Hospital Universitário São Francisco de Assis"),
    ("caxias do sul", r"caxias do sul", "Universidade de Caxias do Sul"),
    ("ijui", r"caridade", "Hospital de Caridade de Ijuí"),
    ("joinville", r"hematologia", "Instituto Joinvilense de Hematologia e Oncologia"),
    ("natal", r"liga contra o cancer", "Liga Norte-Riograndense Contra o Câncer"),
    ("santa maria", r"viver", "Clínica Viver"),
    ("sao luis", r"sao domingos", "Hospital São Domingos"),
    ("teresina", r"oncologistas associados", "Oncoclínica Oncologistas Associados"),
    ("volta redonda", r"oswaldo aranha", "Hospital da Fundação Oswaldo Aranha"),
    # "Hospital de Câncer de Recife" e HCP são a mesma casa — o registro usa
    # a cidade no lugar do estado no nome.
    ("recife", r"hospital de cancer de recife", "Hospital de Câncer de Pernambuco"),

    ("sao paulo", r"oncologia ginecologica e mamaria", "Clínica de Pesquisas e Centro de Estudos em Oncologia Ginecológica e Mamária"),

    # ---- redes com presença em várias cidades (sem trava de cidade)
    (None, r"\boncoclinicas\b|centro paulista de oncologia", "Oncoclínicas"),
    (None, r"\bidor\b|instituto d.?or de pesquisa|rede d.?or", "Instituto D'Or de Pesquisa e Ensino (IDOR)"),

    # ---- casas grafadas sob a cidade errada no registro.
    # O CT.gov traz Hospital de Amor com city='São Paulo' e a Santa Casa de
    # Porto Alegre idem. A regra travada por cidade não dispara nesses casos,
    # então o nome canônico vem por regra global — o card mostra a cidade que
    # o registro informou, mas ao menos não duplica a instituição.
    (None, r"amaral carvalho", "Hospital Amaral Carvalho"),
    (None, r"pio xii|hospital de amor|hospital de cancer de barretos", "Hospital de Amor (Fundação Pio XII)"),
    (None, r"famerp|\bhb onco\b|faculdade regional de medicina", "Hospital de Base / FAMERP"),
    (None, r"santa casa de misericordia de porto alegre", "Santa Casa de Misericórdia de Porto Alegre"),
]


# ── 3. limpeza do nome que não casou nenhuma regra ────────────────────────
LIXO = [
    (r"\(\s*site\s*[0-9\-]+\s*\)", ""),          # "( Site 0310)"
    (r"/\s*id#?\s*[0-9\-]+", ""),                # "/ID# 260827"
    (r"\bid#?\s*[0-9]{4,}\b", ""),
    (r"\s*[-–]\s*$", ""),
    (r"\s*\b(ltda|s/s|s\.a\.?|sa|eireli|me)\b\.?\s*$", ""),
    (r"\s{2,}", " "),
]


def _limpar(nome: str) -> str:
    s = nome.strip()
    for pat, rep in LIXO:
        s = re.sub(pat, rep, s, flags=re.I)
    s = s.strip(" -–,;/")
    # ALL CAPS vira Title Case; nomes com caixa mista o registro já grafou bem.
    if s and s == s.upper() and len(s) > 6:
        s = s.title()
        # siglas de 2–5 letras coladas em Title Case voltam a maiúsculas
        s = re.sub(r"\b(Ibcc|Icesp|Inca|Crio|Nob|Amo|Hcpa|Ufrj|Usp|Hc|Idor|Bp)\b",
                   lambda m: m.group(1).upper(), s)
    return " ".join(s.split())


def resolver(facility: str, cidade: str) -> tuple[str | None, str]:
    """
    Devolve (nome_canonico, motivo).

    nome_canonico é None quando o registro não nomeia o centro; `motivo` diz
    por quê ('placeholder', 'endereco', 'vazio') ou 'ok' / 'canonico'.
    """
    bruto = (facility or "").strip()
    if not bruto:
        return None, "vazio"
    # Casar sempre contra a versão sem acento: os padrões abaixo são escritos
    # sem acento, e "Área Administrativa" não casava "area administrativa".
    alvo = _dea(bruto)
    if PLACEHOLDER.match(alvo):
        return None, "placeholder"
    if ENDERECO.match(alvo):
        return None, "endereco"

    cid = _dea(cidade or "")
    for cidade_regra, padrao, canonico in CANONICOS:
        if cidade_regra and cidade_regra != cid:
            continue
        if re.search(padrao, alvo):
            return canonico, "canonico"

    limpo = _limpar(bruto)
    return (limpo, "ok") if limpo else (None, "vazio")
