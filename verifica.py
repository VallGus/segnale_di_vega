# -*- coding: utf-8 -*-
"""
Controlli tecnici sul gioco. Si lancia con:  python verifica.py

1) Verifica che tutti i collegamenti tra i nodi esistano e che i nomi degli
   oggetti siano corretti.
2) Simula partite complete con giocatrici di diversa precisione, per stimare
   quante moltiplicazioni servono, quante rianimazioni ci sono e quanto dura.
"""

import random
import statistics

import motore as M
import storia as S

SECONDI_PER_DOMANDA = 22      # lettura + calcolo + digitazione, bambina di 8 anni
SECONDI_LETTURA_NODO = 25     # testo narrativo da leggere/commentare


def verifica_struttura() -> list[str]:
    errori = []
    tipi_validi = {"narrazione", "prova", "combattimento", "finale"}
    for id_nodo, nodo in S.STORIA.items():
        if nodo["tipo"] not in tipi_validi:
            errori.append(f"{id_nodo}: tipo sconosciuto {nodo['tipo']}")
        destinazioni = []
        if nodo["tipo"] in ("prova", "combattimento"):
            destinazioni.append(nodo.get("vai_a"))
            if nodo.get("vai_a_ko"):
                destinazioni.append(nodo["vai_a_ko"])
        if nodo["tipo"] == "narrazione":
            if not nodo.get("scelte"):
                errori.append(f"{id_nodo}: narrazione senza scelte")
            destinazioni += [s.get("vai_a") for s in nodo.get("scelte", [])]
        for destinazione in destinazioni:
            if destinazione not in S.STORIA:
                errori.append(f"{id_nodo}: collegamento rotto -> {destinazione}")
        for gruppo in ("dai_oggetti", "oggetti_ok", "oggetti_vittoria"):
            for nome in nodo.get(gruppo, {}):
                if nome not in S.OGGETTI:
                    errori.append(f"{id_nodo}: oggetto inesistente '{nome}'")
        for scelta in nodo.get("scelte", []):
            if scelta.get("richiede") and scelta["richiede"] not in S.OGGETTI:
                errori.append(f"{id_nodo}: richiede oggetto inesistente")
    raggiungibili, da_visitare = set(), [S.NODO_INIZIALE]
    while da_visitare:
        corrente = da_visitare.pop()
        if corrente in raggiungibili:
            continue
        raggiungibili.add(corrente)
        nodo = S.STORIA[corrente]
        for destinazione in ([nodo.get("vai_a"), nodo.get("vai_a_ko")]
                             + [s.get("vai_a") for s in nodo.get("scelte", [])]):
            if destinazione in S.STORIA:
                da_visitare.append(destinazione)
    for id_nodo in S.STORIA:
        if id_nodo not in raggiungibili:
            errori.append(f"{id_nodo}: nodo non raggiungibile")
    return errori


def simula(precisione: float, usa_oggetti: bool = True, seme: int = 0) -> dict:
    random.seed(seme)
    stato = M.nuovo_stato("Test")
    domande = nodi_visti = 0
    while not stato["finita"] and domande < 5000:
        if stato["domanda"]:
            # eventuale cura d'emergenza
            if usa_oggetti and stato["hp"] <= 5 and M.puo_usare_oggetti(stato):
                cure = [n for n in stato["oggetti"]
                        if S.OGGETTI[n]["effetto"] in ("cura", "cura_totale")]
                if cure:
                    M.prepara_uso_oggetto(stato, cure[0])
            domanda = stato["domanda"]
            giusto = random.random() < precisione
            valore = domanda["a"] * domanda["b"] if giusto else -1
            M.rispondi(stato, valore)
            domande += 1
        else:
            nodo = S.STORIA[stato["nodo"]]
            nodi_visti += 1
            if nodo["tipo"] == "finale":
                break
            scelte = [s for s in nodo["scelte"]
                      if not s.get("richiede") or stato["oggetti"].get(s["richiede"], 0) > 0]
            M.scegli(stato, random.choice(scelte)["vai_a"])
    minuti = (domande * SECONDI_PER_DOMANDA + nodi_visti * SECONDI_LETTURA_NODO) / 60
    return {"domande": domande, "rianimazioni": stato["morti"], "minuti": minuti,
            "nodi": nodi_visti, "finita": stato["finita"]}


def distribuzione_fatti(campioni: int = 4000) -> list[tuple[str, int]]:
    stato = M.nuovo_stato("Test")
    conteggio = {}
    for _ in range(campioni):
        domanda = M.crea_domanda(stato, "prova", "mista")
        k = M.chiave(domanda["a"], domanda["b"])
        conteggio[k] = conteggio.get(k, 0) + 1
        stato["ultima_chiave"] = k
    return sorted(conteggio.items(), key=lambda x: -x[1])


if __name__ == "__main__":
    print("=== 1. STRUTTURA ===")
    errori = verifica_struttura()
    print("\n".join(errori) if errori else "Nessun errore. Nodi totali: %d" % len(S.STORIA))

    print("\n=== 2. SIMULAZIONE PARTITE COMPLETE ===")
    for precisione in (0.5, 0.6, 0.7, 0.85):
        risultati = [simula(precisione, seme=s) for s in range(12)]
        print(f"precisione {precisione:.0%} -> "
              f"domande {statistics.mean(r['domande'] for r in risultati):.0f} | "
              f"rianimazioni {statistics.mean(r['rianimazioni'] for r in risultati):.1f} | "
              f"durata stimata {statistics.mean(r['minuti'] for r in risultati) / 60:.1f} h | "
              f"finite {sum(r['finita'] for r in risultati)}/12")

    print("\n=== 3. MOLTIPLICAZIONI PIÙ FREQUENTI (su 4000 estrazioni) ===")
    top = distribuzione_fatti()
    print("  più frequenti:", ", ".join(f"{k}({n})" for k, n in top[:12]))
    print("  meno frequenti:", ", ".join(f"{k}({n})" for k, n in top[-8:]))
