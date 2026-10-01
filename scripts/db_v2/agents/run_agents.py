"""run_agents — executa database-curator / database-verifier pelas DEFINIÇÕES de .claude/agents, com auditoria.

    python3 scripts/db_v2/agents/run_agents.py curator <uid> [<uid> ...] [--paralelo 4]
    python3 scripts/db_v2/agents/run_agents.py verifier <uid> [<uid> ...] [--paralelo 4]
    python3 scripts/db_v2/agents/run_agents.py verifier_b <uid> ...   # 2ª verificação independente dos itens P0
    python3 scripts/db_v2/agents/run_agents.py discovery_curator <uid> ...    # modo discovery (state/discovery/<uid>)
    python3 scripts/db_v2/agents/run_agents.py discovery_verifier <uid> ...

Cada execução roda o Claude Code em modo não interativo A PARTIR DO REPOSITÓRIO, com `--agent database-<papel>`, para
que a definição versionada (inclusive `tools: Read, Grep, Glob`) seja a que vale. A execução é auditada pelo
stream-json e FALHA explicitamente (nada é ingerido) se:
  • o conjunto de ferramentas do init ≠ {Read, Grep, Glob} (ferramenta permitida ausente também falha: sem fallback);
  • o agente chama qualquer outra ferramenta, ou tem permissão negada;
  • o agente lê/procura arquivo fora do pacote do card, do schema e da tarefa.
Os agentes não escrevem arquivos: a saída é a resposta final (JSON), gravada aqui em state/raw/. Transcrição e
auditoria em state/runs/. Nada escreve no Database.
"""
from __future__ import annotations

import concurrent.futures as cf
import glob
import json
import os
import pathlib
import subprocess
import sys

AQUI = pathlib.Path(__file__).resolve().parent
SITE = AQUI.parents[2]
try:
    from . import curator as C, decision_packet as D, delta as DL, discovery as DS, sources as S, verifier as V
except ImportError:
    import delta as DL
    import discovery as DS
    import curator as C
    import sources as S
    import verifier as V
    import decision_packet as D

PERMITIDAS = {"Read", "Grep", "Glob"}
PROIBIDAS_CLI = "Bash,Edit,Write,MultiEdit,NotebookEdit,WebFetch,WebSearch,Agent,Task,Skill,TodoWrite"
RUNS = S.STATE / "runs"
RAW = S.STATE / "raw"


class ExecucaoInvalida(Exception):
    pass


def binario() -> str:
    if os.environ.get("THERATRIALS_CLAUDE_BIN"):
        return os.environ["THERATRIALS_CLAUDE_BIN"]
    cands = sorted(glob.glob(os.path.expanduser(
        "~/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude")))
    if not cands:
        raise ExecucaoInvalida("Claude Code CLI não encontrado (defina THERATRIALS_CLAUDE_BIN)")
    return cands[-1]


def _prompt(papel: str, uid: str) -> tuple[str, list[pathlib.Path]]:
    pacote = S.STATE / "packets" / uid
    schemas = AQUI / "schemas"
    if papel == "curator":
        return (C.tarefa(uid) + "\nLeia só o pacote e o schema acima. Responda APENAS com o JSON.", [pacote, schemas])
    if papel in ("discovery_curator", "discovery_verifier"):      # modo discovery: pasta própria do card
        pasta = S.STATE / "discovery" / uid
        tarefa = DS.tarefa(uid) if papel == "discovery_curator" else DS.tarefa_verifier(uid)
        return (tarefa + "Leia só o diretório do card acima e o schema. Responda APENAS com o JSON.", [pasta, schemas])
    if papel in ("delta_curator", "delta_verifier"):              # delta editorial: componente separado
        pasta = S.STATE / "delta" / uid
        tarefa = DL.tarefa(uid) if papel == "delta_curator" else DL.tarefa_verifier(uid)
        return (tarefa + "Leia só o diretório acima, as instruções e o schema. Responda APENAS com o JSON.",
                [pasta, schemas, DL.INSTRUCOES])
    if papel == "verifier_b":                       # segunda verificação independente, só dos itens P0
        V.entrada(uid, so_ids=D.candidatos_b(uid), sufixo="_b")
        tarefa = S.STATE / "tasks" / f"{uid}.verifier_input_b.json"
    else:
        V.entrada(uid)
        tarefa = S.STATE / "tasks" / f"{uid}.verifier_input.json"
    sha = json.loads(tarefa.read_text())["proposal_sha256"]
    return (f"Entrada: {tarefa}\nSchema de saída: {schemas / 'verification.schema.json'}\nuid: {uid} · "
            f"proposal_sha256: {sha}\nAvalie TODOS os itens e a relação. Leia só a entrada, o pacote do card e o "
            "schema. Responda APENAS com o JSON.", [pacote, schemas, tarefa])


def _caminhos(tool: str, entrada: dict) -> list[str]:
    return [entrada[k] for k in ("file_path", "path") if isinstance(entrada.get(k), str)]


def executar(papel: str, uid: str) -> dict:
    prompt, permitidos = _prompt(papel, uid)
    RUNS.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    agente = {"verifier_b": "database-verifier", "discovery_curator": "database-curator",
              "discovery_verifier": "database-verifier", "delta_curator": "database-curator",
              "delta_verifier": "database-verifier"}.get(papel, f"database-{papel}")   # mesma definição, contexto novo
    cmd = [binario(), "-p", prompt, "--agent", agente, "--output-format", "stream-json", "--verbose",
           "--disallowedTools", PROIBIDAS_CLI]
    proc = subprocess.run(cmd, cwd=SITE, capture_output=True, text=True, timeout=1800)
    (RUNS / f"{uid}.{papel}.jsonl").write_text(proc.stdout, encoding="utf-8")
    audit = {"uid": uid, "papel": papel, "agent": agente, "cwd": str(SITE), "tools_init": None,
             "tools_usadas": [], "caminhos": [], "violacoes": [], "resultado": None, "custo_usd": None}
    final = None
    for linha in proc.stdout.splitlines():
        try:
            e = json.loads(linha)
        except json.JSONDecodeError:
            continue
        if e.get("type") == "system" and e.get("subtype") == "init":
            audit["tools_init"] = sorted(e.get("tools") or [])
        if e.get("type") == "assistant":
            for b in (e.get("message") or {}).get("content") or []:
                if b.get("type") == "tool_use":
                    audit["tools_usadas"].append(b["name"])
                    audit["caminhos"] += _caminhos(b["name"], b.get("input") or {})
        if e.get("type") == "result":
            final = e.get("result")
            audit["resultado"] = e.get("subtype")
            audit["custo_usd"] = e.get("total_cost_usd")
            if e.get("permission_denials"):
                audit["violacoes"].append(f"permissão negada: {e['permission_denials']}")
    if set(audit["tools_init"] or []) != PERMITIDAS:
        audit["violacoes"].append(f"ferramentas do init {audit['tools_init']} ≠ {sorted(PERMITIDAS)}")
    for t in set(audit["tools_usadas"]) - PERMITIDAS:
        audit["violacoes"].append(f"ferramenta proibida usada: {t}")
    for c in audit["caminhos"]:
        p = pathlib.Path(c).resolve()
        if not any(p == d or d in p.parents for d in [x.resolve() for x in permitidos]):
            audit["violacoes"].append(f"leitura fora do pacote: {c}")
    if proc.returncode != 0 or final is None:
        audit["violacoes"].append(f"execução falhou (código {proc.returncode}): {proc.stderr[-300:]}")
    (RUNS / f"{uid}.{papel}.audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    if audit["violacoes"]:
        raise ExecucaoInvalida(f"{uid}/{papel}: {audit['violacoes']}")
    (RAW / f"{uid}.{papel}.json").write_text(final, encoding="utf-8")
    return audit


def main(argv=None) -> int:
    a = list(argv or sys.argv[1:])
    par = 4
    if "--paralelo" in a:
        i = a.index("--paralelo")
        par = int(a[i + 1])
        del a[i:i + 2]
    papel, uids = a[0], a[1:]
    assert papel in ("curator", "verifier", "verifier_b", "discovery_curator", "discovery_verifier",
                     "delta_curator", "delta_verifier"), papel
    if papel == "verifier_b":                        # só cards com item P0; os demais não têm o que reverificar
        sem = [u for u in uids if not D.candidatos_b(u)]
        for u in sem:
            print(f"SKIP verifier_b {u[:44]:44s} sem item P0 nem candidato a AUTO")
        uids = [u for u in uids if u not in sem]
    falhas = 0
    with cf.ThreadPoolExecutor(max_workers=par) as ex:
        futs = {ex.submit(executar, papel, u): u for u in uids}
        for f in cf.as_completed(futs):
            u = futs[f]
            try:
                au = f.result()
                print(f"OK   {papel:8s} {u[:44]:44s} tools={sorted(set(au['tools_usadas']))} "
                      f"leituras={len(au['caminhos'])} custo={au['custo_usd']}")
            except Exception as ex_:
                falhas += 1
                print(f"FAIL {papel:8s} {u[:44]:44s} {ex_}")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
