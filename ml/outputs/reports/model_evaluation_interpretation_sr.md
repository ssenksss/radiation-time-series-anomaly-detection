# Tumačenje rezultata evaluacije modela

Ovaj dokument je kraće objašnjenje rezultata evaluacije. Kompletne numeričke vrednosti se nalaze u tabelama `model_metrics_full.csv` i `model_metrics_best_marked.csv`, dok su grafici sačuvani u folderu `ml/outputs/figures`.

## Uloga labela u projektu

U projektu postoje dva slučaja rada sa podacima.

Prvi slučaj je kada dataset ima kolonu `is_anomaly`. Tada se ta kolona koristi kao originalna oznaka i moguće je izračunati metrike kao što su accuracy, precision, recall, F1-score, ROC-AUC, PR-AUC i konfuziona matrica.

Drugi slučaj je kada dataset nema kolonu `is_anomaly`. To je važan scenario za realne podatke, jer stvarna merenja često neće imati ručno označene anomalije. Tada sistem i dalje može da detektuje potencijalne anomalije, ali ne može objektivno da računa supervised metrike. U tom režimu se prikazuju broj detektovanih anomalija, procenat anomalija i statistika anomaly score vrednosti.

## Zašto supervised modeli imaju veoma visoke rezultate

Supervised modeli su evaluirani na označenom mock datasetu. Taj dataset je koristan za proveru da li pipeline radi pravilno, zato što postoje poznate anomalije. Međutim, anomalije u mock podacima su jasnije od onoga što se može očekivati u realnim merenjima.

Zbog toga modeli kao što su Decision Tree, Random Forest, Gradient Boosting i KNN Classifier postižu veoma visoke rezultate. Te rezultate ne treba predstavljati kao garanciju da će modeli isto raditi na realnim podacima. Oni pokazuju da sistem pravilno koristi labele, trenira modele i računa metrike kada ground truth postoji.

Za realne podatke bez labela važniji su unsupervised modeli, jer oni mogu da rade i kada `is_anomaly` kolona ne postoji.

## Napomena za DBSCAN

DBSCAN je zadržan kao clustering baseline. On je koristan za poređenje, ali ne radi potpuno isto kao modeli koji se treniraju i zatim primenjuju na nove podatke.

Standardni DBSCAN nema klasičnu `predict` metodu za buduće zapise. On grupiše trenutno dostupne tačke i označava tačke u oblastima niske gustine kao šum. Zato ga u radu treba opisati kao eksperimentalni clustering model, a ne kao glavni kandidat za buduću real-time verziju sistema.

## Kratko tumačenje rezultata

Accuracy nije dovoljna metrika za ovaj problem, jer su anomalije retke. Model može imati visoku accuracy vrednost i kada ne pronalazi dovoljno anomalija. Zbog toga su za tumačenje važni precision, recall, F1-score, PR-AUC i konfuziona matrica.

Kod unsupervised modela, K-Means Distance je dao dobar balans između precision i recall vrednosti. Isolation Forest je takođe važan praktičan kandidat, jer je namenjen detekciji anomalija i ne koristi labele tokom treniranja.

HBOS i One-Class SVM su pokazali visoku osetljivost, odnosno visok recall. To znači da pronalaze veliki broj anomalija, ali uz više lažnih alarma. Takvi modeli mogu biti korisni u situacijama kada je važnije ne propustiti potencijalno opasno merenje nego smanjiti broj upozorenja.

Supervised modeli imaju najbolje rezultate na mock datasetu. To treba opisati kao kontrolisani eksperiment nad označenim podacima, a ne kao dokaz da bi isti rezultat bio dobijen nad realnim neoznačenim merenjima.

## Zaključak

Rezultati pokazuju da sistem podržava oba scenarija: evaluaciju kada labele postoje i detekciju anomalija kada labele ne postoje. Označeni mock dataset je iskorišćen za kvantitativno poređenje modela, dok je unsupervised pristup važan za realne podatke.

Za budući rad u realnom vremenu najpraktičniji su modeli koji mogu da se treniraju nad istorijskim podacima i zatim primenjuju na nova merenja. DBSCAN ostaje koristan za poređenje i analizu strukture podataka, ali nije najpogodniji kao glavni real-time model.
