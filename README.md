# radiation-time-series-anomaly-detection
An interactive radiation monitoring system for anomaly detection in time-series data, combining machine learning models with a modern dashboard interface. Developed as part of a Bachelor’s thesis.


# Radiation Monitoring Anomaly Detection System

Prototip web aplikacije za vizuelizaciju merenja zračenja, detekciju anomalija u vremenskim serijama i simulaciju sistema za rano upozorenje primenom metoda mašinskog učenja.

---

## 1. Opis projekta

Ovaj projekat predstavlja istraživačko-praktični prototip sistema za praćenje nivoa zračenja kroz vreme, sa fokusom na:


- analizu vremenskih serija,
- detekciju anomalija,
- prikaz upozorenja,
- pregled detektovanih anomalija,
- prikaz performansi modela za detekciju,
- rad sa dataset-om kroz moderan dashboard interfejs.

Aplikacija je zamišljena kao **prototip sistema za rano upozorenje**, a ne kao produkciona enterprise aplikacija.  
Cilj je da se spoje:

1. **istraživački deo** — analiza i detekcija anomalija nad podacima,
2. **praktični deo** — razvoj moderne web aplikacije koja prikazuje rezultate i simulira realni monitoring sistem.

---

## 2. Glavni cilj projekta

Razvoj kompletne aplikacije za praćenje merenja zračenja i rano otkrivanje anomalija u vremenskim serijama, sa dashboard interfejsom i podrškom za model-based anomaly detection.

---

## 3. Specifični ciljevi

- prikaz vremenske serije nivoa zračenja kroz interaktivni graf
- prikaz threshold linije i anomalnih tačaka
- prikaz aktivnog upozorenja kada se detektuje anomalija
- pregled liste anomalija
- pregled detalja anomalija
- prikaz summary metrika sistema
- prikaz aktivnog modela i osnovnih metrika uspešnosti
- stranica/modul za pregled svih anomalija
- stranica/modul za testiranje modela
- stranica/modul za rad sa dataset-ovima
- stranica/modul za podešavanja sistema
- lokalna Python logika za anomaly detection
- FastAPI backend za isporuku podataka frontendu
- povezivanje Vue frontend-a sa backend-om

---

## 4. Tehnologije

### Frontend
- Vue 3
- TypeScript
- Vite
- Vue Router
- Chart.js
- Custom CSS (dark futuristic design)

### Backend
- Python
- FastAPI

### ML / Data
- pandas
- numpy
- scikit-learn

---

## 5. Arhitektura sistema

Sistem se sastoji iz 3 dela:

### 5.1 Frontend (Vue)
Zadužen za:
- UI/UX
- dashboard
- grafove
- prikaz anomalija
- navigaciju

---

### 5.2 ML logika (Python)
Zadužena za:
- obradu podataka
- detekciju anomalija
- generisanje rezultata

---

### 5.3 Backend (FastAPI)
Zadužen za:
- slanje podataka frontendu
- API endpoint-e

---

## 6. FINALNI SCOPE (ZAKLJUČAN)

⚠️ NE DODAVATI NOVE IDEJE

---

### 6.1 Dashboard (glavni ekran)

Sadrži:

- line chart (radiation over time)
- threshold liniju
- anomaly markers
- alert banner (ANOMALY DETECTED)
- anomalies log panel (desno)
- model testing panel (desno dole)
- summary cards
- anomaly details tabela

👉 Ovo je najvažniji deo aplikacije

---

### 6.2 Anomalies Log

Sadrži:

- listu anomalija
- timestamp
- radiation level
- status
- anomaly score (opciono)
- filter po datumu
- search
- mini chart

---

### 6.3 Model Testing

Sadrži:

- current model (Isolation Forest)
- accuracy (npr. 93.4%)
- progress bar
- comparison chart (Isolation Forest vs LOF)
- metrics:
  - Precision
  - FPR
  - FNR

---

### 6.4 Dataset

Sadrži:

- dataset info
- dataset lista
- preview
- load dataset UI

---

### 6.5 Settings

Sadrži:

- threshold slider
- model selection
- model config
- notification settings (UI)

---

## 7. FUNKCIONALNI PRIORITETI

###  OBAVEZNO (mora raditi)

- dashboard chart (REAL DATA)
- anomaly detection prikaz
- anomaly lista
- summary kartice
- model info
- backend API
- Vue ↔ FastAPI povezivanje

---

###  OPCIONO

- više modela
- anomaly score
- filteri

---

###  UI ONLY (ako nema vremena)

- notifications
- dataset akcije
- napredni filteri

---

## 8. ANTI-CHAOS PRAVILA

Ovo je NAJBITNIJI deo projekta:

❌ nema login sistema  
❌ nema baze  
❌ nema real-time streaming  
❌ nema dodatnih stranica  
❌ nema novih ideja van prototipa  

✔ fokus samo na ono što već postoji  

---

## 9. RAZVOJ PO FAZAMA

---

### FAZA 1 — SETUP

- kreiranje repoa
- Vue projekat
- folder struktura
- mock data

---

### FAZA 2 — DESIGN SYSTEM

Definisati:

- boje
- kartice
- dugmad
- tabela stil
- spacing

👉 Da sve izgleda konzistentno

---

### FAZA 3 — LAYOUT

Napraviti:

- sidebar
- topbar
- grid

---

### FAZA 4 — DASHBOARD (MOCK DATA)

Napraviti:

- chart
- alert
- cards
- anomalies panel
- model panel

 60% aplikacije

---

### FAZA 5 — OSTALE STRANICE

- anomalies
- dataset
- settings
- model testing

---

### FAZA 6 — REAL DATA

- učitati CSV
- mapirati podatke
- prikazati na grafu
- izračunati summary

---

### FAZA 7 — PYTHON ML

- threshold
- Isolation Forest
- anomaly output

---

### FAZA 8 — BACKEND

Endpointi:

- /measurements
- /anomalies
- /summary
- /model-info

---

### FAZA 9 — INTEGRACIJA

- API pozivi
- loading state
- error handling

---

### FAZA 10 — FINAL

- polish UI
- testiranje
- prezentacija

---

## 10. REDOSLED IMPLEMENTACIJE

1. Dashboard  
2. Ostali UI  
3. Real data  
4. ML  
5. Backend  
6. Integracija  

---

## 11. STRUKTURA PROJEKTA
radiation-monitoring/
│
├── frontend/
├── backend/
├── ml/
└── README.md


## 12. Predlog strukture projekta

radiation-monitoring-system/
│
├── frontend/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── views/
│   │   ├── router/
│   │   ├── services/
│   │   ├── stores/
│   │   ├── types/
│   │   ├── mock/
│   │   ├── utils/
│   │   ├── App.vue
│   │   └── main.ts
│   ├── package.json
│   └── vite.config.ts
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   ├── services/
│   │   ├── schemas/
│   │   ├── utils/
│   │   └── data/
│   ├── requirements.txt
│   └── run.py
│
├── ml/
│   ├── datasets/
│   ├── notebooks/
│   ├── scripts/
│   └── outputs/
│
└── README.md

## 13. Ključna filozofija projekta

"Aplikacija je prototip sistema, ne produkcioni proizvod."

---

## Autor
Ksenija Raković



