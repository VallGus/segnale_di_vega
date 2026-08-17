# -*- coding: utf-8 -*-
"""
STORICO — le statistiche che restano, partita dopo partita.

Lo stato di una partita sa com'e' andata *quella* partita. Qui invece si
accumula la storia lunga di una giocatrice, su tutte le partite e su tutti gli
allenamenti. Serve a rispondere a una domanda sola: quali tabelline sa
davvero e quali no.

Struttura di uno storico:

    {
      "giocatore": "marta",
      "creato": "2026-08-17 12:00",
      "aggiornato": "2026-09-02 18:10",
      "sessioni": 7,
      "totale_ok": 412,
      "totale_ko": 118,
      "fatti": {
        "6x7": {"ok": 4, "ko": 9, "serie": 0, "ultimi": [0,1,0,0,1],
                "prima_volta": "...", "ultimo_visto": "..."}
      },
      "giorni": { "2026-08-17": {"ok": 40, "ko": 22} }
    }

Perche' non basta la precisione totale
--------------------------------------
Se Marta sbaglia 6x7 dieci volte in agosto e poi la azzecca dieci volte in
settembre, la precisione totale dice 50%: falso, ormea la sa. Per questo ogni
fatto tiene anche gli ultimi N esiti e la serie di risposte giuste consecutive.
La classificazione guarda il recente, non la media storica.
"""

from __future__ import annotations

import time

MEMORIA_ESITI = 12         # quanti esiti recenti tenere per ogni moltiplicazione
FINESTRA_RECENTE = 5       # su quanti esiti si giudica lo "stato attuale"
SERIE_PER_CONSOLIDARE = 4  # giuste consecutive per dire "questa la sa"
SOGLIA_FRAGILE = 0.6       # sotto questa precisione recente -> da allenare
MINIMO_PER_GIUDICARE = 3   # meno tentativi di cosi' = dati insufficienti
MAX_GIORNI = 400


def _adesso() -> str:
    return time.strftime("%Y-%m-%d %H:%M")


def _oggi() -> str:
    return time.strftime("%Y-%m-%d")


def nuovo(giocatore: str) -> dict:
    return {
        "giocatore": giocatore,
        "creato": _adesso(),
        "aggiornato": _adesso(),
        "sessioni": 0,
        "totale_ok": 0,
        "totale_ko": 0,
        "fatti": {},
        "giorni": {},
    }


def normalizza(storico: dict, giocatore: str) -> dict:
    """Rende utilizzabile uno storico letto da file, anche se vecchio o incompleto."""
    base = nuovo(giocatore)
    if isinstance(storico, dict):
        base.update(storico)
    base["giocatore"] = base.get("giocatore") or giocatore
    for campo, vuoto in (("fatti", {}), ("giorni", {})):
        if not isinstance(base.get(campo), dict):
            base[campo] = vuoto
    for campo in ("sessioni", "totale_ok", "totale_ko"):
        if not isinstance(base.get(campo), int):
            base[campo] = 0
    for k, dati in list(base["fatti"].items()):
        if not isinstance(dati, dict):
            del base["fatti"][k]
            continue
        dati.setdefault("ok", 0)
        dati.setdefault("ko", 0)
        dati.setdefault("serie", 0)
        dati.setdefault("ultimi", [])
        dati.setdefault("prima_volta", base["creato"])
        dati.setdefault("ultimo_visto", base["creato"])
        dati["ultimi"] = [int(bool(x)) for x in dati["ultimi"]][-MEMORIA_ESITI:]
    return base


# ---------------------------------------------------------------------------
# Registrazione
# ---------------------------------------------------------------------------

def registra(storico: dict, chiave_fatto: str, giusto: bool) -> None:
    """Aggiunge una risposta allo storico. Va chiamata a ogni singola risposta."""
    dati = storico["fatti"].setdefault(
        chiave_fatto,
        {"ok": 0, "ko": 0, "serie": 0, "ultimi": [],
         "prima_volta": _adesso(), "ultimo_visto": _adesso()},
    )
    if giusto:
        dati["ok"] += 1
        dati["serie"] += 1
        storico["totale_ok"] += 1
    else:
        dati["ko"] += 1
        dati["serie"] = 0
        storico["totale_ko"] += 1
    dati["ultimi"] = (dati["ultimi"] + [1 if giusto else 0])[-MEMORIA_ESITI:]
    dati["ultimo_visto"] = _adesso()

    giorno = storico["giorni"].setdefault(_oggi(), {"ok": 0, "ko": 0})
    giorno["ok" if giusto else "ko"] += 1
    if len(storico["giorni"]) > MAX_GIORNI:
        for vecchio in sorted(storico["giorni"])[:-MAX_GIORNI]:
            del storico["giorni"][vecchio]
    storico["aggiornato"] = _adesso()


def apri_sessione(storico: dict) -> None:
    storico["sessioni"] = storico.get("sessioni", 0) + 1
    storico["aggiornato"] = _adesso()


def assorbi_partita(storico: dict, statistiche_partita: dict) -> int:
    """
    Travasa nello storico le statistiche di una partita fatta *prima* che lo
    storico esistesse (migrazione dei salvataggi vecchi). Non si usa nel gioco
    normale, dove ogni risposta viene registrata subito.
    """
    aggiunte = 0
    for k, dati in (statistiche_partita or {}).items():
        for _ in range(int(dati.get("ok", 0))):
            registra(storico, k, True)
            aggiunte += 1
        for _ in range(int(dati.get("ko", 0))):
            registra(storico, k, False)
            aggiunte += 1
    return aggiunte


# ---------------------------------------------------------------------------
# Lettura: classificazione dei fatti
# ---------------------------------------------------------------------------

def precisione_recente(dati: dict) -> float:
    ultimi = dati["ultimi"][-FINESTRA_RECENTE:]
    return sum(ultimi) / len(ultimi) if ultimi else 0.0


def stato_fatto(dati: dict) -> str:
    """consolidata | in_corso | fragile — la regola e' volutamente semplice."""
    tentativi = dati["ok"] + dati["ko"]
    if tentativi < MINIMO_PER_GIUDICARE:
        return "in_corso"
    if dati["serie"] >= SERIE_PER_CONSOLIDARE and precisione_recente(dati) >= 0.999:
        return "consolidata"
    if precisione_recente(dati) < SOGLIA_FRAGILE:
        return "fragile"
    return "in_corso"


def tutte_le_coppie() -> list[str]:
    return [f"{a}x{b}" for a in range(1, 11) for b in range(a, 11)]


def riga(storico: dict, chiave_fatto: str) -> dict:
    dati = storico["fatti"].get(chiave_fatto)
    if not dati:
        return {"moltiplicazione": chiave_fatto, "tentativi": 0, "giuste": 0, "sbagliate": 0,
                "precisione": 0.0, "recente": 0.0, "serie": 0, "stato": "mai_vista",
                "ultimo_visto": "-"}
    tentativi = dati["ok"] + dati["ko"]
    return {
        "moltiplicazione": chiave_fatto,
        "tentativi": tentativi,
        "giuste": dati["ok"],
        "sbagliate": dati["ko"],
        "precisione": dati["ok"] / tentativi if tentativi else 0.0,
        "recente": precisione_recente(dati),
        "serie": dati["serie"],
        "stato": stato_fatto(dati),
        "ultimo_visto": dati.get("ultimo_visto", "-"),
    }


def riepilogo(storico: dict) -> dict:
    righe = [riga(storico, k) for k in tutte_le_coppie()]
    per_stato: dict[str, list] = {"consolidata": [], "in_corso": [], "fragile": [], "mai_vista": []}
    for r in righe:
        per_stato[r["stato"]].append(r)

    fragili = sorted(per_stato["fragile"], key=lambda r: (r["recente"], -r["sbagliate"]))
    solide = sorted(per_stato["consolidata"], key=lambda r: (-r["serie"], -r["tentativi"]))
    totale = storico["totale_ok"] + storico["totale_ko"]

    giorni = sorted(storico["giorni"].items())
    andamento = [
        {"giorno": g, "domande": d["ok"] + d["ko"],
         "precisione": d["ok"] / (d["ok"] + d["ko"]) if (d["ok"] + d["ko"]) else 0.0}
        for g, d in giorni
    ]

    return {
        "totale_domande": totale,
        "precisione_globale": storico["totale_ok"] / totale if totale else 0.0,
        "sessioni": storico.get("sessioni", 0),
        "conteggi": {stato: len(lista) for stato, lista in per_stato.items()},
        "fragili": fragili,
        "solide": solide,
        "mai_viste": [r["moltiplicazione"] for r in per_stato["mai_vista"]],
        "tutte": righe,
        "andamento": andamento,
        "andamento_recente": andamento[-14:],
    }


SIMBOLI = {"consolidata": "🟢", "in_corso": "🟡", "fragile": "🔴", "mai_vista": "⬜"}


def griglia(storico: dict) -> list[list[str]]:
    """Matrice 10x10 di simboli, per vedere a colpo d'occhio dove sono i buchi."""
    matrice = []
    for a in range(1, 11):
        riga_matrice = []
        for b in range(1, 11):
            x, y = sorted((a, b))
            riga_matrice.append(SIMBOLI[stato_fatto(storico["fatti"][f"{x}x{y}"])]
                                if f"{x}x{y}" in storico["fatti"] else SIMBOLI["mai_vista"])
        matrice.append(riga_matrice)
    return matrice


# ---------------------------------------------------------------------------
# Semina: lo storico guida la scelta delle domande dall'inizio
# ---------------------------------------------------------------------------

def semina_statistiche(storico: dict, tetto: int = 2) -> dict:
    """
    Converte lo storico in statistiche iniziali per una partita nuova, in modo
    che il motore adattivo sappia da subito su quali tabelline insistere.

    I conteggi vengono compressi entro `tetto` tentativi mantenendo il rapporto
    ok/ko *recente*. La compressione non e' un dettaglio: passando i conteggi
    veri, il peso adattivo va a fondo scala e due sole moltiplicazioni fragili
    si prendono il 60% delle domande, mentre quelle consolidate non ricompaiono
    mai piu' (nessun ripasso). Con tetto=2 le fragili restano attorno al 35-40%
    e le consolidate continuano a girare: allenamento, non punizione.
    """
    seme = {}
    for k, dati in storico.get("fatti", {}).items():
        ultimi = dati["ultimi"][-FINESTRA_RECENTE:] or [1] * dati["ok"] + [0] * dati["ko"]
        if not ultimi:
            continue
        quota_ok = sum(ultimi) / len(ultimi)
        tentativi = min(tetto, max(1, len(ultimi)))
        ok = round(quota_ok * tentativi)
        seme[k] = {"ok": int(ok), "ko": int(tentativi - ok)}
    return seme
