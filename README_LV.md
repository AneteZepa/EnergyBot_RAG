# Latvenergo strategiskas izpetes bots (RAG)

MI darbinata dokumentu analizes sistema, kas izstradata Latvenergo finansu parskatu, ilgtspejas merku un strategisko prezentaciju analizei. Sis projekts demonstre razosanai gatavu RAG (Retrieval-Augmented Generation) darba plūsmu ar mainamiem komponentiem, multimodalu dokumentu parsesanu un hibridu lokalo/attalinato skaitlosanas arhitekturu.

## Galvenas funkcijas

* **Multimodala PDF parsesana:** Izmanto jauno Hugging Face "Docling" rīku, lai ekstrahetu strukturetus datus no sarezgitam energētikas diagrammam un finansu tabulam 2025. gada starpposma parskatos.
* **Hibrida izkliedeta arhitektura:** Orkestresana un lietotaja saskarne darbojas uz viegla klienta (Mac M1), savkart smaga LLM apstrade tiek veikta uz specializeta skaitlosanas servera (Ollama uz PC).
* **Mainams LLM dzinējs:** Buveits, izmantojot LlamaIndex Settings objektu, kas lauj vienkarsi parslēgties no lokaliem Ollama modeliem uz Azure OpenAI vai Google Cloud Vertex AI bez koda izmainam.
* **Persistenta zinasanu baze:** Izmanto ChromaDB efektivai vektoru glabasanai un metadatu filtresanai (piemeram, filtresana pec "Ceturksna parskats" vai "Strategiska prezentacija").

## Tehnologiju kopums

* **Orkestresana:** LlamaIndex (Datu ietvars)
* **Vektoru datubaze:** ChromaDB (Persistenta)
* **Modeli:** * **LLM:** Llama 3.1 (caur Ollama)
    * **Iegulumi (Embeddings):** BGE-Small-v1.5 (Lokali)
    * **OCR/Parsesana:** Docling (Hugging Face / IBM)
* **DevOps:** Docker, Python 3.10+, Git

## Sistēmas arhitektura



Sistēma sastāv no diviem galvenajiem mezgliem:
1. Skaitlosanas serveris (PC): Hostē LLM un apstrada vaicajumus.
2. Lietojumprogrammas mezgls (Mac M1): Veic dokumentu indeksaciju un nodrosina lietotaja saskarni.

## Dati un salidzinosana

Sistema paslaik ir indeksēta ar sadiem Latvenergo koncerna datiem:
* **2025. gada 9 mēnesu starpposma parskats:** EBITDA izmainu un AER investiciju pieauguma analize.
* **2025. gada strategiskas prezentacijas:** Merki 2.3 GW atjaunigas energijas jaudas sasniegsanai.
* **Ceturksnu salidzinasana:** 3, 6 un 9 mēnesu galveno darbibas raditaju (KPI) navigesana.

## Uzstadisana un instalesana

1. Klonet repozitoriju:
git clone https://github.com/anetezepa/EnergyBot_RAG.git

2. Vides iestatisana:
Izveidojiet .env failu, lai noraditu uz jusu skaitlosanas serveri:
OLLAMA_BASE_URL=http://jusu-pc-ip:11434
DATA_PATH=./docs

3. Palaist ar Docker:
docker build -t latvenergo-bot .
docker run -p 8501:8501 latvenergo-bot

## Piemēra vaicajums

Lietotajs: "Kadi ir prognozetie saules energijas kopsavilkuma rādītāji 2030. gadam?"

Bots: "Balstoties uz 2025. gada 9 mēnesu zinojumu un strategisko planu, Latvenergo merkis ir paplasinat AER portfeli lidz 2.3 GW, kur saules energija veido būtisku dalu no jauna jaudu kopskaite, koncentrejoties uz Baltijas tirgus kopējo sinhronizaciju."

## Nakotnes MLOps plans

* **CI/CD Integracija:** Automatiska vektoru datubazes atjauninasana, kad GitHub repozitorija tiek augsupieladēti jauni parskati.
* **Makonu izvietosana:** Vektoru datubazes migracija uz Managed Chroma vai Azure AI Search.
* **Uzlabots RAG:** "Reranking" metodes ieviesana (izmantojot BGE-Reranker), lai palielinatu finansu datu precizitati.