#!/usr/bin/env python3
"""Convertit le dataset Online Retail (.xlsx) en CSV utilisable par Spark.

Usage :
    python3 scripts/convert_to_csv.py

Lit  : data/Online Retail.xlsx
Écrit: data/online_retail.csv
"""
import os
import pandas as pd

SRC = os.path.join("data", "Online Retail.xlsx")
DST = os.path.join("data", "online_retail.csv")


def main() -> None:
    print(f"Lecture de {SRC} ...")
    df = pd.read_excel(SRC, engine="openpyxl")
    print(f"  {df.shape[0]} lignes, {df.shape[1]} colonnes")
    df.to_csv(DST, index=False)
    print(f"CSV écrit dans {DST}")


if __name__ == "__main__":
    main()
