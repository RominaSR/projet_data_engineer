import sqlite3
import pandas as pd
import json

def create_database():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS magasins (
        id_magasin INTEGER PRIMARY KEY,
        ville TEXT NOT NULL,
        nombre_salaries INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS produits (
        id_reference_produit TEXT PRIMARY KEY,
        nom TEXT NOT NULL,
        prix REAL NOT NULL,
        stock INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        id_reference_produit TEXT NOT NULL,
        quantite INTEGER NOT NULL,
        id_magasin INTEGER NOT NULL,
        FOREIGN KEY (id_reference_produit) REFERENCES produits(id_reference_produit),
        FOREIGN KEY (id_magasin) REFERENCES magasins(id_magasin)
    );

    CREATE TABLE IF NOT EXISTS resultats_ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_analyse TEXT NOT NULL,
        resultat TEXT NOT NULL
    );
    """)
    conn.commit()
    conn.close()

def import_data():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Supprimer toutes les données existantes pour éviter les doublons
    cursor.execute("DELETE FROM ventes")
    cursor.execute("DELETE FROM produits")
    cursor.execute("DELETE FROM magasins")

    df_magasins = pd.read_csv("data/magasins.csv")
    df_produits = pd.read_csv("data/produits.csv")
    df_ventes = pd.read_csv("data/ventes.csv")

    # Supprimer les doublons avant l'insertion
    df_ventes.drop_duplicates(subset=["Date", "ID Référence produit", "ID Magasin"], keep="first", inplace=True)

    for _, row in df_magasins.iterrows():
        cursor.execute("INSERT OR IGNORE INTO magasins (id_magasin, ville, nombre_salaries) VALUES (?, ?, ?)", 
                       (row["ID Magasin"], row["Ville"], row["Nombre de salariés"]))

    for _, row in df_produits.iterrows():
        cursor.execute("INSERT OR IGNORE INTO produits (id_reference_produit, nom, prix, stock) VALUES (?, ?, ?, ?)", 
                       (row["ID Référence produit"], row["Nom"], row["Prix"], row["Stock"]))

    for _, row in df_ventes.iterrows():
        cursor.execute("INSERT OR IGNORE INTO ventes (date, id_reference_produit, quantite, id_magasin) VALUES (?, ?, ?, ?)", 
                       (row["Date"], row["ID Référence produit"], row["Quantité"], row["ID Magasin"]))

    conn.commit()
    conn.close()


def analyze_sales():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(p.prix * v.quantite) FROM ventes v JOIN produits p ON v.id_reference_produit = p.id_reference_produit")
    total_sales = cursor.fetchone()[0]

    print(f"Chiffre d'affaires total: {total_sales} €")
    
    conn.close()

def store_analysis_results():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Supprimer les anciens résultats pour éviter les doublons
    cursor.execute("DELETE FROM resultats_ventes")
    
    # Chiffre d'affaires total
    cursor.execute("""
    SELECT SUM(p.prix * v.quantite) 
    FROM ventes v
    JOIN produits p ON v.id_reference_produit = p.id_reference_produit;
    """)
    total_sales = cursor.fetchone()[0]
    cursor.execute("INSERT INTO resultats_ventes (type_analyse, resultat) VALUES (?, ?)", ("Chiffre d'affaires total", total_sales))

    # Ventes par produit
    cursor.execute("""
    SELECT p.nom, SUM(v.quantite)
    FROM ventes v
    JOIN produits p ON v.id_reference_produit = p.id_reference_produit
    GROUP BY p.nom;
    """)
    product_sales = cursor.fetchall()
    product_sales_json = json.dumps([{"produit": row[0], "total_vendu": row[1]} for row in product_sales])
    cursor.execute("INSERT INTO resultats_ventes (type_analyse, resultat) VALUES (?, ?)", ("Ventes par produit", product_sales_json))

    # Ventes par région
    cursor.execute("""
    SELECT m.ville, SUM(p.prix * v.quantite)
    FROM ventes v
    JOIN magasins m ON v.id_magasin = m.id_magasin
    JOIN produits p ON v.id_reference_produit = p.id_reference_produit
    GROUP BY m.ville;
    """)
    region_sales = cursor.fetchall()
    region_sales_json = json.dumps([{"ville": row[0], "chiffre_affaires": row[1]} for row in region_sales])
    cursor.execute("INSERT INTO resultats_ventes (type_analyse, resultat) VALUES (?, ?)", ("Ventes par région", region_sales_json))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_database()
    import_data()
    analyze_sales()
    store_analysis_results()