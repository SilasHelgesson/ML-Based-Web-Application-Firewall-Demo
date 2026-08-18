# README

**English version below** 🇺🇸

## Deutsch 🇩🇪

### Projektbeschreibung

Dieses Projekt besteht aus einer Web Application Firewall auf Basis von maschinellem Lernen und dem absichtlich verwundbaren Webshop, den sie schützt. Ein filternder Reverse-Proxy bewertet jede eingehende Anfrage mit einem Klassifikator aus Zeichen-n-Gramm-TF-IDF und handgebauten Merkmalen und blockiert alles, was nach SQL-Injection aussieht. Dahinter läuft ein kleiner Flask-Shop, in dem jede Datenbankabfrage per String-Interpolation gebaut wird — dieselben Angriffe lassen sich also mit und ohne Proxy fahren und der Unterschied mit `sqlmap` messen.

Entstanden als praktisches Projekt im Modul Internet Security (INSEC) an der TU Berlin.

> [!WARNING]
> `webserver/` ist **absichtlich verwundbar**. SQL-Injection, Second-Order-Injection und Stored XSS sind gewollt und im Quelltext dokumentiert. Der Ordner existiert, um in einer kontrollierten Umgebung angegriffen zu werden: nur lokal ausführen, niemals in ein fremdes Netz stellen und den Code nicht wiederverwenden. Der wiederverwendbare Teil ist der Detektor in `ml/` und `proxy/`.

### Funktionsweise

```
Client ──► Proxy :8080 ──────────────► Webserver :5000 ──► SQLite
             │                    (X-Proxy-Secret Header)
             │  P(malicious) ≥ Schwellenwert → 403
             └── SqliDetector (sqli_model.joblib)
```

Query-String und POST-Body jeder Anfrage werden zusammengefügt und von einer Pipeline mit zwei parallelen Merkmalszweigen bewertet:

1. **Zeichen-n-Gramm-TF-IDF (1–5)** auf dem URL-dekodierten, kleingeschriebenen Text, sodass `%27%20OR%201%3D1` als `' or 1=1` erkannt wird. Zeichen-n-Gramme greifen Signale unterhalb der Tokengrenze ab (`1=1`, `--`, `/**/`) und überstehen Verschleierung durch Inline-Kommentare wie `uni/**/on`.
2. **16 handgebaute numerische Merkmale** auf dem Rohtext: Sonderzeichendichte, Anzahl von Anführungszeichen, Semikola und Gleichheitszeichen, SQL-Schlüsselwörter, Kommentarmarker, Hex-Literale, Tautologien, Shannon-Entropie und Länge. Kodierungsartefakte bleiben hier auch ohne Dekodierung sichtbar.

Darauf eine logistische Regression, ca. 1,8 ms pro Anfrage (Auf meinem billiegen ThinkPad).

### Ergebnisse

Trainiert auf SQLiV3 (30.863 gelabelte Query-Strings), stratifizierter 75/25-Split:

| Metrik | Wert |
|---|---|
| Accuracy | 0,998 |
| Precision / Recall / F1 (Angriffsklasse) | 0,996 / 0,997 / 0,997 |
| ROC-AUC / PR-AUC | 0,9993 / 0,9968 |
| False Positives / False Negatives | 10 / 9 (von 7.716 Testfällen) |
| Latenz | 1,82 ms Mittel, 2,35 ms p95 |

**Robustheit gegen Verschleierung:** Auf 9.627 WAF-A-MoLE-Payloads, die nicht im Training vorkamen (Oktal-, Binär- und Hex-Literale, exotische Whitespaces, Groß-/Kleinschreibungs-Mangling), liegt die Erkennungsrate bei **97,1 %** (Schwellenwert 0,5). Die vollständige Ausgabe steht in [`ml/results/training_run.txt`](ml/results/training_run.txt), die `sqlmap`-Läufe mit und ohne Proxy in [`sqlmap-reports/`](sqlmap-reports/).

### Voraussetzungen

Stellen Sie sicher, dass Sie einen Python 3.x Interpreter sowie alle erforderlichen Pakete installiert haben. Diese sind in der Datei `requirements.txt` aufgeführt.

```bash
pip install -r requirements.txt
```

### Installation und Ausführung

1. Klonen Sie das Repository auf Ihren lokalen Rechner.

   ```bash
   git clone https://github.com/SilasHelgesson/sqli-ml-waf
   cd sqli-ml-waf
   ```

2. Installieren Sie die Abhängigkeiten.

   ```bash
   pip install -r requirements.txt
   ```

3. Starten Sie den verwundbaren Webserver (nur lokal).

   ```bash
   python webserver/main.py
   ```

4. Starten Sie in einem zweiten Terminal den filternden Proxy.

   ```bash
   python proxy/main.py
   ```

Ungeschützter Webserver auf <http://127.0.0.1:5000>, gefiltert auf <http://127.0.0.1:8080>. Der Demo-Login lautet `admin` / `admin`. Dieselbe Payload gegen beide Ports:

```bash
curl "http://127.0.0.1:5000/products?category=peripherals'%20UNION%20SELECT%20id,username,password,email,'x'%20FROM%20users--"   # Daten werden geleakt
curl "http://127.0.0.1:8080/products?category=peripherals'%20UNION%20SELECT%20id,username,password,email,'x'%20FROM%20users--"   # 403
```

Beide Prozesse lesen ihre Einstellungen aus Umgebungsvariablen: `PROXY_SECRET` (muss auf beiden Seiten übereinstimmen), `SQLI_MODEL`, `SQLI_THRESHOLD` (Standard 0,9), `BACKEND_URL`, `PROXY_PORT`, `WEBSERVER_PORT` und `REQUIRE_PROXY=1`, um direkte Zugriffe am Proxy vorbei abzulehnen.

Zum Neutrainieren:

```bash
cd ml
python train.py --data data/SQLiV3.csv --text-col 0 --label-col 1
python evaluate_model.py --model sqli_model.joblib --data data/fuzzed_data.csv
```

### Demo

<p align="center">
  <a href="https://www.youtube.com/watch?v=vIIwcqnJH6Y">
    <img src="https://img.youtube.com/vi/vIIwcqnJH6Y/hqdefault.jpg" alt="Demo-Video">
  </a>
</p>

### Projektstruktur

```
ml/                 Merkmalsextraktion, Training, Auswertung, trainiertes Modell
  data/             SQLiV3-Trainingsdaten + adversariale WAF-A-MoLE-Daten
  results/          aufgezeichnete Ausgabe der Referenzläufe
proxy/              filternder Reverse-Proxy
webserver/          absichtlich verwundbarer Flask-Shop (das Ziel)
sqlmap-reports/     sqlmap-Ausgaben, mit und ohne Proxy
docs/attacks.md     die Payloads für die einzelnen Endpunkte
```

Details zur Pipeline, zur Herkunft der Daten und zu den bekannten Lücken stehen in [`ml/README.md`](ml/README.md).

### Lizenz

Der Code in diesem Repository steht unter der [GNU General Public License v3.0 oder später](LICENSE).

Die mitgelieferten Datensätze fallen **nicht** unter diese Lizenz und behalten ihre ursprünglichen Bedingungen. `ml/data/SQLiV3.csv` und `ml/data/fuzzed_data.csv` stammen aus [`nidnogg/sqliv5-dataset`](https://github.com/nidnogg/sqliv5-dataset) von [Henrique Vermelho de Toledo](https://github.com/nidnogg) (MIT, siehe [`ml/data/LICENSE.upstream`](ml/data/LICENSE.upstream)), das wiederum auf [SQLiV3](https://www.kaggle.com/datasets/syedsaqlainhussain/sql-injection-dataset) von Syed Saqlain Hussain und dem Fuzzer [WAF-A-MoLE](https://github.com/AvalZ/WAF-A-MoLE) von Andrea Valenza und Luca Demetrio aufbaut.

## English 🇺🇸

### Project Description

This project is a machine-learning web application firewall and the deliberately vulnerable shop it protects. A filtering reverse proxy scores every inbound request with a character n-gram TF-IDF + handcrafted-feature classifier and blocks the ones that look like SQL injection. Behind it sits a small Flask shop whose every database query is built by string interpolation, so the same attacks can be run with and without the proxy in front and the difference measured with `sqlmap`.

Built as the practical project for the Internet Security (INSEC) course at TU Berlin.

> [!WARNING]
> `webserver/` is **intentionally vulnerable**. SQL injection, second-order injection and stored XSS are all deliberate and documented in the source. It exists to be attacked in a controlled setting: run it on localhost only, never expose it to an untrusted network, and don't reuse the code. The reusable part is the detector in `ml/` and `proxy/`.

### How It Works

```
client ──► proxy :8080 ──────────────► webserver :5000 ──► SQLite
             │                    (X-Proxy-Secret header)
             │  P(malicious) ≥ threshold → 403
             └── SqliDetector (sqli_model.joblib)
```

Each request's query string and POST body are concatenated and scored by a pipeline with two parallel feature branches:

1. **char n-gram TF-IDF (1–5)** over the URL-decoded, lowercased text, so `%27%20OR%201%3D1` is matched as `' or 1=1`. Character n-grams catch sub-token signals (`1=1`, `--`, `/**/`) and survive inline-comment obfuscation such as `uni/**/on`.
2. **16 handcrafted numeric features** over the raw text: special-character density, quote/semicolon/equals counts, SQL keyword and comment-marker counts, hex-literal and tautology flags, Shannon entropy and length. Encoding artefacts stay visible here even before decoding.

Logistic regression on top, ~1.8 ms per request.

### Results

Trained on SQLiV3 (30,863 labelled query strings), 75/25 stratified split:

| metric | value |
|---|---|
| accuracy | 0.998 |
| precision / recall / F1 (attack class) | 0.996 / 0.997 / 0.997 |
| ROC-AUC / PR-AUC | 0.9993 / 0.9968 |
| false positives / false negatives | 10 / 9 (of 7,716 test) |
| latency | 1.82 ms mean, 2.35 ms p95 |

**Robustness against obfuscation:** on 9,627 WAF-A-MoLE payloads never seen in training (octal/binary/hex literals, exotic whitespace, case mangling) the detection rate is **97.1%** at threshold 0.5. Full recorded output is in [`ml/results/training_run.txt`](ml/results/training_run.txt), and the `sqlmap` runs with and without the proxy are in [`sqlmap-reports/`](sqlmap-reports/).

### Prerequisites

Ensure you have Python 3.x installed as well as the required packages. These are listed in the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### Installation and Execution

1. Clone the repository to your local machine.

   ```bash
   git clone https://github.com/SilasHelgesson/sqli-ml-waf
   cd sqli-ml-waf
   ```

2. Install the dependencies.

   ```bash
   pip install -r requirements.txt
   ```

3. Start the vulnerable web server (localhost only).

   ```bash
   python webserver/main.py
   ```

4. In a second terminal, start the filtering proxy.

   ```bash
   python proxy/main.py
   ```

Unprotected backend on <http://127.0.0.1:5000>, filtered on <http://127.0.0.1:8080>. The demo login is `admin` / `admin`. Try the same payload against both ports:

```bash
curl "http://127.0.0.1:5000/products?category=peripherals'%20UNION%20SELECT%20id,username,password,email,'x'%20FROM%20users--"   # leaks
curl "http://127.0.0.1:8080/products?category=peripherals'%20UNION%20SELECT%20id,username,password,email,'x'%20FROM%20users--"   # 403
```

Both processes read their settings from the environment: `PROXY_SECRET` (must match on both sides), `SQLI_MODEL`, `SQLI_THRESHOLD` (default 0.9), `BACKEND_URL`, `PROXY_PORT`, `WEBSERVER_PORT`, and `REQUIRE_PROXY=1` to reject anything that didn't come through the proxy.

To retrain:

```bash
cd ml
python train.py --data data/SQLiV3.csv --text-col 0 --label-col 1
python evaluate_model.py --model sqli_model.joblib --data data/fuzzed_data.csv
```

### Demo

<p align="center">
  <a href="https://www.youtube.com/watch?v=vIIwcqnJH6Y">
    <img src="https://img.youtube.com/vi/vIIwcqnJH6Y/hqdefault.jpg" alt="Demo video">
  </a>
</p>

### Project Structure

```
ml/                 feature extraction, training, evaluation, saved model
  data/             SQLiV3 training set + WAF-A-MoLE adversarial set
  results/          recorded output of the reference runs
proxy/              filtering reverse proxy
webserver/          deliberately vulnerable Flask shop (the target)
sqlmap-reports/     sqlmap output, protected vs unprotected
docs/attacks.md     the payloads used against each endpoint
```

Details on the pipeline, dataset provenance and known gaps are in [`ml/README.md`](ml/README.md).

### License

The code in this repository is licensed under the [GNU General Public License v3.0 or later](LICENSE).

The bundled datasets are **not** covered by that license and remain under their original terms. `ml/data/SQLiV3.csv` and `ml/data/fuzzed_data.csv` come from [`nidnogg/sqliv5-dataset`](https://github.com/nidnogg/sqliv5-dataset) by [Henrique Vermelho de Toledo](https://github.com/nidnogg) (MIT — see [`ml/data/LICENSE.upstream`](ml/data/LICENSE.upstream)), which builds on [SQLiV3](https://www.kaggle.com/datasets/syedsaqlainhussain/sql-injection-dataset) by Syed Saqlain Hussain and the adversarial fuzzer [WAF-A-MoLE](https://github.com/AvalZ/WAF-A-MoLE) by Andrea Valenza and Luca Demetrio.
