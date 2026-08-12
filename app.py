"""Streamlit application for lead analysis, dashboarding, and orchestration.

This module owns the UI and coordinates scoring, persistence, and webhook delivery.
"""

import csv
import io
from typing import Any, Dict, List

import plotly.express as px
import streamlit as st

from database import get_all_leads, initialize_database, save_lead
from modules.lead_scoring import analyze_lead
from n8n_client import send_lead_to_n8n
from ai_client import AIClientError, analyze_lead_with_ai


# Configure the Streamlit page for a polished dashboard feel.
st.set_page_config(page_title="AI Lead Qualification", page_icon="🤖", layout="wide")


# Inject custom CSS to make the dashboard look more modern and attractive.
st.markdown(
    """
    <style>
    .main {
        background: linear-gradient(135deg, #0f172a, #1e293b);
        color: #f8fafc;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .stTextInput > div > div > input,
    .stTextArea > div > textarea,
    .stSelectbox > div > div {
        background-color: #111827;
        color: white;
    }
    .stButton > button {
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def main() -> None:
    """Render the main dashboard and lead analysis experience."""
    initialize_database()

    st.title("🤖 AI Lead Qualification System")
    st.caption("A beginner-friendly lead scoring app powered by Ollama and Streamlit.")

    page = st.sidebar.radio("Navigate", ["Lead Analyzer", "Dashboard"])

    if page == "Dashboard":
        render_dashboard()
        return

    render_lead_overview_cards()

    # A welcoming summary section with a quick description.
    st.markdown("""
    This app helps a sales team quickly decide whether a lead is worth pursuing.
    It scores each lead from 0 to 100, classifies it as Hot, Warm, or Cold,
    and explains the reasoning using the local qwen2.5:3b model.
    """)

    # Two columns for a balanced layout.
    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.markdown("### Lead Intake Form")
        with st.form("lead_form"):
            name = st.text_input("Name", placeholder="Enter the lead's name")
            email = st.text_input("Email", placeholder="name@company.com")
            phone = st.text_input("Phone", placeholder="+1 555 123 4567")
            company = st.text_input("Company", placeholder="Company name")
            industry = st.selectbox(
                "Industry",
                [
                    "Technology",
                    "Healthcare",
                    "Finance",
                    "Education",
                    "Manufacturing",
                    "Retail",
                    "Other",
                ],
            )
            company_size = st.selectbox(
                "Company Size",
                [
                    "1-10",
                    "11-50",
                    "51-200",
                    "201-500",
                    "501-1000",
                    "1001-5000",
                    "5000+",
                ],
            )
            budget = st.text_input("Budget", placeholder="e.g. 15000")
            timeline = st.selectbox(
                "Timeline",
                ["ASAP", "This month", "Next 1-3 months", "Later"],
            )
            requirement = st.text_area(
                "Requirement",
                placeholder="Describe the problem or project the lead needs help with.",
            )
            lead_source = st.selectbox(
                "Lead Source",
                ["Website", "Referral", "Cold Outreach", "Partner", "Other"],
            )

            submitted = st.form_submit_button("Analyze Lead", width="stretch")

        if submitted:
            form_data = {
                "name": name,
                "email": email,
                "phone": phone,
                "company": company,
                "industry": industry,
                "company_size": company_size,
                "budget": budget,
                "timeline": timeline,
                "requirement": requirement,
                "lead_source": lead_source,
            }

            try:
                deterministic_analysis = analyze_lead(form_data)
                ai_analysis = analyze_lead_with_ai(
                    {
                        "score": deterministic_analysis["score"],
                        "category": deterministic_analysis["category"],
                        "company": company,
                        "industry": industry,
                        "company_size": company_size,
                        "budget": budget,
                        "timeline": timeline,
                        "requirement": requirement,
                    }
                )

                save_lead(
                    {
                        "name": name,
                        "company": company,
                        "industry": industry,
                        "company_size": company_size,
                        "budget": budget,
                        "timeline": timeline,
                        "requirement": requirement,
                        "score": deterministic_analysis["score"],
                        "category": deterministic_analysis["category"],
                        "reason": ai_analysis["reason"],
                        "next_action": ai_analysis["next_action"],
                        "risks": ai_analysis["risks"],
                    }
                )

                send_lead_to_n8n(
                    {
                        "name": name,
                        "company": company,
                        "industry": industry,
                        "company_size": company_size,
                        "budget": budget,
                        "timeline": timeline,
                        "requirement": requirement,
                        "score": deterministic_analysis["score"],
                        "category": deterministic_analysis["category"],
                        "reason": ai_analysis["reason"],
                        "next_action": ai_analysis["next_action"],
                        "risks": ai_analysis["risks"],
                    }
                )

                st.markdown("## Lead Analysis Result")

                score_col, category_col = st.columns(2)

                with score_col:
                    st.metric("AI Lead Score", deterministic_analysis["score"])

                with category_col:
                    category = deterministic_analysis["category"]
                    st.metric("Category", category)

                if category == "Hot":
                    st.error("🔥 High-priority lead")
                elif category == "Warm":
                    st.warning("🟡 Follow-up lead")
                else:
                    st.info("🔵 Lower-priority lead")

                st.markdown("### Reason")
                st.write(ai_analysis["reason"])

                st.markdown("### Next Action")
                st.write(ai_analysis["next_action"])

                st.markdown("### Potential Risks")
                st.write(ai_analysis["risks"])

                st.success("Lead saved successfully.")

            except AIClientError:
                st.error(
                    "Ollama is not available right now. Make sure the local server is running at http://localhost:11434 and the qwen2.5:3b model is installed."
                )

    with right_col:
        st.markdown("### What the system checks")
        st.info(
            "The scoring uses the local Ollama model to review the submitted lead details and return a structured qualification result."
        )
        st.markdown(
            """
        - The model evaluates budget strength.
        - Timeline urgency affects qualification.
        - Requirement clarity helps judge intent.
        - The response is parsed from JSON for safe display.
        """
        )


def render_lead_overview_cards() -> None:
    """Render top-level lead metrics from the saved SQLite leads."""
    leads = get_all_leads()
    total_leads = len(leads)
    hot_leads = sum(1 for lead in leads if str(lead.get("category", "")).strip() == "Hot")
    warm_leads = sum(1 for lead in leads if str(lead.get("category", "")).strip() == "Warm")
    cold_leads = sum(1 for lead in leads if str(lead.get("category", "")).strip() == "Cold")
    average_score = round(
        sum(int(lead.get("score", 0) or 0) for lead in leads) / total_leads, 1
    ) if total_leads else 0

    metric_col_1, metric_col_2, metric_col_3, metric_col_4, metric_col_5 = st.columns(5)
    metric_col_1.metric("Total Leads", total_leads)
    metric_col_2.metric("Hot Leads", hot_leads)
    metric_col_3.metric("Warm Leads", warm_leads)
    metric_col_4.metric("Cold Leads", cold_leads)
    metric_col_5.metric("Average Score", average_score)


def render_dashboard_charts(leads: List[Dict[str, Any]]) -> None:
    """Render dashboard charts for lead category and industry distribution."""
    category_data = {
        "Category": ["Hot", "Warm", "Cold"],
        "Count": [
            sum(1 for lead in leads if str(lead.get("category", "")).strip() == "Hot"),
            sum(1 for lead in leads if str(lead.get("category", "")).strip() == "Warm"),
            sum(1 for lead in leads if str(lead.get("category", "")).strip() == "Cold"),
        ],
    }

    industry_counts: dict[str, int] = {}
    for lead in leads:
        industry = str(lead.get("industry", "")).strip() or "Unknown"
        industry_counts[industry] = industry_counts.get(industry, 0) + 1

    category_figure = px.bar(
        category_data,
        x="Category",
        y="Count",
        color="Category",
        text="Count",
        title="Lead Distribution by Category",
        color_discrete_map={"Hot": "#ef4444", "Warm": "#f59e0b", "Cold": "#3b82f6"},
    )
    category_figure.update_traces(textposition="outside", cliponaxis=False)
    category_figure.update_layout(
        showlegend=False,
        margin=dict(t=60, l=20, r=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f8fafc"),
    )

    industry_figure = px.pie(
        names=list(industry_counts.keys()),
        values=list(industry_counts.values()),
        title="Lead Distribution by Industry",
        hole=0.35,
    )
    industry_figure.update_traces(textposition="inside", textinfo="percent+label")
    industry_figure.update_layout(
        margin=dict(t=60, l=20, r=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f8fafc"),
        legend_title_text="Industry",
    )

    chart_col_1, chart_col_2 = st.columns(2)
    with chart_col_1:
        st.plotly_chart(category_figure, width="stretch")
    with chart_col_2:
        st.plotly_chart(industry_figure, width="stretch")


def render_dashboard() -> None:
    """Render the saved lead dashboard without changing the analyzer page."""
    st.markdown("## Lead Dashboard")

    leads = get_all_leads()

    render_lead_overview_cards()
    render_dashboard_charts(leads)

    st.markdown("### Search & Filters")
    filter_col_1, filter_col_2, filter_col_3, filter_col_4 = st.columns([2, 2, 1, 1])

    search_query = filter_col_1.text_input(
        "Search by name or company",
        placeholder="Search leads",
    )
    category_filter = filter_col_2.multiselect(
        "Category",
        ["Hot", "Warm", "Cold"],
        default=["Hot", "Warm", "Cold"],
    )
    min_score = filter_col_3.slider(
        "Minimum Score",
        min_value=0,
        max_value=100,
        value=0,
        step=1,
    )
    sort_option = filter_col_4.selectbox(
    "Sort by",
    ["Highest Score", "Lowest Score", "Newest"],
)

    filtered_leads = []
    search_term = search_query.strip().lower()
    for lead in leads:
        lead_name = str(lead.get("name", "")).strip()
        lead_company = str(lead.get("company", "")).strip()
        lead_category = str(lead.get("category", "")).strip()
        lead_score = int(lead.get("score", 0) or 0)

        if search_term and search_term not in f"{lead_name} {lead_company}".lower():
            continue
        if category_filter and lead_category not in category_filter:
            continue
        if lead_score < min_score:
            continue

        filtered_leads.append(
    {
        "Name": lead_name,
        "Company": lead_company,
        "Industry": str(lead.get("industry", "")).strip(),
        "Budget": str(lead.get("budget", "")).strip(),
        "Timeline": str(lead.get("timeline", "")).strip(),
        "Score": lead_score,
        "Category": lead_category,
        "Reason": str(lead.get("reason", "")).strip(),
        "Next Action": str(lead.get("next_action", "")).strip(),
        "Risks": str(lead.get("risks", "")).strip(),
    }
)
        if sort_option == "Highest Score":
         filtered_leads.sort(key=lambda lead: lead["Score"], reverse=True)
        elif sort_option == "Lowest Score":
         filtered_leads.sort(key=lambda lead: lead["Score"])

    st.dataframe(filtered_leads, width="stretch", hide_index=True)
    
    csv_buffer = io.StringIO()
    csv_columns = ["Name", "Company", "Industry", "Budget", "Timeline", "Score", "Category"]
    writer = csv.DictWriter(csv_buffer, fieldnames=csv_columns)
    writer.writeheader()
    writer.writerows(
    {
        column: lead.get(column, "")
        for column in csv_columns
    }
    for lead in filtered_leads
)

    st.download_button(
        "Download Filtered Leads (CSV)",
        data=csv_buffer.getvalue(),
        file_name="filtered_leads.csv",
        mime="text/csv",
        width="stretch",
    )

    st.markdown("### Top Qualified Leads")
    top_leads = sorted(
        leads,
        key=lambda lead: int(lead.get("score", 0) or 0),
        reverse=True,
    )[:5]
    top_leads_rows = [
        {
            "Name": str(lead.get("name", "")).strip(),
            "Company": str(lead.get("company", "")).strip(),
            "Industry": str(lead.get("industry", "")).strip(),
            "Score": int(lead.get("score", 0) or 0),
            "Category": str(lead.get("category", "")).strip(),
        }
        for lead in top_leads
    ]
    st.table(top_leads_rows)

    st.markdown("### Lead Details")
    if filtered_leads:
        selected_lead_index = st.selectbox(
            "Select a lead",
            options=list(range(len(filtered_leads))),
            format_func=lambda index: f"{filtered_leads[index]['Name']} - {filtered_leads[index]['Company']} ({filtered_leads[index]['Category']})",
        )

        selected_lead = filtered_leads[selected_lead_index]
        detail_col_1, detail_col_2 = st.columns(2)

        with detail_col_1:
            with st.container(border=True):
                st.markdown(f"**Name:** {selected_lead['Name']}")
                st.markdown(f"**Company:** {selected_lead['Company']}")
                st.markdown(f"**Industry:** {selected_lead['Industry']}")
                st.markdown(
                    f"**Company Size:** {str(next((lead.get('company_size', '') for lead in leads if str(lead.get('name', '')).strip() == selected_lead['Name'] and str(lead.get('company', '')).strip() == selected_lead['Company']), '')).strip()}"
                )
                st.markdown(f"**Budget:** {selected_lead['Budget']}")
                st.markdown(f"**Timeline:** {selected_lead['Timeline']}")
                st.markdown(f"**Score:** {selected_lead['Score']}")
                st.markdown(f"**Category:** {selected_lead['Category']}")

        with detail_col_2:
            matched_lead = next(
                (
                    lead
                    for lead in leads
                    if str(lead.get("name", "")).strip() == selected_lead["Name"]
                    and str(lead.get("company", "")).strip() == selected_lead["Company"]
                    and int(lead.get("score", 0) or 0) == selected_lead["Score"]
                    and str(lead.get("category", "")).strip() == selected_lead["Category"]
                ),
                {},
            )
            with st.container(border=True):
                st.markdown("**Requirement**")
                st.write(str(matched_lead.get("requirement", "")).strip())
                st.markdown("**Reason**")
                st.write(str(matched_lead.get("reason", "")).strip())
                st.markdown("**Next Action**")
                st.write(str(matched_lead.get("next_action", "")).strip())
                st.markdown("**Risks**")
                st.write(str(matched_lead.get("risks", "")).strip())
    else:
        st.info("No filtered leads available to show details.")


if __name__ == "__main__":
    main()
