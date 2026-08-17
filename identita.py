# -*- coding: utf-8 -*-
"""
IDENTITA' — codici segreti delle giocatrici.

A cosa serve davvero
--------------------
A impedire che una bambina apra per sbaglio (o per curiosita') la partita di
un'altra e la sovrascriva. Questo e' il problema concreto quando il link gira in
una classe, e questo modulo lo risolve.

A cosa NON serve
----------------
Non e' sicurezza. Un codice di quattro cifre ha diecimila combinazioni: chi ha
in mano l'archivio e un po' di pazienza le prova tutte. E le bambine si
scambieranno i codici comunque. Serratura da camera, non da banca.

Cosa si fa per non peggiorare le cose
-------------------------------------
Il codice non viene mai scritto in chiaro: nell'archivio finisce solo
un'impronta PBKDF2-HMAC-SHA256 con sale casuale per ogni giocatrice. Se il file
dell'archivio finisse dove non deve, i codici non sarebbero leggibili a occhio.
Il sale diverso per ciascuna impedisce di forzarle tutte in un colpo solo.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time

ALGORITMO = "pbkdf2_sha256"
ITERAZIONI = 200_000        # circa un decimo di secondo: impercettibile al login,
                            # fastidioso per chi prova diecimila combinazioni
BYTE_SALE = 16
CIFRE_MINIME = 4
CIFRE_MASSIME = 8
TENTATIVI_MASSIMI = 5       # per sessione, prima di fermarsi


def normalizza(codice: str) -> str:
    """Tiene solo le cifre: gli spazi e i trattini che i bambini aggiungono no."""
    return "".join(c for c in (codice or "") if c.isdigit())


def codice_valido(codice: str) -> tuple[bool, str]:
    pulito = normalizza(codice)
    if not pulito:
        return False, "Il codice è fatto solo di numeri."
    if len(pulito) < CIFRE_MINIME:
        return False, f"Serve un codice di almeno {CIFRE_MINIME} cifre."
    if len(pulito) > CIFRE_MASSIME:
        return False, f"Massimo {CIFRE_MASSIME} cifre."
    if len(set(pulito)) == 1:
        return False, "Un codice tutto uguale (1111) si indovina subito. Cambialo."
    return True, ""


def _impronta(codice: str, sale: bytes, iterazioni: int) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", normalizza(codice).encode("utf-8"), sale, iterazioni)


def crea(codice: str) -> dict:
    """Costruisce la credenziale da salvare nell'archivio. Non contiene il codice."""
    sale = os.urandom(BYTE_SALE)
    return {
        "algoritmo": ALGORITMO,
        "iterazioni": ITERAZIONI,
        "sale": sale.hex(),
        "impronta": _impronta(codice, sale, ITERAZIONI).hex(),
        "creato": time.strftime("%Y-%m-%d %H:%M"),
    }


def verifica(credenziale: dict | None, codice: str) -> bool:
    """
    Confronto a tempo costante fra il codice inserito e l'impronta salvata.

    `compare_digest` invece di `==` per non far capire, dal tempo di risposta,
    quante cifre iniziali sono giuste.
    """
    if not credenziale or credenziale.get("algoritmo") != ALGORITMO:
        return False
    try:
        sale = bytes.fromhex(credenziale["sale"])
        attesa = bytes.fromhex(credenziale["impronta"])
        iterazioni = int(credenziale.get("iterazioni", ITERAZIONI))
    except (KeyError, ValueError):
        return False
    return hmac.compare_digest(_impronta(codice, sale, iterazioni), attesa)
