# -*- coding: utf-8 -*-
"""
Prepara .streamlit/secrets.toml partendo dal JSON del service account.

Esiste per un motivo solo: il campo `private_key` contiene delle sequenze \n che
ricopiate a mano nel TOML si rompono quasi sempre, e l'errore che ne esce
("No key could be detected", "Incorrect padding") non dice niente di utile.

Uso:
    python prepara_segreti.py CHIAVE.json FILE_ID [PASSWORD_GENITORE]

    CHIAVE.json        il JSON scaricato da Google Cloud Console
    FILE_ID            il pezzo dell'indirizzo del file su Drive fra /d/ e /view:
                       https://drive.google.com/file/d/QUESTO_PEZZO/view
    PASSWORD_GENITORE  facoltativa. Apre l'area "Per i grandi" nell'app, da cui
                       si vedono le statistiche di tutte e si reimpostano i
                       codici dimenticati. Se non la metti, quell'area resta
                       chiusa quando l'app e' pubblicata (scelta voluta: meglio
                       inaccessibile che aperta a tutti per una dimenticanza).

Scrive .streamlit/secrets.toml e stampa a schermo lo stesso contenuto, da
incollare nei Secrets di Streamlit Community Cloud.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

CAMPI_ATTESI = ("type", "project_id", "private_key_id", "private_key",
                "client_email", "client_id", "token_uri")


def componi(credenziali: dict, file_id: str, password: str | None) -> str:
    righe = [
        "# Generato da prepara_segreti.py — NON caricare questo file su GitHub.",
        "",
        "[drive]",
        f'file_id = "{file_id}"',
        "",
    ]
    if password:
        righe += ["[genitore]", f'password = "{password}"', ""]
    righe.append("[gcp_service_account]")
    for campo, valore in credenziali.items():
        if campo == "private_key":
            # Le sequenze \n restano letterali: e' cosi' che le vuole google-auth.
            fuggito = valore.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')
            righe.append(f'{campo} = "{fuggito}"')
        else:
            righe.append(f'{campo} = "{valore}"')
    return "\n".join(righe) + "\n"


def main() -> None:
    if len(sys.argv) not in (3, 4):
        print(__doc__)
        raise SystemExit(1)

    percorso_json = Path(sys.argv[1]).expanduser()
    file_id = sys.argv[2].strip()
    password = sys.argv[3].strip() if len(sys.argv) == 4 else None

    if not percorso_json.exists():
        raise SystemExit(f"File non trovato: {percorso_json}")
    if "/" in file_id or len(file_id) < 20:
        raise SystemExit("Il secondo argomento deve essere solo il file_id, "
                         "non l'indirizzo completo. Sta fra /d/ e /view.")
    if password is not None and len(password) < 8:
        raise SystemExit("La password del genitore deve essere di almeno 8 caratteri.")
    if password and '"' in password:
        raise SystemExit("Evita le virgolette doppie nella password.")

    credenziali = json.loads(percorso_json.read_text(encoding="utf-8"))
    mancanti = [c for c in CAMPI_ATTESI if c not in credenziali]
    if mancanti:
        raise SystemExit("Il JSON non sembra la chiave di un service account. "
                         f"Campi mancanti: {', '.join(mancanti)}")

    contenuto = componi(credenziali, file_id, password)
    destinazione = Path(__file__).resolve().parent / ".streamlit" / "secrets.toml"
    destinazione.parent.mkdir(exist_ok=True)
    destinazione.write_text(contenuto, encoding="utf-8")

    print(f"Scritto: {destinazione}")
    print(f"Service account: {credenziali['client_email']}")
    if not password:
        print("Nessuna password genitore: l'area «Per i grandi» sara' chiusa "
              "sull'app pubblicata. Rilancia con un terzo argomento per attivarla.")
    print()
    print("Controlla che l'email del service account compaia fra i condivisi "
          "della cartella su Drive, con ruolo Editor.")
    print()
    print("--- da incollare nei Secrets di Streamlit Community Cloud ---")
    print(contenuto)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        pass          # succede solo quando l'output viene troncato (| head)
