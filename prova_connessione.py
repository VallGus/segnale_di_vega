# -*- coding: utf-8 -*-
"""
Prove sulla robustezza della connessione a Drive.

Si lancia con:  python prova_connessione.py

Riproduce il guasto vero incontrato in produzione:

    SSLError: [SSL: DECRYPTION_FAILED_OR_BAD_RECORD_MAC] decryption failed

Sotto googleapiclient c'e' httplib2, che non e' thread-safe. Streamlit esegue
ogni rerun in un thread diverso: con un client condiviso, due thread scrivono
sulla stessa connessione TLS e la corrompono. Questo test verifica che
  1. ogni thread abbia il proprio client;
  2. una connessione guasta venga ricostruita e l'operazione ripetuta;
  3. un errore persistente venga comunque riportato, non nascosto;
  4. dieci thread in parallelo non si disturbino.

Il piano dei guasti e' una coda: il primo client creato prende il primo valore,
il secondo il secondo. Cosi' si simula «la connessione aperta si e' rotta, quella
nuova funziona» — che e' il caso reale. Se invece si guastano tutti i client, si
sta collaudando un'altra cosa (guasto persistente, punto 3).
"""

from __future__ import annotations

import ssl
import threading

import archivio as A

esiti: list[bool] = []
_blocco = threading.Lock()


def controlla(descrizione: str, condizione: bool) -> None:
    esiti.append(bool(condizione))
    print(f"  [{'ok' if condizione else 'FALLITO'}] {descrizione}")


class ClienteFinto:
    """Finge il client Drive. Conta le chiamate e sa guastarsi su richiesta."""

    def __init__(self, guasti: int):
        self.guasti = guasti
        self.chiamate = 0
        self.thread = threading.current_thread().name

    def chiama(self):
        self.chiamate += 1
        if self.guasti > 0:
            self.guasti -= 1
            raise ssl.SSLError("[SSL: DECRYPTION_FAILED_OR_BAD_RECORD_MAC] "
                               "decryption failed or bad record mac")
        return "contenuto"


class Officina:
    """Costruisce i client finti secondo un piano di guasti."""

    def __init__(self):
        self.piano: list[int] = []
        self.sempre_guasti = False
        self.creati: list[ClienteFinto] = []

    def costruisci(self) -> ClienteFinto:
        with _blocco:
            if self.sempre_guasti:
                guasti = 99
            else:
                guasti = self.piano.pop(0) if self.piano else 0
            cliente = ClienteFinto(guasti)
            self.creati.append(cliente)
            return cliente


def main() -> None:
    officina = Officina()
    vero_servizio = A._servizio
    A.ATTESA_PRIMA_DEL_RITENTATIVO = 0

    def servizio_finto(ricostruisci: bool = False):
        if ricostruisci:
            A._per_thread.servizio = None
        if getattr(A._per_thread, "servizio", None) is None:
            A._per_thread.servizio = officina.costruisci()
        return A._per_thread.servizio

    A._servizio = servizio_finto

    try:
        print("1. Un client per thread")
        A._per_thread.servizio = None
        primo = A._servizio()
        controlla("riusato nello stesso thread", A._servizio() is primo)

        altrui: list = []
        filo = threading.Thread(target=lambda: altrui.append(A._servizio()), name="secondo")
        filo.start()
        filo.join()
        controlla("un altro thread ne ottiene uno diverso", altrui[0] is not primo)
        controlla("i due client sanno da che thread vengono",
                  primo.thread != altrui[0].thread)

        print("\n2. Connessione guasta: ricostruita e operazione ripetuta")
        A._per_thread.servizio = None
        officina.creati.clear()
        officina.piano = [1, 0]          # il primo client si rompe, il secondo no
        risultato = A._con_ritentativo(lambda s: s.chiama())
        controlla("l'operazione riesce comunque", risultato == "contenuto")
        controlla("sono stati costruiti due client", len(officina.creati) == 2)
        controlla("il primo aveva provato e fallito", officina.creati[0].chiamate == 1)
        controlla("il secondo ha portato a termine", officina.creati[1].chiamate == 1)

        print("\n3. Guasto persistente: l'errore emerge, non viene nascosto")
        A._per_thread.servizio = None
        officina.sempre_guasti = True
        try:
            A._con_ritentativo(lambda s: s.chiama())
            controlla("errore propagato al chiamante", False)
        except ssl.SSLError:
            controlla("errore propagato al chiamante", True)
        officina.sempre_guasti = False

        print("\n4. Dieci thread in parallelo")
        officina.creati.clear()
        officina.piano = []
        identita: dict[str, int] = {}

        def lavora():
            A._per_thread.servizio = None
            cliente = A._servizio()
            for _ in range(5):
                A._con_ritentativo(lambda s: s.chiama())
            with _blocco:
                identita[threading.current_thread().name] = id(cliente)

        fili = [threading.Thread(target=lavora, name=f"t{i}") for i in range(10)]
        for f in fili:
            f.start()
        for f in fili:
            f.join()
        controlla("dieci thread hanno lavorato", len(identita) == 10)
        controlla("nessun client condiviso fra thread", len(set(identita.values())) == 10)
        controlla("cinque chiamate a testa, nessuna persa",
                  sorted(c.chiamate for c in officina.creati) == [5] * 10)
        controlla("nessuna connessione corrotta",
                  all(c.guasti == 0 for c in officina.creati))
    finally:
        A._servizio = vero_servizio
        A._per_thread.servizio = None

    falliti = esiti.count(False)
    print(f"\n{len(esiti) - falliti}/{len(esiti)} prove superate.")
    if falliti:
        raise SystemExit(1)
    print("Tutto verde: connessione per thread e ripresa dai guasti.")


if __name__ == "__main__":
    main()
