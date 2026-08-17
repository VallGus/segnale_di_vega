# Codici segreti e accessi

## Il problema che risolve

Prima, il menu elencava tutte le partite con nome e capitolo, e chiunque poteva
premere «Continua» su quella di un'altra — sovrascrivendola. In famiglia è un
non-problema; con la classe di Marta diventa il primo incidente.

Adesso: scrivi il tuo nome e il tuo codice, ritrovi la tua partita. Le altre non
le vedi nemmeno esistere.

## Quanto vale questa protezione

Diciamolo chiaro, perché contarci più di quanto merita è il modo per farsi male:

**Cosa ferma.** Che una bambina apra per sbaglio o per curiosità la partita di
un'altra. Questo è il problema reale e lo ferma bene.

**Cosa non ferma.** Un codice di quattro cifre ha diecimila combinazioni: chi ha
in mano l'archivio e un po' di pazienza le prova tutte. E le bambine si
scambieranno i codici comunque — è quello che fanno i bambini. Serratura da
camera, non da banca.

**Cosa si fa per non peggiorare le cose.** Il codice non viene mai scritto in
chiaro. Nell'archivio finisce solo un'impronta PBKDF2-HMAC-SHA256 a 200.000
iterazioni, con sale casuale diverso per ogni giocatrice. Se il file finisse dove
non deve, i codici non sarebbero leggibili a occhio, e il sale diverso impedisce
di forzarle tutte in un colpo solo. Il confronto usa `hmac.compare_digest`, che
non lascia capire dal tempo di risposta quante cifre iniziali sono giuste.

Inoltre: cinque codici sbagliati e la sessione si blocca, il che rende la forza
bruta dal browser impraticabile.

## Come funziona per chi gioca

**Prima volta:** scrive nome e codice, e li registra. Non serve nessuna
approvazione da parte tua: il link basta.

**Volte successive:** stesso nome, stesso codice, ritrova la partita.

**Nome già preso:** se il codice non corrisponde, l'app dice di scegliere un
altro nome. Due Sofia nella stessa classe useranno `sofia` e `sofia b`.

Codici rifiutati: meno di 4 cifre, tutte le cifre uguali (`1111`), lettere.

## L'area «Per i grandi»

Protetta da una password che sta nei Secrets, **non nel codice**. Da lì vedi le
statistiche di tutte le giocatrici, il log di chi ha usato l'app, e puoi
assegnare un codice nuovo a chi l'ha dimenticato — perché succederà.

Si configura aggiungendo ai Secrets:

```toml
[genitore]
password = "scegli-una-password-lunga"
```

oppure passandola come terzo argomento a `prepara_segreti.py`:

```bash
python prepara_segreti.py CHIAVE.json FILE_ID "la-tua-password"
```

**Se non la configuri**, l'area resta chiusa quando l'app è pubblicata, e aperta
solo quando il gioco gira in locale sul tuo Mac. È una scelta voluta: meglio
inaccessibile che aperta a tutti per una dimenticanza di configurazione.

## Partite create prima dei codici

Non hanno una credenziale, quindi restano **adottabili**: il primo che entra con
quel nome sceglie il codice, e da quel momento il nome è protetto. Partita e
statistiche non vengono toccate.

È un buco, ed è limitato al passaggio di versione: se qualcuno indovinasse un
nome esistente prima del legittimo proprietario, se lo prenderebbe. Con le
partite che hai adesso (la tua) il rischio è nullo — ti basta entrare una volta
per chiuderlo.

## Cosa resta aperto

**Scritture in contemporanea.** L'archivio è un file unico su Drive. L'app lo
rilegge prima di ogni scrittura e sovrascrive solo la propria parte, quindi la
finestra di collisione è di circa un secondo per salvataggio. Con tre o quattro
bambine sparse nel pomeriggio è trascurabile; con dieci tutte insieme all'uscita
da scuola non lo è più. Se arrivi a quel punto, la soluzione è un database vero
al posto del file JSON: scritture indipendenti, nessuna collisione.

**Nessuna cifratura dei dati di gioco.** Nomi, capitoli e statistiche stanno in
chiaro nell'archivio. Chi ha accesso al file li legge. Il file è privato sul tuo
Drive, condiviso solo col service account, quindi il perimetro è quello.

## Le prove

```bash
python prova_accessi.py      # codici: hash, sale, rifiuti, separazione dati
python prova_genitori.py     # area genitori, adozione partite vecchie, reset
python prova_interfaccia.py  # tutti i percorsi dell'interfaccia, senza browser
```
