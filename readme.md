## 3. SAMOSTATNÁ PRÁCE

### Zadání:

Navrhněte distribuovanou aplikaci realizující distribuovanou cache se stromovou strukturou. Jedná se o binární strom,
kde počet úrovní bude 3 nebo 4. Počet úrovní je volitelný pomocí konfiguračního parametru, stejně jako identifikace
(IP adresa nebo jméno) kořenového uzlu. Hierarchická struktura cache bude evidována jako odpovídající model v
Apache Zookeeper.

### Základní podmínky:
- V konfiguraci (parametr ve Vagrantfile) bude možné definovat, který uzel bude kořen stromu a kolik úrovní
stromu má být vytvořeno.
- Počet úrovní binárního stromu je konfigurovatelný a může být buď 3, nebo 4 (včetně kořene)
- Po startu systému se všechny vytvořené uzly připojí ke kořenovému, s jehož pomocí vytvoří stromovou
strukturu, jejíž aktuální stav bude zaznamenám v odpovídajícím modelu Zookeeperu

- Apache Zookeper využijte pouze pro evidenci stromové struktury cache, nikoli k implementaci key-
value úložiště.

- Funkce stromové cache:
  - každý uzel pracuje jako jednoduchý key-value store, který implementuje pomocí REST API tři
základní op.erace PUT, GET a DELETE
  - primární kopii dat udržuje kořenový uzel, ostatní uzly pracují jako cache.
  - Funkce operace GET: pokud daný uzel (list nebo jeho nadřazený uzel) nezná hodnotu klíče, dotáže se
na ni svého nadřazeného uzlu. Dotaz se takto může rekurzivně dostat až ke kořenovému uzlu, který
odpoví buď tím, že klíč opravdu neexistuje, popř. odpoví celým key-value záznamem, který si
dotazující se uzel uloží do svojí cache. Znamená to, že pokud se takto dotáže uzel, který je listem,
uloží se vrácený záznam key-value do všech uzlů, které jsou na cestě ke kořenovému.
  - Operace PUT: funguje stejným způsobem jako GET a je tedy propagována až do kořene, jen s tím
rozdílem, že uzel nečeká až hodnota bude uložena na kořenovém uzlu, ale pouze na jeho nadřazeném
uzlu.
  - Operace DELETE: funguje stejným způsobem jako PUT.
- Implementované REST API popište pomocí OpenAPI, viz https://swagger.io/resources/open-api/
- Realizuje i jednoduchou klientskou aplikaci, pomocí které se lze z příkazové řádky provádět uvedené 3
operace na libovolném uzlu.
- Ze způsobu funkce popsané hierarchické cache je zřejmé, že chybí mechanismus pro zajištění tvz. „cache
coherence“. Změny (PUT a DELETE) jsou propagovány pouze směrem nahoru ke kořenovému uzlu, nikoliv
do ostatních větví stromu. Provedťe úvahu o tom, jak by bylo možné v tomto modelu zajistit cache
coherence. Nejdříve sami definujte podmínky (např. rychlost konvergence, požadavky na aktuálnost
dat, apod.) a pak na jejich základně navrhněte řešení.

### Technické podmínky

- Využití nástrojů Vagrant a Docker pro vytvoření a spuštění infrastruktury.
- Sestavení aplikace musí být možné v prostředí Unix/Linux




# Popis implementace




### Definované endpointy

### Open API

### Zookeeper
Při nastartování clientské aplikace se uzel připojí k běžícímu Zookeeper kontejneru (běžící na adrese

#### Test vytvořené struktury





## Sestavení a spuštění

## Testování aplikace


### Terminál
Součástí řešení je i ve složce *client/terminal* skript, který slouží k otestování jednotlivých endpointů. Při sestavování se přibaluje k rodičovskému docker containeru. Využívá systémových proměnných, které používá pro identifikaci všech možných adres na které můžou být zasílány HTTP požadavky. Tudíž je potřeba tento script spustit při připojení k docker terminálu rodičovského kontejneru. Skript se v kontejneru nachází na ve složce /opt/terminal/ a může být spušten pomocí příkazu ``/usr/bin/python3 /opt/terminal/main.py``.

Po spuštění vypíše program všechny dostupné uzly a je možné do něj zadávat následující příkazy:

- put <node_id> <key> <value>
  - přidání/přepsání záznamu do stromové struktury 
- get <node_id> <key>
  - vypsání hodnoty k předanému klíči
- delete <node_id> <key>
  - odstranění klíče ze stromové struktury
- exit
  - ukončení programu

kde:
- <node_id> je id uzlu na který bude zasílána žádost. Id uzlu se určuje podle seznamu, který program vypsal při spuštění. Indexuje se od 0.
- <key> klíč pod kterým chce uživatel přistupovat k hodnotě
- <value> hodnota kterou chce uživatel uložit




## Cache coherence
