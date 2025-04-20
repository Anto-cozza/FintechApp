import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
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

# Initial app configuration
st.set_page_config(
    page_title="ContractME",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Utility functions
def load_css():
    st.markdown("""
    <style>
        /* General style */
        .main {
            background-color: #f8f9fa;
            padding: 20px;
        }
        
        /* Titles */
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
        
        /* Metrics */
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
        
        /* Calendar */
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
        
        /* Logo and sidebar */
        .sidebar-logo {
            text-align: center;
            margin-bottom: 20px;
        }
        
        /* Buttons and input */
        .stButton button {
            background-color: #4e73df;
            color: white;
            border-radius: 5px;
        }
        
        /* Tables */
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

# Session state initialization
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
        st.session_state.categories = ["Home", "Work", "Health", "Finance", "Education", "Other"]

# Function to display logo
def display_logo():
    st.markdown("""
    <div class="sidebar-logo">
        <h1 style="color: #4e73df;">📄 ContractME</h1>
        <p>Manage your documents with ease</p>
    </div>
    """, unsafe_allow_html=True)

# Function to create sidebar
def create_sidebar():
    with st.sidebar:
        display_logo()
        
        st.markdown("---")
        
        menu = ["Dashboard", "Documents", "Deadlines", "Subscriptions", "Calendar", "AI Assistant"]
        choice = st.radio("Navigation", menu)
        
        st.markdown("---")
        
        st.markdown("""
        <div style="text-align: center; margin-top: 20px; font-size: small;">
            © 2025 ContractME<br>
            Version 1.0
        </div>
        """, unsafe_allow_html=True)
        
        return choice

# 1. Document Upload Module
def upload_document():
    st.markdown("<h2>Upload a New Document</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        doc_name = st.text_input("Document Name")
        doc_category = st.selectbox("Category", st.session_state.categories)
        custom_category = st.text_input("Add new category (optional)")
        
        if custom_category and custom_category not in st.session_state.categories:
            st.session_state.categories.append(custom_category)
            st.success(f"Category '{custom_category}' added!")
    
    with col2:
        uploaded_file = st.file_uploader("Upload a document", 
                                       type=["pdf", "jpg", "jpeg", "png", "txt", "md"],
                                       help="Supported formats: PDF, JPG, PNG, TXT, MD")
        
        has_expiry = st.checkbox("Document has an expiry date")
        
        if has_expiry:
            expiry_date = st.date_input("Expiry date", min_value=datetime.now().date())
        else:
            expiry_date = None
    
    if st.button("Upload Document"):
        if doc_name and uploaded_file:
            # Temporary file saving
            file_extension = uploaded_file.name.split(".")[-1].lower()
            
            # To determine document type
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
                
            # Creating document object
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
            
            # Adding to session
            st.session_state.documents.append(document)
            
            # If it has an expiry date, we also add it as a deadline
            if expiry_date:
                deadline = {
                    "id": len(st.session_state.deadlines) + 1,
                    "title": f"Expiry {doc_name}",
                    "date": expiry_date,
                    "description": f"Deadline for document '{doc_name}'",
                    "category": doc_category if not custom_category else custom_category,
                    "document_id": document["id"]
                }
                st.session_state.deadlines.append(deadline)
            
            st.success(f"Document '{doc_name}' uploaded successfully!")
        else:
            st.error("Please enter a name for the document and upload a file.")

def view_documents():
    st.markdown("<h2>Your Documents</h2>", unsafe_allow_html=True)
    
    if not st.session_state.documents:
        st.info("You haven't uploaded any documents yet. Use the form above to upload your first document.")
        return
    
    # Remove duplicates based on name
    unique_docs = {}
    for doc in st.session_state.documents:
        name = doc.get("name", "Unnamed Document")
        unique_docs[name] = doc
    
    # Use only unique documents
    st.session_state.documents = list(unique_docs.values())
    
    # Filter by category
    all_categories = ["All"] + st.session_state.categories
    filter_category = st.selectbox("Filter by category", all_categories)
    
    filtered_docs = st.session_state.documents
    if filter_category != "All":
        filtered_docs = [doc for doc in st.session_state.documents if doc["category"] == filter_category]
    
    if not filtered_docs:
        st.info(f"There are no documents in the '{filter_category}' category.")
        return
    
    # Document display
    for i, doc in enumerate(filtered_docs):
        col1, col2 = st.columns([2, 3])
        
        with col1:
            st.markdown(f"""
            <div class="card">
                <h3>{doc['name']}</h3>
                <p><strong>Category:</strong> {doc['category']}</p>
                <p><strong>Upload date:</strong> {doc['upload_date'].strftime('%m/%d/%Y')}</p>
                <p><strong>File type:</strong> {doc['filename'].split('.')[-1].upper()}</p>
                
                {f"<p><strong>Expiry date:</strong> {doc['expiry_date'].strftime('%m/%d/%Y')}</p>" if doc['expiry_date'] else ""}
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Delete document {doc['name']}", key=f"del_doc_{doc['id']}"):
                # Remove the document
                st.session_state.documents.remove(doc)
                # Remove any associated deadlines
                st.session_state.deadlines = [d for d in st.session_state.deadlines if d.get('document_id') != doc['id']]
                st.success(f"Document '{doc['name']}' deleted successfully!")
                st.rerun()
        
        with col2:
            st.markdown("<div class='card'><h4>Preview</h4>", unsafe_allow_html=True)
            
            if doc["type"] == "image":
                st.markdown(f"""
                <img src="data:image/png;base64,{doc['preview']}" 
                     style="max-width: 100%; max-height: 300px; display: block; margin: 0 auto;">
                """, unsafe_allow_html=True)
                
            elif doc["type"] == "pdf":
                st.markdown(f"""
                <p>PDF preview not available directly. 
                   <a href="data:application/pdf;base64,{doc['preview']}" download="{doc['name']}.pdf">
                   Download PDF</a></p>
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

# 2. Deadline Management Module
def add_deadline():
    st.markdown("<h2>Add a New Deadline</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        deadline_title = st.text_input("Deadline Title")
        deadline_category = st.selectbox("Category", st.session_state.categories)
        
    with col2:
        deadline_date = st.date_input("Deadline Date", min_value=datetime.now().date())
        
        # Option to link to an existing document
        doc_options = ["No linked document"] + [doc["name"] for doc in st.session_state.documents]
        selected_doc = st.selectbox("Linked document (optional)", doc_options)
        
    deadline_desc = st.text_area("Description", height=100)
    
    if st.button("Add Deadline"):
        if deadline_title and deadline_date:
            # Find the ID of the selected document, if present
            doc_id = None
            if selected_doc != "No linked document":
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
            st.success(f"Deadline '{deadline_title}' added successfully!")
        else:
            st.error("Title and date are required!")

def view_deadlines():
    st.markdown("<h2>Your Deadlines</h2>", unsafe_allow_html=True)
    
    if not st.session_state.deadlines:
        st.info("You haven't added any deadlines yet.")
        return
    
    # Sort deadlines by date
    sorted_deadlines = sorted(st.session_state.deadlines, key=lambda x: x["date"])
    
    # Filter by periods
    period_options = ["All", "Next 7 days", "Next 30 days", "Next 3 months", "Expired"]
    selected_period = st.selectbox("View deadlines by period", period_options)
    
    filtered_deadlines = sorted_deadlines
    today = datetime.now().date()
    
    if selected_period == "Next 7 days":
        end_date = today + timedelta(days=7)
        filtered_deadlines = [d for d in sorted_deadlines if today <= d["date"] <= end_date]
    elif selected_period == "Next 30 days":
        end_date = today + timedelta(days=30)
        filtered_deadlines = [d for d in sorted_deadlines if today <= d["date"] <= end_date]
    elif selected_period == "Next 3 months":
        end_date = today + timedelta(days=90)
        filtered_deadlines = [d for d in sorted_deadlines if today <= d["date"] <= end_date]
    elif selected_period == "Expired":
        filtered_deadlines = [d for d in sorted_deadlines if d["date"] < today]
    
    if not filtered_deadlines:
        st.info(f"There are no deadlines in the selected period ({selected_period}).")
        return
    
    # Display deadlines in a table
    deadlines_data = []
    
    for d in filtered_deadlines:
        # Calculate if expired or imminent
        days_left = (d["date"] - today).days
        status = "⚠️ Expired" if days_left < 0 else "🔄 Imminent" if days_left <= 7 else "✅ Future"
        
        # Find the name of the associated document, if present
        doc_name = "None"
        if d.get("document_id"):
            for doc in st.session_state.documents:
                if doc["id"] == d["document_id"]:
                    doc_name = doc["name"]
                    break
        
        deadlines_data.append({
            "ID": d["id"],
            "Title": d["title"],
            "Date": d["date"].strftime("%m/%d/%Y"),
            "Days remaining": max(days_left, 0) if days_left >= 0 else f"Expired {abs(days_left)} days ago",
            "Category": d["category"],
            "Document": doc_name,
            "Status": status
        })
    
    df = pd.DataFrame(deadlines_data)
    
    # Display as colored table
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
    
    # Table display
    html_table = "<table class='deadline-table'>"
    
    # Header
    html_table += "<tr>"
    for col in df.columns:
        html_table += f"<th>{col}</th>"
    html_table += "</tr>"
    
    # Rows
    for _, row in df.iterrows():
        html_table += "<tr>"
        for i, value in enumerate(row):
            cell_class = ""
            if df.columns[i] == "Status":
                if "Expired" in value:
                    cell_class = "status-expired"
                elif "Imminent" in value:
                    cell_class = "status-imminent"
                else:
                    cell_class = "status-future"
            
            html_table += f"<td class='{cell_class}'>{value}</td>"
        html_table += "</tr>"
    
    html_table += "</table>"
    
    st.markdown(html_table, unsafe_allow_html=True)
    
    # Chart of upcoming deadlines
    st.markdown("<h3>Chart of Upcoming Deadlines</h3>", unsafe_allow_html=True)
    
    upcoming_deadlines = [d for d in sorted_deadlines if d["date"] >= today][:10]  # Take the next 10
    
    if upcoming_deadlines:
        df_chart = pd.DataFrame([
            {
                "Title": d["title"], 
                "Date": d["date"], 
                "Days remaining": (d["date"] - today).days
            } for d in upcoming_deadlines
        ])
        
        df_chart = df_chart.sort_values("Date")
        
        fig = px.bar(
            df_chart, 
            x="Title", 
            y="Days remaining",
            title="Days remaining to upcoming deadlines",
            color="Days remaining",
            color_continuous_scale=["#e74a3b", "#f6c23e", "#1cc88a"],
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("There are no future deadlines to display in the chart.")

# 3. Subscription Module
def add_subscription():
    st.markdown("<h2>Add a New Subscription</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        sub_name = st.text_input("Subscription Name")
        sub_type = st.selectbox("Type", ["Streaming", "Services", "Utilities", "Gym", "Software", "Other"])
        
    with col2:
        sub_renewal_date = st.date_input("Next renewal date", min_value=datetime.now().date())
        sub_cost = st.number_input("Monthly cost ($)", min_value=0.0, step=0.01)
        
    sub_desc = st.text_area("Description", placeholder="Enter additional details...", height=100)
    
    if st.button("Add Subscription"):
        if sub_name and sub_renewal_date:
            subscription = {
                "id": len(st.session_state.subscriptions) + 1,
                "name": sub_name,
                "type": sub_type,
                "renewal_date": sub_renewal_date,
                "cost": float(sub_cost),  # Ensure cost is a float
                "description": sub_desc
            }
            
            st.session_state.subscriptions.append(subscription)
            
            # Also add a deadline for the renewal
            deadline = {
                "id": len(st.session_state.deadlines) + 1,
                "title": f"Renewal {sub_name}",
                "date": sub_renewal_date,
                "description": f"Subscription renewal '{sub_name}' - ${sub_cost}",
                "category": "Subscriptions",
                "subscription_id": subscription["id"]
            }
            st.session_state.deadlines.append(deadline)
            
            st.success(f"Subscription '{sub_name}' added successfully!")
        else:
            st.error("Name and renewal date are required!")

def view_subscriptions():
    st.markdown("<h2>Your Subscriptions</h2>", unsafe_allow_html=True)
    
    if not st.session_state.subscriptions:
        st.info("You haven't added any subscriptions yet.")
        return
    
    # Display subscriptions in cards
    # Ensure each subscription has a 'cost' key and it's a number
    for sub in st.session_state.subscriptions:
        if "cost" not in sub or not isinstance(sub["cost"], (int, float)):
            sub["cost"] = 0.0
            
    total_monthly_cost = sum(sub["cost"] for sub in st.session_state.subscriptions)
    
    st.markdown(f"""
    <div class="metric">
        <div class="metric-label">Total Monthly Cost</div>
        <div class="metric-value">${total_monthly_cost:.2f}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Verify that each subscription has a valid renewal_date before sorting
    for sub in st.session_state.subscriptions:
        # Always reset the renewal date for safety
        try:
            # Try to access the date, if it doesn't exist or is not valid, set a default
            renewal_date = sub.get("renewal_date")
            if renewal_date is None or not hasattr(renewal_date, "year"):
                sub["renewal_date"] = datetime.now().date()
        except:
            # In case of any error, set a default date
            sub["renewal_date"] = datetime.now().date()
    
    # Remove duplicates based on name
    unique_subs = {}
    for sub in st.session_state.subscriptions:
        name = sub.get("name", "Unnamed Subscription")
        unique_subs[name] = sub
    
    # Use only unique subscriptions
    st.session_state.subscriptions = list(unique_subs.values())
    
    # Safe sorting
    try:
        sorted_subs = sorted(st.session_state.subscriptions, key=lambda x: x["renewal_date"])
    except:
        # If sorting fails, use the unsorted list
        sorted_subs = st.session_state.subscriptions.copy()
    
    # Display cards in a grid
    col1, col2 = st.columns(2)
    
    for i, sub in enumerate(sorted_subs):
        # Alternate columns
        with col1 if i % 2 == 0 else col2:
            # Check safely if we can calculate days to renewal
            try:
                days_to_renewal = (sub["renewal_date"] - datetime.now().date()).days
            except:
                days_to_renewal = 0
                
            status_color = "#e74a3b" if days_to_renewal <= 3 else "#f6c23e" if days_to_renewal <= 7 else "#1cc88a"
            
            # Make sure name and other required fields are present
            name = sub.get("name", "Unnamed Subscription")
            sub_type = sub.get("type", "Not specified")
            cost_value = sub.get("cost", 0)
            description = sub.get("description", "")
            
            if not isinstance(cost_value, (int, float)):
                cost_value = 0
                
            st.markdown(f"""
            <div class="card" style="border-left: 5px solid {status_color};">
                <h3>{name}</h3>
                <p><strong>Type:</strong> {sub_type}</p>
                <p><strong>Monthly cost:</strong> ${cost_value:.2f}</p>
                <p><strong>Next renewal:</strong> {sub["renewal_date"].strftime('%m/%d/%Y')}</p>
                <p><strong>Days to renewal:</strong> <span style="color: {status_color}; font-weight: bold;">{days_to_renewal}</span></p>
                <p><strong>Description:</strong> {description}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Get the name of the subscription safely
            name = sub.get("name", "Unnamed Subscription")
            sub_id = sub.get("id", 0)
            
            if st.button(f"Delete {name}", key=f"del_sub_{sub_id}_{name}"):
                # Remove subscription
                st.session_state.subscriptions.remove(sub)
                # Remove any associated deadlines
                st.session_state.deadlines = [d for d in st.session_state.deadlines if d.get('subscription_id') != sub['id']]
                st.success(f"Subscription '{sub['name']}' deleted successfully!")
                st.rerun()
    
    # Pie chart of subscription costs
    st.markdown("<h3>Distribution of Subscription Costs</h3>", unsafe_allow_html=True)
    
    if sorted_subs:
        # For the pie chart, ensure all data is valid
        valid_subs = []
        for sub in sorted_subs:
            if "cost" in sub and isinstance(sub["cost"], (int, float)):
                # Make sure there's a valid name
                if "name" not in sub or not sub["name"]:
                    sub["name"] = "Unnamed Subscription"
                valid_subs.append(sub)
        
        if valid_subs:
            fig = px.pie(
                names=[sub["name"] for sub in valid_subs],
                values=[sub["cost"] for sub in valid_subs],
                title="Monthly cost distribution",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("There are no subscriptions with valid costs to display.")
    else:
        st.info("There are no subscriptions to display.")

# 4. Calendar Module
def generate_calendar():
    st.markdown("<h2>Calendar of Deadlines and Renewals</h2>", unsafe_allow_html=True)
    
    # Month/year selection
    col1, col2 = st.columns(2)
    
    with col1:
        current_year = datetime.now().year
        year_options = list(range(current_year, current_year + 3))
        selected_year = st.selectbox("Year", year_options)
    
    with col2:
        month_options = list(range(1, 13))
        month_names = [calendar.month_name[m] for m in month_options]
        selected_month_name = st.selectbox("Month", month_names)
        selected_month = month_options[month_names.index(selected_month_name)]
    
    # Generate the calendar
    cal = calendar.monthcalendar(selected_year, selected_month)
    
    # Get all events for the selected month
    events = []
    
    # Add deadlines
    for deadline in st.session_state.deadlines:
        if deadline["date"].year == selected_year and deadline["date"].month == selected_month:
            events.append({
                "day": deadline["date"].day,
                "title": deadline["title"],
                "type": "deadline",
                "id": deadline["id"],
                "category": deadline["category"]
            })
    
    # Add subscription renewals
    for sub in st.session_state.subscriptions:
        if sub["renewal_date"].year == selected_year and sub["renewal_date"].month == selected_month:
            events.append({
                "day": sub["renewal_date"].day,
                "title": f"Renewal {sub.get('name', 'Unnamed')}",
                "type": "subscription",
                "id": sub.get("id", 0),
                "cost": sub.get("cost", 0)
            })
    
    # Create calendar HTML directly
    week_days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    # Start with header
    calendar_html = f"<h3 style='text-align: center;'>{calendar.month_name[selected_month]} {selected_year}</h3>"
    calendar_html += "<table class='calendar'><tr>"
    
    # Add days of week
    for day in week_days:
        calendar_html += f"<th>{day}</th>"
    
    calendar_html += "</tr>"
    
    # Add weeks and days
    for week in cal:
        calendar_html += "<tr>"
        
        for day in week:
            if day == 0:
                # Empty day
                calendar_html += "<td></td>"
            else:
                # Find events for this day
                day_events = [e for e in events if e["day"] == day]
                
                # Check if today
                is_today = (datetime.now().day == day and 
                           datetime.now().month == selected_month and 
                           datetime.now().year == selected_year)
                
                today_style = "background-color: #e8f4f8; font-weight: bold;"
                
                calendar_html += f"<td style='{today_style if is_today else ''}'>"
                calendar_html += f"<div class='calendar-day'>{day}</div>"
                
                # Add events
                for event in day_events:
                    event_class = "calendar-event urgent" if event["type"] == "deadline" else "calendar-event"
                    event_title = event["title"]
                    
                    if event["type"] == "subscription":
                        cost = event.get("cost", 0)
                        if isinstance(cost, (int, float)):
                            event_title += f" - ${cost:.2f}"
                    
                    calendar_html += f"<div class='{event_class}'>{event_title}</div>"
                
                calendar_html += "</td>"
        
        calendar_html += "</tr>"
    
    calendar_html += "</table>"
    
    st.markdown(calendar_html, unsafe_allow_html=True)
    
    # Legend
    st.markdown("""
    <div style='margin-top: 20px;'>
        <span class='calendar-event' style='display: inline-block; margin-right: 10px;'>Subscription</span>
        <span class='calendar-event urgent' style='display: inline-block;'>Deadline</span>
    </div>
    """, unsafe_allow_html=True)

# 5. AI Assistant Module
def ai_assistant():
    st.markdown("<h2>AI Assistant</h2>", unsafe_allow_html=True)
    
    # Document selection
    document_options = ["No document selected"] + [doc["name"] for doc in st.session_state.documents]
    selected_doc_name = st.selectbox("Select a document to ask questions about", document_options)
    
    selected_doc = None
    if selected_doc_name != "No document selected":
        for doc in st.session_state.documents:
            if doc["name"] == selected_doc_name:
                selected_doc = doc
                break
    
    # Display chat history
    st.markdown("<h3>Chat History</h3>", unsafe_allow_html=True)
    
    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            st.markdown(f"""
            <div class="chat-message chat-user">
                <strong>You:</strong> {chat["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message chat-assistant">
                <strong>AI Assistant:</strong> {chat["content"]}
            </div>
            """, unsafe_allow_html=True)
    
    # User input
    user_input = st.text_input("Type your question...")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        if st.button("Send Question"):
            if user_input:
                # Add the question to the chat
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": user_input
                })
                
                # Generate a simulated AI response
                ai_response = simulate_ai_response(user_input, selected_doc)
                
                # Add the response to the chat
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": ai_response
                })
                
                st.rerun()
    
    with col2:
        if st.button("Clear Chat"):
            st.session_state.chat_history = []
            st.success("Chat history cleared!")
            st.rerun()

def simulate_ai_response(user_input, doc):
    """Simulates an AI response based on the selected document"""
    
    # Predefined responses to simulate AI
    general_responses = [
        "I can help you manage your documents and deadlines. What would you like to know?",
        "This is a simulated assistant. In a complete version, I could analyze your documents and provide more relevant responses.",
        "I don't have access to a real language model. This is a response simulation.",
        "To get more detailed information, you should connect a real AI model to this app."
    ]
    
    document_responses = [
        f"I've examined the document '{doc['name']}'. What specifically would you like to know?",
        f"The document '{doc['name']}' is in the '{doc['category']}' category. I can help you interpret it.",
        f"This document was uploaded on {doc['upload_date'].strftime('%m/%d/%Y')}. How can I help you?",
        f"I'm analyzing '{doc['name']}'. Remember this is a simulated AI assistant."
    ]
    
    # Specific responses based on keywords in the question
    if "deadline" in user_input.lower() or "expiry" in user_input.lower() or "renewal" in user_input.lower():
        if doc and doc.get("expiry_date"):
            return f"The deadline for '{doc['name']}' is set for {doc['expiry_date'].strftime('%m/%d/%Y')}."
        else:
            return "I couldn't find any deadline information in the selected document."
    
    elif "content" in user_input.lower() or "what" in user_input.lower() and "says" in user_input.lower():
        if doc and doc["type"] == "text":
            preview = doc["preview"]
            # Limit the response length
            if len(preview) > 300:
                preview = preview[:300] + "..."
            return f"Here's an excerpt from the document: \n\n{preview}"
        else:
            return "I can't extract text content from this type of document."
    
    elif "category" in user_input.lower():
        if doc:
            return f"The document '{doc['name']}' belongs to the '{doc['category']}' category."
        else:
            return "You haven't selected a document."
    
    # Random responses
    if doc:
        return random.choice(document_responses)
    else:
        return random.choice(general_responses)

# 6. Dashboard
def dashboard():
    st.markdown("<h1>Dashboard</h1>", unsafe_allow_html=True)
    
    # Main metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate metrics
    total_docs = len(st.session_state.documents)
    
    # Documents uploaded in the last 7 days
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    docs_last_week = sum(1 for doc in st.session_state.documents if doc["upload_date"] >= week_ago)
    
    # Number of categories used
    used_categories = set()
    for doc in st.session_state.documents:
        used_categories.add(doc["category"])
    
    # Upcoming deadlines
    week_later = today + timedelta(days=7)
    upcoming_deadlines = sum(1 for d in st.session_state.deadlines if today <= d["date"] <= week_later)
    
    # Display metrics
    with col1:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-value">{total_docs}</div>
            <div class="metric-label">Total Documents</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-value">{docs_last_week}</div>
            <div class="metric-label">New Documents (7 days)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-value">{len(used_categories)}</div>
            <div class="metric-label">Categories Used</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric">
            <div class="metric-value">{upcoming_deadlines}</div>
            <div class="metric-label">Upcoming Deadlines</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h3>Document Distribution by Category</h3>", unsafe_allow_html=True)
        
        if st.session_state.documents:
            # Count documents by category
            category_counts = {}
            for doc in st.session_state.documents:
                category = doc["category"]
                if category in category_counts:
                    category_counts[category] += 1
                else:
                    category_counts[category] = 1
            
            # Create chart
            fig = px.pie(
                names=list(category_counts.keys()),
                values=list(category_counts.values()),
                title="Documents by Category",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("You haven't uploaded any documents yet. The chart will appear when you add documents.")
    
    with col2:
        st.markdown("<h3>Upcoming Deadlines</h3>", unsafe_allow_html=True)
        
        if st.session_state.deadlines:
            # Upcoming deadlines sorted by date
            upcoming = sorted([d for d in st.session_state.deadlines if d["date"] >= today], 
                              key=lambda x: x["date"])[:10]  # Show the next 10
            
            if upcoming:
                deadline_data = []
                for d in upcoming:
                    days_left = (d["date"] - today).days
                    deadline_data.append({
                        "Title": d["title"] if len(d["title"]) <= 20 else d["title"][:17] + "...",
                        "Days": days_left,
                        "Date": d["date"].strftime("%m/%d/%Y")
                    })
                
                df = pd.DataFrame(deadline_data)
                
                # Create horizontal bar chart
                fig = px.bar(
                    df,
                    y="Title",
                    x="Days",
                    orientation='h',
                    title="Days remaining to upcoming deadlines",
                    color="Days",
                    color_continuous_scale=["#e74a3b", "#f6c23e", "#1cc88a"],
                    text="Date",
                    labels={"Title": "", "Days": "Days remaining"}
                )
                
                fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("There are no future deadlines.")
        else:
            st.info("You haven't added any deadlines yet. The chart will appear when you add deadlines.")
    
    # Recent documents and upcoming deadlines
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h3>Recent Documents</h3>", unsafe_allow_html=True)
        
        if st.session_state.documents:
            # Last 5 uploaded documents
            recent_docs = sorted(st.session_state.documents, 
                                 key=lambda x: x["upload_date"], 
                                 reverse=True)[:5]
            
            for doc in recent_docs:
                st.markdown(f"""
                <div class="card" style="margin-bottom: 10px; padding: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: bold;">{doc["name"]}</span>
                        <span style="color: #7b8a8b;">{doc["upload_date"].strftime('%m/%d/%Y')}</span>
                    </div>
                    <div style="color: #4e73df; font-size: 13px;">{doc["category"]}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("You haven't uploaded any documents yet.")
    
    with col2:
        st.markdown("<h3>Next 5 Deadlines</h3>", unsafe_allow_html=True)
        
        if st.session_state.deadlines:
            # Next 5 deadlines
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
                            <span style="color: {status_color}; font-weight: bold;">{days_left} days</span>
                        </div>
                        <div>{deadline["date"].strftime('%m/%d/%Y')}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("There are no future deadlines.")
        else:
            st.info("You haven't added any deadlines yet.")

# Application main
def main():
    # Initialization
    load_css()
    init_session_state()
    
    # Creating sidebar for navigation
    page = create_sidebar()
    
    # Page management
    if page == "Dashboard":
        dashboard()
    
    elif page == "Documents":
        st.markdown("<h1>Document Management</h1>", unsafe_allow_html=True)
        
        # Tab for upload or view
        tab1, tab2 = st.tabs(["Upload Documents", "View Documents"])
        
        with tab1:
            upload_document()
        
        with tab2:
            view_documents()
    
    elif page == "Deadlines":
        st.markdown("<h1>Deadline Management</h1>", unsafe_allow_html=True)
        
        # Tab for add or view
        tab1, tab2 = st.tabs(["Add Deadline", "View Deadlines"])
        
        with tab1:
            add_deadline()
        
        with tab2:
            view_deadlines()
    
    elif page == "Subscriptions":
        st.markdown("<h1>Subscription Management</h1>", unsafe_allow_html=True)
        
        # Tab for add or view
        tab1, tab2 = st.tabs(["Add Subscription", "View Subscriptions"])
        
        with tab1:
            add_subscription()
        
        with tab2:
            view_subscriptions()
    
    elif page == "Calendar":
        st.markdown("<h1>Calendar</h1>", unsafe_allow_html=True)
        generate_calendar()
    
    elif page == "AI Assistant":
        st.markdown("<h1>AI Assistant</h1>", unsafe_allow_html=True)
        ai_assistant()

if __name__ == '__main__':
    main()
