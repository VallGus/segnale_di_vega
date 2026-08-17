# -*- coding: utf-8 -*-
"""
Prova dell'interfaccia senza browser, con AppTest di Streamlit.

Si lancia con:  python prova_interfaccia.py

Controlla che menu, avvio partita, risposte, allenamento e pannelli dello
storico non generino eccezioni. Non verifica l'estetica: verifica che nulla si
rompa lungo i percorsi che una bambina percorre davvero.
"""

import shutil

from streamlit.testing.v1 import AppTest

import archivio as A


def controlla(app, passo: str) -> None:
    if app.exception:
        for eccezione in app.exception:
            print(f"  ECCEZIONE in «{passo}»: {eccezione.value}")
        raise SystemExit(1)
    print(f"  ok: {passo}")


def premi(app, etichetta: str):
    for pulsante in app.button:
        if pulsante.label == etichetta:
            return pulsante.click().run()
    raise SystemExit(f"pulsante non trovato: {etichetta}")


def main() -> None:
    shutil.rmtree(A.CARTELLA_LOCALE, ignore_errors=True)

    app = AppTest.from_file("app.py", default_timeout=90).run()
    controlla(app, "apertura del menu")

    app = premi(app, "Comincia")
    controlla(app, "avvio di una partita nuova")

    for giro in range(8):
        if app.text_input:
            app.text_input[0].set_value("48" if giro % 3 else "0")
            app = premi(app, "Rispondi")
            controlla(app, f"risposta al giro {giro}")
        else:
            scelte = [b for b in app.button
                      if b.label not in ("Salva adesso", "Torna al menu")]
            if scelte:
                app = scelte[0].click().run()
                controlla(app, f"scelta narrativa al giro {giro}")

    if app.radio:
        app = app.radio[0].set_value("Storico completo").run()
        controlla(app, "pannello «Storico completo»")

    app = premi(app, "Torna al menu")
    controlla(app, "ritorno al menu")

    for pulsante in app.button:
        if pulsante.label.startswith("Modalità allenamento"):
            app = pulsante.click().run()
            break
    controlla(app, "ingresso in allenamento")

    app.text_input[0].set_value("42")
    app = premi(app, "Rispondi")
    controlla(app, "risposta in allenamento")

    app = premi(app, "Torna al menu")
    controlla(app, "uscita da allenamento")

    app = premi(app, "Storico e statistiche")
    controlla(app, "pannello storico dal menu")

    print("\nTutto verde: nessuna eccezione nell'interfaccia.")


if __name__ == "__main__":
    main()
