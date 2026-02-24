import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import psycopg2
from psycopg2 import extras

# --- CONFIGURATION POSTGRESQL ---
# Modifie ces valeurs selon tes accès locaux
DB_CONFIG = {
    "host": "localhost",
    "database": "Porc_BD",
    "user": "postgres",
    "password": "azerty",
    "port": "5432"
}

st.set_page_config(page_title="Gestion Porcherie Pro", layout="wide")

# --- FONCTIONS DE CONNEXION ---
def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    # Table des porcs
    cur.execute('''CREATE TABLE IF NOT EXISTS porcs 
                 (id SERIAL PRIMARY KEY, nom TEXT NOT NULL, date_naiss DATE NOT NULL)''')
    # Table de suivi avec contrainte de clé étrangère
    cur.execute('''CREATE TABLE IF NOT EXISTS suivi 
                 (id SERIAL PRIMARY KEY, porc_id INTEGER REFERENCES porcs(id) ON DELETE CASCADE, 
                  action TEXT, date_prevue DATE, etat TEXT)''')
    conn.commit()
    cur.close()
    conn.close()

init_db()

# --- LOGIQUE MÉTIER ---
def enregistrer_porc(nom, date_n):
    conn = get_connection()
    cur = conn.cursor()
    try:
        # 1. Insérer le porc et récupérer son ID
        cur.execute("INSERT INTO porcs (nom, date_naiss) VALUES (%s, %s) RETURNING id", (nom, date_n))
        porc_id = cur.fetchone()[0]
        
        # 2. Définir le protocole
        protocole = [
            ("Injection de Fer", 3, "Non fait"),
            ("Injection vitamine (VITAM STRESS)", 6, "Non fait"),
            ("Gestion Production/Castration", 15, "En attente"),
            ("Rappel Fer & Surveillance Anémie", 21, "En attente"),
            ("Sevrage & Vermifuge Truie", 35, "En attente")
        ]
        
        # 3. Insertion groupée des tâches
        for action, delai, etat_init in protocole:
            date_p = date_n + timedelta(days=delai)
            cur.execute("INSERT INTO suivi (porc_id, action, date_prevue, etat) VALUES (%s, %s, %s, %s)",
                      (porc_id, action, date_p, etat_init))
        
        conn.commit()
    except Exception as e:
        st.error(f"Erreur : {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

# --- INTERFACE ---
st.title("🐖 Gestion Porcherie - PostgreSQL")

with st.sidebar:
    st.header("➕ Nouveau Porc")
    nom = st.text_input("Nom/Numéro")
    d_naiss = st.date_input("Date de naissance")
    if st.button("Enregistrer"):
        if nom:
            enregistrer_porc(nom, d_naiss)
            st.success(f"{nom} enregistré avec succès !")
        else:
            st.warning("Veuillez saisir un nom.")

# --- AFFICHAGE ET MISE À JOUR ---
conn = get_connection()
df_porcs = pd.read_sql_query("SELECT * FROM porcs ORDER BY id DESC", conn)

if not df_porcs.empty:
    choix_porc = st.selectbox("Choisir un animal :", df_porcs['nom'].tolist())
    porc_id = df_porcs[df_porcs['nom'] == choix_porc]['id'].values[0]
    
    # Récupérer les données de suivi
    query = f"SELECT id, action, date_prevue, etat FROM suivi WHERE porc_id = {porc_id} ORDER BY date_prevue ASC"
    df_suivi = pd.read_sql_query(query, conn)
    
    st.write(f"### Planning de soins")
    
    # Éditeur interactif
    edited_df = st.data_editor(
        df_suivi,
        column_config={
            "id": None,
            "etat": st.column_config.SelectboxColumn("Action réalisée", options=[
                "Non fait", "Fait", "En attente", 
                "Choix futur producteur", "Castration du reste", "Choix + Castration terminés",
                "Rappel injection fer fait", "Surveillance anémie faite", "Rappel + Surveillance terminés",
                "Sevrage fait", "Injection vermifuge faite", "Sevrage + Vermifuge terminés"
            ]),
            "action": st.column_config.TextColumn("Etape", disabled=True),
            "date_prevue": st.column_config.DateColumn("Date Prévue", disabled=True)
        },
        hide_index=True, use_container_width=True
    )

    if st.button("Sauvegarder les modifications"):
        cur = conn.cursor()
        for _, row in edited_df.iterrows():
            cur.execute("UPDATE suivi SET etat = %s WHERE id = %s", (row['etat'], row['id']))
        conn.commit()
        cur.close()
        st.success("Base de données PostgreSQL mise à jour !")
else:
    st.info("Aucun animal dans la base de données.")

conn.close()
