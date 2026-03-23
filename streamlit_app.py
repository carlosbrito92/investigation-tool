import streamlit as st
import re

# Configuração da Página
st.set_page_config(page_title="Dossier Pro", layout="wide")

def validate(value, label):
    """Retorna o valor ou o aviso em negrito e caixa alta se estiver faltando."""
    if not value or str(value).strip() in ["", "None", "N/A", "-"]:
        return f"**(MISSING {label.upper()} PLEASE UPDATE)**"
    return str(value).strip()

def extract_data(text):
    # Regex Patterns aprimorados
    patterns = {
        "domain": r"(?:domain:|investigation is)\s+([a-z0-9.-]+)",
        "cnpj": r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}",
        "razao": r"Razão Social:\s+([^\n\r]+)",
        "fantasia": r"Nome Fantasia:\s+([^\n\r]+)",
        "founding_date": r"(?:Fundada em|Created on|Data de Abertura:)\s+([\d/]+|[\d-]+)",
        "location": r"(?:Município:|Cidade:|Logradouro:)\s+([^\n\r]+)",
        "activity": r"(?:CNAE principal|atividade/CNAE principal)\s+[\d\-]+\s+-\s+([^,.\n\r]+)",
        "status": r"Situação(?:\s+Cadastral)?:\s+(\w+)",
        "website": r"(?:company website:\"|Links\s+)(https?://[^\s\"]+)",
        "fb": r"https://www.facebook.com/[^\s/\"']+",
        "ig": r"https://www.instagram.com/[^\s/\"']+",
        "li": r"https://www.linkedin.com/in/[^\s/\"']+"
    }
    
    res = {}
    for key, pat in patterns.items():
        match = re.search(pat, text, re.I)
        res[key] = match.group(1) if match and match.groups() else (match.group(0) if match else None)
    return res

# --- INTERFACE ---
st.title("🕵️ Dossier Structure Tool")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Raw Data Input")
    raw_input = st.text_area("Cole os dados aqui:", height=500, placeholder="Whois, CNPJ, Redes Sociais...")

if raw_input:
    data = extract_data(raw_input)
    
    # Validação
    dom = validate(data['domain'], "Domain")
    cnpj = validate(data['cnpj'], "CNPJ")
    razao = validate(data['razao'], "Legal Name")
    fantasia = validate(data['fantasia'], "Fantasy Name")
    date = validate(data['founding_date'], "Date")
    loc = validate(data['location'], "Location")
    act = validate(data['activity'], "Activity")
    stat = validate(data['status'], "Status")
    web = validate(data['website'], "Website")
    fb = validate(data['fb'], "Facebook")
    ig = validate(data['ig'], "Instagram")
    li = validate(data['li'], "LinkedIn")

    # Descrição About
    desc = (f"{razao}, operating under the Corporate Taxpayer ID (CNPJ) {cnpj}, "
            f"was founded on {date}. The company's official registry name is {razao}. "
            f"Located in the city of {loc}, its main area of activity is {act}. "
            f"According to the Brazilian Federal Revenue, the company's current status is {stat}.")

    # Montagem do Dossier
    final_dossier = f"""**ACTIONABLE DOMAIN:**
{dom}

**LEGAL INFO/NAME OF THE COMPANY:**
CNPJ: {cnpj}
Fantasy Name [nome fantasia]: {fantasia}
Legal Name [razão social]: {razao}

**COMPANY DESCRIPTION/ABOUT:**
{desc}

**COMPANY WEBSITE:**
{web}

**CONTACT/ADDRESS INFORMATION:**
** (MISSING ADDRESS PLEASE UPDATE) **

**SOCIAL MEDIA:**
Facebook: {fb}
Instagram: {ig}
LinkedIn: {li}

**OBSERVATIONS:**
** (MISSING OBSERVATION PLEASE UPDATE) **"""

    with col2:
        st.subheader("Formatted Dossier")
        # Mostra os avisos de erro em vermelho na UI para facilitar a revisão
        missing_count = final_dossier.count("MISSING")
        if missing_count > 0:
            st.error(f"Atenção: Existem {missing_count} campos pendentes.")
        else:
            st.success("Tudo pronto!")

        st.code(final_dossier, language="markdown")

# Rodapé
st.markdown("---")
st.caption("Ferramenta Privada de Uso Interno - Sem processamento em nuvem externa.")
