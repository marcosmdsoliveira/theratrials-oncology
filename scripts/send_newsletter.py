#!/usr/bin/env python3
"""
TheraTrials Oncology — Newsletter Sender (Buttondown)
===========================================================
Envia a newsletter gerada pelo generate_newsletter.py via API do Buttondown.

Requer:
  - Variável de ambiente BUTTONDOWN_API_KEY (secret no GitHub Actions)
  - Arquivo newsletters/YYYY-MM.md gerado previamente

A API do Buttondown é simples:
  POST https://api.buttondown.com/v1/emails
  Headers: Authorization: Token <API_KEY>
  Body: { "subject": "...", "body": "...", "status": "draft"|"about_to_send" }

Por padrão, cria como DRAFT para revisão manual.
Para envio direto, use: python scripts/send_newsletter.py --send

Sem dependências externas — só stdlib (urllib + json).

Uso local:
    export BUTTONDOWN_API_KEY=your_key_here
    python scripts/send_newsletter.py              # cria draft
    python scripts/send_newsletter.py --send       # envia direto

Uso CI (GitHub Action):
    Mesmo comando. A key vem do secrets.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
BUTTONDOWN_API = "https://api.buttondown.com/v1/emails"
THIS_FILE = Path(__file__).resolve()
SITE_DIR = THIS_FILE.parent.parent
NEWSLETTERS_DIR = SITE_DIR / "newsletters"

MONTHS_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def send_newsletter(edition: str | None = None, send_now: bool = False) -> int:
    """
    Envia a newsletter para Buttondown.

    Args:
        edition: "YYYY-MM" string. Se None, usa o mês atual.
        send_now: Se True, envia imediatamente. Se False, cria como draft.
    """
    api_key = os.environ.get("BUTTONDOWN_API_KEY")
    if not api_key:
        print("[newsletter] ERRO: BUTTONDOWN_API_KEY não definida.")
        print("[newsletter] Configure: export BUTTONDOWN_API_KEY=your_key")
        print("[newsletter] Ou adicione como secret no GitHub Actions.")
        return 1

    # Determine edition
    if not edition:
        now = datetime.now(timezone.utc)
        edition = now.strftime("%Y-%m")

    md_path = NEWSLETTERS_DIR / f"{edition}.md"
    if not md_path.exists():
        print(f"[newsletter] ERRO: Arquivo não encontrado: {md_path}")
        print(f"[newsletter] Execute generate_newsletter.py primeiro.")
        return 1

    # Read content
    body = md_path.read_text(encoding="utf-8")

    # Build subject
    year, month = edition.split("-")
    month_name = MONTHS_PT[int(month)]
    subject = f"TheraTrials Newsletter — {month_name} {year}"

    # API call
    status = "about_to_send" if send_now else "draft"
    payload = {
        "subject": subject,
        "body": body,
        "status": status,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BUTTONDOWN_API,
        data=data,
        headers={
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "TheraTrials-Oncology/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            email_id = result.get("id", "?")
            email_status = result.get("status", status)
            print(f"[newsletter] Sucesso!")
            print(f"  ID:      {email_id}")
            print(f"  Subject: {subject}")
            print(f"  Status:  {email_status}")
            if email_status == "draft":
                print(f"\n  A newsletter foi criada como RASCUNHO.")
                print(f"  Acesse https://buttondown.com/emails para revisar e enviar.")
            else:
                print(f"\n  A newsletter será enviada aos assinantes em breve.")
            return 0

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        print(f"[newsletter] ERRO HTTP {e.code}: {e.reason}")
        print(f"[newsletter] Resposta: {error_body}")
        return 1

    except urllib.error.URLError as e:
        print(f"[newsletter] ERRO de conexão: {e.reason}")
        return 1


def main():
    send_now = "--send" in sys.argv
    edition = None

    # Check for --edition YYYY-MM argument
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg == "--edition" and i < len(sys.argv) - 1:
            edition = sys.argv[i + 1]

    if send_now:
        print("[newsletter] Modo: ENVIO DIRETO (about_to_send)")
    else:
        print("[newsletter] Modo: RASCUNHO (draft)")
        print("[newsletter] Use --send para enviar diretamente.")

    return send_newsletter(edition=edition, send_now=send_now)


if __name__ == "__main__":
    sys.exit(main())
