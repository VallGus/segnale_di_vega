# Lo storico permanente

Il gioco tiene due contabilità diverse, e la differenza conta.

**Statistiche di partita** (`stato["statistiche"]`) — vivono dentro una partita e
servono al motore per decidere la domanda successiva. Si azzerano a partita nuova.

**Storico permanente** (`storico.py`) — vive nell'archivio, legato al nome del
salvataggio, e accumula **tutte** le risposte di quella giocatrice: partite,
allenamenti, sessioni diverse, mesi diversi. È da qui che si legge cosa sa
davvero e cosa no.

---

## Perché la precisione media non basta

Se Marta sbaglia `6x7` dieci volte in agosto e la azzecca dieci volte in
settembre, la precisione totale dice **50%**. È un numero vero e inutile: quella
tabellina ormai la sa.

Per questo ogni moltiplicazione tiene tre cose invece di una:

| campo | cosa è | a cosa serve |
|---|---|---|
| `ok` / `ko` | conteggi di sempre | quante volte è stata incontrata |
| `ultimi` | gli ultimi 12 esiti (1/0) | com'è andata **di recente** |
| `serie` | giuste consecutive attuali | se è stata consolidata adesso |

La classificazione guarda il recente, non la media storica:

- 🟢 **consolidata** — almeno 4 giuste di fila e nessun errore nelle ultime 5
- 🟡 **in corso** — precisione recente fra 60% e 99%, o meno di 3 tentativi
  (troppi pochi dati per dire qualcosa)
- 🔴 **da allenare** — sotto il 60% nelle ultime 5
- ⬜ **mai capitata** — non è ancora uscita nemmeno una volta

Le soglie sono in cima a `storico.py` (`SERIE_PER_CONSOLIDARE`,
`SOGLIA_FRAGILE`, `FINESTRA_RECENTE`): sono il primo posto da toccare dopo aver
visto qualche settimana di dati reali.

---

## Lo storico guida il gioco, non solo il resoconto

A ogni partita nuova le statistiche iniziali vengono **seminate** dallo storico
(`semina_statistiche`). Il motore adattivo sa quindi dalla prima domanda su cosa
insistere, invece di dover riscoprire le debolezze ogni volta da zero.

La semina è **compressa** di proposito, e questo è il parametro più delicato di
tutto il file. Passando i conteggi veri, il peso adattivo va a fondo scala:

| compressione | domande sulle fragili | domande sulle consolidate |
|---|---|---|
| nessuna (conteggi veri) | **60%** | 6% |
| `tetto=4` | 55% | 7% |
| `tetto=2` (attuale) | **37%** | 38% |
| `tetto=1` | 26% | 50% |

Senza compressione due sole moltiplicazioni deboli si prendono il 60% delle
domande — punizione, non allenamento — e quelle già imparate non ricompaiono
mai più, quindi non vengono mai ripassate. Con `tetto=2` le fragili restano
sotto attenzione forte e il ripasso continua a girare.

---

## Dove si legge

**Durante la partita** — pannello in fondo, *Per i grandi: come stanno andando le
tabelline*, linguetta **Storico completo**.

**Dal menu** — pulsante **Storico e statistiche**: si scegle la giocatrice e si
vede tutto, compreso *Chi ha usato l'app*.

**In allenamento** — pannello *Storico permanente di questa giocatrice*.

La griglia 10x10 di simboli è il colpo d'occhio: le righe e le colonne dove si
addensa il rosso sono le tabelline su cui lavorare. Sotto, la tabella **Da
allenare** dà i numeri: tentativi, errori, precisione totale e precisione delle
ultime 5, che è quella che conta.

---

## Le prove

```bash
python verifica.py           # struttura della storia + simulazioni di partita
python prova_storico.py      # archivio, accumulo fra sessioni, semina
python prova_interfaccia.py  # tutti i percorsi dell'interfaccia, senza browser
```

`prova_storico.py` simula tre sessioni di una giocatrice debole di proposito su
`7x8` e `6x7` e verifica che il sistema le riconosca e le porti in cima alle
domande. Da rilanciare dopo ogni modifica alle soglie.
