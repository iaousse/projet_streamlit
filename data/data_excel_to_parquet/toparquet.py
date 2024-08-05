import pandas as pd
import sys

def excel_to_parquet(excel_file, parquet_file):
    # Lire le fichier Excel
    df = pd.read_excel(excel_file)
    
    # Convertir la colonne 'supervisor' en chaîne de caractères
    if 'supervisor' in df.columns:
        df['supervisor'] = df['supervisor'].astype(str)
    
    # Convertir toutes les colonnes de type 'object' en 'string'
    for col in df.select_dtypes(include=['object']):
        df[col] = df[col].astype(str)
    
    # Sauvegarder en format Parquet
    df.to_parquet(parquet_file)
    print(f"Fichier converti avec succès : {parquet_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python toparquet.py fichier_excel.xlsx fichier_sortie.parquet")
    else:
        excel_to_parquet(sys.argv[1], sys.argv[2])