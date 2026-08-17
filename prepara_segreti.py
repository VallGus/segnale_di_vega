# -*- coding: utf-8 -*-
"""
Prepara .streamlit/secrets.toml partendo dal JSON del service account.

Esiste per un motivo solo: il campo `private_key` contiene delle sequenze \n che
ricopiate a mano nel TOML si rompono quasi sempre, e l'errore che ne esce
("No key could be detected", "Incorrect padding") non dice niente di utile.

Uso:
    python prepara_segreti.py ~/Downloads/segnale-di-vega-abc123.json FILE_ID

dove FILE_ID e' il pezzo dell'indirizzo del file su Drive fra /d/ e /view:
    https://drive.google.com/file/d/QUESTO_PEZZO/view

Scrive .streamlit/secrets.toml e stampa a schermo lo stesso contenuto, da
incollare nei Secrets di Streamlit Community Cloud.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

CAMPI_ATTESI = ("type", "project_id", "private_key_id", "private_key",
                "client_email", "client_id", "token_uri")


def componi(credenziali: dict, file_id: str) -> str:
    righe = [
        "# Generato da prepara_segreti.py — NON caricare questo file su GitHub.",
        "",
        "[drive]",
        f'file_id = "{file_id}"',
        "",
        "[gcp_service_account]",
    ]
    for campo, valore in credenziali.items():
        if campo == "private_key":
            # Le sequenze \n restano letterali: e' cosi' che le vuole google-auth.
            fuggito = valore.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')
            righe.append(f'{campo} = "{fuggito}"')
        else:
            righe.append(f'{campo} = "{valore}"')
    return "\n".join(righe) + "\n"


def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__)
        raise SystemExit(1)

    percorso_json, file_id = Path(sys.argv[1]).expanduser(), sys.argv[2].strip()

    if not percorso_json.exists():
        raise SystemExit(f"File non trovato: {percorso_json}")
    if "/" in file_id or len(file_id) < 20:
        raise SystemExit("Il secondo argomento deve essere solo il file_id, "
                         "non l'indirizzo completo. Sta fra /d/ e /view.")

    credenziali = json.loads(percorso_json.read_text(encoding="utf-8"))
    mancanti = [c for c in CAMPI_ATTESI if c not in credenziali]
    if mancanti:
        raise SystemExit("Il JSON non sembra la chiave di un service account. "
                         f"Campi mancanti: {', '.join(mancanti)}")

    contenuto = componi(credenziali, file_id)
    destinazione = Path(__file__).resolve().parent / ".streamlit" / "secrets.toml"
    destinazione.parent.mkdir(exist_ok=True)
    destinazione.write_text(contenuto, encoding="utf-8")

    print(f"Scritto: {destinazione}")
    print(f"Service account: {credenziali['client_email']}")
    print()
    print("Controlla che questa email compaia fra i condivisi della cartella "
          "su Drive, con ruolo Editor.")
    print()
    print("--- da incollare nei Secrets di Streamlit Community Cloud ---")
    print(contenuto)


if __name__ == "__main__":
    main()
