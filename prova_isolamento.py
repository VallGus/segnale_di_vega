# -*- coding: utf-8 -*-
"""
Prova che le prove non possano toccare Google Drive.

Si lancia con:  python prova_isolamento.py

Riproduce la situazione che ha causato il guaio: credenziali Drive configurate
(come sulla macchina di casa) e una prova in corso. Se l'isolamento funziona,
la prova scrive su file e la strada verso Drive non viene nemmeno imboccata.

Questo test va lanciato PRIMA degli altri quando si tocca archivio.py: e' quello
che protegge i dati veri.
"""

from __future__ import annotations

import os

os.environ["VEGA_ARCHIVIO"] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "salvataggi", "_prova_isolamento.json"
)

import archivio as A          # noqa: E402
import motore as M            # noqa: E402

esiti: list[bool] = []


def controlla(descrizione: str, condizione: bool) -> None:
    esiti.append(bool(condizione))
    print(f"  [{'ok' if condizione else 'FALLITO'}] {descrizione}")


def main() -> None:
    A.percorso_locale().unlink(missing_ok=True)
    A.invalida_cache()

    print("1. Senza credenziali")
    controlla("modalita' locale", A.modalita() == "locale")
    controlla("percorso di prova in uso",
              A.percorso_locale().name == "_prova_isolamento.json")

    print("\n2. Con credenziali Drive presenti (la situazione di casa)")
    veri_segreti = A._segreti
    A._segreti = lambda: {
        "credenziali": {"client_email": "bot@progetto.iam.gserviceaccount.com"},
        "file_id": "FILE_ID_FINTO_ABBASTANZA_LUNGO",
    }
    try:
        controlla("modalita' ANCORA locale", A.modalita() == "locale")

        # Se qualcuno imboccasse la strada di Drive, queste funzioni esploderebbero:
        # le sostituiamo con trappole che segnalano il passaggio.
        passaggi: list[str] = []
        veri = (A._leggi_drive, A._scrivi_drive)
        A._leggi_drive = lambda: passaggi.append("lettura") or {}
        A._scrivi_drive = lambda dati: passaggi.append("scrittura")
        try:
            storico_g = M.carica_storico("cavia")
            stato = M.nuovo_stato("Cavia", storico_g)
            M.salva(stato, "cavia", storico_g, 1)
            M.imposta_credenziale("cavia", {"algoritmo": "pbkdf2_sha256", "sale": "00",
                                            "impronta": "00", "iterazioni": 1})
            controlla("Drive non e' stato mai chiamato", passaggi == [])
        finally:
            A._leggi_drive, A._scrivi_drive = veri

        controlla("il file di prova esiste", A.percorso_locale().exists())
        controlla("i dati sono nel file di prova",
                  "cavia" in A.percorso_locale().read_text(encoding="utf-8"))
        controlla("l'archivio vero non e' stato creato",
                  not (A.CARTELLA_LOCALE / "archivio_vega.json").exists()
                  or "cavia" not in (A.CARTELLA_LOCALE / "archivio_vega.json")
                  .read_text(encoding="utf-8"))
    finally:
        A._segreti = veri_segreti

    print("\n3. Senza VEGA_ARCHIVIO le credenziali tornano a contare")
    del os.environ["VEGA_ARCHIVIO"]
    A.invalida_cache()
    A._segreti = lambda: {"credenziali": {"client_email": "x@y.z"}, "file_id": "X" * 25}
    try:
        controlla("modalita' drive quando serve", A.modalita() == "drive")
    finally:
        A._segreti = veri_segreti

    falliti = esiti.count(False)
    print(f"\n{len(esiti) - falliti}/{len(esiti)} prove superate.")
    if falliti:
        raise SystemExit(1)
    print("Tutto verde: le prove non possono raggiungere Drive.")


if __name__ == "__main__":
    main()
