# -*- coding: utf-8 -*-
"""
Prove sui codici segreti.

Si lancia con:  python prova_accessi.py

Verifica che:
  1. un codice giusto entri e uno sbagliato no;
  2. il codice non sia mai scritto in chiaro nell'archivio;
  3. due giocatrici con lo stesso codice abbiano impronte diverse (sale);
  4. i codici debolissimi vengano rifiutati;
  5. le partite di due giocatrici restino separate;
  6. il cambio di codice non tocchi partita e statistiche.
"""

from __future__ import annotations

import json
import os

os.environ["VEGA_ARCHIVIO"] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "salvataggi", "_prova_accessi.json"
)

import archivio as A          # noqa: E402
import identita as ID         # noqa: E402
import motore as M            # noqa: E402
import storico as ST          # noqa: E402

esiti: list[bool] = []


def controlla(descrizione: str, condizione: bool) -> None:
    esiti.append(bool(condizione))
    print(f"  [{'ok' if condizione else 'FALLITO'}] {descrizione}")


def main() -> None:
    A.percorso_locale().unlink(missing_ok=True)
    A.invalida_cache()

    print("1. Registrazione e verifica del codice")
    M.imposta_credenziale("marta", ID.crea("2468"))
    controlla("il nome risulta registrato", M.slot_registrato("marta"))
    controlla("codice giusto accettato", ID.verifica(M.credenziale("marta"), "2468"))
    controlla("codice sbagliato rifiutato", not ID.verifica(M.credenziale("marta"), "2469"))
    controlla("codice vuoto rifiutato", not ID.verifica(M.credenziale("marta"), ""))
    controlla("spazi e trattini ignorati", ID.verifica(M.credenziale("marta"), "24-68"))
    controlla("nome mai registrato non risulta", not M.slot_registrato("sconosciuta"))

    print("\n2. Il codice non finisce in chiaro nell'archivio")
    testo = A.percorso_locale().read_text(encoding="utf-8")
    controlla("la stringa '2468' non appare nel file", "2468" not in testo)
    credenziale = M.credenziale("marta")
    controlla("nessun campo contiene il codice",
              all("2468" not in str(v) for v in credenziale.values()))
    controlla("l'algoritmo e' dichiarato", credenziale["algoritmo"] == "pbkdf2_sha256")

    print("\n3. Sale diverso per ogni giocatrice")
    M.imposta_credenziale("irene", ID.crea("2468"))     # stesso codice di proposito
    controlla("impronte diverse a parita' di codice",
              M.credenziale("marta")["impronta"] != M.credenziale("irene")["impronta"])
    controlla("sali diversi",
              M.credenziale("marta")["sale"] != M.credenziale("irene")["sale"])
    controlla("il codice di Irene funziona comunque",
              ID.verifica(M.credenziale("irene"), "2468"))

    print("\n4. Codici troppo deboli rifiutati")
    for codice, atteso in (("123", False), ("1111", False), ("", False),
                           ("abcd", False), ("1234", True), ("90210", True)):
        valido, _ = ID.codice_valido(codice)
        controlla(f"codice «{codice or 'vuoto'}» -> {'accettato' if atteso else 'rifiutato'}",
                  valido == atteso)

    print("\n5. Partite separate fra giocatrici")
    for slot, nome in (("marta", "Marta"), ("irene", "Irene")):
        storico_slot = M.carica_storico(slot)
        stato = M.nuovo_stato(nome, storico_slot)
        ST.registra(storico_slot, "6x7", slot == "marta")
        M.salva(stato, slot, storico_slot, 1)
    controlla("due partite distinte nell'archivio",
              {v["slot"] for v in M.elenco_salvataggi()} == {"marta", "irene"})
    controlla("storico di Marta indipendente",
              M.carica_storico("marta")["fatti"]["6x7"]["ok"] == 1)
    controlla("storico di Irene indipendente",
              M.carica_storico("irene")["fatti"]["6x7"]["ko"] == 1)

    print("\n6. Cambio di codice senza perdita di dati")
    prima = M.carica("marta")
    M.imposta_credenziale("marta", ID.crea("777888"))
    A.invalida_cache()
    controlla("codice nuovo valido", ID.verifica(M.credenziale("marta"), "777888"))
    controlla("codice vecchio non valido", not ID.verifica(M.credenziale("marta"), "2468"))
    controlla("partita intatta", M.carica("marta")["nodo"] == prima["nodo"])
    controlla("statistiche intatte", M.carica_storico("marta")["fatti"]["6x7"]["ok"] == 1)

    print("\n7. Struttura del file")
    dati = json.loads(A.percorso_locale().read_text(encoding="utf-8"))
    controlla("sezione credenziali presente", set(dati["credenziali"]) == {"marta", "irene"})
    controlla("sezioni tutte presenti",
              {"partite", "storici", "credenziali", "accessi"} <= set(dati))

    falliti = esiti.count(False)
    print(f"\n{len(esiti) - falliti}/{len(esiti)} prove superate.")
    if falliti:
        raise SystemExit(1)
    print("Tutto verde.")


if __name__ == "__main__":
    main()
