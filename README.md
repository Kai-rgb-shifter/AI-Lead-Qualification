# AI Lead Qualification System

An AI-powered lead qualification and sales automation platform built with Python, Streamlit, Ollama, SQLite, and n8n.

The system evaluates sales leads using a hybrid scoring approach that combines deterministic business rules with local LLM-generated guidance. It stores lead history, provides interactive analytics, and automatically sends qualified lead information to Gmail and Google Sheets through n8n.



## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt


## Features

- Hybrid AI lead scoring using rules-based logic plus Ollama-generated guidance.
- Streamlit dashboard with lead metrics, Plotly charts, search, filters, and lead details.
- SQLite persistence for saving and retrieving lead history.
- Plotly analytics for category distribution and industry breakdowns.
- Search and filtering across saved leads.
- CSV export for filtered lead data.
- Gmail notifications via n8n workflow integration.
- Google Sheets integration via n8n workflow automation.

## 🏗️ Architecture

```text
                    ┌─────────────────────┐
                    │    Streamlit UI     │
                    │   Lead Analyzer     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Hybrid AI Scoring  │
                    │ Rules + Ollama      │
                    │    Qwen 2.5         │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┴─────────────┐
                 ▼                           ▼
        ┌─────────────────┐         ┌─────────────────┐
        │  SQLite Database│         │    Dashboard    │
        │   Lead Storage  │         │ Plotly Analytics│
        └────────┬────────┘         └─────────────────┘
                 │
                 ▼
        ┌─────────────────┐
        │   n8n Webhook   │
        │   Automation    │
        └────────┬────────┘
                 │
          ┌──────┴──────┐
          ▼             ▼
     ┌─────────┐   ┌──────────────┐
     │  Gmail  │   │Google Sheets │
     │ Alerts  │   │ Lead Logging │
     └─────────┘   └──────────────┘
```

## 🧠 How Hybrid Lead Scoring Works

The application uses a hybrid approach that combines deterministic business rules with local AI-generated guidance.

### 1. Lead Input

The user submits information such as:

- Name
- Company
- Industry
- Company Size
- Budget
- Timeline
- Business Requirement

### 2. Rule-Based Scoring

The application first evaluates the lead using predefined business rules.

These rules provide a consistent baseline score and category based on factors such as budget, company characteristics, timeline, and lead requirements.

### 3. Local AI Analysis

The lead information is then provided to a locally running Ollama model (`qwen2.5:3b`).

The model generates additional business-oriented guidance, including:

- Reason
- Recommended Next Action
- Potential Risks

### 4. Final Lead Qualification

The deterministic scoring and AI-generated analysis are combined to produce a structured lead qualification result.

Each lead is classified as:

- 🔥 Hot
- 🟡 Warm
- 🔵 Cold

with a score from 0–100.

### 5. Storage & Automation

The qualified lead is saved to SQLite and sent to the configured n8n webhook.

n8n then automates downstream actions such as:

- Gmail notifications
- Google Sheets logging

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Frontend | Streamlit |
| AI / LLM | Ollama + Qwen 2.5 |
| Lead Scoring | Hybrid Rules + AI |
| Database | SQLite |
| Automation | n8n |
| Visualization | Plotly |
| Data Processing | Pandas |
| Notifications | Gmail |
| Lead Storage | Google Sheets |


## 📸 Screenshots

### Lead Analyzer

![Lead Analyzer](assets/lead-analyzer.1.png)
![Lead Analyzer](assets/lead-analyzer.2.png)
![Lead Analyzer](assets/lead-analyzer.3.png)


### Dashboard

![Dashboard](assets/dashboard.1.png)
![Dashboard](assets/dashboard.2.png)
![Dashboard](assets/dashboard.3.png)

### n8n Workflow

![n8n Workflow](assets/workflow.png)

### Gmail Notification

![Gmail Notification](assets/gmail.1.png)
![Gmail Notification](assets/gmail.2.png)

### Google Sheets

![Google Sheets](assets/spreadsheet.png)


## Project Structure

```text
AI-Lead-Qualification/
├── app.py                # Streamlit UI, dashboard, and lead analyzer
├── database.py           # SQLite setup, persistence, and retrieval helpers
├── n8n_client.py         # Webhook delivery for lead notifications
├── ollama_client.py      # Local Ollama client for AI guidance
├── modules/
│   ├── __init__.py
│   └── lead_scoring.py   # Deterministic scoring logic
├── requirements.txt      # Python dependencies
├── README.md             # Project documentation
└── leads.db              # SQLite database created at runtime
```

## Installation

1. Clone the repository and open the project folder.
2. Create and activate a virtual environment if needed.
3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Make sure Ollama is running locally and the `qwen2.5:3b` model is available.
5. Configure any n8n webhook workflows you want to use for notifications or Google Sheets automation.

## Usage

1. Start the Streamlit app:

   ```bash
   streamlit run app.py
   ```

2. Use the Lead Analyzer page to submit a lead and generate a score.
3. Open the Dashboard page to review metrics, charts, search and filter saved leads, export filtered results, and inspect top qualified leads.
4. Use the Lead Details section to view the full record for any filtered lead.

## Future Improvements

- Add user authentication and role-based access.
- Expand dashboard analytics with trend lines and conversion tracking.
- Add configurable scoring rules through the UI.
- Support additional notification channels through n8n.
- Add automated tests for the dashboard and persistence layer.

## License

No license has been specified for this project. Add one before distributing or using the project outside your own environment.
