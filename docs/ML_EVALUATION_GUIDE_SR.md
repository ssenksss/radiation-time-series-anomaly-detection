# ML evaluacija — beleške za diplomski rad

Ovaj fajl koristim kao pomoćne beleške za poglavlje o evaluaciji modela. Nije zamišljen kao glavni tekst diplomskog rada, već kao pregled onoga što je urađeno u ML delu projekta.

## Ideja aplikacije

Aplikacija je zamišljena kao sistem u koji se učitavaju merenja nivoa zračenja, a zatim se nad tim podacima vrši detekcija anomalija. Trenutno se podaci učitavaju iz CSV ili ZIP fajlova, dok je kasnije moguće proširenje na podatke koji stižu u realnom vremenu.

Kod mock podataka postoji kolona `is_anomaly`. Ona predstavlja poznatu oznaku i može da se koristi za proveru tačnosti modela. Kod realnih podataka ova kolona ne mora da postoji. U tom slučaju sistem ne može da zna unapred šta je stvarna anomalija, već model sam generiše rezultat `predicted_anomaly` i vrednost `anomaly_score`.

Zato su u projektu jasno razdvojena dva slučaja:

- podaci sa labelama, gde je moguća evaluacija modela
- podaci bez labela, gde je moguća detekcija anomalija, ali ne i računanje supervised metrika

## Zašto koristim supervised i unsupervised modele

U projektu su zadržana oba pristupa zato što odgovaraju različitim situacijama.

Unsupervised modeli su važni za realne podatke, jer u praksi često ne postoji ručno označena kolona koja govori da li je neko merenje anomalija. Ovi modeli ne koriste labele tokom treniranja, već pokušavaju da pronađu neuobičajene zapise na osnovu strukture podataka.

Supervised modeli se koriste kada postoji kolona `is_anomaly`. Tada model može da uči iz poznatih primera normalnih i anomalnih merenja, pa se njegov rezultat može uporediti sa stvarnom oznakom.

Ovakva podela mi omogućava da prikažem i praktičan scenario rada sa realnim podacima bez labela, i kontrolisanu evaluaciju na označenom skupu podataka.

## Korišćeni modeli

### Unsupervised modeli

- Isolation Forest
- Local Outlier Factor
- One-Class SVM
- DBSCAN
- K-Means Distance
- Gaussian Mixture Model
- PCA Reconstruction Error
- HBOS
- ECOD

Ovi modeli nisu izabrani nasumično. Pokrivaju nekoliko čestih pristupa detekciji anomalija: izolaciju neuobičajenih tačaka, lokalnu gustinu, učenje granice normalnog ponašanja, klasterizaciju, udaljenost od centra klastera, probabilističko modelovanje, rekonstrukcionu grešku i distribucione metode.

### Supervised modeli

- Logistic Regression
- Decision Tree
- Random Forest
- Gradient Boosting
- KNN Classifier

Ovi modeli predstavljaju standardne tradicionalne klasifikacione algoritme. Izabrani su da bi se uporedili jednostavan linearni model, interpretabilan model stabla, ensemble modeli i distance-based klasifikator.

## Train/test podela

Pošto su podaci vremenska serija, korišćena je hronološka podela umesto slučajne podele.

```text
prvih 70% podataka  -> trening skup
poslednjih 30%      -> test skup
```

Ovo je logičnije za ovakav tip podataka, jer model ne treba da trenira na budućim merenjima i zatim se testira na ranijim merenjima.

Kod unsupervised modela labele se ne koriste tokom treniranja. Ako labele postoje, koriste se tek posle predikcije, za računanje metrika.

DBSCAN je poseban slučaj, jer standardni DBSCAN nema klasičnu `predict` metodu za nove podatke. Zbog toga je u projektu tretiran kao clustering baseline. Koristan je za poređenje, ali nije najpraktičniji izbor za budući real-time rad.

## Metrike

Za označene podatke računaju se:

- accuracy
- precision
- recall
- F1-score
- ROC-AUC
- PR-AUC
- FPR
- FNR
- TP, TN, FP i FN
- vreme treniranja
- vreme predikcije
- statistika anomaly score vrednosti

Za accuracy, precision, recall, F1-score, ROC-AUC i PR-AUC bolji je veći rezultat. Za FPR, FNR, standardnu devijaciju, varijansu, vreme treniranja i vreme predikcije bolji je manji rezultat.

Accuracy nije dovoljna sama po sebi, jer su anomalije retke. Model može da ima visoku accuracy vrednost čak i ako ne pronađe dovoljno anomalija. Zato su za ovaj problem posebno važni recall, precision, F1-score i PR-AUC.

Regresione metrike kao MAE, MSE, RMSE i R² nisu korišćene kao glavne metrike zato što cilj ovog rada nije predikcija tačne numeričke vrednosti nivoa zračenja. Cilj je detekcija da li je merenje normalno ili anomalno.

## Vizuelizacije

U projektu se generišu sledeći grafici:

- konfuzione matrice
- ROC krive
- Precision-Recall krive
- poređenje klasifikacionih metrika
- poređenje ROC-AUC i PR-AUC vrednosti
- vreme treniranja i predikcije
- box plot anomaly score vrednosti
- swarm plot anomaly score vrednosti
- learning curves za supervised modele
- convergence prikaz za Gradient Boosting

Ovi grafici služe da se rezultati ne prikažu samo u tabeli, već i vizuelno.

## Realni podaci bez labela

Ako realni dataset nema kolonu `is_anomaly`, tada se ne prikazuju accuracy, precision, recall i F1-score, jer ne postoji stvarna oznaka sa kojom bi se rezultat uporedio.

U tom slučaju sistem prikazuje:

- broj detektovanih anomalija
- procenat anomalija
- prosečan anomaly score
- standardnu devijaciju i varijansu score vrednosti
- listu detektovanih anomalija

Ovo je važno zato što sistem ne izmišlja evaluacione rezultate. Ako nema labela, postoji detekcija anomalija, ali ne postoji objektivna supervised evaluacija.

## Formulacija za diplomski

U radu se može objasniti ovako:

> Sistem trenutno obrađuje podatke učitane iz CSV fajlova, dok je struktura aplikacije postavljena tako da se kasnije može proširiti na rad sa podacima u realnom vremenu. Kod označenih skupova podataka koristi se kolona `is_anomaly`, koja omogućava izračunavanje klasifikacionih metrika. Kod neoznačenih realnih skupova podataka sistem sam generiše predikciju anomalije, ali ne računa supervised metrike jer ne postoji ground-truth oznaka.
