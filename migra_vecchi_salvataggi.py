# -*- coding: utf-8 -*-
"""
Porta i salvataggi della versione precedente nell'archivio nuovo.

La versione vecchia scriveva un file per partita (salvataggi/marta.json). Quella
nuova usa un unico documento (salvataggi/archivio_vega.json, o Google Drive).
Questo script legge i vecchi file e li travasa, fondendo anche le statistiche
accumulate nello storico permanente: cosi' le tabelline gia' allenate non
ripartono da zero.

Uso:
    python migra_vecchi_salvataggi.py            # mostra cosa farebbe
    python migra_vecchi_salvataggi.py --scrivi   # esegue

Non cancella niente: i vecchi file restano dove sono.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import archivio as A
import motore as M
import storico as ST

# I file dell'archivio nuovo e delle prove non sono salvataggi vecchi.
DA_IGNORARE = {"archivio_vega.json"}


def vecchi_file() -> list[Path]:
    if not A.CARTELLA_LOCALE.exists():
        return []
    return sorted(
        percorso for percorso in A.CARTELLA_LOCALE.glob("*.json")
        if percorso.name not in DA_IGNORARE and not percorso.name.startswith("_")
    )


def leggi(percorso: Path) -> dict | None:
    try:
        dati = json.loads(percorso.read_text(encoding="utf-8"))
    except Exception as errore:
        print(f"  {percorso.name}: illeggibile ({errore}) — salto")
        return None
    if not isinstance(dati, dict) or "nodo" not in dati:
        print(f"  {percorso.name}: non sembra un salvataggio — salto")
        return None
    return dati


def main() -> None:
    scrivi_davvero = "--scrivi" in sys.argv
    trovati = vecchi_file()

    if not trovati:
        print(f"Nessun salvataggio vecchio in {A.CARTELLA_LOCALE}.")
        print("Se li stai recuperando da un backup, rimettili li' e rilancia.")
        return

    print(f"Archivio di destinazione: {A.percorso_locale() if A.modalita() == 'locale' else 'Google Drive'}")
    print(f"Trovati {len(trovati)} file da migrare.\n")

    da_migrare = []
    for percorso in trovati:
        dati = leggi(percorso)
        if dati is None:
            continue
        slot = M.pulisci_slot(percorso.stem)
        statistiche = dati.get("statistiche", {})
        risposte = sum(v.get("ok", 0) + v.get("ko", 0) for v in statistiche.values())
        print(f"  {percorso.name} -> slot '{slot}'")
        print(f"      giocatrice: {dati.get('nome', '?')} · "
              f"frammenti: {len(dati.get('frammenti', []))}/6 · "
              f"risposte da fondere nello storico: {risposte}")
        da_migrare.append((slot, dati, statistiche))

    if not da_migrare:
        print("\nNiente di utilizzabile.")
        return

    if not scrivi_davvero:
        print("\nProva a vuoto: non ho scritto niente.")
        print("Per eseguire davvero:  python migra_vecchi_salvataggi.py --scrivi")
        return

    print()
    for slot, dati, statistiche in da_migrare:
        storico_slot = M.carica_storico(slot)
        aggiunte = ST.assorbi_partita(storico_slot, statistiche)
        if not storico_slot.get("sessioni"):
            storico_slot["sessioni"] = 1
        riuscito = M.salva(dati, slot, storico_slot, 0)
        esito = "fatto" if riuscito else f"NON riuscito ({A.ultimo_errore()})"
        print(f"  {slot}: {aggiunte} risposte nello storico · {esito}")

    print("\nControllo finale — partite ora nell'archivio:")
    A.invalida_cache()
    for voce in M.elenco_salvataggi():
        print(f"  {voce['slot']} · {voce['capitolo']} · {voce['frammenti']}/6 · {voce['salvato']}")
    print("\nI vecchi file non sono stati toccati: cancellali a mano quando sei "
          "sicuro che tutto torni.")


if __name__ == "__main__":
    main()
