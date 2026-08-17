# Il Segnale di Vega

Gioco di ruolo testuale in Streamlit per imparare le tabelline da 1x1 a 10x10.
Avventura fantascientifica in 7 capitoli, combattimenti a turni, trappole,
oggetti magici e salvataggi su file. Ogni azione del gioco passa da una
moltiplicazione.

## Avvio

```bash
python3 -m venv ~/virtualenvs/vega
source ~/virtualenvs/vega/bin/activate
pip install streamlit
cd <cartella del gioco>
streamlit run app.py
```

Si apre nel browser. Prima schermata: nome, nome del salvataggio, "Comincia".
I salvataggi finiscono in `salvataggi/<nome>.json` — un file per partita, e il
gioco salva da solo dopo ogni singola mossa (niente lavoro perso se si chiude
il coperchio del portatile).

## Meccaniche

| Situazione | Cosa serve | Se la risposta è giusta | Se è sbagliata |
|---|---|---|---|
| Attacco | 1 moltiplicazione | il colpo va a segno (2 danni, 3 con il Guanto Ionico) | colpo a vuoto |
| Difesa | 1 moltiplicazione | schivi | perdi 2-3 punti vita |
| Trappola / serratura / dialogo | 1 moltiplicazione | passi, a volte trovi un oggetto | perdi 1-3 punti vita e prosegui comunque |
| Oggetto magico | 1 moltiplicazione | l'oggetto si attiva | l'oggetto **non** si consuma, si riprova |
| Vita a zero | 3 moltiplicazioni giuste **di fila** | torni in piedi con 3 punti vita | la serie riparte da zero, nessun'altra penalità |

Dettagli pensati per non spegnere la motivazione:

- **Tre risposte giuste di fila = colpo critico** (danno doppio). È l'unico
  premio "a raffica": incentiva la costanza, non la velocità.
- **Non si perde mai la partita.** La morte costa tempo, non progressi.
- **Dopo ogni errore compare il risultato giusto e un trucco per ricordarlo**
  (`x9` = `x10` meno una volta, `x6` = `x5` più una volta, `x4` e `x8` per
  raddoppi). L'errore diventa un micro-insegnamento, non una punizione.
- **Ogni vittoria ridà 2 punti vita**, così la salute non si eroda in modo
  irreversibile.
- Un solo elemento non testuale: la barra della vita in ASCII. Nessuna
  animazione, nessun suono, nessuna distrazione.

## Le moltiplicazioni che escono più spesso

Le estrazioni sono pesate su due livelli.

1. **Peso statistico fisso.** Le tabelline con 1, 2, 5, 10 pesano 1. Le
   combinazioni fra 6-7-8-9 pesano 8. Le sei più difficili in assoluto secondo
   la letteratura sulla primaria (6x7, 7x8, 6x8, 6x9, 7x9, 8x9) più 4x7 e 3x8
   ricevono un bonus aggiuntivo.
2. **Peso adattivo.** Ogni fatto sbagliato aumenta la propria probabilità di
   ritornare (+80% per errore), ogni fatto azzeccato la riduce (-25%). È una
   ripetizione spaziata grezza ma funziona: le tabelline che Marta sbaglia
   tornano a trovarla.

Distribuzione misurata su 4000 estrazioni: 6x7, 8x9, 6x8, 7x8, 6x9, 7x9 escono
~260-300 volte ciascuna; 2x2, 5x5, 10x10 circa 10 volte. `7x8` e `8x7` sono
contate come lo stesso fatto nelle statistiche ma mostrate in ordine casuale.

## Durata (simulata, non promessa)

`verifica.py` gioca partite complete per stimare il carico. Con 22 secondi per
domanda e 25 secondi di lettura per scena:

| Precisione della giocatrice | Moltiplicazioni | Rianimazioni | Durata stimata |
|---|---|---|---|
| 50% | ~935 | ~30 | ~5,9 h |
| 60% | ~477 | ~9 | ~3,1 h |
| 70% | ~330 | ~0 | ~2,3 h |
| 85% | ~240 | 0 | ~1,7 h |

Cioè: all'inizio, quando le tabelline non ci sono, il gioco dura tanto e
allena molto; man mano che imparano, scorre. È il comportamento giusto, ma
significa che la durata non è una costante: sono 4-6 sessioni da un'ora per
una bambina che parte da zero, meno se va forte.

Se serve **più lunga**: alzare `hp` dei nemici in `storia.py` (+50% di HP =
+50% di domande in combattimento) oppure abbassare `DANNO_BASE` in `motore.py`.
Se serve **più corta**: il contrario.

## Altre leve, tutte in cima ai file

`motore.py`: `VITA_INIZIALE` (14), `DANNO_BASE` (2), `BONUS_CRITICO`,
`VITA_DOPO_RIANIMAZIONE` (3), `RISPOSTE_PER_RIANIMARSI` (3),
`CURA_DOPO_VITTORIA` (2).

`storia.py`: tutto il contenuto è dato, non codice. Un nuovo pianeta è un
blocco di nodi con `tipo`, `testo`, `vai_a`. Ogni nodo può dichiarare la fascia
di difficoltà delle sue moltiplicazioni (`facile`, `media`, `tosta`, `mista`) —
così una trappola d'inizio capitolo può essere gentile e il boss finale no.

## Controlli tecnici

```bash
python verifica.py
```

Verifica che nessun collegamento fra scene sia rotto, che non esistano nodi
irraggiungibili, che gli oggetti citati esistano; poi simula 48 partite
complete e stampa la distribuzione delle moltiplicazioni. Da rilanciare dopo
ogni aggiunta di contenuto.

## Modalità allenamento

Dal menu iniziale: solo moltiplicazioni, stessi pesi, nessuna storia. Utile
per cinque minuti in coda dal dentista.

## Pannello "Per i grandi"

In fondo alla schermata di gioco: numero di domande, precisione complessiva,
numero di rianimazioni e le dieci moltiplicazioni con la precisione più bassa.
Serve per decidere su cosa insistere fuori dal gioco, non per giudicare la
partita.

## La storia

Marta e il drone Bit attraversano sei pianeti per raccogliere sei Frammenti di
Senso e riaccendere l'Archivio Galattico, che qualcuno sta cancellando.
I sei pianeti sono sei modi di sbagliare la vita: chi conta tutto senza usare
niente, chi vuole essere guardato senza farsi conoscere, chi si prende cura di
una cosa sola, chi ha costruito muri finché non sente più la pioggia, chi fa
il suo dovere senza sapere più perché, chi ha proibito il gioco per
efficienza.

L'antagonista è l'Ordinatore: una macchina costruita da bambini spaventati di
perdere le cose care, che ha concluso che la soluzione è cancellare tutto
prima che si rompa. Nel finale si può spegnerlo o ripararlo cambiandone la
consegna da *cancella* a *custodisci*. Il finale buono non è vincere: è capire
perché si è rotto.

L'impianto — viaggio fra pianeti abitati ognuno da un adulto con un'idea
storta della vita, con una verità semplice alla fine — è un omaggio dichiarato
a *Il piccolo principe*. Personaggi, pianeti e testi sono originali.
