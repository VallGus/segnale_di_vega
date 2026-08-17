# -*- coding: utf-8 -*-
"""
ARCHIVIO — dove vivono i dati del gioco.

Un unico documento JSON contiene tutto:

    {
      "versione": 1,
      "aggiornato": "2026-08-17 12:00",
      "partite":     { "marta": {...stato...} },
      "storici":     { "marta": {...storico permanente...} },
      "credenziali": { "marta": {...impronta del codice segreto...} },
      "accessi":     [ {"giocatore": "marta", "quando": "...", "domande": 34} ]
    }

Due modalita', scelte automaticamente:

  * "drive"   -> se in st.secrets ci sono le credenziali del service account e
                 l'id del file. Il file NON viene creato dall'app: lo crei tu
                 su Drive e lo condividi in scrittura col service account.
                 Motivo: un service account non ha quota di storage propria e
                 la creazione di file su un Drive consumer puo' fallire.
                 L'aggiornamento di un file esistente e' invece sempre valido.
  * "locale"  -> file in ./salvataggi/archivio_vega.json (sviluppo sul Mac).

Nessuna dipendenza obbligatoria: se le librerie Google mancano o i segreti non
ci sono, si ricade su locale senza rompere niente.
"""

from __future__ import annotations

import io
import json
import os
import threading
import time
from pathlib import Path

CARTELLA_LOCALE = Path(__file__).resolve().parent / "salvataggi"


def percorso_locale() -> Path:
    """
    Dove sta l'archivio in modalita' locale.

    La variabile d'ambiente VEGA_ARCHIVIO permette di spostarlo: le prove la
    usano per lavorare su un file usa e getta. Senza questa via d'uscita un test
    che azzera l'archivio cancellerebbe le partite vere, ed e' esattamente
    quello che e' successo la prima volta.
    """
    scelta = os.environ.get("VEGA_ARCHIVIO")
    return Path(scelta).expanduser() if scelta else CARTELLA_LOCALE / "archivio_vega.json"


def _archivio_forzato() -> bool:
    return bool(os.environ.get("VEGA_ARCHIVIO"))

AMBITI_DRIVE = ["https://www.googleapis.com/auth/drive"]

# Quante volte lasciar ritentare a Google le richieste che tornano 5xx.
RITENTATIVI_GOOGLE = 3
ATTESA_PRIMA_DEL_RITENTATIVO = 0.4

# Cache in memoria: evita di rileggere Drive a ogni rerun di Streamlit.
_cache: dict = {"dati": None, "letto": 0.0}
_ultimo_errore: str | None = None

# Il client Drive NON si tiene in una variabile globale.
#
# Sotto googleapiclient c'e' httplib2, che non e' thread-safe: Streamlit esegue
# ogni rerun in un thread diverso, e due thread che scrivono sulla stessa
# connessione TLS la corrompono. Il sintomo e' un errore illeggibile,
# "SSLError: DECRYPTION_FAILED_OR_BAD_RECORD_MAC", che con una persona sola
# compare di rado e con tre bambine diventa sistematico.
# Un client per thread risolve alla radice.
_per_thread = threading.local()


def archivio_vuoto() -> dict:
    return {"versione": 1, "aggiornato": None, "partite": {}, "storici": {},
            "credenziali": {}, "accessi": []}


# ---------------------------------------------------------------------------
# Configurazione
# ---------------------------------------------------------------------------

def _segreti() -> dict:
    """Legge st.secrets in modo difensivo: fuori da Streamlit non deve esplodere."""
    try:
        import streamlit as st
        return {
            "credenziali": dict(st.secrets["gcp_service_account"]),
            "file_id": str(st.secrets["drive"]["file_id"]),
        }
    except Exception:
        return {}


def modalita() -> str:
    """
    "drive" oppure "locale".

    VEGA_ARCHIVIO ha la precedenza assoluta sui segreti: se e' impostata si
    lavora su file, punto. Prima non era cosi', e la conseguenza e' stata che le
    prove lanciate su una macchina con le credenziali Drive configurate
    scrivevano sull'archivio vero — creando giocatrici finte e sovrascrivendo
    una partita reale. Spostare il percorso del file non basta: bisogna
    escludere del tutto la strada che porta a Drive.
    """
    if _archivio_forzato():
        return "locale"
    return "drive" if _segreti() else "locale"


def segreti_presenti() -> bool:
    """
    Vero se l'app ha delle credenziali configurate, a prescindere da dove sta
    scrivendo adesso.

    Serve a distinguere «sto sviluppando sul portatile senza configurazione» da
    «questa installazione e' destinata alla pubblicazione»: la seconda va
    protetta anche se in questo momento sta scrivendo su file. Usare modalita()
    per questa decisione era sbagliato, perche' le prove forzano la modalita'
    locale e si portavano dietro i permessi dello sviluppo.
    """
    return bool(_segreti())


def ultimo_errore() -> str | None:
    return _ultimo_errore


def email_service_account() -> str | None:
    conf = _segreti()
    if conf:
        return conf["credenziali"].get("client_email")
    return None


# ---------------------------------------------------------------------------
# Backend Drive
# ---------------------------------------------------------------------------

def _servizio(ricostruisci: bool = False):
    if ricostruisci:
        _per_thread.servizio = None
    if getattr(_per_thread, "servizio", None) is not None:
        return _per_thread.servizio
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build

    conf = _segreti()
    credenziali = Credentials.from_service_account_info(conf["credenziali"], scopes=AMBITI_DRIVE)
    _per_thread.servizio = build("drive", "v3", credentials=credenziali, cache_discovery=False)
    return _per_thread.servizio


def _con_ritentativo(operazione):
    """
    Esegue l'operazione e, se la connessione si e' guastata, la ripete una volta
    con un client nuovo.

    Una connessione TLS puo' rompersi per motivi che non dipendono da noi: rete
    mobile che cambia cella, connessione tenuta aperta troppo a lungo, hiccup del
    server. Ricostruire il client e riprovare una volta trasforma un errore
    visibile in un ritardo di mezzo secondo. Si ritenta una volta sola: se
    fallisce anche la seconda, il problema e' reale e va mostrato.
    """
    try:
        return operazione(_servizio())
    except Exception:
        time.sleep(ATTESA_PRIMA_DEL_RITENTATIVO)
        return operazione(_servizio(ricostruisci=True))


def _leggi_drive() -> dict:
    conf = _segreti()

    def operazione(servizio):
        return servizio.files().get_media(fileId=conf["file_id"]).execute(
            num_retries=RITENTATIVI_GOOGLE)

    contenuto = _con_ritentativo(operazione)
    testo = contenuto.decode("utf-8").strip() if isinstance(contenuto, bytes) else str(contenuto)
    if not testo:
        return archivio_vuoto()
    return json.loads(testo)


def _scrivi_drive(dati: dict) -> None:
    from googleapiclient.http import MediaIoBaseUpload

    conf = _segreti()
    corpo = json.dumps(dati, ensure_ascii=False, indent=1).encode("utf-8")

    def operazione(servizio):
        # Il MediaIoBaseUpload va ricreato a ogni tentativo: dopo un errore il
        # flusso sottostante e' stato consumato in parte e ripartirebbe da meta'.
        media = MediaIoBaseUpload(io.BytesIO(corpo), mimetype="application/json",
                                  resumable=False)
        return servizio.files().update(fileId=conf["file_id"], media_body=media).execute(
            num_retries=RITENTATIVI_GOOGLE)

    _con_ritentativo(operazione)


# ---------------------------------------------------------------------------
# Backend locale
# ---------------------------------------------------------------------------

def _leggi_locale() -> dict:
    percorso = percorso_locale()
    if not percorso.exists():
        return archivio_vuoto()
    return json.loads(percorso.read_text(encoding="utf-8"))


def _scrivi_locale(dati: dict) -> None:
    percorso = percorso_locale()
    percorso.parent.mkdir(parents=True, exist_ok=True)
    percorso.write_text(json.dumps(dati, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------------------------------------------------------------------------
# API pubblica
# ---------------------------------------------------------------------------

def _normalizza(dati: dict) -> dict:
    base = archivio_vuoto()
    if isinstance(dati, dict):
        base.update({k: v for k, v in dati.items() if k in base or k == "versione"})
    for campo, vuoto in (("partite", {}), ("storici", {}), ("credenziali", {}), ("accessi", [])):
        if not isinstance(base.get(campo), type(vuoto)):
            base[campo] = vuoto
    return base


def leggi(forza: bool = False) -> dict:
    """Ritorna l'archivio completo. Usa la cache salvo forza=True."""
    global _ultimo_errore
    if not forza and _cache["dati"] is not None:
        return _cache["dati"]
    try:
        dati = _leggi_drive() if modalita() == "drive" else _leggi_locale()
        _ultimo_errore = None
    except Exception as errore:                     # rete giu', permessi, JSON rotto
        _ultimo_errore = f"lettura: {type(errore).__name__}: {errore}"
        dati = _cache["dati"] if _cache["dati"] is not None else archivio_vuoto()
    _cache["dati"] = _normalizza(dati)
    _cache["letto"] = time.time()
    return _cache["dati"]


def scrivi(dati: dict) -> bool:
    """Salva l'archivio. Ritorna True se il salvataggio remoto e' andato a buon fine."""
    global _ultimo_errore
    dati = _normalizza(dati)
    dati["aggiornato"] = time.strftime("%Y-%m-%d %H:%M")
    _cache["dati"] = dati
    try:
        if modalita() == "drive":
            _scrivi_drive(dati)
        else:
            _scrivi_locale(dati)
        _ultimo_errore = None
        return True
    except Exception as errore:
        _ultimo_errore = f"scrittura: {type(errore).__name__}: {errore}"
        return False


def aggiorna(modifica) -> bool:
    """
    Rilegge l'archivio dalla fonte, applica `modifica(archivio)` e riscrive.

    La rilettura serve perche' piu' persone possono giocare in parallelo: cosi'
    si scrive sopra solo la propria parte e non si cancella quella degli altri.
    Non e' un lock: se due salvano nello stesso secondo, vince l'ultimo. Per un
    uso familiare e' un rischio accettabile.
    """
    dati = leggi(forza=True)
    modifica(dati)
    return scrivi(dati)


def invalida_cache() -> None:
    _cache["dati"] = None
