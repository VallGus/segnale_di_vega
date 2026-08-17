"""
Motore di gioco per "Il Segnale di Vega".

Contiene tutta la logica: generazione delle moltiplicazioni (pesata sulle
tabelline statisticamente piu' difficili + adattiva sugli errori del giocatore),
combattimento a turni, oggetti, morte/rianimazione, salvataggi.

I salvataggi passano da `archivio.py` (un unico documento JSON, su Google Drive
o su disco locale) e le statistiche di lungo periodo da `storico.py`.

Nessuna dipendenza da Streamlit: si puo' testare e simulare da riga di comando.
"""

from __future__ import annotations

import random
import time

import archivio as A
import storia as S
import storico as ST

VITA_INIZIALE = 14
DANNO_BASE = 2          # danno del colpo del giocatore
BONUS_CRITICO = 2       # danno aggiuntivo dopo 3 risposte esatte di fila
VITA_DOPO_RIANIMAZIONE = 3
RISPOSTE_PER_RIANIMARSI = 3
CURA_DOPO_VITTORIA = 2
MAX_RIGHE_DIARIO = 40


# ---------------------------------------------------------------------------
# 1. Generazione delle moltiplicazioni
# ---------------------------------------------------------------------------

FACILI = {1, 2, 5, 10}
DIFFICILI = {6, 7, 8, 9}

# Le coppie che le ricerche su scuola primaria segnalano come piu' resistenti
# (oltre alla tabellina del 7 e dell'8 in generale).
CATTIVISSIME = {(6, 7), (7, 8), (6, 8), (7, 9), (8, 9), (6, 9), (4, 7), (3, 8)}


def chiave(a: int, b: int) -> str:
    """Chiave normalizzata per le statistiche: 7x8 e 8x7 sono lo stesso fatto."""
    x, y = sorted((a, b))
    return f"{x}x{y}"


def peso_base(a: int, b: int) -> float:
    """Quanto spesso questa moltiplicazione deve uscire (piu' alto = piu' spesso)."""
    x, y = sorted((a, b))
    if x in FACILI or y in FACILI:
        return 1.0
    if x in DIFFICILI and y in DIFFICILI:
        peso = 8.0
    elif x in DIFFICILI or y in DIFFICILI:
        peso = 5.0
    else:
        peso = 3.0                      # combinazioni di 3 e 4
    if (x, y) in CATTIVISSIME:
        peso += 4.0
    return peso


def _in_fascia(a: int, b: int, fascia: str) -> bool:
    x, y = sorted((a, b))
    if fascia == "facile":
        return x in FACILI or y in FACILI
    if fascia == "media":
        return not (x in DIFFICILI and y in DIFFICILI)
    if fascia == "tosta":
        return x not in FACILI and y not in FACILI
    return True                          # "mista"


def peso_adattivo(a: int, b: int, statistiche: dict) -> float:
    """Peso base corretto in base a come e' andata finora su quel fatto."""
    peso = peso_base(a, b)
    dati = statistiche.get(chiave(a, b), {"ok": 0, "ko": 0})
    fattore = 1.0 + 0.8 * dati["ko"] - 0.25 * dati["ok"]
    return max(0.35, min(peso * fattore, 60.0))


def crea_domanda(stato: dict, contesto: str, fascia: str = "mista") -> dict:
    """Estrae una moltiplicazione da 1x1 a 10x10 secondo i pesi."""
    coppie = [(a, b) for a in range(1, 11) for b in range(1, 11) if _in_fascia(a, b, fascia)]
    pesi = [peso_adattivo(a, b, stato["statistiche"]) for a, b in coppie]

    ultima = stato.get("ultima_chiave")
    for i, (a, b) in enumerate(coppie):
        if chiave(a, b) == ultima:       # evita di ripetere lo stesso fatto due volte di fila
            pesi[i] *= 0.05

    a, b = random.choices(coppie, weights=pesi, k=1)[0]
    if random.random() < 0.5:            # mostra a volte 7x8, a volte 8x7
        a, b = b, a
    return {"a": a, "b": b, "contesto": contesto, "aiuto": bool(stato.get("aiuto_attivo"))}


def suggerimento(a: int, b: int) -> str:
    """Un aiuto per ragionare, non solo il risultato."""
    if 9 in (a, b):
        altro = b if a == 9 else a
        return f"Trucco del 9: {altro}x9 = {altro}x10 - {altro} = {altro * 10} - {altro} = {altro * 9}"
    if 6 in (a, b):
        altro = b if a == 6 else a
        return f"Trucco del 6: {altro}x6 = {altro}x5 + {altro} = {altro * 5} + {altro} = {altro * 6}"
    if 8 in (a, b):
        altro = b if a == 8 else a
        return (f"Trucco dell'8: raddoppia tre volte -> {altro} -> {altro * 2} -> "
                f"{altro * 4} -> {altro * 8}")
    if 4 in (a, b):
        altro = b if a == 4 else a
        return f"Trucco del 4: raddoppia due volte -> {altro} -> {altro * 2} -> {altro * 4}"
    if b % 2 == 0:
        return f"{a}x{b} = {a}x{b // 2} + {a}x{b // 2} = {a * (b // 2)} + {a * (b // 2)} = {a * b}"
    return f"{a}x{b} = {a}x{b - 1} + {a} = {a * (b - 1)} + {a} = {a * b}"


# ---------------------------------------------------------------------------
# 2. Stato della partita
# ---------------------------------------------------------------------------

def nuovo_stato(nome_giocatrice: str = "Marta", storico_precedente: dict | None = None) -> dict:
    """
    Crea una partita nuova. Se si passa uno storico, le statistiche iniziali
    vengono seminate da quello: il motore adattivo sa da subito su quali
    tabelline insistere, invece di ripartire da zero a ogni partita.
    """
    stato = {
        "nome": nome_giocatrice,
        "nodo": None,
        "hp": VITA_INIZIALE,
        "hp_max": VITA_INIZIALE,
        "danno_base": DANNO_BASE,
        "scudo": 0,
        "aiuto_attivo": False,
        "serie_giuste": 0,
        "oggetti": {},
        "frammenti": [],
        "statistiche": {},
        "totale_ok": 0,
        "totale_ko": 0,
        "morti": 0,
        "domanda": None,
        "combattimento": None,
        "morte": None,
        "diario": [],
        "ultima_chiave": None,
        "finita": False,
        "creato": time.strftime("%Y-%m-%d %H:%M"),
    }
    if storico_precedente:
        stato["statistiche"] = ST.semina_statistiche(storico_precedente)
    entra_nodo(stato, S.NODO_INIZIALE)
    return stato


def diario(stato: dict, testo: str) -> None:
    stato["diario"].append(testo)
    del stato["diario"][:-MAX_RIGHE_DIARIO]


def nodo_corrente(stato: dict) -> dict:
    return S.STORIA[stato["nodo"]]


def personalizza(testo: str, stato: dict) -> str:
    """
    Sostituisce {nome} col nome di chi sta giocando.

    Il nome sta in un segnaposto dentro `storia.py` invece che cablato nel testo:
    cosi' la storia resta un file di dati validi per qualsiasi giocatore, e
    aggiungere un'altra variabile in futuro costa una riga qui, non 82 modifiche
    sparse. Il fallback e' "tu": una frase come «Ti chiami tu» sarebbe brutta ma
    non manderebbe in errore il gioco se il nome mancasse.
    """
    if not testo:
        return testo
    return testo.replace("{nome}", (stato.get("nome") or "").strip() or "tu")


def fascia_corrente(stato: dict) -> str:
    return nodo_corrente(stato).get("fascia", "mista")


def aggiungi_oggetto(stato: dict, nome: str, quanti: int = 1) -> None:
    stato["oggetti"][nome] = stato["oggetti"].get(nome, 0) + quanti
    diario(stato, f"[+] Hai trovato: {nome} x{quanti}")


def cura(stato: dict, punti: int) -> int:
    prima = stato["hp"]
    stato["hp"] = min(stato["hp_max"], stato["hp"] + punti)
    return stato["hp"] - prima


# ---------------------------------------------------------------------------
# 3. Movimento tra i nodi della storia
# ---------------------------------------------------------------------------

def entra_nodo(stato: dict, id_nodo: str) -> None:
    stato["nodo"] = id_nodo
    nodo = S.STORIA[id_nodo]
    stato["combattimento"] = None
    stato["domanda"] = None

    if nodo.get("cura"):
        recuperati = cura(stato, nodo["cura"])
        if recuperati:
            diario(stato, f"[+] Recuperi {recuperati} punti vita.")
    for nome, quanti in nodo.get("dai_oggetti", {}).items():
        aggiungi_oggetto(stato, nome, quanti)
    if nodo.get("frammento") and nodo["frammento"] not in stato["frammenti"]:
        stato["frammenti"].append(nodo["frammento"])
        diario(stato, f"[*] Frammento di Senso ottenuto: {nodo['frammento']}")
    if nodo.get("vita_max_extra"):
        stato["hp_max"] += nodo["vita_max_extra"]
        cura(stato, nodo["vita_max_extra"])
    if nodo.get("danno_base"):
        stato["danno_base"] = nodo["danno_base"]

    if nodo["tipo"] == "prova":
        stato["domanda"] = crea_domanda(stato, "prova", nodo.get("fascia", "mista"))
    elif nodo["tipo"] == "combattimento":
        nemico = dict(nodo["nemico"])
        nemico["hp_max"] = nemico["hp"]
        stato["combattimento"] = nemico
        stato["domanda"] = crea_domanda(stato, "attacco", nodo.get("fascia", "mista"))
    elif nodo["tipo"] == "finale":
        stato["finita"] = True


def scegli(stato: dict, id_nodo: str) -> None:
    entra_nodo(stato, id_nodo)


# ---------------------------------------------------------------------------
# 4. Risoluzione delle risposte
# ---------------------------------------------------------------------------

def _registra(stato: dict, a: int, b: int, giusto: bool, storico: dict | None = None) -> None:
    dati = stato["statistiche"].setdefault(chiave(a, b), {"ok": 0, "ko": 0})
    dati["ok" if giusto else "ko"] += 1
    stato["ultima_chiave"] = chiave(a, b)
    if storico is not None:
        ST.registra(storico, chiave(a, b), giusto)
    if giusto:
        stato["totale_ok"] += 1
        stato["serie_giuste"] += 1
    else:
        stato["totale_ko"] += 1
        stato["serie_giuste"] = 0


def _subisci(stato: dict, danno: int) -> None:
    if stato["scudo"] > 0:
        stato["scudo"] -= 1
        diario(stato, f"[=] Lo Scudo di Fase assorbe il colpo (cariche rimaste: {stato['scudo']}).")
        return
    stato["hp"] = max(0, stato["hp"] - danno)
    diario(stato, f"[-] Perdi {danno} punti vita. Vita: {stato['hp']}/{stato['hp_max']}")


def _dopo_danno(stato: dict, prossimo_nodo: str | None) -> None:
    """Se la vita e' finita apre la fase di rianimazione, altrimenti prosegue."""
    if stato["hp"] <= 0:
        stato["morti"] += 1
        stato["morte"] = {"serie": 0, "prossimo": prossimo_nodo}
        stato["domanda"] = crea_domanda(stato, "rianimazione", "media")
        diario(stato, "[!] La tuta va in riserva. Bit accende il rianimatore.")
        return
    if prossimo_nodo:
        entra_nodo(stato, prossimo_nodo)
    else:
        stato["domanda"] = crea_domanda(stato, "attacco", fascia_corrente(stato))


def _vittoria(stato: dict) -> dict:
    nodo = nodo_corrente(stato)
    nemico = stato["combattimento"]
    diario(stato, f"[*] {nemico['nome']} è fuori gioco!")
    stato["combattimento"] = None
    recuperati = cura(stato, CURA_DOPO_VITTORIA)
    if recuperati:
        diario(stato, f"[+] Riprendi fiato: +{recuperati} punti vita.")
    for nome, quanti in nodo.get("oggetti_vittoria", {}).items():
        aggiungi_oggetto(stato, nome, quanti)
    entra_nodo(stato, nodo["vai_a"])
    return {"esito": "vittoria"}


def rispondi(stato: dict, risposta: int | None, storico: dict | None = None) -> dict:
    """
    Applica la risposta alla domanda in corso. Ritorna un riepilogo per la UI.

    Se si passa `storico`, la risposta viene registrata anche nella storia di
    lungo periodo della giocatrice (in memoria: il salvataggio e' a carico di chi
    chiama, cosi' si possono accorpare piu' risposte in una sola scrittura).
    """
    domanda = stato["domanda"]
    if domanda is None:
        return {"esito": "nessuna_domanda"}

    a, b = domanda["a"], domanda["b"]
    corretto = a * b
    giusto = (risposta == corretto)
    contesto = domanda["contesto"]
    stato["aiuto_attivo"] = False
    _registra(stato, a, b, giusto, storico)

    esito = {
        "giusto": giusto,
        "domanda": f"{a} x {b}",
        "risposta_esatta": corretto,
        "suggerimento": None if giusto else suggerimento(a, b),
        "critico": False,
    }
    nodo = nodo_corrente(stato)

    # ---- rianimazione -----------------------------------------------------
    if contesto == "rianimazione":
        if giusto:
            stato["morte"]["serie"] += 1
            fatte = stato["morte"]["serie"]
            if fatte >= RISPOSTE_PER_RIANIMARSI:
                stato["hp"] = VITA_DOPO_RIANIMAZIONE
                prossimo = stato["morte"]["prossimo"]
                stato["morte"] = None
                diario(stato, f"[+] Rianimata! Torni in piedi con {VITA_DOPO_RIANIMAZIONE} punti vita.")
                if prossimo:
                    entra_nodo(stato, prossimo)
                else:
                    stato["domanda"] = crea_domanda(stato, "attacco", fascia_corrente(stato))
            else:
                diario(stato, f"[ok] Rianimazione {fatte}/{RISPOSTE_PER_RIANIMARSI}.")
                stato["domanda"] = crea_domanda(stato, "rianimazione", "media")
        else:
            stato["morte"]["serie"] = 0
            diario(stato, "[..] La serie riparte da zero. Nessuna fretta.")
            stato["domanda"] = crea_domanda(stato, "rianimazione", "media")
        return esito

    # ---- prova di percorso (trappole, serrature, dialoghi) ----------------
    if contesto == "prova":
        stato["domanda"] = None
        if giusto:
            diario(stato, f"[ok] {a}x{b}={corretto}. "
                          f"{personalizza(nodo.get('testo_ok', 'Riuscito!'), stato)}")
            for nome, quanti in nodo.get("oggetti_ok", {}).items():
                aggiungi_oggetto(stato, nome, quanti)
            if nodo.get("cura_ok"):
                cura(stato, nodo["cura_ok"])
            entra_nodo(stato, nodo["vai_a"])
        else:
            diario(stato, f"[x] {a}x{b} fa {corretto}. "
                          f"{personalizza(nodo.get('testo_ko', 'Colpita!'), stato)}")
            _subisci(stato, nodo.get("danno", 2))
            _dopo_danno(stato, nodo.get("vai_a_ko", nodo["vai_a"]))
        return esito

    # ---- il tuo attacco ---------------------------------------------------
    if contesto == "attacco":
        nemico = stato["combattimento"]
        if giusto:
            danno = stato["danno_base"]
            if stato["serie_giuste"] > 0 and stato["serie_giuste"] % 3 == 0:
                danno += BONUS_CRITICO
                esito["critico"] = True
            nemico["hp"] = max(0, nemico["hp"] - danno)
            extra = " COLPO CRITICO!" if esito["critico"] else ""
            diario(stato, f"[ok] {a}x{b}={corretto}. Colpisci {nemico['nome']} "
                          f"(-{danno}).{extra} Nemico: {nemico['hp']}/{nemico['hp_max']}")
            if nemico["hp"] <= 0:
                esito.update(_vittoria(stato))
                return esito
        else:
            diario(stato, f"[x] {a}x{b} fa {corretto}. Il colpo va a vuoto.")
        stato["domanda"] = crea_domanda(stato, "difesa", nodo.get("fascia", "mista"))
        return esito

    # ---- la difesa --------------------------------------------------------
    if contesto == "difesa":
        nemico = stato["combattimento"]
        if giusto:
            diario(stato, f"[ok] {a}x{b}={corretto}. Schivi {nemico.get('attacco', 'il colpo')}!")
            stato["domanda"] = crea_domanda(stato, "attacco", nodo.get("fascia", "mista"))
        else:
            diario(stato, f"[x] {a}x{b} fa {corretto}. {nemico.get('attacco', 'Il colpo')} ti prende.")
            _subisci(stato, nemico.get("danno", 2))
            _dopo_danno(stato, None)
        return esito

    # ---- uso di un oggetto ------------------------------------------------
    if contesto == "oggetto":
        nome = domanda["oggetto"]
        if giusto:
            diario(stato, f"[ok] {a}x{b}={corretto}. Attivi {nome}!")
            _applica_effetto(stato, nome)
            stato["oggetti"][nome] -= 1
            if stato["oggetti"][nome] <= 0:
                del stato["oggetti"][nome]
            if stato["combattimento"] and stato["combattimento"]["hp"] <= 0:
                esito.update(_vittoria(stato))
                return esito
        else:
            diario(stato, f"[x] {a}x{b} fa {corretto}. {nome} non si attiva, ma resta nello zaino.")
        if stato["combattimento"]:
            stato["domanda"] = crea_domanda(stato, "difesa", nodo.get("fascia", "mista"))
        else:
            sospesa = domanda.get("sospesa")
            if sospesa:
                sospesa["aiuto"] = bool(stato["aiuto_attivo"])
            stato["domanda"] = sospesa
        return esito

    return esito


# ---------------------------------------------------------------------------
# 5. Oggetti
# ---------------------------------------------------------------------------

def puo_usare_oggetti(stato: dict) -> bool:
    """Gli oggetti si usano nel proprio turno di attacco o fuori dal combattimento."""
    if stato["morte"]:
        return False
    if stato["domanda"] is None:
        return True
    return stato["domanda"]["contesto"] in ("attacco", "prova")


def prepara_uso_oggetto(stato: dict, nome: str) -> None:
    sospesa = stato["domanda"] if (stato["domanda"] and stato["domanda"]["contesto"] == "prova") else None
    domanda = crea_domanda(stato, "oggetto", "media")
    domanda["oggetto"] = nome
    domanda["sospesa"] = sospesa
    stato["domanda"] = domanda


def _applica_effetto(stato: dict, nome: str) -> None:
    oggetto = S.OGGETTI[nome]
    effetto, valore = oggetto["effetto"], oggetto.get("valore", 0)
    if effetto == "cura":
        recuperati = cura(stato, valore)
        diario(stato, f"[+] Recuperi {recuperati} punti vita. Vita: {stato['hp']}/{stato['hp_max']}")
    elif effetto == "cura_totale":
        stato["hp"] = stato["hp_max"]
        diario(stato, f"[+] Vita al massimo: {stato['hp']}/{stato['hp_max']}")
    elif effetto == "danno":
        if stato["combattimento"]:
            nemico = stato["combattimento"]
            nemico["hp"] = max(0, nemico["hp"] - valore)
            diario(stato, f"[!] Il lampo colpisce {nemico['nome']} (-{valore}). "
                          f"Nemico: {nemico['hp']}/{nemico['hp_max']}")
    elif effetto == "scudo":
        stato["scudo"] += valore
        diario(stato, f"[=] Scudo attivo: {stato['scudo']} cariche.")
    elif effetto == "aiuto":
        stato["aiuto_attivo"] = True
        diario(stato, "[?] La Lente del Tempo illuminerà la prossima moltiplicazione.")
    elif effetto == "vita_max":
        stato["hp_max"] += valore
        cura(stato, valore)
        diario(stato, f"[+] Vita massima ora {stato['hp_max']}.")


# ---------------------------------------------------------------------------
# 6. Salvataggi
# ---------------------------------------------------------------------------

def pulisci_slot(nome_slot: str) -> str:
    pulito = "".join(c for c in nome_slot.lower() if c.isalnum() or c in " _-").strip()
    return pulito.replace(" ", "_") or "partita"


def salva(stato: dict, nome_slot: str, storico: dict | None = None,
          domande_sessione: int = 0) -> bool:
    """
    Scrive partita (e storico, se dato) nell'archivio condiviso.

    Rilegge prima di scrivere, cosi' due giocatrici in parallelo non si
    cancellano a vicenda. Ritorna True se la scrittura remota e' riuscita.
    """
    slot = pulisci_slot(nome_slot)
    dati_partita = dict(stato)
    dati_partita["salvato"] = time.strftime("%Y-%m-%d %H:%M")
    dati_partita["slot"] = slot

    def modifica(arch: dict) -> None:
        arch["partite"][slot] = dati_partita
        if storico is not None:
            arch["storici"][slot] = storico
        accessi = arch.setdefault("accessi", [])
        voce = {
            "slot": slot,
            "nome": stato.get("nome", slot),
            "quando": dati_partita["salvato"],
            "domande_totali": stato.get("totale_ok", 0) + stato.get("totale_ko", 0),
            "domande_sessione": domande_sessione,
            "capitolo": S.STORIA.get(stato.get("nodo"), {}).get("capitolo", "?"),
            "frammenti": len(stato.get("frammenti", [])),
        }
        # Una riga per slot per giorno: il log resta leggibile nel tempo.
        oggi = dati_partita["salvato"][:10]
        for indice, esistente in enumerate(accessi):
            if esistente.get("slot") == slot and str(esistente.get("quando", ""))[:10] == oggi:
                accessi[indice] = voce
                break
        else:
            accessi.append(voce)
        del accessi[:-500]

    return A.aggiorna(modifica)


def carica(nome_slot: str) -> dict | None:
    stato = A.leggi().get("partite", {}).get(pulisci_slot(nome_slot))
    if stato is None:
        return None
    stato = dict(stato)
    for campo, default in (("scudo", 0), ("aiuto_attivo", False), ("morti", 0),
                           ("danno_base", DANNO_BASE), ("finita", False),
                           ("statistiche", {}), ("diario", []), ("frammenti", []),
                           ("oggetti", {}), ("totale_ok", 0), ("totale_ko", 0)):
        stato.setdefault(campo, default)
    return stato


def carica_storico(nome_slot: str) -> dict:
    slot = pulisci_slot(nome_slot)
    grezzo = A.leggi().get("storici", {}).get(slot)
    return ST.normalizza(grezzo or {}, slot)


def salva_storico(storico: dict, nome_slot: str) -> bool:
    slot = pulisci_slot(nome_slot)

    def modifica(arch: dict) -> None:
        arch["storici"][slot] = storico

    return A.aggiorna(modifica)


def elimina_partita(nome_slot: str, anche_storico: bool = False) -> bool:
    slot = pulisci_slot(nome_slot)

    def modifica(arch: dict) -> None:
        arch["partite"].pop(slot, None)
        if anche_storico:
            arch["storici"].pop(slot, None)

    return A.aggiorna(modifica)


def elenco_salvataggi() -> list[dict]:
    voci = []
    for slot, dati in sorted(A.leggi().get("partite", {}).items()):
        if not isinstance(dati, dict):
            continue
        voci.append({
            "slot": slot,
            "nome": dati.get("nome", slot),
            "capitolo": S.STORIA.get(dati.get("nodo"), {}).get("capitolo", "?"),
            "frammenti": len(dati.get("frammenti", [])),
            "salvato": dati.get("salvato", "?"),
            "finita": bool(dati.get("finita")),
        })
    return sorted(voci, key=lambda v: v["salvato"], reverse=True)


def elenco_giocatori() -> list[str]:
    arch = A.leggi()
    return sorted(set(arch.get("partite", {})) | set(arch.get("storici", {}))
                  | set(arch.get("credenziali", {})))


# ---------------------------------------------------------------------------
# 6b. Codici segreti
# ---------------------------------------------------------------------------

def credenziale(nome_slot: str) -> dict | None:
    return A.leggi().get("credenziali", {}).get(pulisci_slot(nome_slot))


def slot_registrato(nome_slot: str) -> bool:
    """
    Vero se il nome e' gia' stato preso da qualcuno con un codice.

    I salvataggi creati prima dei codici non hanno credenziale: restano
    adottabili dal primo che entra con quel nome e sceglie un codice. E' un buco
    noto e limitato al passaggio di versione.
    """
    return credenziale(nome_slot) is not None


def imposta_credenziale(nome_slot: str, nuova: dict | None) -> bool:
    """Salva (o cancella, con None) il codice segreto di una giocatrice."""
    slot = pulisci_slot(nome_slot)

    def modifica(arch: dict) -> None:
        if nuova is None:
            arch["credenziali"].pop(slot, None)
        else:
            arch["credenziali"][slot] = nuova

    return A.aggiorna(modifica)


# ---------------------------------------------------------------------------
# 7. Statistiche per i grandi
# ---------------------------------------------------------------------------

def riepilogo_statistiche(stato: dict, minimo_tentativi: int = 2) -> dict:
    righe = []
    for k, dati in stato["statistiche"].items():
        tentativi = dati["ok"] + dati["ko"]
        righe.append({
            "moltiplicazione": k,
            "tentativi": tentativi,
            "giuste": dati["ok"],
            "sbagliate": dati["ko"],
            "precisione": dati["ok"] / tentativi if tentativi else 0.0,
        })
    da_allenare = [r for r in righe if r["tentativi"] >= minimo_tentativi]
    da_allenare.sort(key=lambda r: (r["precisione"], -r["sbagliate"]))
    totale = stato["totale_ok"] + stato["totale_ko"]
    return {
        "totale_domande": totale,
        "precisione_globale": stato["totale_ok"] / totale if totale else 0.0,
        "tutte": sorted(righe, key=lambda r: -r["sbagliate"]),
        "da_allenare": da_allenare[:10],
    }
