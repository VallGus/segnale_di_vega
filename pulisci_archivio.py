# -*- coding: utf-8 -*-
"""
Ispeziona e ripulisce l'archivio (su Drive o locale).

Serve per togliere le giocatrici di prova finite nell'archivio vero, o per
ripartire da zero.

Uso:
    python pulisci_archivio.py                       elenca cosa c'e' dentro
    python pulisci_archivio.py --togli marta irene   rimuove quelle giocatrici
    python pulisci_archivio.py --azzera              svuota tutto

Le rimozioni chiedono conferma. Prima di modificare qualcosa viene salvata una
copia dell'archivio in salvataggi/copia_prima_della_pulizia_<data>.json: se
qualcosa va storto si rimette a mano.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import archivio as A
import motore as M


def copia_di_sicurezza(dati: dict) -> Path:
    A.CARTELLA_LOCALE.mkdir(parents=True, exist_ok=True)
    percorso = (A.CARTELLA_LOCALE /
                f"copia_prima_della_pulizia_{time.strftime('%Y%m%d_%H%M%S')}.json")
    percorso.write_text(json.dumps(dati, ensure_ascii=False, indent=1), encoding="utf-8")
    return percorso


def elenca(dati: dict) -> list[str]:
    slot = sorted(set(dati.get("partite", {})) | set(dati.get("storici", {}))
                  | set(dati.get("credenziali", {})))
    if not slot:
        print("  (archivio vuoto)")
        return []
    print(f"  {'giocatrice':<16} {'partita':<10} {'codice':<8} {'risposte':>9}  ultimo salvataggio")
    for s in slot:
        partita = dati.get("partite", {}).get(s)
        storico_s = dati.get("storici", {}).get(s) or {}
        risposte = storico_s.get("totale_ok", 0) + storico_s.get("totale_ko", 0)
        print(f"  {s:<16} {'sì' if partita else '—':<10} "
              f"{'sì' if s in dati.get('credenziali', {}) else '—':<8} "
              f"{risposte:>9}  {(partita or {}).get('salvato', '—')}")
    return slot


def conferma(domanda: str) -> bool:
    risposta = input(f"{domanda} [scrivi CONFERMO] ").strip()
    return risposta == "CONFERMO"


def main() -> None:
    dove = "Google Drive" if A.modalita() == "drive" else str(A.percorso_locale())
    print(f"Archivio: {dove}\n")

    dati = A.leggi(forza=True)
    if A.ultimo_errore():
        raise SystemExit(f"Non riesco a leggere l'archivio → {A.ultimo_errore()}")

    slot = elenca(dati)
    print()

    if "--azzera" in sys.argv:
        if not slot:
            print("Niente da azzerare.")
            return
        print(f"Sto per svuotare TUTTO l'archivio su {dove}.")
        if not conferma("Confermi?"):
            print("Annullato, niente toccato.")
            return
        print(f"Copia di sicurezza: {copia_di_sicurezza(dati)}")
        vuoto = A.archivio_vuoto()
        print("Fatto." if A.scrivi(vuoto) else f"NON riuscito → {A.ultimo_errore()}")
        return

    if "--togli" in sys.argv:
        richiesti = [M.pulisci_slot(a) for a in sys.argv[sys.argv.index("--togli") + 1:]
                     if not a.startswith("--")]
        da_togliere = [s for s in richiesti if s in slot]
        ignorati = [s for s in richiesti if s not in slot]
        if ignorati:
            print(f"Non presenti, salto: {', '.join(ignorati)}")
        if not da_togliere:
            print("Niente da rimuovere.")
            return
        print(f"Sto per rimuovere da {dove}: {', '.join(da_togliere)}")
        print("Partita, statistiche e codice di queste giocatrici andranno perse.")
        if not conferma("Confermi?"):
            print("Annullato, niente toccato.")
            return
        print(f"Copia di sicurezza: {copia_di_sicurezza(dati)}")

        def modifica(arch: dict) -> None:
            for s in da_togliere:
                arch["partite"].pop(s, None)
                arch["storici"].pop(s, None)
                arch["credenziali"].pop(s, None)
            arch["accessi"] = [v for v in arch.get("accessi", [])
                               if v.get("slot") not in da_togliere]

        if A.aggiorna(modifica):
            print("Fatto. Situazione adesso:")
            elenca(A.leggi(forza=True))
        else:
            print(f"NON riuscito → {A.ultimo_errore()}")
        return

    print("Nessuna modifica richiesta. Opzioni: --togli NOME [NOME...] oppure --azzera")


if __name__ == "__main__":
    main()
