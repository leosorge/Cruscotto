# Finance Cruscotto

App Streamlit ricavata dai sette notebook dell'autore. Integra 30 titoli e le sezioni IG, mm e za. Non richiede Colab, montaggio Drive o esecuzione di notebook.

## Avvio

Usare Python 3.12. Installare `pip install -r requirements.txt`, poi avviare `streamlit run app.py`.

## Pubblicazione

Caricare i file della cartella in un repository GitHub e selezionare `app.py` come file principale su Streamlit Community Cloud. Non includere dati personali o credenziali. Nessuna pubblicazione è stata effettuata durante la creazione del progetto.

## Comportamento

Per za, il pulsante Aggiorna usa la ricerca Yahoo per ISIN e FT Markets come fallback, adattati da Untitled64. IG e mm mantengono Morningstar e i ticker Yahoo originali. La disponibilità dei fornitori e la correttezza dei ticker/classi devono essere verificate dal server di destinazione. Le date delle quotazioni sono visibili. Il riferimento di inizio anno è l'ultimo prezzo disponibile entro il 1 gennaio, senza utilizzare prezzi successivi alla data richiesta. Non vengono applicate le modifiche manuali dimostrative del notebook originario.

Le quantità sono convenzionalmente uno. Non vengono mostrate somme patrimoniali: prezzi con valute o convenzioni diverse non rappresentano un portafoglio confrontabile. La variazione è sul prezzo, senza cedole/distribuzioni. La media per banca è aritmetica e riguarda solo titoli con dati disponibili.

I titoli senza storico o ticker utilizzabile restano N/D. Per strumenti Borsa Italiana sono conservati i link originari; lo scraping generico del notebook è stato escluso perché potrebbe riconoscere numeri che non sono prezzi. Il BTP ha un ISIN configurato diverso da quello nel link originario: verificare la corretta classe/negoziabilità prima di utilizzare una quotazione. Non sono stati inventati prezzi.

## Verifiche

Il progetto include controlli sulla normalizzazione dello storico, sulle date e sui dati mancanti. Le quotazioni live e il deployment Streamlit devono essere verificati nell'ambiente di destinazione.

Verifica effettuata: avvio con Streamlit AppTest, 25 titoli presenti e nessuna eccezione iniziale. Una richiesta reale Yahoo ha restituito un limite di richieste (HTTP 429); nessuna quotazione aggiornata è stata confermata.

## Verifica del 3 ottobre 2026
Corretto il parametro session di mstarpy: richiede una MorningstarSession, non una requests.Session generica. La prova reale su Pictet Security fallisce ora all’avvio di Chrome richiesto da mstarpy. Yahoo restituisce HTTP 429. Nessuna quotazione è stata recuperata; il deploy Streamlit non è verificato.

## Aggiornamento za del 31 ottobre 2026

La sezione za contiene i 12 fondi con nomi e ISIN forniti dall'autore. Le sezioni IG e mm restano invariate. Tutte le viste, i grafici e il CSV usano la stessa anagrafica `titoli.json`. Gli ISIN sono visibili anche prima del recupero delle quotazioni. I ticker Yahoo precedenti di za sono rimossi: non sono stati verificati per le classi indicate. Il recupero di za avviene per ISIN tramite Yahoo e FT; in caso di indisponibilità i valori restano N/D.

## Metodo Untitled64 (31 ottobre 2026)

`fund_sources.py` riprende Yahoo Search e lo storico FT dal notebook Untitled64. Le date sono dinamiche, la valuta FT segue l’anagrafica, e za non avvia più mstarpy/Chrome. Sei test superati; prova live: 11 quotazioni za su 12, BGF World Tech LU0376438312 N/D, come nell’esecuzione salvata di Untitled64.

`Finance_Cruscotto.ipynb` scarica gli stessi moduli e la stessa anagrafica da questo repository. Non esegue più i vecchi notebook concatenati che interrompevano l’avvio. Produce una lista di osservazione senza quantità patrimoniali; i file quantità originali rimangono separati. I vecchi output sono rimossi per evitare di confonderli con nuove quotazioni.
