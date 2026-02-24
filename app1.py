import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(page_title="Gestion Porcherie v1.2", layout="wide")

st.title("🐖 Gestionnaire de Santé Porcine - Précision Technique")

# --- FORMULAIRE DE SAISIE ---
with st.sidebar:
    st.header("Nouvel Enregistrement")
    nom_porc = st.text_input("Nom ou Numéro du porc", placeholder="Ex: P-001")
    date_naiss = st.date_input("Date de Naissance", datetime.now())
    generer = st.button("Générer le calendrier")

# --- INITIALISATION DU STATE ---
if "df_suivi" not in st.session_state:
    st.session_state.df_suivi = None

if generer and nom_porc:
    # On définit les étapes et les options de réponse associées
    # Format : { "Nom de l'action": [Liste des options possibles] }
    config_actions = {
        "Injection de Fer": ["Non fait", "Fait"],
        "Injection vitamine (VITAM STRESS)": ["Non fait", "Fait"],
        "Gestion Production/Castration": [
            "En attente", 
            "Choix futur producteur", 
            "Castration du reste", 
            "Choix + Castration terminés"
        ],
        "Rappel Fer & Surveillance Anémie": [
            "En attente", 
            "Rappel injection fer fait", 
            "Surveillance anémie faite", 
            "Rappel + Surveillance terminés"
        ],
        "Sevrage & Vermifuge": [
            "En attente", 
            "Sevrage fait", 
            "Injection vermifuge faite", 
            "Sevrage + Vermifuge terminés"
        ]
    }
    
    delais = [3, 6, 15, 21, 35]
    taches = []
    
    for (action, options), delai in zip(config_actions.items(), delais):
        date_action = date_naiss + timedelta(days=delai)
        taches.append({
            "Action": action,
            "Date Prévue": date_action.strftime("%d/%m/%Y"),
            "Âge": f"{delai} jours",
            "État / Résultat": options[0], # Option par défaut (la première de la liste)
            "Options": options # On stocke les options pour le menu déroulant
        })
    
    st.session_state.df_suivi = pd.DataFrame(taches)
    st.session_state.nom_actuel = nom_porc

# --- AFFICHAGE ET ÉDITION ---
if st.session_state.df_suivi is not None:
    st.write(f"### Suivi détaillé pour : **{st.session_state.nom_actuel}**")
    
    # Utilisation de data_editor avec configuration de colonne 'Selectbox'
    # La colonne "État / Résultat" devient un menu déroulant dynamique
    edited_df = st.data_editor(
        st.session_state.df_suivi,
        column_config={
            "État / Résultat": st.column_config.SelectboxColumn(
                "Action réalisée",
                help="Sélectionnez l'état d'avancement spécifique",
                width="large",
                options=[
                    "Non fait", "Fait", 
                    "En attente", 
                    "Choix futur producteur", "Castration du reste", "Choix + Castration terminés",
                    "Rappel injection fer fait", "Surveillance anémie faite", "Rappel + Surveillance terminés",
                    "Sevrage fait", "Injection vermifuge faite", "Sevrage + Vermifuge terminés"
                ],
                required=True,
            ),
            "Options": None, # On cache la colonne technique des options
            "Action": st.column_config.TextColumn(disabled=True),
            "Date Prévue": st.column_config.TextColumn(disabled=True),
            "Âge": st.column_config.TextColumn(disabled=True),
        },
        hide_index=True,
        use_container_width=True
    )

    st.session_state.df_suivi = edited_df
    
    st.success("ℹ️ Modifiez l'état directement dans la colonne 'Action réalisée' pour mettre à jour le registre.")

else:
    st.info("Saisissez les informations à gauche pour générer le tableau de bord.")