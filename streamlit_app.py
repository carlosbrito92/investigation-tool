import streamlit as st
import re

# Configuração da Página
st.set_page_config(page_title="Gerador de Dossier Profissional", layout="centered")

def validate(value, label):
    """Retorna o valor ou o aviso em negrito e caixa alta se estiver faltando."""
    if not value or str(value).strip() in ["", "None", "N/A"]:
        return f"**(MISSING {label.upper()} PLEASE UPDATE)**"
    return str(value).strip()

def extract_data(text):
    # Regex Patterns ajustados para os seus exemplos (Whois, CNPJ, Redes Sociais)
    patterns = {
        "domain": r"(?:domain:|investigation is)\s+([a-z0-9.-]+)",
        "cnpj": r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}",
        "razao": r"Razão Social:\s+([^\n\r]+)",
        "founding_date": r"(?:Fundada em|Created on)\s+([\d/]+|[\d-]+)",
        "location": r"(?:Município:|Cidade:)\s+([^\n\r]+)",
        "activity": r"(?:CNAE principal|atividade/CNAE principal)\s+[\d\-]+\s+-\s+([^,.\n\r]+)",
        "status": r"Situação(?:\s+Cadastral)?:\s+(\w+)",
        "website": r"company website:\"(https?://[^\s\"]+)",
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
st.title("🕵️ Ferramenta de Estruturação de Dossier")
st.markdown("Cole os dados brutos abaixo para gerar o relatório formatado.")

raw_input = st.text_area("Dados Brutos (Whois, LinkedIn, CNPJ, etc):", height=300)

if raw_input:
    data = extract_data(raw_input)
    
    # Validação de cada campo
    dom = validate(data['domain'], "Domain")
    cnpj = validate(data['cnpj'], "CNPJ")
    name = validate(data['razao'], "Company Name")
    date = validate(data['founding_date'], "Foundation Date")
    loc = validate(data['location'], "Location")
    act = validate(data['activity'], "Main Activity")
    stat = validate(data['status'], "Current Status")
    web = validate(data['website'], "Website")
    fb = validate(data['fb'], "Facebook")
    ig = validate(data['ig'], "Instagram")
    li = validate(data['li'], "LinkedIn")

    # Construção da descrição (About) com a estrutura solicitada
    # Usamos f-strings para manter as quebras de linha naturais
    desc = (f"{name}, operating under the Corporate Taxpayer ID (CNPJ) {cnpj}, "
            f"was founded on {date}. The company's official registry name is {name}. "
            f"Located in the city of {loc}, its main area of activity is {act}. "
            f"According to the Brazilian Federal Revenue, the company's current status is {stat}.")

    # Montagem do Dossier Final com espaçamento visual (Double Newline)
    final_dossier = f"""**ACTIONABLE DOMAIN:**
{dom}

**LEGAL INFO/NAME OF THE COMPANY:**
CNPJ {cnpj} - {name}

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

    st.markdown("---")
    st.subheader("Resultado Estruturado")
    
    # O componente st.code cria uma caixa que mantém a formatação 
    # e oferece um botão "Copy" nativo no canto superior direito.
    st.code(final_dossier, language="markdown")
    
    st.info("💡 Clique no ícone de copiar no canto superior direito do bloco acima.")
