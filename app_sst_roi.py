import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import io

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ROI Prévention SST",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

h1, h2, h3 { font-family: 'DM Serif Display', serif; }

.main { background: #0f1117; }

.stApp {
    background: linear-gradient(135deg, #0f1117 0%, #1a1f2e 100%);
}

.metric-card {
    background: linear-gradient(135deg, #1e2535 0%, #252d40 100%);
    border: 1px solid #2e3a55;
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    margin: 8px 0;
}
.metric-card .label {
    font-size: 12px;
    color: #7a8aaa;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 8px;
}
.metric-card .value {
    font-family: 'DM Serif Display', serif;
    font-size: 2.2rem;
    color: #f0f4ff;
    line-height: 1;
}
.metric-card .unit {
    font-size: 13px;
    color: #4ade80;
    margin-top: 6px;
}

.section-header {
    background: linear-gradient(90deg, #1a3a5c 0%, transparent 100%);
    border-left: 4px solid #3b82f6;
    padding: 12px 20px;
    border-radius: 0 12px 12px 0;
    margin: 28px 0 18px 0;
}
.section-header h3 {
    color: #e0eaff;
    margin: 0;
    font-size: 1.1rem;
}

.insight-box {
    background: linear-gradient(135deg, #0f2a1a 0%, #1a3a25 100%);
    border: 1px solid #2d6a4f;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 12px 0;
    color: #a7f3d0;
    font-size: 0.9rem;
    line-height: 1.6;
}
.insight-box .icon { font-size: 1.2rem; margin-right: 8px; }

.warning-box {
    background: linear-gradient(135deg, #2a1f0f 0%, #3a2a1a 100%);
    border: 1px solid #d97706;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 12px 0;
    color: #fcd34d;
    font-size: 0.9rem;
}

.hero-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2.8rem;
    color: #f0f4ff;
    line-height: 1.2;
    margin-bottom: 8px;
}
.hero-sub {
    color: #7a8aaa;
    font-size: 1rem;
    margin-bottom: 32px;
}

div[data-testid="stSidebar"] {
    background: #13192a !important;
    border-right: 1px solid #1e2a3f;
}

.stSlider > div > div { background: #1e2535 !important; }
label { color: #c0ccdd !important; }

.stSelectbox > div > div {
    background: #1e2535 !important;
    border-color: #2e3a55 !important;
    color: #e0eaff !important;
}

.formula-box {
    background: #0a0f1a;
    border: 1px solid #1e2a3f;
    border-radius: 10px;
    padding: 16px 20px;
    font-family: 'Courier New', monospace;
    color: #7dd3fc;
    font-size: 0.9rem;
    margin: 12px 0;
}

.tab-content { padding: 20px 0; }
</style>
""", unsafe_allow_html=True)

# ── DATA & CONSTANTS ──────────────────────────────────────────────────────────

SECTEURS = {
    "Bâtiment & Construction": {
        "taux_sinistralite": 0.058,     # accidents / salarié / an
        "cout_moyen_accident": 35000,   # € coût total moyen
        "multiplicateur": 4.2,          # coût indirect / coût direct
        "roi_moyen": 2.8,
        "color": "#f97316",
        "absenteisme_base": 0.072,
    },
    "Industrie Manufacturière": {
        "taux_sinistralite": 0.041,
        "cout_moyen_accident": 28000,
        "multiplicateur": 3.8,
        "roi_moyen": 3.1,
        "color": "#3b82f6",
        "absenteisme_base": 0.055,
    },
    "Chimie & Pétrochimie": {
        "taux_sinistralite": 0.023,
        "cout_moyen_accident": 52000,
        "multiplicateur": 5.1,
        "roi_moyen": 4.2,
        "color": "#8b5cf6",
        "absenteisme_base": 0.038,
    },
    "Logistique & Transport": {
        "taux_sinistralite": 0.049,
        "cout_moyen_accident": 31000,
        "multiplicateur": 3.5,
        "roi_moyen": 2.6,
        "color": "#06b6d4",
        "absenteisme_base": 0.068,
    },
    "Agroalimentaire": {
        "taux_sinistralite": 0.035,
        "cout_moyen_accident": 22000,
        "multiplicateur": 3.2,
        "roi_moyen": 2.9,
        "color": "#10b981",
        "absenteisme_base": 0.048,
    },
    "Santé & Social": {
        "taux_sinistralite": 0.044,
        "cout_moyen_accident": 19000,
        "multiplicateur": 2.9,
        "roi_moyen": 2.4,
        "color": "#ec4899",
        "absenteisme_base": 0.082,
    },
}

TAILLES = {
    "TPE (< 10 salariés)":    {"capacite_invest": 0.008, "economies_scale": 0.7,  "label": "TPE"},
    "PE (10–49 salariés)":    {"capacite_invest": 0.012, "economies_scale": 0.85, "label": "PE"},
    "PME (50–249 salariés)":  {"capacite_invest": 0.018, "economies_scale": 1.0,  "label": "PME"},
    "ETI (250–999 salariés)": {"capacite_invest": 0.025, "economies_scale": 1.18, "label": "ETI"},
    "GE (≥ 1000 salariés)":   {"capacite_invest": 0.035, "economies_scale": 1.35, "label": "GE"},
}

ACTIONS = {
    "Formation & sensibilisation":        {"cout_par_sal": 350,  "efficacite": 0.22, "horizon": 2},
    "EPI & équipements de protection":    {"cout_par_sal": 520,  "efficacite": 0.28, "horizon": 3},
    "Ergonomie & aménagement des postes": {"cout_par_sal": 1800, "efficacite": 0.35, "horizon": 5},
    "Systèmes de détection / alarme":     {"cout_par_sal": 900,  "efficacite": 0.18, "horizon": 7},
    "Programme de bien-être / TMS":       {"cout_par_sal": 450,  "efficacite": 0.25, "horizon": 3},
    "Audit & certification ISO 45001":    {"cout_par_sal": 2500, "efficacite": 0.40, "horizon": 4},
}

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Paramètres")
    st.markdown("---")

    secteur_nom = st.selectbox("🏭 Secteur industriel", list(SECTEURS.keys()))
    taille_nom  = st.selectbox("🏢 Taille d'entreprise", list(TAILLES.keys()))

    st.markdown("---")
    nb_salaries = st.slider("👷 Nombre de salariés", 5, 2000, 80, step=5)
    salaire_moy = st.slider("💶 Salaire moyen annuel (€)", 20000, 65000, 32000, step=1000)
    budget_prev = st.slider("💰 Budget prévention (€/an)", 1000, 500000, 25000, step=1000)

    st.markdown("---")
    st.markdown("**🎯 Actions de prévention**")
    actions_sel = st.multiselect(
        "Sélectionner les actions",
        list(ACTIONS.keys()),
        default=["Formation & sensibilisation", "EPI & équipements de protection"],
    )

    st.markdown("---")
    horizon_ans = st.slider("📅 Horizon d'analyse (années)", 1, 10, 5)
    taux_actualisation = st.slider("📈 Taux d'actualisation (%)", 2, 10, 5) / 100

# ── CALCULS ───────────────────────────────────────────────────────────────────
s = SECTEURS[secteur_nom]
t = TAILLES[taille_nom]

# Accidents attendus sans prévention
accidents_annuels = nb_salaries * s["taux_sinistralite"]
cout_direct_annuel = accidents_annuels * s["cout_moyen_accident"]
cout_indirect_annuel = cout_direct_annuel * s["multiplicateur"]
cout_total_annuel = cout_direct_annuel + cout_indirect_annuel

# Efficacité combinée des actions
if actions_sel:
    efficacite_combinee = 1 - np.prod([1 - ACTIONS[a]["efficacite"] for a in actions_sel])
    efficacite_combinee = min(efficacite_combinee * t["economies_scale"], 0.75)
else:
    efficacite_combinee = 0.0

economies_annuelles = cout_total_annuel * efficacite_combinee
# Absentéisme
reduction_absenteisme = nb_salaries * salaire_moy * s["absenteisme_base"] * efficacite_combinee * 0.5
benefices_totaux_annuels = economies_annuelles + reduction_absenteisme

# ROI simple
roi_simple = ((benefices_totaux_annuels - budget_prev) / budget_prev * 100) if budget_prev > 0 else 0

# VAN sur horizon
cash_flows = []
for annee in range(1, horizon_ans + 1):
    montee_efficacite = min(1.0, 0.6 + 0.1 * annee)
    cf = benefices_totaux_annuels * montee_efficacite - budget_prev
    cf_actualise = cf / (1 + taux_actualisation) ** annee
    cash_flows.append(cf_actualise)

van = sum(cash_flows)
# Délai de récupération
cumul = 0
delai_recuperation = None
for i, cf in enumerate(cash_flows):
    cumul += cf
    if cumul >= 0 and delai_recuperation is None:
        delai_recuperation = i + 1

# Seuil de rentabilité
seuil = benefices_totaux_annuels / (1 + s["roi_moyen"]) if s["roi_moyen"] > 0 else budget_prev

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-title">🛡️ Modélisation ROI — Prévention SST</div>
<div class="hero-sub">Sujet 2 · Retour sur investissement de la prévention santé-sécurité au travail selon le secteur et la taille d'entreprise</div>
""", unsafe_allow_html=True)

# ── MÉTRIQUES CLÉS ────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)

def metric_card(col, label, value, unit="", color="#4ade80"):
    col.markdown(f"""
    <div class="metric-card">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
        <div class="unit" style="color:{color}">{unit}</div>
    </div>""", unsafe_allow_html=True)

metric_card(c1, "ROI Simple", f"{roi_simple:+.0f}%", "retour sur investissement", "#4ade80" if roi_simple > 0 else "#f87171")
metric_card(c2, "VAN", f"{van/1000:+.0f}k€", f"sur {horizon_ans} ans", "#60a5fa")
metric_card(c3, "Économies annuelles", f"{economies_annuelles/1000:.0f}k€", "accidents évités", "#a78bfa")
metric_card(c4, "Coût total risque", f"{cout_total_annuel/1000:.0f}k€", "sans prévention / an", "#fb923c")
metric_card(c5, "Récupération", f"{delai_recuperation or '>'+str(horizon_ans)} an{'s' if delai_recuperation and delai_recuperation > 1 else ''}", "délai de retour", "#34d399")

st.markdown("<br>", unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 ROI & Cash Flows",
    "💸 Modèle de Coût",
    "📈 Seuil de Rentabilité",
    "🏭 Benchmark Sectoriel",
    "📋 Rapport & Formules",
])

# ═══════════════════════════════════════════════════════════════
# TAB 1 — ROI & Cash Flows
# ═══════════════════════════════════════════════════════════════
with tab1:
    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.markdown('<div class="section-header"><h3>Évolution des Cash Flows actualisés</h3></div>', unsafe_allow_html=True)

        annees = list(range(1, horizon_ans + 1))
        cumuls = np.cumsum(cash_flows)

        fig = go.Figure()
        colors_bar = ["#4ade80" if cf >= 0 else "#f87171" for cf in cash_flows]
        fig.add_trace(go.Bar(
            x=annees, y=cash_flows,
            name="CF annuel actualisé",
            marker_color=colors_bar,
            marker_line_width=0,
            opacity=0.85,
        ))
        fig.add_trace(go.Scatter(
            x=annees, y=cumuls,
            name="VAN cumulée",
            line=dict(color="#60a5fa", width=3),
            mode="lines+markers",
            marker=dict(size=8, color="#60a5fa"),
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="#475569", line_width=1.5)
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c0ccdd", family="DM Sans"),
            legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1e2a3f"),
            xaxis=dict(gridcolor="#1e2a3f", title="Année"),
            yaxis=dict(gridcolor="#1e2a3f", title="€"),
            height=360,
            margin=dict(l=0, r=0, t=20, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown('<div class="section-header"><h3>Décomposition des bénéfices</h3></div>', unsafe_allow_html=True)

        labels = ["Économies\naccidents", "Réduction\nabsentéisme", "Budget\nprévention"]
        vals   = [economies_annuelles, reduction_absenteisme, -budget_prev]
        colors_wf = ["#4ade80", "#34d399", "#f87171"]

        fig2 = go.Figure(go.Waterfall(
            orientation="v",
            measure=["relative", "relative", "relative"],
            x=labels,
            y=vals,
            connector=dict(line=dict(color="#2e3a55", width=1.5)),
            increasing=dict(marker_color="#4ade80"),
            decreasing=dict(marker_color="#f87171"),
            text=[f"{v/1000:+.1f}k€" for v in vals],
            textposition="outside",
            textfont=dict(color="#e0eaff"),
        ))
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c0ccdd", family="DM Sans"),
            xaxis=dict(gridcolor="#1e2a3f"),
            yaxis=dict(gridcolor="#1e2a3f", title="€/an"),
            height=360,
            margin=dict(l=0, r=0, t=20, b=0),
            showlegend=False,
        )
        st.plotly_chart(fig2, use_container_width=True)

    if roi_simple > 100:
        st.markdown(f'<div class="insight-box"><span class="icon">✅</span> Excellent ROI de <strong>{roi_simple:.0f}%</strong> — chaque euro investi rapporte <strong>{roi_simple/100:.1f}€</strong>. Ce résultat est cohérent avec les études BIT qui montrent un retour moyen de 2,2€ par euro investi dans la prévention SST.</div>', unsafe_allow_html=True)
    elif roi_simple > 0:
        st.markdown(f'<div class="insight-box"><span class="icon">📈</span> ROI positif de <strong>{roi_simple:.0f}%</strong>. Les actions de prévention sont rentables mais leur optimisation peut améliorer ce résultat.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="warning-box">⚠️ ROI négatif ({roi_simple:.0f}%). Révisez la combinaison d\'actions ou le budget pour atteindre la rentabilité.</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# TAB 2 — Modèle de Coût
# ═══════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header"><h3>Modèle de Coût Total des Accidents (iceberg)</h3></div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 3])

    with col1:
        # Composantes coûts directs
        cout_soins        = cout_direct_annuel * 0.45
        cout_indemnites   = cout_direct_annuel * 0.35
        cout_cotisations  = cout_direct_annuel * 0.20

        # Composantes coûts indirects
        cout_remplacement = cout_indirect_annuel * 0.30
        cout_productivite = cout_indirect_annuel * 0.28
        cout_admin        = cout_indirect_annuel * 0.18
        cout_image        = cout_indirect_annuel * 0.14
        cout_enquete      = cout_indirect_annuel * 0.10

        data_cout = pd.DataFrame({
            "Composante": [
                "🏥 Soins médicaux", "📄 Indemnités journalières", "📊 Surcotisations AT",
                "👤 Remplacement/formation", "📉 Perte productivité", "🗂️ Coûts administratifs",
                "📢 Atteinte image/moral", "🔍 Enquête & réorganisation"
            ],
            "Montant (€/an)": [
                cout_soins, cout_indemnites, cout_cotisations,
                cout_remplacement, cout_productivite, cout_admin,
                cout_image, cout_enquete
            ],
            "Type": ["Direct"]*3 + ["Indirect"]*5
        })
        data_cout["Montant (€/an)"] = data_cout["Montant (€/an)"].round(0).astype(int)
        st.dataframe(
            data_cout.style.apply(
                lambda x: ["background-color: #1a2f1a; color: #4ade80" if v == "Direct"
                           else "background-color: #1a1a2f; color: #a78bfa" for v in x],
                subset=["Type"]
            ),
            use_container_width=True, hide_index=True,
        )

        st.markdown(f"""
        <div class="metric-card" style="margin-top:16px;">
            <div class="label">Coûts Directs</div>
            <div class="value">{cout_direct_annuel/1000:.0f}k€</div>
            <div class="unit" style="color:#4ade80">visibles / assurables</div>
        </div>
        <div class="metric-card">
            <div class="label">Coûts Indirects ×{s['multiplicateur']}</div>
            <div class="value">{cout_indirect_annuel/1000:.0f}k€</div>
            <div class="unit" style="color:#f87171">cachés / non assurés</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Iceberg chart
        fig3 = go.Figure()

        # Base (indirects) — sous la ligne
        fig3.add_trace(go.Bar(
            x=["Coûts Indirects\n(cachés)"],
            y=[cout_indirect_annuel],
            name="Coûts Indirects",
            marker_color="#7c3aed",
            marker_line_width=0,
            width=0.5,
        ))
        fig3.add_trace(go.Bar(
            x=["Coûts Directs\n(visibles)"],
            y=[cout_direct_annuel],
            name="Coûts Directs",
            marker_color="#059669",
            marker_line_width=0,
            width=0.5,
        ))

        # Donut — répartition
        fig3b = go.Figure(go.Pie(
            labels=["Soins médicaux", "Indemnités", "Surcotisations",
                    "Remplacement", "Productivité", "Administratif", "Image", "Enquête"],
            values=[cout_soins, cout_indemnites, cout_cotisations,
                    cout_remplacement, cout_productivite, cout_admin, cout_image, cout_enquete],
            hole=0.55,
            marker_colors=["#4ade80","#34d399","#6ee7b7","#818cf8","#a78bfa","#c4b5fd","#e879f9","#f0abfc"],
            textinfo="label+percent",
            textfont=dict(size=10, color="#e0eaff"),
        ))
        fig3b.add_annotation(
            text=f"<b>{cout_total_annuel/1000:.0f}k€</b><br>total/an",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#e0eaff", family="DM Serif Display"),
        )
        fig3b.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c0ccdd", family="DM Sans"),
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
            height=380,
            margin=dict(l=0, r=0, t=20, b=0),
            title=dict(text="Répartition des coûts totaux", font=dict(color="#c0ccdd"), x=0.5),
        )
        st.plotly_chart(fig3b, use_container_width=True)

    st.markdown(f'<div class="insight-box"><span class="icon">🧊</span><strong>Effet iceberg :</strong> Pour {secteur_nom}, le multiplicateur indirect/direct est de <strong>×{s["multiplicateur"]}</strong>. Soit pour chaque €1 de coût direct visible, <strong>€{s["multiplicateur"]:.1f} de coûts cachés</strong> (perte de productivité, turnover, démotivation des équipes, impact image).</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# TAB 3 — Seuil de Rentabilité
# ═══════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header"><h3>Analyse du Seuil de Rentabilité SST</h3></div>', unsafe_allow_html=True)

    col_a, col_b = st.columns([3, 2])

    with col_a:
        budgets = np.linspace(0, cout_total_annuel * 0.8, 300)
        benefices_courbe = [
            (cout_total_annuel * min(b / (b + 5000) * 0.85 * t["economies_scale"], 0.75) + reduction_absenteisme)
            for b in budgets
        ]
        rois_courbe = [(b - budgets[i]) / budgets[i] * 100 if budgets[i] > 0 else 0
                       for i, b in enumerate(benefices_courbe)]

        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(
            x=budgets/1000, y=[b/1000 for b in benefices_courbe],
            name="Bénéfices (€k)", line=dict(color="#4ade80", width=3),
            fill="tozeroy", fillcolor="rgba(74,222,128,0.08)",
        ))
        fig4.add_trace(go.Scatter(
            x=budgets/1000, y=budgets/1000,
            name="Coût du programme", line=dict(color="#f87171", width=2, dash="dash"),
        ))
        # Point actuel
        ben_actuel = benefices_totaux_annuels
        fig4.add_trace(go.Scatter(
            x=[budget_prev/1000], y=[ben_actuel/1000],
            name="Votre situation",
            mode="markers",
            marker=dict(size=14, color="#fbbf24", symbol="star", line=dict(color="#fff", width=1)),
        ))
        # Zone rentable
        idx_seuil = next((i for i, (b, c) in enumerate(zip(benefices_courbe, budgets)) if b > c), None)
        if idx_seuil:
            fig4.add_vline(
                x=budgets[idx_seuil]/1000,
                line_dash="dot", line_color="#fbbf24", line_width=1.5,
                annotation_text=f"Seuil ≈ {budgets[idx_seuil]/1000:.0f}k€",
                annotation_font_color="#fbbf24",
            )

        fig4.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c0ccdd", family="DM Sans"),
            legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1e2a3f"),
            xaxis=dict(gridcolor="#1e2a3f", title="Budget prévention (k€)"),
            yaxis=dict(gridcolor="#1e2a3f", title="Montant (k€)"),
            height=380,
            margin=dict(l=0, r=0, t=20, b=0),
        )
        st.plotly_chart(fig4, use_container_width=True)

    with col_b:
        st.markdown('<div class="section-header"><h3>ROI par niveau d\'investissement</h3></div>', unsafe_allow_html=True)

        niveaux = {
            "Minimal (0.5% MS)": nb_salaries * salaire_moy * 0.005,
            "Standard (1%)":     nb_salaries * salaire_moy * 0.010,
            "Recommandé (2%)":   nb_salaries * salaire_moy * 0.020,
            "Intensif (3%)":     nb_salaries * salaire_moy * 0.030,
        }

        rois_niv = []
        for nom, b in niveaux.items():
            efficacite_niv = min(b / (b + 8000) * 0.85 * t["economies_scale"], 0.72)
            eco = cout_total_annuel * efficacite_niv + reduction_absenteisme * efficacite_niv
            r = (eco - b) / b * 100 if b > 0 else 0
            rois_niv.append({"Niveau": nom, "Budget (€)": round(b), "ROI (%)": round(r, 1), "Éco. annuelles (€)": round(eco)})

        df_niv = pd.DataFrame(rois_niv)
        st.dataframe(
            df_niv.style.background_gradient(subset=["ROI (%)"], cmap="RdYlGn"),
            use_container_width=True, hide_index=True,
        )

        # Budget optimal estimé
        budget_optimal = nb_salaries * salaire_moy * 0.018 * t["economies_scale"]
        st.markdown(f"""
        <div class="metric-card" style="margin-top:16px;">
            <div class="label">Budget optimal estimé</div>
            <div class="value">{budget_optimal/1000:.0f}k€/an</div>
            <div class="unit">≈ {budget_optimal/nb_salaries:.0f}€ par salarié</div>
        </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# TAB 4 — Benchmark Sectoriel
# ═══════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header"><h3>Comparaison Sectorielle & par Taille d\'Entreprise</h3></div>', unsafe_allow_html=True)

    # Radar chart — secteurs
    categories = ["ROI moyen", "Taux sinistralité\n(inversé)", "Coût accident\n(€k)", "Multiplicateur\nindirect"]

    fig5 = go.Figure()
    for nom, data in SECTEURS.items():
        vals_radar = [
            data["roi_moyen"] / 5,
            1 - data["taux_sinistralite"] / 0.06,
            data["cout_moyen_accident"] / 60000,
            data["multiplicateur"] / 6,
        ]
        vals_radar += [vals_radar[0]]  # fermer le polygone
        categories_closed = categories + [categories[0]]

        fig5.add_trace(go.Scatterpolar(
            r=vals_radar,
            theta=categories_closed,
            name=nom,
            line=dict(color=data["color"], width=2),
            fill="toself",
            fillcolor=data["color"] + "22",
        ))

    fig5.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 1], gridcolor="#1e2a3f", tickfont=dict(color="#7a8aaa")),
            angularaxis=dict(gridcolor="#1e2a3f", tickfont=dict(color="#c0ccdd", size=11)),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#c0ccdd", family="DM Sans"),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1e2a3f", font=dict(size=10)),
        height=420,
        margin=dict(l=40, r=40, t=30, b=20),
        title=dict(text="Profil de risque & ROI par secteur", font=dict(color="#c0ccdd"), x=0.5),
    )
    st.plotly_chart(fig5, use_container_width=True)

    # Bar chart — ROI par taille
    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown('<div class="section-header"><h3>ROI selon la taille d\'entreprise</h3></div>', unsafe_allow_html=True)
        tailles_labels = [v["label"] for v in TAILLES.values()]
        roi_par_taille = [s["roi_moyen"] * v["economies_scale"] for v in TAILLES.values()]

        fig6 = go.Figure(go.Bar(
            x=tailles_labels,
            y=roi_par_taille,
            marker_color=["#f97316","#fbbf24","#4ade80","#34d399","#10b981"],
            text=[f"×{r:.1f}" for r in roi_par_taille],
            textposition="outside",
            textfont=dict(color="#e0eaff"),
        ))
        fig6.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c0ccdd", family="DM Sans"),
            xaxis=dict(gridcolor="#1e2a3f"),
            yaxis=dict(gridcolor="#1e2a3f", title="ROI moyen (multiplicateur)"),
            height=300,
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=False,
        )
        st.plotly_chart(fig6, use_container_width=True)
        st.markdown('<div class="insight-box"><span class="icon">📊</span>Les <strong>grandes entreprises</strong> bénéficient d\'économies d\'échelle en SST (+35% de ROI vs TPE), mais les <strong>TPE/PME</strong> ont proportionnellement plus à gagner car leur sinistralité relative est plus élevée.</div>', unsafe_allow_html=True)

    with col_d:
        st.markdown('<div class="section-header"><h3>Coût annuel du risque par secteur</h3></div>', unsafe_allow_html=True)
        sect_noms = list(SECTEURS.keys())
        cout_risques = [SECTEURS[s_n]["taux_sinistralite"] * SECTEURS[s_n]["cout_moyen_accident"] * (1 + SECTEURS[s_n]["multiplicateur"]) * 100
                        for s_n in sect_noms]  # pour 100 salariés

        fig7 = go.Figure(go.Bar(
            x=sect_noms,
            y=cout_risques,
            orientation="v",
            marker_color=[SECTEURS[s_n]["color"] for s_n in sect_noms],
            text=[f"{c/1000:.0f}k€" for c in cout_risques],
            textposition="outside",
            textfont=dict(color="#e0eaff", size=10),
        ))
        fig7.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#c0ccdd", family="DM Sans", size=10),
            xaxis=dict(gridcolor="#1e2a3f", tickangle=-30),
            yaxis=dict(gridcolor="#1e2a3f", title="Coût total risque (€/100 sal.)"),
            height=300,
            margin=dict(l=0, r=0, t=30, b=60),
            showlegend=False,
        )
        st.plotly_chart(fig7, use_container_width=True)

# ═══════════════════════════════════════════════════════════════
# TAB 5 — Rapport & Formules
# ═══════════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-header"><h3>Cadre Méthodologique & Formules</h3></div>', unsafe_allow_html=True)

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.markdown("#### 📐 Formules utilisées")
        st.markdown("""
        <div class="formula-box">
        ROI (%) = [(Bénéfices - Coûts) / Coûts] × 100
        </div>
        <div class="formula-box">
        Coût Total = Coûts Directs × (1 + Multiplicateur)
        </div>
        <div class="formula-box">
        VAN = Σ [ CF_t / (1 + r)^t ]  pour t = 1..N
        </div>
        <div class="formula-box">
        Efficacité combinée = 1 − Π(1 − e_i) × K_taille
        </div>
        <div class="formula-box">
        Budget optimal ≈ MS × 1,8% × K_taille
        </div>
        """, unsafe_allow_html=True)

    with col_f2:
        st.markdown("#### 📚 Références scientifiques")
        st.markdown("""
        - **BIT (2019)** — *The return on prevention: Calculating the costs and benefits of investments in occupational safety and health* — ROI moyen global : **2,2€ par €1 investi**
        - **INRS (2023)** — Coûts des accidents du travail en France — multiplicateur indirect moyen : **×3 à ×5**
        - **HSE UK** — *Cost-benefit framework for safety interventions* — seuil de rentabilité dès 0,8% de la masse salariale
        - **EUOSHA (2022)** — *Healthy Workplaces Campaign* — réduction absentéisme : 25-50% avec programme structuré
        - **ISO 45001:2018** — Référentiel international SMSST
        """)

    st.markdown('<div class="section-header"><h3>Rapport de Synthèse</h3></div>', unsafe_allow_html=True)

    rapport_md = f"""
## 🛡️ Rapport ROI Prévention SST

**Entreprise analysée :** {taille_nom} — {secteur_nom}
**Nombre de salariés :** {nb_salaries} | **Salaire moyen :** {salaire_moy:,}€

---

### 1. Exposition au Risque

| Indicateur | Valeur |
|---|---|
| Taux de sinistralité sectoriel | {s['taux_sinistralite']*100:.1f}% |
| Accidents attendus / an | {accidents_annuels:.1f} |
| Coût direct annuel | {cout_direct_annuel:,.0f}€ |
| Coût indirect annuel (×{s['multiplicateur']}) | {cout_indirect_annuel:,.0f}€ |
| **Coût total annuel du risque** | **{cout_total_annuel:,.0f}€** |

### 2. Programme de Prévention

Actions sélectionnées : {', '.join(actions_sel) if actions_sel else 'Aucune'}
Budget annuel : **{budget_prev:,}€** ({budget_prev/nb_salaries:.0f}€/salarié)
Efficacité estimée : **{efficacite_combinee*100:.1f}%** de réduction du risque

### 3. Résultats Financiers

| Indicateur | Valeur |
|---|---|
| Économies accidents | {economies_annuelles:,.0f}€/an |
| Réduction absentéisme | {reduction_absenteisme:,.0f}€/an |
| **ROI Simple** | **{roi_simple:+.0f}%** |
| VAN sur {horizon_ans} ans | {van:,.0f}€ |
| Délai de récupération | {delai_recuperation or ">"+str(horizon_ans)} an(s) |

### 4. Recommandation

{"✅ Investissement rentable : poursuivre et intensifier le programme." if roi_simple > 0 else "⚠️ Programme insuffisant : augmenter le budget ou réorienter les actions."}
Budget optimal recommandé : **{nb_salaries * salaire_moy * 0.018 * t['economies_scale']:,.0f}€/an**
"""

    st.markdown(rapport_md)

    # Téléchargement
    st.download_button(
        label="📥 Télécharger le rapport (.md)",
        data=rapport_md,
        file_name="rapport_roi_sst.md",
        mime="text/markdown",
        use_container_width=True,
    )

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div style="text-align:center; color:#475569; font-size:0.8rem;">Modèle basé sur les données BIT · INRS · EUOSHA · HSE UK — Projet SMSST Sujet 2</div>',
    unsafe_allow_html=True,
)
