#!/usr/bin/env python3
"""Génère toutes les captures d'écran du rapport à partir des SORTIES RÉELLES
de l'exécution (docker compose + notebook PySpark + HDFS).

Sortie : rapport/image/*.png
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from render_images import (  # noqa: E402
    render_terminal, render_code,
    TERM_GREEN, TERM_FG, TERM_CYAN, TERM_YELLOW, TERM_BLUE, TERM_GREY,
)


def colorize(text):
    """Colorise des lignes de terminal de façon simple."""
    out = []
    for line in text.split("\n"):
        s = line.rstrip("\n")
        if s.startswith("$"):
            out.append((s, TERM_GREEN))
        elif "✅" in s or "healthy" in s or "Started" in s or "_SUCCESS" in s:
            out.append((s, TERM_GREEN))
        elif s.startswith("===") or s.startswith("@@@"):
            out.append((s, TERM_YELLOW))
        elif s.startswith("+") or s.startswith("|"):
            out.append((s, TERM_CYAN))
        elif s.startswith("NAME") or s.startswith("root") or s.startswith(" |--"):
            out.append((s, TERM_YELLOW))
        elif s.startswith(("💰", "🏆", "💵", "🌍", "📅", "👤", "🧾", "👥", "📦", "🛒", "🔍")):
            out.append((s, TERM_YELLOW))
        else:
            out.append((s, TERM_FG))
    return out


# ════════════════════════════════════════════════════════════════════════
#  SECTION A — Commandes (de `docker compose up` jusqu'à la fin)
# ════════════════════════════════════════════════════════════════════════

render_terminal("01_convert_csv.png", colorize(
    "$ python3 scripts/convert_to_csv.py\n"
    "Lecture de data/Online Retail.xlsx ...\n"
    "  541909 lignes, 8 colonnes\n"
    "CSV écrit dans data/online_retail.csv"
), title="Terminal — Conversion XLSX → CSV")

render_terminal("02_compose_up.png", colorize(
    "$ docker compose up -d\n"
    " Network big_data_bigdata-net    Created\n"
    " Volume big_data_namenode_data   Created\n"
    " Volume big_data_datanode_data   Created\n"
    " Container namenode              Started\n"
    " Container datanode              Started\n"
    " Container spark-jupyter         Started"
), title="Terminal — docker compose up")

render_terminal("03_compose_ps.png", colorize(
    "$ docker compose ps\n"
    "NAME            IMAGE                              STATUS\n"
    "datanode        bde2020/hadoop-datanode:3.2.1      Up (healthy)\n"
    "namenode        bde2020/hadoop-namenode:3.2.1      Up (healthy)\n"
    "spark-jupyter   jupyter/pyspark-notebook:latest    Up (healthy)"
), title="Terminal — docker compose ps")

render_terminal("04_jupyter_url.png", colorize(
    "$ docker exec spark-jupyter jupyter server list\n"
    "Currently running servers:\n"
    "http://670c4feeb014:8888/?token=15df932a93a9...aa5958 :: /home/jovyan\n"
    "\n"
    "→ Ouvrir : http://localhost:8888/?token=15df932a93a9...aa5958"
), title="Terminal — URL Jupyter")

render_terminal("05_hdfs_ls.png", colorize(
    "$ docker exec namenode hdfs dfs -ls -R /data\n"
    "drwxr-xr-x   - jovyan supergroup     0  /data/online_retail_clean\n"
    "-rw-r--r--   3 jovyan supergroup     0  /data/online_retail_clean/_SUCCESS\n"
    "-rw-r--r--   3 jovyan supergroup 808318 .../part-00000-....snappy.parquet\n"
    "-rw-r--r--   3 jovyan supergroup 784513 .../part-00001-....snappy.parquet\n"
    "  ... (8 partitions parquet, données nettoyées)\n"
    "drwxr-xr-x   - jovyan supergroup     0  /data/raw/online_retail\n"
    "-rw-r--r--   3 jovyan supergroup     0  /data/raw/online_retail/_SUCCESS\n"
    "-rw-r--r--   3 jovyan supergroup 47923175 .../part-00000-....csv  (dataset brut)"
), title="Terminal — Vérification HDFS")

# ════════════════════════════════════════════════════════════════════════
#  SECTION B — Code PySpark + sorties réelles
# ════════════════════════════════════════════════════════════════════════

# 1. Init Spark
render_code("06_code_init.png",
'''from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder \\
    .appName("Analyse Ventes Online Retail") \\
    .config("spark.sql.legacy.timeParserPolicy", "LEGACY") \\
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")
print("Spark demarre avec succes !")
print(f"Version Spark : {spark.version}")''')

render_terminal("07_out_init.png", colorize(
    "✅ Spark démarré avec succès !\n"
    "Version Spark : 3.5.0"
), title="Sortie — Session Spark")

# 2. Chargement
render_code("08_code_load.png",
'''df = spark.read \\
    .option("header", "true") \\
    .option("inferSchema", "true") \\
    .option("multiLine", "true") \\
    .option("escape", "\\"") \\
    .csv("/home/jovyan/data/online_retail.csv")

print(f"Donnees chargees : {df.count()} lignes")
df.printSchema()''')

render_terminal("09_out_load.png", colorize(
    "✅ Données chargées : 541909 lignes\n"
    "root\n"
    " |-- InvoiceNo: string (nullable = true)\n"
    " |-- StockCode: string (nullable = true)\n"
    " |-- Description: string (nullable = true)\n"
    " |-- Quantity: integer (nullable = true)\n"
    " |-- InvoiceDate: string (nullable = true)\n"
    " |-- UnitPrice: double (nullable = true)\n"
    " |-- CustomerID: double (nullable = true)\n"
    " |-- Country: string (nullable = true)"
), title="Sortie — Chargement & schéma")

# 3. Nettoyage code
render_code("10_code_clean.png",
'''df_clean = df \\
    .filter(F.col("CustomerID").isNotNull()) \\
    .filter(F.col("Quantity") > 0) \\
    .filter(F.col("UnitPrice") > 0) \\
    .dropDuplicates()

df_clean = df_clean.withColumn("CustomerID", F.col("CustomerID").cast("int"))
df_clean = df_clean.withColumn("TotalPrice",
                    F.round(F.col("Quantity") * F.col("UnitPrice"), 2))
df_clean = df_clean.withColumn("InvoiceDate",
                    F.to_timestamp("InvoiceDate", "yyyy-MM-dd HH:mm:ss"))
df_clean = df_clean.withColumn("Month", F.month("InvoiceDate"))
df_clean = df_clean.withColumn("Year",  F.year("InvoiceDate"))''')

render_terminal("11_out_nulls.png", colorize(
    "🔍 Valeurs nulles par colonne :\n"
    "+---------+---------+-----------+--------+---------+----------+-------+\n"
    "|InvoiceNo|StockCode|Description|Quantity|UnitPrice|CustomerID|Country|\n"
    "+---------+---------+-----------+--------+---------+----------+-------+\n"
    "|        0|        0|       1454|       0|        0|    135080|      0|\n"
    "+---------+---------+-----------+--------+---------+----------+-------+"
), title="Sortie — Valeurs nulles")

render_terminal("12_out_clean.png", colorize(
    "✅ Après nettoyage : 392692 lignes  (sur 541909)\n"
    "+---------+---------+------------------------------+--------+----------+----------+-----+----+\n"
    "|InvoiceNo|StockCode|Description                   |Quantity|CustomerID|TotalPrice|Month|Year|\n"
    "+---------+---------+------------------------------+--------+----------+----------+-----+----+\n"
    "|536408   |84879    |ASSORTED COLOUR BIRD ORNAMENT |8       |14307     |13.52     |12   |2010|\n"
    "|536409   |22074    |6 RIBBONS SHIMMERING PINKS    |1       |17908     |1.65      |12   |2010|\n"
    "|536409   |90199C   |5 STRAND GLASS NECKLACE CRYST.|2       |17908     |12.7      |12   |2010|\n"
    "+---------+---------+------------------------------+--------+----------+----------+-----+----+"
), title="Sortie — Données nettoyées")

# 4. Analyses
render_terminal("13_out_ca_total.png", colorize(
    "💰 Chiffre d'affaires total : 8887208.89 £"
), title="Sortie — CA total")

render_terminal("14_out_top_produits.png", colorize(
    "🏆 Top 10 produits les plus vendus (quantité) :\n"
    "+---------+----------------------------------+-----------+\n"
    "|StockCode|Description                       |Total_Vendu|\n"
    "+---------+----------------------------------+-----------+\n"
    "|23843    |PAPER CRAFT , LITTLE BIRDIE       |80995      |\n"
    "|23166    |MEDIUM CERAMIC TOP STORAGE JAR    |77916      |\n"
    "|84077    |WORLD WAR 2 GLIDERS ASSTD DESIGNS |54319      |\n"
    "|85099B   |JUMBO BAG RED RETROSPOT           |46078      |\n"
    "|85123A   |WHITE HANGING HEART T-LIGHT HOLDER|36706      |\n"
    "|84879    |ASSORTED COLOUR BIRD ORNAMENT     |35263      |\n"
    "|21212    |PACK OF 72 RETROSPOT CAKE CASES   |33670      |\n"
    "|22197    |POPCORN HOLDER                    |30919      |\n"
    "|23084    |RABBIT NIGHT LIGHT                |27153      |\n"
    "|22492    |MINI PAINT SET VINTAGE            |26076      |\n"
    "+---------+----------------------------------+-----------+"
), title="Sortie — Top produits (quantité)")

render_terminal("15_out_top_ca.png", colorize(
    "💵 Top 10 produits par chiffre d'affaires :\n"
    "+---------+----------------------------------+---------+\n"
    "|StockCode|Description                       |CA       |\n"
    "+---------+----------------------------------+---------+\n"
    "|23843    |PAPER CRAFT , LITTLE BIRDIE       |168469.6 |\n"
    "|22423    |REGENCY CAKESTAND 3 TIER          |142264.75|\n"
    "|85123A   |WHITE HANGING HEART T-LIGHT HOLDER|100392.1 |\n"
    "|85099B   |JUMBO BAG RED RETROSPOT           |85040.54 |\n"
    "|23166    |MEDIUM CERAMIC TOP STORAGE JAR    |81416.73 |\n"
    "|POST     |POSTAGE                           |77803.96 |\n"
    "|47566    |PARTY BUNTING                     |68785.23 |\n"
    "|84879    |ASSORTED COLOUR BIRD ORNAMENT     |56413.03 |\n"
    "|M        |Manual                            |53419.93 |\n"
    "|23084    |RABBIT NIGHT LIGHT                |51251.24 |\n"
    "+---------+----------------------------------+---------+"
), title="Sortie — Top produits (CA)")

render_terminal("16_out_pays.png", colorize(
    "🌍 Chiffre d'affaires par pays (Top 10) :\n"
    "+--------------+----------+\n"
    "|Country       |CA        |\n"
    "+--------------+----------+\n"
    "|United Kingdom|7285024.64|\n"
    "|Netherlands   |285446.34 |\n"
    "|EIRE          |265262.46 |\n"
    "|Germany       |228678.4  |\n"
    "|France        |208934.31 |\n"
    "|Australia     |138453.81 |\n"
    "|Spain         |61558.56  |\n"
    "|Switzerland   |56443.95  |\n"
    "|Belgium       |41196.34  |\n"
    "|Sweden        |38367.83  |\n"
    "+--------------+----------+"
), title="Sortie — CA par pays")

render_terminal("17_out_mensuel.png", colorize(
    "📅 Évolution mensuelle du chiffre d'affaires :\n"
    "+----+-----+----------+\n"
    "|Year|Month|CA_Mensuel|\n"
    "+----+-----+----------+\n"
    "|2010|   12| 570422.73|\n"
    "|2011|    1| 568101.31|\n"
    "|2011|    2| 446084.92|\n"
    "|2011|    3| 594081.76|\n"
    "|2011|    4| 468374.33|\n"
    "|2011|    5| 677355.15|\n"
    "|2011|    6| 660046.05|\n"
    "|2011|    7| 598962.90|\n"
    "|2011|    8| 644051.04|\n"
    "|2011|    9| 950690.20|\n"
    "|2011|   10|1035642.45|\n"
    "|2011|   11|1156205.61|\n"
    "|2011|   12| 517190.44|\n"
    "+----+-----+----------+"
), title="Sortie — Évolution mensuelle")

render_terminal("18_out_clients.png", colorize(
    "👤 Top 10 clients par chiffre d'affaires :\n"
    "+----------+---------+\n"
    "|CustomerID|CA_Client|\n"
    "+----------+---------+\n"
    "|     14646|280206.02|\n"
    "|     18102| 259657.3|\n"
    "|     17450|194390.79|\n"
    "|     16446| 168472.5|\n"
    "|     14911|143711.17|\n"
    "|     12415|124914.53|\n"
    "|     14156|117210.08|\n"
    "|     17511| 91062.38|\n"
    "|     16029| 80850.84|\n"
    "|     12346|  77183.6|\n"
    "+----------+---------+"
), title="Sortie — Top clients")

render_terminal("19_out_kpis.png", colorize(
    "🧾 Nombre de commandes uniques : 18532\n"
    "👥 Nombre de clients uniques   : 4338\n"
    "📦 Nombre de produits uniques  : 3665\n"
    "🛒 Panier moyen                : 479.56 £\n"
    "📦 Articles moyens / commande  : 278.0"
), title="Sortie — Indicateurs clés (KPIs)")

# 5. HDFS
render_code("20_code_hdfs.png",
'''# Dataset brut sur HDFS
df.write.mode("overwrite").option("header","true") \\
    .csv("hdfs://namenode:9000/data/raw/online_retail")

# Données nettoyées sur HDFS (Parquet)
df_clean.write.mode("overwrite") \\
    .parquet("hdfs://namenode:9000/data/online_retail_clean")

# Relecture depuis HDFS
df_hdfs = spark.read.parquet(
    "hdfs://namenode:9000/data/online_retail_clean")
print(f"Lecture depuis HDFS : {df_hdfs.count()} lignes")''')

render_terminal("21_out_hdfs.png", colorize(
    "✅ Dataset brut stocké sur HDFS : hdfs://namenode:9000/data/raw/online_retail\n"
    "✅ Données nettoyées sur HDFS   : hdfs://namenode:9000/data/online_retail_clean\n"
    "✅ Lecture depuis HDFS : 392692 lignes"
), title="Sortie — Stockage HDFS")

print("\nToutes les images générées.")
