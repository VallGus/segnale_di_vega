# -*- coding: utf-8 -*-
"""
Prova dell'interfaccia senza browser, con AppTest di Streamlit.

Si lancia con:  python prova_interfaccia.py

Percorre le strade che una bambina percorre davvero: registrazione, uscita,
rientro col codice giusto, rientro col codice sbagliato, partita, allenamento.
Verifica anche che una seconda giocatrice non veda la partita della prima, che
e' il motivo per cui i codici esistono.
"""

from __future__ import annotations

import os

os.environ["VEGA_ARCHIVIO"] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "salvataggi", "_prova_interfaccia.json"
)

from streamlit.testing.v1 import AppTest   # noqa: E402

import archivio as A                       # noqa: E402

esiti: list[bool] = []


def controlla(app, passo: str, condizione: bool = True) -> None:
    rotto = bool(app.exception)
    if rotto:
        for eccezione in app.exception:
            print(f"  [ECCEZIONE] {passo}: {eccezione.value}")
    esiti.append(not rotto and condizione)
    if not rotto:
        print(f"  [{'ok' if condizione else 'FALLITO'}] {passo}")


def premi(app, etichetta: str):
    for pulsante in app.button:
        if pulsante.label == etichetta:
            return pulsante.click().run()
    raise SystemExit(f"pulsante non trovato: «{etichetta}». "
                     f"Presenti: {[b.label for b in app.button]}")


def invia(app, form: str = "Entra"):
    for pulsante in app.button:
        if pulsante.label == form:
            return pulsante.click().run()
    raise SystemExit(f"submit non trovato: {form}")


def testo(app) -> str:
    pezzi = [e.value for e in app.markdown] + [e.value for e in app.caption] \
        + [e.value for e in app.error] + [e.value for e in app.success] \
        + [e.value for e in app.info] + [e.value for e in app.warning] \
        + [e.value for e in app.title] + [e.value for e in app.subheader]
    return " ".join(str(p) for p in pezzi)


def accedi(app, nome: str, codice: str):
    app.text_input[0].set_value(nome)
    app.text_input[1].set_value(codice)
    return invia(app)


def main() -> None:
    A.percorso_locale().unlink(missing_ok=True)

    app = AppTest.from_file("app.py", default_timeout=90).run()
    controlla(app, "schermata di accesso aperta", "Entra" in testo(app))

    print("\n1. Registrazione di una giocatrice nuova")
    app = accedi(app, "Marta", "24")
    controlla(app, "codice troppo corto rifiutato", "almeno 4" in testo(app))

    app = accedi(app, "Marta", "1111")
    controlla(app, "codice tutto uguale rifiutato", "indovina" in testo(app))

    app = accedi(app, "Marta", "2468")
    controlla(app, "registrata ed entrata", "Ciao Marta" in testo(app))

    print("\n2. Partita")
    app = premi(app, "Comincia l'avventura")
    controlla(app, "partita avviata", bool(app.button))

    for giro in range(6):
        if app.text_input:
            app.text_input[0].set_value("48" if giro % 3 else "0")
            app = premi(app, "Rispondi")
            controlla(app, f"risposta al giro {giro}")
        else:
            scelte = [b for b in app.button
                      if b.label not in ("Salva adesso", "Metti in pausa")]
            if scelte:
                app = scelte[0].click().run()
                controlla(app, f"scelta narrativa al giro {giro}")

    if app.radio:
        app = app.radio[0].set_value("Tutto lo storico").run()
        controlla(app, "pannello dello storico dentro la partita")

    print("\n3. Pausa, uscita e rientro")
    app = premi(app, "Metti in pausa")
    controlla(app, "tornata alla scrivania", "Ciao Marta" in testo(app))
    controlla(app, "la partita in corso e' segnalata", "partita in corso" in testo(app))

    app = premi(app, "Esci")
    controlla(app, "uscita completata", "Ciao Marta" not in testo(app))

    app = accedi(app, "Marta", "9999")
    controlla(app, "codice sbagliato respinto", "sbagliato" in testo(app))
    controlla(app, "non e' entrata", "Ciao Marta" not in testo(app))

    app = accedi(app, "Marta", "2468")
    controlla(app, "rientro col codice giusto", "Ciao Marta" in testo(app))
    controlla(app, "ritrova la sua partita", "partita in corso" in testo(app))

    print("\n4. Allenamento")
    app = premi(app, "Allenamento (solo tabelline, senza storia)")
    controlla(app, "allenamento aperto", "Allenamento" in testo(app))
    app.text_input[0].set_value("42")
    app = premi(app, "Rispondi")
    controlla(app, "risposta in allenamento")
    app = premi(app, "Torna indietro")
    controlla(app, "uscita da allenamento", "Ciao Marta" in testo(app))

    print("\n5. Una seconda giocatrice non vede la prima")
    app = premi(app, "Esci")
    app = accedi(app, "Irene", "13579")
    controlla(app, "Irene registrata", "Ciao Irene" in testo(app))
    contenuto = testo(app)
    controlla(app, "nessuna traccia di Marta nella sua schermata",
              "Marta" not in contenuto and "marta" not in contenuto)
    controlla(app, "Irene non ha partite in corso", "partita in corso" not in contenuto)

    print("\n6. Il nome di un'altra non si prende col codice sbagliato")
    app = premi(app, "Esci")
    app = accedi(app, "Marta", "0000")
    controlla(app, "respinta", "sbagliato" in testo(app))
    controlla(app, "suggerisce di cambiare nome", "un altro" in testo(app))

    falliti = esiti.count(False)
    print(f"\n{len(esiti) - falliti}/{len(esiti)} prove superate.")
    if falliti:
        raise SystemExit(1)
    print("Tutto verde: nessuna eccezione e accessi separati.")


if __name__ == "__main__":
    main()
