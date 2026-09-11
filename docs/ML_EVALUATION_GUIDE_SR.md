# ML evaluacija — beleške za diplomski rad

Ovaj dokument predstavlja pomoćni pregled ML dela projekta. Nije zamena za glavno poglavlje diplomskog rada, već sažetak implementirane logike i načina tumačenja rezultata.

## Ideja aplikacije

Aplikacija učitava merenja nivoa zračenja i nad njima vrši detekciju anomalija. Trenutno se podaci unose preko CSV ili ZIP fajlova, dok je obrada podataka u realnom vremenu planirana kao buduće proširenje.

Kod mock podataka postoji kolona `is_anomaly`, koja predstavlja poznatu oznaku. Kod realnih podataka ova kolona ne mora da postoji. U tom slučaju model generiše `predicted_anomaly` i `anomaly_score`, ali sistem ne prikazuje metrike za koje je potrebna poznata tačna oznaka.

Zato su razdvojena dva slučaja:

- podaci sa labelama, kod kojih je moguća objektivna evaluacija
- podaci bez labela, kod kojih je moguća detekcija, ali ne i računanje supervised metrika

## Zašto se koriste supervised i unsupervised modeli

Unsupervised modeli su važni za realne podatke jer u praksi često ne postoji unapred pripremljena oznaka anomalije. Oni uče strukturu podataka bez korišćenja `is_anomaly` kolone. Ako labele postoje, koriste se tek nakon predikcije za proveru rezultata.

Supervised modeli se koriste samo kada postoje poznati primeri normalnih i anomalnih merenja. Oni uče iz tih primera, a zatim se ocenjuju na kasnijem test periodu.

Ova podela omogućava prikaz praktičnog scenarija bez labela i kontrolisane evaluacije na označenom skupu.

## Korišćeni modeli

### Unsupervised modeli

- Isolation Forest
- Local Outlier Factor
- One-Class SVM
- DBSCAN
- K-Means
- Gaussian Mixture Model
- PCA
- HBOS
- ECOD

Modeli pokrivaju izolacione, lokalno-gustinske, granične, klasterske, probabilističke, rekonstrukcione i distribucione pristupe detekciji anomalija.

DBSCAN je zadržan kao clustering baseline. Standardni DBSCAN nema isti reusable `predict` tok za buduće zapise kao ostali operativni detektori.

### Supervised modeli

- Logistic Regression
- Decision Tree
- Random Forest
- Gradient Boosting
- KNN Classifier

Ovim izborom porede se linearni klasifikator, interpretabilno stablo, dva ensemble pristupa i distance-based klasifikator.

## Train/test podela

Pošto su podaci vremenska serija, koristi se hronološka podela:

```text
prvih 70% podataka  → trening skup
poslednjih 30%      → test skup
```

Model zato ne trenira na budućim merenjima pa se zatim testira na ranijim. Vrednosti za popunjavanje nedostajućih podataka i parametri skaliranja računaju se samo iz trening skupa.

## Metrike

Za označene podatke računaju se:

- accuracy
- precision
- recall
- F1-score
- ROC-AUC
- PR-AUC
- FPR i FNR
- TP, TN, FP i FN
- vreme treniranja i predikcije
- statistika anomaly score vrednosti

Accuracy nije dovoljna kao jedini kriterijum jer su anomalije retke. Zbog neuravnoteženosti skupa posebno su važni precision, recall, F1-score, PR-AUC i konfuziona matrica.

Regresione metrike MAE, MSE, RMSE i R² nisu primarne jer cilj nije predikcija sledeće tačne vrednosti zračenja, već klasifikacija ili detekcija anomalnih merenja.

Standardna devijacija i varijansa anomaly score vrednosti prikazuju raspodelu rezultata jednog modela. Ne koriste se za proglašavanje najboljeg modela jer različiti algoritmi proizvode score vrednosti na različitim skalama.

## Vizuelizacije

Projekat generiše:

- poređenje accuracy, precision, recall i F1-score vrednosti
- poređenje ROC-AUC i PR-AUC vrednosti
- konfuzione matrice
- ROC krive
- Precision-Recall krive sa positive-class baseline vrednošću
- grafikone vremena treniranja i predikcije
- raspodele karakteristika pre i posle skaliranja
- korelacionu matricu ulaznih karakteristika

## Realni podaci bez labela

Ako dataset nema kolonu `is_anomaly`, ne prikazuju se accuracy, precision, recall, F1-score, ROC-AUC ili konfuziona matrica. Bez ground-truth oznake te vrednosti ne mogu objektivno da se izračunaju.

U tom slučaju sistem prikazuje:

- broj detektovanih anomalija
- procenat anomalija
- prosečan anomaly score
- standardnu devijaciju i varijansu score vrednosti
- listu detektovanih anomalija

Na taj način sistem ne izmišlja evaluacione rezultate za realne neoznačene podatke.

## Predložena formulacija za rad

Sistem trenutno obrađuje podatke učitane iz CSV ili ZIP fajlova, dok je arhitektura postavljena tako da se kasnije može proširiti obradom podataka u realnom vremenu. Kod označenih skupova kolona `is_anomaly` omogućava treniranje supervised modela i objektivnu proveru predikcija. Unsupervised modeli ne koriste ovu kolonu tokom treniranja, već samo prilikom naknadne evaluacije. Kod neoznačenih realnih skupova sistem generiše predikcije anomalija, ali ne računa metrike za koje ne postoji ground-truth oznaka.
