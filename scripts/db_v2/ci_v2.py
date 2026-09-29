"""ci_v2 — checagem do Database v2 em modo COMPATIBILIDADE/SOMBRA (CI).

    python3 scripts/db_v2/ci_v2.py [--report v2-report.json]

Etapas (todas offline, sem secrets, determinísticas):
  1. testes do v2 (test_db_v2.py);
  2. lift do data.js para um diretório TEMPORÁRIO;
  3. validate_v2 sobre a sombra;
  4. export_legacy --check: a sombra tem de reproduzir o data.js byte a byte.

Falha (saída 1) em qualquer erro estrutural E_* do validador, em teste quebrado, em round-trip divergente,
em registro 'curated' na sombra ou se o data.js publicado mudar durante a execução.
Lacunas de completude (W_*), unknown herdado, módulo sugerido e sugestões de curadoria NÃO falham: vão para o
resumo ($GITHUB_STEP_SUMMARY, quando existir) e para o relatório JSON (artifact).
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import io
import json
import os
import pathlib
import sys
import tempfile
import unittest

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import bibliografia as B  # noqa: E402
import export_legacy as X  # noqa: E402
import lift_v1 as LF  # noqa: E402
import v2lib as L  # noqa: E402
import validate_v2 as V  # noqa: E402


def sem_rede() -> None:
    """Garante execução offline: qualquer tentativa de conexão neste processo vira erro."""
    import socket

    def bloqueado(*_a, **_k):
        raise RuntimeError("ci_v2 roda offline: acesso à rede bloqueado")

    class SocketSemRede(socket.socket):
        def connect(self, *_a, **_k):
            bloqueado()

        def connect_ex(self, *_a, **_k):
            bloqueado()

    socket.socket = SocketSemRede  # type: ignore[misc]
    socket.create_connection = bloqueado  # type: ignore[assignment]


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def rodar_testes() -> tuple[bool, str]:
    buf = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromNames(["test_db_v2", "test_bibliografia"])
    res = unittest.TextTestRunner(stream=buf, verbosity=0).run(suite)
    return res.wasSuccessful(), f"{res.testsRun} testes, {len(res.failures)} falhas, {len(res.errors)} erros"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default="v2-report.json")
    ap.add_argument("--base-ref", default="HEAD^", help="commit contra o qual o uid tem de ser imutável")
    a = ap.parse_args(argv)
    sem_rede()
    sha_antes = sha(L.DATA_JS)
    relatorio = {"modo": "shadow/compatibilidade", "data_js_sha256": sha_antes, "etapas": {}}
    falhas = []

    ok, txt = rodar_testes()
    relatorio["etapas"]["testes"] = {"ok": ok, "resumo": txt}
    if not ok:
        falhas.append(f"testes: {txt}")

    with tempfile.TemporaryDirectory(prefix="db_v2_shadow_") as tmp:
        sombra = pathlib.Path(tmp) / "shadow"
        saida = io.StringIO()
        _stdout, sys.stdout = sys.stdout, saida
        try:
            LF.main(["--out", str(sombra)])
        finally:
            sys.stdout = _stdout
        lift = json.loads(saida.getvalue())
        relatorio["etapas"]["lift"] = {k: lift[k] for k in ("cards", "record_type", "estados", "incertezas", "sugestoes")}

        recs, arqs = V.carregar(sombra)
        curados = [u for u, r in recs.items() if r["curation"]["level"] == "curated"]
        atuais = {c["uid"]: c for c in L.ler_data_js(L.DATA_JS.read_text(encoding="utf-8"))[1]["studies"]}
        base = V.uids_head(a.base_ref)
        relatorio["base_ref"] = a.base_ref if base is not None else f"{a.base_ref} indisponível (checagem de uid pulada)"
        rep = V.validar(recs, arqs, base, atuais)
        for u in curados:
            rep.add(u, "E_CURATED_IN_SHADOW", "curation.level", "a sombra do CI nunca contém registro curated")
        cod = collections.Counter(i["codigo"] for i in rep.itens)
        erros = rep.erros()
        relatorio["etapas"]["validate_v2"] = {
            "registros": len(recs), "erros": len(erros), "codigos": dict(sorted(cod.items())),
            "lacunas_mais_frequentes": collections.Counter(
                i["caminho"] for i in rep.itens if i["codigo"] == "W_REQUIRED").most_common(10),
            "primeiros_erros": erros[:50]}
        if erros:
            falhas.append(f"validate_v2: {len(erros)} erro(s) estrutural(is)")

        gerado = X.exportar(sombra)
        cmp_ = X.comparar(gerado, L.DATA_JS.read_text(encoding="utf-8"))
        relatorio["etapas"]["export_legacy"] = {k: v for k, v in cmp_.items() if k != "cards_divergentes"}
        relatorio["etapas"]["export_legacy"]["cards_divergentes"] = cmp_["cards_divergentes"][:20]
        if not cmp_["bytes_identicos"]:
            falhas.append("export_legacy: a sombra não reproduz o data.js byte a byte")

    # camada bibliográfica (informativo): cobertura do snapshot e cards com citation estruturada
    estudos = L.ler_data_js(L.DATA_JS.read_text(encoding="utf-8"))[1]["studies"]
    snap = B.carregar_snapshot() if B.SNAPSHOT.exists() else {}
    pmids = {B.pmid_do_card(c) for c in estudos} - {None}
    relatorio["etapas"]["bibliografia"] = {"cards_com_citation": sum(1 for c in estudos if c.get("citation")),
                                           "pmids": len(pmids), "pmids_fora_do_snapshot": sorted(pmids - set(snap))}

    sha_depois = sha(L.DATA_JS)
    if sha_depois != sha_antes:
        falhas.append("o data.js publicado mudou durante o CI do v2")
    relatorio["falhas"] = falhas
    relatorio["resultado"] = "FAIL" if falhas else "PASS"
    pathlib.Path(a.report).write_text(json.dumps(relatorio, ensure_ascii=False, indent=1), encoding="utf-8")

    v = relatorio["etapas"]["validate_v2"]
    linhas = [
        "## Database v2 — modo sombra",
        f"**{relatorio['resultado']}** · data.js `{sha_antes[:12]}` inalterado: {'sim' if sha_depois == sha_antes else 'NÃO'}",
        "",
        "| etapa | resultado |", "|---|---|",
        f"| testes | {relatorio['etapas']['testes']['resumo']} |",
        f"| lift | {lift['cards']} registros-sombra; {lift['incertezas']} incertezas; {lift['sugestoes']} sugestões |",
        f"| validate_v2 | {v['erros']} erro(s); {v['codigos'].get('W_REQUIRED', 0)} lacunas de completude (não bloqueiam) |",
        f"| export_legacy | byte a byte: {'sim' if relatorio['etapas']['export_legacy']['bytes_identicos'] else 'NÃO'} |",
        f"| bibliografia | {relatorio['etapas']['bibliografia']['cards_com_citation']} cards com citation; "
        f"{len(relatorio['etapas']['bibliografia']['pmids_fora_do_snapshot'])} PMID(s) fora do snapshot (não bloqueia) |",
    ]
    if falhas:
        linhas += ["", "### Falhas", *[f"- {f}" for f in falhas]]
    texto = "\n".join(linhas) + "\n"
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write(texto)
    print(texto)
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
