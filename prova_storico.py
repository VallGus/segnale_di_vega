# -*- coding: utf-8 -*-
"""
Prova end-to-end di archivio + storico, in modalita' locale.

Si lancia con:  python prova_storico.py

Simula tre sessioni della stessa giocatrice, con una debolezza mirata su 7x8 e
6x7, e verifica che:
  1. la partita si salvi e si ricarichi identica;
  2. lo storico accumuli fra sessioni diverse;
  3. la classificazione riconosca fragili e consolidate;
  4. la semina faccia uscire piu' spesso le moltiplicazioni fragili.
"""

import random
import shutil

import archivio as A
import motore as M
import storia as S
import storico as ST

DEBOLI = {"7x8", "6x7"}


def gioca(slot: str, mosse: int, seme: int) -> dict:
    """Una sessione: carica o crea, risponde `mosse` volte, salva."""
    random.seed(seme)
    stato = M.carica(slot)
    storico_g = M.carica_storico(slot)
    ST.apri_sessione(storico_g)
    if stato is None:
        stato = M.nuovo_stato("Marta", storico_g)

    for _ in range(mosse):
        if stato["finita"]:
            break
        if stato["domanda"]:
            d = stato["domanda"]
            k = M.chiave(d["a"], d["b"])
            # sbaglia quasi sempre sulle deboli, quasi mai sul resto
            giusto = random.random() < (0.15 if k in DEBOLI else 0.9)
            M.rispondi(stato, d["a"] * d["b"] if giusto else -1, storico_g)
        else:
            nodo = S.STORIA[stato["nodo"]]
            if nodo["tipo"] == "finale":
                break
            possibili = [s for s in nodo["scelte"]
                         if not s.get("richiede") or stato["oggetti"].get(s["richiede"], 0) > 0]
            M.scegli(stato, random.choice(possibili)["vai_a"])
    M.salva(stato, slot, storico_g, mosse)
    return storico_g


def main() -> None:
    shutil.rmtree(A.CARTELLA_LOCALE, ignore_errors=True)
    A.invalida_cache()

    print("modalita' archivio:", A.modalita())
    print()

    for numero, (mosse, seme) in enumerate([(120, 1), (120, 2), (120, 3)], start=1):
        A.invalida_cache()
        st_g = gioca("marta", mosse, seme)
        r = ST.riepilogo(st_g)
        print(f"sessione {numero}: risposte totali {r['totale_domande']:>4} · "
              f"precisione {r['precisione_globale']:.0%} · "
              f"consolidate {r['conteggi']['consolidata']:>2} · "
              f"fragili {r['conteggi']['fragile']:>2} · "
              f"mai viste {r['conteggi']['mai_vista']:>2}")

    print()
    A.invalida_cache()
    storico_finale = M.carica_storico("marta")
    r = ST.riepilogo(storico_finale)

    print("--- lo storico e' sopravvissuto alla rilettura dell'archivio ---")
    print("sessioni registrate:", r["sessioni"])
    print("prime 6 da allenare:", ", ".join(
        f"{x['moltiplicazione']} ({x['sbagliate']} err, ultime5 {x['recente']:.0%})"
        for x in r["fragili"][:6]))
    print("consolidate (prime 8):", ", ".join(x["moltiplicazione"] for x in r["solide"][:8]))

    print()
    print("--- le deboli sono state riconosciute? ---")
    fragili = {x["moltiplicazione"] for x in r["fragili"]}
    for k in sorted(DEBOLI):
        riga = ST.riga(storico_finale, k)
        esito = "OK" if k in fragili else "NON RILEVATA"
        print(f"  {k}: {riga['giuste']} giuste / {riga['sbagliate']} sbagliate · "
              f"stato {riga['stato']} -> {esito}")

    print()
    print("--- la semina indirizza le domande verso le deboli? ---")
    seme_stat = ST.semina_statistiche(storico_finale)
    stato_nuovo = M.nuovo_stato("Marta", storico_finale)
    assert stato_nuovo["statistiche"] == seme_stat, "la semina non e' stata applicata"
    conteggio: dict[str, int] = {}
    stato_prova = M.nuovo_stato("Marta", storico_finale)
    for _ in range(3000):
        d = M.crea_domanda(stato_prova, "prova", "mista")
        k = M.chiave(d["a"], d["b"])
        conteggio[k] = conteggio.get(k, 0) + 1
        stato_prova["ultima_chiave"] = k
    ordinate = sorted(conteggio.items(), key=lambda x: -x[1])
    print("  piu' frequenti con semina:", ", ".join(f"{k}({n})" for k, n in ordinate[:8]))
    for k in sorted(DEBOLI):
        posizione = [i for i, (kk, _) in enumerate(ordinate) if kk == k][0] + 1
        print(f"  {k} in posizione {posizione} su {len(ordinate)} ({conteggio[k]} estrazioni)")

    print()
    print("--- salvataggi presenti nell'archivio ---")
    for voce in M.elenco_salvataggi():
        print(f"  {voce['slot']} · {voce['capitolo']} · {voce['frammenti']}/6 · {voce['salvato']}")
    print("accessi registrati:", len(A.leggi().get("accessi", [])))
    print("griglia (riga del 7):", " ".join(ST.griglia(storico_finale)[6]))


if __name__ == "__main__":
    main()
