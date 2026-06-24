# Projet Big Data – Analyse de Données de Vente (Online Retail)

Analyse des ventes d'un site e-commerce avec **Apache Spark (PySpark)** et stockage du
dataset sur un cluster **Hadoop HDFS**, le tout orchestré avec **Docker Compose**.

Dataset : [Online Retail – UCI](https://archive.ics.uci.edu/dataset/352/online+retail)
(~541 909 transactions).

## Membres du groupe
- Alaa Belhadj
- Zackaria Ajli
- Oussema Jebaari
- Aziz Ben Guirat
- Mohamed Hamdaoui

## Architecture
| Service   | Image                          | Rôle                         | URL |
|-----------|--------------------------------|------------------------------|-----|
| namenode  | bde2020/hadoop-namenode        | Maître HDFS                  | http://localhost:9870 |
| datanode  | bde2020/hadoop-datanode        | Stockage HDFS                | http://localhost:9864 |
| spark     | jupyter/pyspark-notebook       | Spark + Jupyter (PySpark)    | http://localhost:8888 |

## Prérequis
- Docker Desktop
- Python 3 avec `pandas` et `openpyxl` (uniquement pour générer le CSV)

## Démarrage

### 1. Générer le CSV à partir du `.xlsx`
```bash
python3 scripts/convert_to_csv.py
```
Produit `data/online_retail.csv` (monté ensuite dans le conteneur Spark).

### 2. Lancer la stack
```bash
docker compose up -d
docker compose ps
```

### 3. Ouvrir Jupyter
Récupérer l'URL avec le token :
```bash
docker exec spark-jupyter jupyter server list
```
Puis ouvrir http://localhost:8888 (le notebook est dans `work/analyse_ventes.ipynb`).

### 4. Exécuter le notebook
`notebooks/analyse_ventes.ipynb` réalise :
1. Initialisation de la session Spark
2. Chargement du CSV
3. Nettoyage / transformation (nulls, retours, doublons, `TotalPrice`, dates)
4. Analyses : top produits, CA par pays, évolution mensuelle, top clients
5. Indicateurs (KPIs) : CA total, commandes/clients/produits uniques, panier moyen
6. Stockage sur HDFS (dataset brut + données nettoyées en Parquet)

### 5. Vérifier le stockage HDFS
```bash
docker exec namenode hdfs dfs -ls -R /data
```
Interface web HDFS : http://localhost:9870 (onglet *Utilities → Browse the file system*).

### 6. Arrêter la stack
```bash
docker compose down          # garde les volumes (données HDFS conservées)
docker compose down -v       # supprime aussi les volumes
```

## Structure du projet
```
.
├── docker-compose.yml         # NameNode + DataNode + Spark/Jupyter
├── hadoop.env                 # Configuration HDFS
├── data/
│   ├── Online Retail.xlsx     # Dataset source
│   └── online_retail.csv      # Dataset converti (généré)
├── notebooks/
│   └── analyse_ventes.ipynb   # Application PySpark
├── scripts/
│   ├── convert_to_csv.py      # Conversion xlsx -> csv
│   └── get-jupyter-url.ps1    # URL Jupyter (Windows)
└── rapport/
    ├── rapport.tex            # Rapport LaTeX (Overleaf)
    └── image/                 # Captures d'écran
```
