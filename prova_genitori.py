# -*- coding: utf-8 -*-
"""
Prove sull'area per i grandi e sulle partite create prima dei codici.

Si lancia con:  python prova_genitori.py

Le partite della versione precedente non hanno un codice segreto. Restano
"adottabili": il primo che entra con quel nome sceglie il codice. Questo test
verifica che l'adozione funzioni e che dopo l'adozione il nome sia protetto.

Verifica inoltre che l'area per i grandi resti chiusa senza la password e che
il reset del codice non tocchi partita e statistiche.
"""

from __future__ import annotations

import json
import os

os.environ["VEGA_ARCHIVIO"] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "salvataggi", "_prova_genitori.json"
)

from streamlit.testing.v1 import AppTest   # noqa: E402

import archivio as A                       # noqa: E402
import identita as ID                      # noqa: E402
import motore as M                         # noqa: E402
import storico as ST                       # noqa: E402

PASSWORD = "password-di-prova"
esiti: list[bool] = []


def controlla(descrizione: str, condizione: bool) -> None:
    esiti.append(bool(condizione))
    print(f"  [{'ok' if condizione else 'FALLITO'}] {descrizione}")


def testo(app) -> str:
    pezzi = [e.value for e in app.markdown] + [e.value for e in app.caption] \
        + [e.value for e in app.error] + [e.value for e in app.success] \
        + [e.value for e in app.info] + [e.value for e in app.warning] \
        + [e.value for e in app.title] + [e.value for e in app.subheader]
    return " ".join(str(p) for p in pezzi)


def prepara_partita_senza_codice() -> None:
    """Ricrea la situazione dell'archivio prima dell'introduzione dei codici."""
    A.percorso_locale().unlink(missing_ok=True)
    A.invalida_cache()
    storico_g = M.carica_storico("gabriele")
    for _ in range(4):
        ST.registra(storico_g, "6x7", True)
    stato = M.nuovo_stato("Gabriele", storico_g)
    M.salva(stato, "gabriele", storico_g, 4)
    # Toglie la sezione credenziali, come nell'archivio vecchio
    dati = json.loads(A.percorso_locale().read_text(encoding="utf-8"))
    dati.pop("credenziali", None)
    A.percorso_locale().write_text(json.dumps(dati, ensure_ascii=False), encoding="utf-8")
    A.invalida_cache()


def main() -> None:
    print("1. Partita vecchia senza codice")
    prepara_partita_senza_codice()
    controlla("la partita c'e'", M.carica("gabriele") is not None)
    controlla("le statistiche ci sono",
              M.carica_storico("gabriele")["fatti"]["6x7"]["ok"] == 4)
    controlla("il nome NON risulta registrato", not M.slot_registrato("gabriele"))

    print("\n2. Adozione: chi entra con quel nome sceglie il codice")
    app = AppTest.from_file("app.py", default_timeout=90).run()
    app.text_input[0].set_value("Gabriele")
    app.text_input[1].set_value("5150")
    app = [b for b in app.button if b.label == "Entra"][0].click().run()
    controlla("entrato senza eccezioni", not app.exception)
    controlla("accolto", "Ciao Gabriele" in testo(app))
    controlla("ritrova la partita vecchia", "partita in corso" in testo(app))
    A.invalida_cache()
    controlla("statistiche vecchie conservate",
              M.carica_storico("gabriele")["fatti"]["6x7"]["ok"] == 4)
    controlla("ora il nome e' protetto", M.slot_registrato("gabriele"))
    controlla("col codice sbagliato non si entra piu'",
              not ID.verifica(M.credenziale("gabriele"), "0000"))

    print("\n3. Area per i grandi senza password configurata, app pubblicata")
    app = AppTest.from_file("app.py", default_timeout=90)
    app.secrets["gcp_service_account"] = {"client_email": "x@y.iam.gserviceaccount.com"}
    app.secrets["drive"] = {"file_id": "FINTO_ABBASTANZA_LUNGO_123456"}
    app = app.run()
    contenuto = testo(app)
    controlla("nessuna eccezione", not app.exception)
    controlla("l'area avvisa che va configurata", "Aggiungi nei Secrets" in contenuto)
    controlla("nessun nome di giocatrice esposto", "gabriele" not in contenuto.lower())

    print("\n4. Area per i grandi con password")
    app = AppTest.from_file("app.py", default_timeout=90)
    app.secrets["genitore"] = {"password": PASSWORD}
    app = app.run()
    controlla("nessuna eccezione", not app.exception)
    campi = app.text_input
    controlla("compare il campo password", len(campi) >= 3)

    campi[-1].set_value("sbagliata")
    app = [b for b in app.button if b.label == "Apri"][0].click().run()
    controlla("password sbagliata respinta", "Password sbagliata" in testo(app))
    controlla("area ancora chiusa", not any(b.label == "Cambia il codice" for b in app.button))

    app.text_input[-1].set_value(PASSWORD)
    app = [b for b in app.button if b.label == "Apri"][0].click().run()
    controlla("password giusta accettata", not app.exception)
    controlla("compare il reset del codice",
              any("Cambia il codice" in b.label for b in app.button))
    controlla("si vedono le statistiche della giocatrice",
              "Risposte totali" in testo(app) or bool(app.metric))

    print("\n5. Reset del codice dall'area genitori")
    prima = M.carica("gabriele")
    app.text_input[-1].set_value("31415")
    app = [b for b in app.button if "Cambia il codice" in b.label][0].click().run()
    controlla("nessuna eccezione", not app.exception)
    A.invalida_cache()
    controlla("codice nuovo attivo", ID.verifica(M.credenziale("gabriele"), "31415"))
    controlla("codice vecchio disattivato",
              not ID.verifica(M.credenziale("gabriele"), "5150"))
    controlla("partita intatta", M.carica("gabriele")["nodo"] == prima["nodo"])
    controlla("statistiche intatte",
              M.carica_storico("gabriele")["fatti"]["6x7"]["ok"] == 4)

    falliti = esiti.count(False)
    print(f"\n{len(esiti) - falliti}/{len(esiti)} prove superate.")
    if falliti:
        raise SystemExit(1)
    print("Tutto verde.")


if __name__ == "__main__":
    main()
