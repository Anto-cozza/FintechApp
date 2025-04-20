import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
import os
import tempfile
import random
import io
import base64
from PIL import Image
import numpy as np

# Configurazione iniziale dell'app
st.set_page_config(
    page_title="ContractME",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Funzioni di utilità
def load_css():
    st.markdown("""
    <style>
        /* Stile generale */
        .main {
            background-color: #f8f9fa;
            padding: 20px;
        }
        
        /* Titoli */
        h1, h2, h3 {
            color: #2c3e50;
            font-family: 'Helvetica Neue', sans-serif;
        }
        
        /* Cards */
        .card {
            border-radius: 10px;
            background-color: white;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin-bottom: 20px;
        }
        
        /* Metriche */
        .metric {
            background-color: #f1f8ff;
            border-left: 5px solid #4e73df;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 15px;
        }
        
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }
        
        .metric-label {
            font-size: 14px;
            color: #7b8a8b;
        }
        
        /* Calendario */
        .calendar {
            width: 100%;
            border-collapse: collapse;
        }
        
        .calendar th {
            background-color: #4e73df;
            color: white;
            text-align: center;
            padding: 10px;
        }
        
        .calendar td {
            border: 1px solid #e3e6f0;
            height: 80px;
            vertical-align: top;
            padding: 5px;
        }
        
        .calendar-day {
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .calendar-event {
            background-color: #1cc88a;
            color: white;
            border-radius: 3px;
            padding: 2px 5px;
            margin-bottom: 2px;
            font-size: 12px;
        }
        
        .calendar-event.urgent {
            background-color: #e74a3b;
        }
        
        /* Logo e sidebar */
        .sidebar-logo {
            text-align: center;
            margin-bottom: 20px;
        }
        
        /* Bottoni e input */
        .stButton button {
            background-color: #4e73df;
            color: white;
            border-radius: 5px;
        }
        
        /* Tabelle */
        .dataframe {
            width: 100%;
            margin-bottom: 15px;
        }
        
        /* Chat */
        .chat-message {
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 10px;
        }
        
        .chat-user {
            background-color: #f1f8ff;
            text-align: right;
        }
        
        .chat-assistant {
            background-color: #e8f4f8;
        }
        
        /* Loader */
        .loader {
            border: 16px solid #f3f3f3;
            border-top: 16px solid #3498db;
            border-radius: 50%;
            width: 120px;
            height: 120px;
            animation: spin 2s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
    """, unsafe_allow_html=True)

# Inizializzazione dello stato della sessione
def init_session_state():
    if 'documents' not in st.session_state:
        st.session_state.documents = []
    
    if 'deadlines' not in st.session_state:
        st.session_state.deadlines = []
    
    if 'subscriptions' not in st.session_state:
        st.session_state.subscriptions = []
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if 'categories' not in st.session_state:
        st.session_state.categories = ["Casa", "Lavoro", "Salute", "Finanza", "Istruzione", "Altro"]

# Funzione per visualizzare il logo
def display_logo():
    st.markdown("""
    <div class="sidebar-logo">
        <h1 style="color: #4e73df;">📄 ContractME</h1>
        <p>Gestisci i tuoi documenti con semplicità</p>
    </div>
    """, unsafe_allow_html=True)

# Funzione per creare la sidebar
def create_sidebar():
    with st.sidebar:
        display_logo()
        
        st.markdown("---")
        
        menu = ["Dashboard", "Documenti", "Scadenze", "Abbonamenti", "Calendario", "Assistente AI"]
        choice = st.radio("Navigazione", menu)
        
        st.markdown("---")
        
        st.markdown("""
        <div style="text-align: center; margin-top: 20px; font-size: small;">
            © 2025 ContractME<br>
            Versione 1.0
        </div>
        """, unsafe_allow_html=True)
        
        return choice

# 1. Modulo di caricamento documenti
def upload_document():
    st.markdown("<h2>Carica un nuovo documento</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        doc_name = st.text_input("Nome del documento")
        doc_category = st.selectbox("Categoria", st.session_state.categories)
        custom_category = st.text_input("Aggiungi nuova categoria (opzionale)")
        
        if custom_category and custom_category not in st.session_state.categories:
            st.session_state.categories.append(custom_category)
            st.success(f"Categoria '{custom_category}' aggiunta!")
    
    with col2:
        uploaded_file = st.file_uploader("Carica un documento", 
                                       type=["pdf", "jpg", "jpeg", "png", "txt", "md"],
                                       help="Formati supportati: PDF, JPG, PNG, TXT, MD")
        
        has_expiry = st.checkbox("Il documento ha una scadenza")
        
        if has_expiry:
            expiry_date = st.date_input("Data di scadenza", min_value=datetime.now().date())
        else:
            expiry_date = None
    
    if st.button("Carica documento"):
        if doc_name and uploaded_file:
            # Salvataggio temporaneo del file
            file_extension = uploaded_file.name.split(".")[-1].lower()
            
            # Per determinare il tipo di documento
            doc_type = ""
            preview_data = None
            
            if file_extension in ["jpg", "jpeg", "png"]:
                doc_type = "image"
                image = Image.open(uploaded_file)
                img_bytes = io.BytesIO()
                image.save(img_bytes, format="PNG")
                preview_data = base64.b64encode(img_bytes.getvalue()).decode()
            
            elif file_extension == "pdf":
                doc_type = "pdf"
                preview_data = base64.b64encode(uploaded_file.read()).decode()
                
            elif file_extension in ["txt", "md"]:
                doc_type = "text"
                preview_data = uploaded_file.read().decode()
                
            # Creazione dell'oggetto documento
            document = {
                "id": len(st.session_state.documents) + 1,
                "name": doc_name,
                "category": doc_category if not custom_category else custom_category,
                "type": doc_type,
                "preview": preview_data,
                "upload_date": datetime.now().date(),
                "expiry_date": expiry_date,
                "filename": uploaded_file.name
            }
            
            # Aggiunta alla sessione
            st.session_state.documents.append(document)
            
            # Se ha data di scadenza, aggiungiamo anche come deadline
            if expiry_date:
                deadline = {
                    "id": len(st.session_state.deadlines) + 1,
                    "title": f"Scadenza {doc_name}",
                    "date": expiry_date,
                    "description": f"Scadenza per il documento '{doc_name}'",
                    "category": doc_category if not custom_category else custom_category,
                    "document_id": document["id"]
                }
                st.session_state.deadlines.append(deadline)
            
            st.success(f"Documento '{doc_name}' caricato con successo!")
        else:
            st.error("Per favore, inserisci un nome per il documento e carica un file.")

def view_documents():
    st.markdown("<h2>I tuoi documenti</h2>", unsafe_allow_html=True)
    
    if not st.session_state.documents:
        st.info("Non hai ancora caricato documenti. Usa il modulo sopra per caricare il tuo primo documento.")
        return
    
    # Rimuovi eventuali duplicati basati sul nome
    unique_docs = {}
    for doc in st.session_state.documents:
        name = doc.get("name", "Documento senza nome")
        unique_docs[name] = doc
    
    # Usa solo documenti unici
    st.session_state.documents = list(unique_docs.values())
    
    # Filtro per categoria
    all_categories = ["Tutti"] + st.session_state.categories
    filter_category = st.selectbox("Filtra per categoria", all_categories)
    
    filtered_docs = st.session_state.documents
    if filter_category != "Tutti":
        filtered_docs = [doc for doc in st.session_state.documents if doc["category"] == filter_category]
    
    if not filtered_docs:
        st.info(f"Non ci sono documenti nella categoria '{filter_category}'.")
        return
    
    # Visualizzazione documenti
    for i, doc in enumerate(filtered_docs):
        col1, col2 = st.columns([2, 3])
        
        with col1:
            st.markdown(f"""
            <div class="card">
                <h3>{doc['name']}</h3>
                <p><strong>Categoria:</strong> {doc['category']}</p>
                <p><strong>Data caricamento:</strong> {doc['upload_date'].strftime('%d/%m/%Y')}</p>
                <p><strong>Tipo file:</strong> {doc['filename'].split('.')[-1].upper()}</p>
                
                {f"<p><strong>Data scadenza:</strong> {doc['expiry_date'].strftime('%d/%m/%Y')}</p>" if doc['expiry_date'] else ""}
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Elimina documento {doc['name']}", key=f"del_doc_{doc['id']}"):
                # Rimuovi il documento
                st.session_state.documents.remove(doc)
                # Rimuovi eventuali scadenze associate
                st.session_state.deadlines = [d for d in st.session_state.deadlines if d.get('document_id') != doc['id']]
                st.success(f"Documento '{doc['name']}' eliminato con successo!")
                st.rerun()
        
        with col2:
            st.markdown("<div class='card'><h4>Anteprima</h4>", unsafe_allow_html=True)
            
            if doc["type"] == "image":
                st.markdown(f"""
                <img src="data:image/png;base64,{doc['preview']}" 
                     style="max-width: 100%; max-height: 300px; display: block; margin: 0 auto;">
                """, unsafe_allow_html=True)
                
            elif doc["type"] == "pdf":
                st.markdown(f"""
                <p>Anteprima PDF non disponibile direttamente. 
                   <a href="data:application/pdf;base64,{doc['preview']}" download="{doc['name']}.pdf">
                   Scarica il PDF</a></p>
                """, unsafe_allow_html=True)
                
            elif doc["type"] == "text":
                st.markdown(f"""
                <div style="background-color: #f5f5f5; padding: 10px; border-radius: 5px; 
                            max-height: 300px; overflow-y: auto; font-family: monospace;">
                    {doc['preview'].replace('\n', '<br>')}
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<hr>", unsafe_allow_html=True)

# 2. Modulo di gestione scadenze
def add_deadline():
    st.markdown("<h2>Aggiungi una nuova scadenza</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        deadline_title = st.text_input("Titolo della scadenza")
        deadline_category = st.selectbox("Categoria", st.session_state.categories)
        
    with col2:
        deadline_date = st.date_input("Data scadenza", min_value=datetime.now().date())
        
        # Opzione per collegare a un documento esistente
        doc_options = ["Nessun documento collegato"] + [doc["name"] for doc in st.session_state.documents]
        selected_doc = st.selectbox("Documento collegato (opzionale)", doc_options)
        
    deadline_desc = st.text_area("Descrizione", height=100)
    
    if st.button("Aggiungi scadenza"):
        if deadline_title and deadline_date:
            # Trova l'ID del documento selezionato, se presente
            doc_id = None
            if selected_doc != "Nessun documento collegato":
                for doc in st.session_state.documents:
                    if doc["name"] == selected_doc:
                        doc_id = doc["id"]
                        break
            
            deadline = {
                "id": len(st.session_state.deadlines) + 1,
                "title": deadline_title,
                "date": deadline_date,
                "description": deadline_desc,
                "category": deadline_category,
                "document_id": doc_id
            }
            
            st.session_state.deadlines.append(deadline)
            st.success(f"Scadenza '{deadline_title}' aggiunta con successo!")
        else:
            st.error("Titolo e data sono obbligatori!")

def view_deadlines():
    st.markdown("<h2>Le tue scadenze</h2>", unsafe_allow_html=True)
    
    if not st.session_state.deadlines:
        st.info("Non hai ancora aggiunto scadenze.")
        return
    
    # Ordiniamo le scadenze per data
    sorted_deadlines = sorted(st.session_state.deadlines, key=lambda x: x["date"])
    
    # Filtro per periodi
    period_options = ["Tutte", "Prossimi 7 giorni", "Prossimi 30 giorni", "Prossimi 3 mesi", "Scadute"]
    selected_period = st.selectbox("Visualizza scadenze per periodo", period_options)
    
    filtered_deadlines = sorted_deadlines
    today = datetime.now().date()
    
    if selected_period == "Prossimi 7 giorni":
        end_date = today + timedelta(days=7)
        filtered_deadlines = [d for d in sorted_deadlines if today <= d["date"] <= end_date]
    elif selected_period == "Prossimi 30 giorni":
        end_date = today + timedelta(days=30)
        filtered_deadlines = [d for d in sorted_deadlines if today <= d["date"] <= end_date]
    elif selected_period == "Prossimi 3 mesi":
        end_date = today + timedelta(days=90)
        filtered_deadlines = [d for d in sorted_deadlines if today <= d["date"] <= end_date]
    elif selected_period == "Scadute":
        filtered_deadlines = [d for d in sorted_deadlines if d["date"] < today]
    
    if not filtered_deadlines:
        st.info(f"Non ci sono scadenze nel periodo selezionato ({selected_period}).")
        return
    
    # Visualizziamo le scadenze in una tabella
    deadlines_data = []
    
    for d in filtered_deadlines:
        # Calcoliamo se scaduta o imminente
        days_left = (d["date"] - today).days
        status = "⚠️ Scaduta" if days_left < 0 else "🔄 Imminente" if days_left <= 7 else "✅ Futura"
        
        # Troviamo il nome del documento associato, se presente
        doc_name = "Nessuno"
        if d.get("document_id"):
            for doc in st.session_state.documents:
                if doc["id"] == d["document_id"]:
                    doc_name = doc["name"]
                    break
        
        deadlines_data.append({
            "ID": d["id"],
            "Titolo": d["title"],
            "Data": d["date"].strftime("%d/%m/%Y"),
            "Giorni rimanenti": max(days_left, 0) if days_left >= 0 else f"Scaduta da {abs(days_left)} giorni",
            "Categoria": d["category"],
            "Documento": doc_name,
            "Stato": status
        })
    
    df = pd.DataFrame(deadlines_data)
    
    # Visualizzazione come tabella colorata
    st.markdown("""
    <style>
    .deadline-table {
        font-family: Arial, sans-serif;
        border-collapse: collapse;
        width: 100%;
    }
    .deadline-table th {
        background-color: #4e73df;
        color: white;
        padding: 12px;
        text-align: left;
    }
    .deadline-table td {
        padding: 10px;
        border-bottom: 1px solid #ddd;
    }
    .deadline-table tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    .deadline-table tr:hover {
        background-color: #f1f1f1;
    }
    
    .status-expired {
        color: #e74a3b;
        font-weight: bold;
    }
    .status-imminent {
        color: #f6c23e;
        font-weight: bold;
    }
    .status-future {
        color: #1cc88a;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Visualizzazione della tabella
    html_table = "<table class='deadline-table'>"
    
    # Intestazione
    html_table += "<tr>"
    for col in df.columns:
        html_table += f"<th>{col}</th>"
    html_table += "</tr>"
    
    # Righe
    for _, row in df.iterrows():
        html_table += "<tr>"
        for i, value in enumerate(row):
            cell_class = ""
            if df.columns[i] == "Stato":
                if "Scaduta" in value:
                    cell_class = "status-expired"
                elif "Imminente" in value:
                    cell_class = "status-imminent"
                else:
                    cell_class = "status-future"
            
            html_table += f"<td class='{cell_class}'>{value}</td>"
        html_table += "</tr>"
    
    html_table += "</table>"
    
    st.markdown(html_table, unsafe_allow_html=True)
    
    # Grafico delle prossime scadenze
    st.markdown("<h3>Grafico delle prossime scadenze</h3>", unsafe_allow_html=True)
    
    upcoming_deadlines = [d for d in sorted_deadlines if d["date"] >= today][:10]  # Prendiamo le prossime 10
    
    if upcoming_deadlines:
        df_chart = pd.DataFrame([
            {
                "Titolo": d["title"], 
                "Data": d["date"], 
                "Giorni rimanenti": (d["date"] - today).days
            } for d in upcoming_deadlines
        ])
        
        df_chart = df_chart.sort_values("Data")
        
        fig = px.bar(
            df_chart, 
            x="Titolo", 
            y="Giorni rimanenti",
            title="Giorni rimanenti alle prossime scadenze",
            color="Giorni rimanenti",
            color_continuous_scale=["#e74a3b", "#f6c23e", "#1cc88a"],
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Non ci sono scadenze future da visualizzare nel grafico.")

# 3. Modulo Abbonamenti
def add_subscription():
    st.markdown("<h2>Aggiungi un nuovo abbonamento</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        sub_name = st.text_input("Nome abbonamento")
        sub_type = st.selectbox("Tipo", ["Streaming", "Servizi", "Utility", "Palestra", "Software", "Altro"])
        
    with col2:
        sub_renewal_date = st.date_input("Data prossimo rinnovo", min_value=datetime.now().date())
        sub_cost = st.number_input("Costo mensile (€)", min_value=0.0, step=0.01)
        
    sub_desc = st.text_area("Descrizione", placeholder="Inserisci ulteriori dettagli...", height=100)
    
    if st.button("Aggiungi abbonamento"):
        if sub_name and sub_renewal_date:
            subscription = {
                "id": len(st.session_state.subscriptions) + 1,
                "name": sub_name,
                "type": sub_type,
                "renewal_date": sub_renewal_date,
                "cost": float(sub_cost),  # Assicuriamoci che il costo sia un float
                "description": sub_desc
            }
            
            st.session_state.subscriptions.append(subscription)
            
            # Aggiungiamo anche una scadenza per il rinnovo
            deadline = {
                "id": len(st.session_state.deadlines) + 1,
                "title": f"Rinnovo {sub_name}",
                "date": sub_renewal_date,
                "description": f"Rinnovo abbonamento '{sub_name}' - {sub_cost}€",
                "category": "Abbonamenti",
                "subscription_id": subscription["id"]
            }
            st.session_state.deadlines.append(deadline)
            
            st.success(f"Abbonamento '{sub_name}' aggiunto con successo!")
        else:
            st.error("Nome e data di rinnovo sono obbligatori!")

def view_subscriptions():
    st.markdown("<h2>I tuoi abbonamenti</h2>", unsafe_allow_html=True)
    
    if not st.session_state.subscriptions:
        st.info("Non hai ancora aggiunto abbonamenti.")
        return
    
    # Visualizziamo gli abbonamenti in cards
    # Assicuriamoci che ogni abbonamento abbia una chiave 'cost' e che sia un numero
    for sub in st.session_state.subscriptions:
        if "cost" not in sub or not isinstance(sub["cost"], (int, float)):
            sub["cost"] = 0.0
            
    total_monthly_cost = sum(sub["cost"] for sub in st.session_state.subscriptions)
    
    st.markdown(f"""
    <div class="metric">
        <div class="metric-label">Costo mensile totale</div>
        <div class="metric-value">{total_monthly_cost:.2f} €</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Ordinati per data di rinnovo
    # Ordinati per data di rinnovo
    # Verifichiamo che ogni abbonamento abbia una renewal_date valida prima di ordinare
    for sub in st.session_state.subscriptions:
        # Reimposta sempre la data di rinnovo per sicurezza
        try:
            # Proviamo ad accedere alla data, se non esiste o non è valida, impostiamo una predefinita
            renewal_date = sub.get("renewal_date")
            if renewal_date is None or not hasattr(renewal_date, "year"):
                sub["renewal_date"] = datetime.now().date()
        except:
            # In caso di qualsiasi errore, imposta una data di default
            sub["renewal_date"] = datetime.now().date()
    
    # Rimuovi eventuali duplicati basati sul nome
    unique_subs = {}
    for sub in st.session_state.subscriptions:
        name = sub.get("name", "Abbonamento senza nome")
        unique_subs[name] = sub
    
    # Usa solo abbonamenti unici
    st.session_state.subscriptions = list(unique_subs.values())
    
    # Ordinamento sicuro
    try:
        sorted_subs = sorted(st.session_state.subscriptions, key=lambda x: x["renewal_date"])
    except:
        # Se l'ordinamento fallisce, usa la lista non ordinata
        sorted_subs = st.session_state.subscriptions.copy()
    
    # Visualizziamo le card in una griglia
    col1, col2 = st.columns(2)
    
    for i, sub in enumerate(sorted_subs):
        # Alterniamo le colonne
        with col1 if i % 2 == 0 else col2:
            # Controlla in modo sicuro se è possibile calcolare i giorni al rinnovo
            try:
                days_to_renewal = (sub["renewal_date"] - datetime.now().date()).days
            except:
                days_to_renewal = 0
                
            status_color = "#e74a3b" if days_to_renewal <= 3 else "#f6c23e" if days_to_renewal <= 7 else "#1cc88a"
            
            # Assicuriamoci che il nome e altri campi necessari siano presenti
            name = sub.get("name", "Abbonamento senza nome")
            sub_type = sub.get("type", "Non specificato")
            cost_value = sub.get("cost", 0)
            description = sub.get("description", "")
            
            if not isinstance(cost_value, (int, float)):
                cost_value = 0
                
            st.markdown(f"""
            <div class="card" style="border-left: 5px solid {status_color};">
                <h3>{name}</h3>
                <p><strong>Tipo:</strong> {sub_type}</p>
                <p><strong>Costo mensile:</strong> {cost_value:.2f} €</p>
                <p><strong>Prossimo rinnovo:</strong> {sub["renewal_date"].strftime('%d/%m/%Y')}</p>
                <p><strong>Giorni al rinnovo:</strong> <span style="color: {status_color}; font-weight: bold;">{days_to_renewal}</span></p>
                <p><strong>Descrizione:</strong> {description}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Ottieni il nome dell'abbonamento in modo sicuro
            name = sub.get("name", "Abbonamento senza nome")
            sub_id = sub.get("id", 0)
            
            if st.button(f"Elimina {name}", key=f"del_sub_{sub_id}_{name}"):
                # Rimuovi abbonamento
                st.session_state.subscriptions.remove(sub)
                # Rimuovi eventuali scadenze associate
                st.session_state.deadlines = [d for d in st.session_state.deadlines if d.get('subscription_id') != sub['id']]
                st.success(f"Abbonamento '{sub['name']}' eliminato con successo!")
                st.rerun()
    
    # Grafico a torta dei costi degli abbonamenti
    st.markdown("<h3>Distribuzione dei costi degli abbonamenti</h3>", unsafe_allow_html=True)
    if sorted_subs:
        # Assicuriamoci che tutti gli abbonamenti abbiano un costo valido e un nome
        valid_subs = []
        for sub in sorted_subs:
            if "cost" in sub and isinstance(sub["cost"], (int, float)):
                # Assicuriamoci che ci sia un nome valido
                if "name" not in sub or not sub["name"]:
                    sub["name"] = "Abbonamento senza nome"
                valid_subs.append(sub)
        
        if valid_subs:
            fig = px.pie(
                names=[sub["name"] for sub in valid_subs],
                values=[sub["cost"] for sub in valid_subs],
                title="Distribuzione costi mensili",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Non ci sono abbonamenti con costi validi da visualizzare.")
    else:
        st.info("Non ci sono abbonamenti da visualizzare.")

# 4. Modulo Calendario
def generate_calendar():
    st.markdown("<h2>Calendario scadenze e rinnovi</h2>", unsafe_allow_html=True)
    
    # Selezione mese/anno
    col1, col2 = st.columns(2)
    
    with col1:
        current_year = datetime.now().year
        year_options = list(range(current_year, current_year + 3))
        selected_year = st.selectbox("Anno", year_options)
    
    with col2:
        month_options = list(range(1, 13))
        month_names = [calendar.month_name[m] for m in month_options]
        selected_month_name = st.selectbox("Mese", month_names)
        selected_month = month_options[month_names.index(selected_month_name)]
    
    # Generiamo il calendario
    cal = calendar.monthcalendar(selected_year, selected_month)
    
    # Otteniamo tutti gli eventi del mese selezionato
    events = []
    
    # Aggiungiamo le scadenze
    for deadline in st.session_state.deadlines:
        if deadline["date"].year == selected_year and deadline["date"].month == selected_month:
            events.append({
                "day": deadline["date"].day,
                "title": deadline["title"],
                "type": "deadline",
                "id": deadline["id"],
                "category": deadline["category"]
            })
    
    # Aggiungiamo i rinnovi degli abbonamenti
    for sub in st.session_state.subscriptions:
        if sub["renewal_date"].year == selected_year and sub["renewal_date"].month == selected_month:
            events.append({
                "day": sub["renewal_date"].day,
                "title": f"Rinnovo {sub['name']}",
                "type": "subscription",
                "id": sub["id"],
                "cost": sub["cost"]
            })
    
    # Creiamo l'HTML del calendario
    week_days = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
    
    calendar_html = f"""
    <h3 style="text-align: center;">{calendar.month_name[selected_month]} {selected_year}</h3>
    <table class="calendar">
        <tr>
    """
    
    for day in week_days:
        calendar_html += f"<th>{day}</th>"
    
    calendar_html += "</tr>"
    
    # Aggiungiamo le settimane
    for week in cal:
        calendar_html += "<tr>"
        
        for day in week:
            if day == 0:
                # Giorno vuoto (non fa parte del mese)
                calendar_html += "<td></td>"
            else:
                # Troviamo gli eventi di questo giorno
                day_events = [e for e in events if e["day"] == day]
                
                # Impostiamo uno stile se oggi
                is_today = (datetime.now().day == day and 
                            datetime.now().month == selected_month and 
                            datetime.now().year == selected_year)
                
                today_style = "background-color: #e8f4f8; font-weight: bold;"
                
                calendar_html += f"<td style='{today_style if is_today else ''}'>"
                calendar_html += f"<div class='calendar-day'>{day}</div>"
                
                # Aggiungiamo gli eventi
                for event in day_events:
                    event_class = "calendar-event urgent" if event["type"] == "deadline" else "calendar-event"
                    event_title = event["title"]
                    
                    if event["type"] == "subscription":
                        event_title += f" - {event['cost']:.2f}€"
                    
                    calendar_html += f"<div class='{event_class}'>{event_title}</div>"
                
                calendar_html += "</td>"
        
        calendar_html += "</tr>"
    
    calendar_html += "</table>"
    
    st.markdown(calendar_html, unsafe_allow_html=True)
    
    # Legenda
    st.markdown("""
    <div style='margin-top: 20px;'>
        <span class='calendar-event' style='display: inline-block; margin-right: 10px;'>Abbonamento</span>
        <span class='calendar-event urgent' style='display: inline-block;'>Scadenza</span>
    </div>
    """, unsafe_allow_html=True)

# 5. Modulo Assistente AI
def ai_assistant():
    st.markdown("<h2>Assistente AI</h2>", unsafe_allow_html=True)
    
    # Selezione del documento
    document_options = ["Nessun documento selezionato"] + [doc["name"] for doc in st.session_state.documents]
    selected_doc_name = st.selectbox("Seleziona un documento per fare domande", document_options)
    
    selected_doc = None
    if selected_doc_name != "Nessun documento selezionato":
        for doc in st.session_state.documents:
            if doc["name"] == selected_doc_name:
                selected_doc = doc
                break
    
    # Visualizziamo la cronologia della chat
    st.markdown("<h3>Cronologia chat</h3>", unsafe_allow_html=True)
    
    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            st.markdown(f"""
            <div class="chat-message chat-user">
                <strong>Tu:</strong> {chat["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message chat-assistant">
                <strong>Assistente AI:</strong> {chat["content"]}
            </div>
            """, unsafe_allow_html=True)
    
    # Input per l'utente
    user_input = st.text_input("Scrivi la tua domanda...")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        if st.button("Invia domanda"):
            if user_input:
                # Aggiungiamo la domanda alla chat
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": user_input
                })
                
                # Generiamo una risposta AI simulata
                ai_response = simulate_ai_response(user_input, selected_doc)
                
                # Aggiungiamo la risposta alla chat
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": ai_response
                })
                
                st.rerun()
    
    with col2:
        if st.button("Cancella chat"):
            st.session_state.chat_history = []
            st.success("Cronologia chat cancellata!")
            st.rerun()

def simulate_ai_response(user_input, doc):
    """Simula una risposta AI basata sul documento selezionato"""
    
    # Risposte predefinite per simulare l'AI
    general_responses = [
        "Posso aiutarti a gestire i tuoi documenti e scadenze. Cosa vorresti sapere?",
        "Questo è un assistente simulato. In una versione completa, potrei analizzare i tuoi documenti e rispondere in modo più pertinente.",
        "Non ho accesso a un modello di linguaggio reale. Questa è una simulazione di risposta.",
        "Per ottenere informazioni più dettagliate, dovresti collegare un vero modello AI a questa app."
    ]
    
    document_responses = [
        f"Ho esaminato il documento '{doc['name']}'. Cosa vuoi sapere nello specifico?",
        f"Il documento '{doc['name']}' è nella categoria '{doc['category']}'. Posso aiutarti a interpretarlo.",
        f"Questo documento è stato caricato il {doc['upload_date'].strftime('%d/%m/%Y')}. Come posso aiutarti?",
        f"Sto analizzando '{doc['name']}'. Ricorda che questa è una simulazione di assistente AI."
    ]
    
    # Risposte specifiche basate su parole chiave nella domanda
    if "scadenza" in user_input.lower() or "rinnovo" in user_input.lower():
        if doc and doc.get("expiry_date"):
            return f"La scadenza per '{doc['name']}' è prevista per il {doc['expiry_date'].strftime('%d/%m/%Y')}."
        else:
            return "Non ho trovato informazioni sulle scadenze nel documento selezionato."
    
    elif "contenuto" in user_input.lower() or "cosa" in user_input.lower() and "dice" in user_input.lower():
        if doc and doc["type"] == "text":
            preview = doc["preview"]
            # Limitiamo la lunghezza della risposta
            if len(preview) > 300:
                preview = preview[:300] + "..."
            return f"Ecco un estratto del documento: \n\n{preview}"
        else:
            return "Non posso estrarre il contenuto testuale da questo tipo di documento."
    
    elif "categoria" in user_input.lower():
        if doc:
            return f"Il documento '{doc['name']}' appartiene alla categoria '{doc['category']}'."
        else:
            return "Non hai selezionato un documento."
    
    # Risposte casuali
    if doc:
        return random.choice(document_responses)
    else:
        return random.choice(general_responses)

# 6. Dashboard
def dashboard():
    st.markdown("<h1>Dashboard</h1>", unsafe_allow_html=True)
    
    # Metriche principali
    col1, col2, col3, col4 = st.columns(4)
    
    # Calcolo delle metriche
    total_docs = len(st.session_state.documents)
    
    # Documenti caricati negli ultimi 7 giorni
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    docs_last_week = sum(1 for doc in st.session_state.documents if doc["upload_date"] >= week_ago)
    
    # Numero di categorie utilizzate
    used_categories = set()
    for doc in st.session_state.documents:
        used_categories.add(doc["category"])
    
    # Scadenze imminenti
    week_later = today + timedelta(days=7)
    upcoming_deadlines = sum(1 for d in st.session_state.deadlines if today <= d["date"] <= week_later)
    
    # Visualizzazione metriche
    with col1:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-value">{total_docs}</div>
            <div class="metric-label">Documenti totali</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-value">{docs_last_week}</div>
            <div class="metric-label">Nuovi documenti (7 giorni)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-value">{len(used_categories)}</div>
            <div class="metric-label">Categorie utilizzate</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-value">{upcoming_deadlines}</div>
            <div class="metric-label">Scadenze imminenti</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Grafici
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h3>Distribuzione documenti per categoria</h3>", unsafe_allow_html=True)
        
        if st.session_state.documents:
            # Conteggio documenti per categoria
            category_counts = {}
            for doc in st.session_state.documents:
                category = doc["category"]
                if category in category_counts:
                    category_counts[category] += 1
                else:
                    category_counts[category] = 1
            
            # Creazione grafico
            fig = px.pie(
                names=list(category_counts.keys()),
                values=list(category_counts.values()),
                title="Documenti per categoria",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Non hai ancora caricato documenti. Il grafico apparirà quando aggiungerai documenti.")
    
    with col2:
        st.markdown("<h3>Prossime scadenze</h3>", unsafe_allow_html=True)
        
        if st.session_state.deadlines:
            # Prossime scadenze ordinate per data
            upcoming = sorted([d for d in st.session_state.deadlines if d["date"] >= today], 
                              key=lambda x: x["date"])[:10]  # Mostriamo le prossime 10
            
            if upcoming:
                deadline_data = []
                for d in upcoming:
                    days_left = (d["date"] - today).days
                    deadline_data.append({
                        "Titolo": d["title"] if len(d["title"]) <= 20 else d["title"][:17] + "...",
                        "Giorni": days_left,
                        "Data": d["date"].strftime("%d/%m/%Y")
                    })
                
                df = pd.DataFrame(deadline_data)
                
                # Creazione grafico a barre orizzontale
                fig = px.bar(
                    df,
                    y="Titolo",
                    x="Giorni",
                    orientation='h',
                    title="Giorni rimanenti alle prossime scadenze",
                    color="Giorni",
                    color_continuous_scale=["#e74a3b", "#f6c23e", "#1cc88a"],
                    text="Data",
                    labels={"Titolo": "", "Giorni": "Giorni rimanenti"}
                )
                
                fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Non ci sono scadenze future.")
        else:
            st.info("Non hai ancora aggiunto scadenze. Il grafico apparirà quando aggiungerai scadenze.")
    
    # Documenti recenti e prossime scadenze
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h3>Documenti recenti</h3>", unsafe_allow_html=True)
        
        if st.session_state.documents:
            # Ultimi 5 documenti caricati
            recent_docs = sorted(st.session_state.documents, 
                                 key=lambda x: x["upload_date"], 
                                 reverse=True)[:5]
            
            for doc in recent_docs:
                st.markdown(f"""
                <div class="card" style="margin-bottom: 10px; padding: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: bold;">{doc["name"]}</span>
                        <span style="color: #7b8a8b;">{doc["upload_date"].strftime('%d/%m/%Y')}</span>
                    </div>
                    <div style="color: #4e73df; font-size: 13px;">{doc["category"]}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Non hai ancora caricato documenti.")
    
    with col2:
        st.markdown("<h3>Prossime 5 scadenze</h3>", unsafe_allow_html=True)
        
        if st.session_state.deadlines:
            # Prossime 5 scadenze
            next_deadlines = sorted([d for d in st.session_state.deadlines if d["date"] >= today], 
                                    key=lambda x: x["date"])[:5]
            
            if next_deadlines:
                for deadline in next_deadlines:
                    days_left = (deadline["date"] - today).days
                    status_color = "#e74a3b" if days_left <= 3 else "#f6c23e" if days_left <= 7 else "#1cc88a"
                    
                    st.markdown(f"""
                    <div class="card" style="margin-bottom: 10px; padding: 10px; border-left: 5px solid {status_color};">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-weight: bold;">{deadline["title"]}</span>
                            <span style="color: {status_color}; font-weight: bold;">{days_left} giorni</span>
                        </div>
                        <div>{deadline["date"].strftime('%d/%m/%Y')}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Non ci sono scadenze future.")
        else:
            st.info("Non hai ancora aggiunto scadenze.")

# Main dell'applicazione
def main():
    # Inizializzazione
    load_css()
    init_session_state()
    
    # Creazione della sidebar per la navigazione
    page = create_sidebar()
    
    # Gestione pagine
    if page == "Dashboard":
        dashboard()
    
    elif page == "Documenti":
        st.markdown("<h1>Gestione Documenti</h1>", unsafe_allow_html=True)
        
        # Tab per upload o visualizzazione
        tab1, tab2 = st.tabs(["Carica documenti", "Visualizza documenti"])
        
        with tab1:
            upload_document()
        
        with tab2:
            view_documents()
    
    elif page == "Scadenze":
        st.markdown("<h1>Gestione Scadenze</h1>", unsafe_allow_html=True)
        
        # Tab per aggiunta o visualizzazione
        tab1, tab2 = st.tabs(["Aggiungi scadenza", "Visualizza scadenze"])
        
        with tab1:
            add_deadline()
        
        with tab2:
            view_deadlines()
    
    elif page == "Abbonamenti":
        st.markdown("<h1>Gestione Abbonamenti</h1>", unsafe_allow_html=True)
        
        # Tab per aggiunta o visualizzazione
        tab1, tab2 = st.tabs(["Aggiungi abbonamento", "Visualizza abbonamenti"])
        
        with tab1:
            add_subscription()
        
        with tab2:
            view_subscriptions()
    
    elif page == "Calendario":
        st.markdown("<h1>Calendario</h1>", unsafe_allow_html=True)
        generate_calendar()
    
    elif page == "Assistente AI":
        st.markdown("<h1>Assistente AI</h1>", unsafe_allow_html=True)
        ai_assistant()

if __name__ == '__main__':
    main()
