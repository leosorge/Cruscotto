# Finance Cruscotto

App Streamlit ricavata dai sette notebook dell'autore. Integra 25 titoli e le sezioni IG, mm e za. Non richiede Colab, montaggio Drive o esecuzione di notebook.

## Avvio

Usare Python 3.12. Installare `pip install -r requirements.txt`, poi avviare `streamlit run app.py`.

## Pubblicazione

Caricare i file della cartella in un repository GitHub e selezionare `app.py` come file principale su Streamlit Community Cloud. Non includere dati personali o credenziali. Nessuna pubblicazione è stata effettuata durante la creazione del progetto.

## Comportamento

Il pulsante Aggiorna recupera i dati da Morningstar per ISIN, poi da Yahoo mediante i ticker originali. La disponibilità dei fornitori e la correttezza dei ticker/classi devono essere verificate dal server di destinazione. Le date delle quotazioni sono visibili. Il riferimento di inizio anno è l'ultimo prezzo disponibile entro il 1 gennaio, senza utilizzare prezzi successivi alla data richiesta. Non vengono applicate le modifiche manuali dimostrative del notebook originario.

Le quantità sono convenzionalmente uno. Non vengono mostrate somme patrimoniali: prezzi con valute o convenzioni diverse non rappresentano un portafoglio confrontabile. La variazione è sul prezzo, senza cedole/distribuzioni. La media per banca è aritmetica e riguarda solo titoli con dati disponibili.

I titoli senza storico o ticker utilizzabile restano N/D. Per strumenti Borsa Italiana sono conservati i link originari; lo scraping generico del notebook è stato escluso perché potrebbe riconoscere numeri che non sono prezzi. Il BTP ha un ISIN configurato diverso da quello nel link originario: verificare la corretta classe/negoziabilità prima di utilizzare una quotazione. Non sono stati inventati prezzi.

## Verifiche

Il progetto include controlli sulla normalizzazione dello storico, sulle date e sui dati mancanti. Le quotazioni live e il deployment Streamlit devono essere verificati nell'ambiente di destinazione.

Verifica effettuata: avvio con Streamlit AppTest, 25 titoli presenti e nessuna eccezione iniziale. Una richiesta reale Yahoo ha restituito un limite di richieste (HTTP 429); nessuna quotazione aggiornata è stata confermata.

## Verifica del 3 ottobre 2026
Corretto il parametro session di mstarpy: richiede una MorningstarSession, non una requests.Session generica. La prova reale su Pictet Security fallisce ora all’avvio di Chrome richiesto da mstarpy. Yahoo restituisce HTTP 429. Nessuna quotazione è stata recuperata; il deploy Streamlit non è verificato.
