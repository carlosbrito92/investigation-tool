import streamlit as st
import re

# Configuração da Página
st.set_page_config(page_title="Investigative Dossier Builder", layout="wide")

def validate(value, label):
    """Retorna o valor ou o aviso em negrito se estiver faltando."""
    if not value or str(value).strip() in ["", "None", "N/A", "-", "None"]:
        return f"**(MISSING {label.upper()} PLEASE UPDATE)**"
    return str(value).strip()

def format_phone(phone_list):
    """Adiciona +55 e formata números de telefone encontrados."""
    if not phone_list:
        return f"**(MISSING PHONE PLEASE UPDATE)**"
    formatted = []
    for p in phone_list:
        # Remove caracteres não numéricos para padronizar
        clean_p = re.sub(r"\D", "", p)
        formatted.append(f"+55 {p.strip()}")
    return " / ".join(formatted)

def extract_data(text):
    # Regex Patterns
    patterns = {
        "domain": r"(?:domain:|investigation is)\s+([a-z0-9.-]+)",
        "cnpj": r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}",
        "razao": r"Razão Social:\s+([^\n\r]+)",
        "fantasia": r"Nome Fantasia:\s+([^\n\r]+)",
        "founding_date": r"(?:Fundada em|Created on|Data de Abertura:)\s+([\d/]+|[\d-]+)",
        "location": r"(?:Município:|Cidade:)\s+([^\n\r]+)",
        "activity": r"(?:CNAE principal|atividade/CNAE principal)\s+[\d\-]+\s+-\s+([^,.\n\r]+)",
        "status": r"Situação(?:\s+Cadastral)?:\s+(\w+)",
        "address": r"(?:Endereço completo:|Logradouro:)\s+([^\n\r]+(?:-[^\n\r]+)?)",
        "emails": r"[\w\.-]+@[\w\.-]+\.\w+",
        "phones": r"\(\d{2}\)\s\d{4,5}-\d{4}",
        "fb": r"https://www.facebook.com/[^\s/\"']+",
        "ig": r"https://www.instagram.com/[^\s/\"']+",
        "li": r"https://www.linkedin.com/in/[^\s/\"']+"
    }
    
    res = {}
    for key, pat in patterns.items():
        if key in ["emails", "phones"]: # Campos que podem ter múltiplos
            res[key] = list(set(re.findall(pat, text, re.I)))
        else:
            match = re.search(pat, text, re.I)
            res[key] = match.group(1) if match and match.groups() else (match.group(0) if match else None)
    
    # Captura de Sócios (Quadro de Sócios)
    # Procura por padrões comuns em sites de CNPJ: "Sócio-Administrador: Nome"
    partners_raw = re.findall(r"(?:Sócio-Administrador|Sócio):\s+([^\n\r]+)", text)
    res["partners"] = partners_raw if partners_raw else []
    
    return res

# --- INTERFACE STREAMLIT ---
st.title("🕵️ Dossier Structure Tool")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Raw Data Input")
    raw_input = st.text_area("Paste research data:", height=500)

if raw_input:
    data = extract_data(raw_input)
    
    # Validações individuais
    dom = validate(data['domain'], "Domain")
    cnpj = validate(data['cnpj'], "CNPJ")
    razao = validate(data['razao'], "Legal Name")
    fantasia = validate(data['fantasia'], "Fantasy Name")
    date = validate(data['founding_date'], "Foundation Date")
    loc = validate(data['location'], "Location")
    act = validate(data['activity'], "Activity")
    stat = validate(data['status'], "Status")
    addr = validate(data['address'], "Address")
    
    # Telefones e Emails
    phones_str = format_phone(data['phones'])
    emails_str = " / ".join(data['emails']) if data['emails'] else f"**(MISSING EMAIL PLEASE UPDATE)**"
    
    # Redes Sociais (Filtro para remover None)
    social_links = [data['fb'], data['ig'], data['li']]
    social_str = "\n".join([link for link in social_links if link]) if any(social_links) else f"**(MISSING SOCIAL MEDIA PLEASE UPDATE)**"

    # Construção dos Sócios
    partners_block = ""
    if not data['partners']:
        partners_block = "Partner: **(MISSING PARTNER PLEASE UPDATE)**\nEmail - **(MISSING INFO)**\nSource - **(MISSING INFO)**"
    else:
        for p in data['partners']:
            partners_block += f"Partner: {p} (Sócio-Administrador)\nEmail - **(CHECK PERSONAL EMAIL)**\nSource - Receita Federal / LinkedIn\n\n"

    # Template do Dossier
    description = (f"{razao}, operating under the Corporate Taxpayer ID (CNPJ) {cnpj}, "
                   f"was founded on {date}. The company's official registry name is {razao}. "
                   f"Located in the city of {loc}, its main area of activity is {act}. "
                   f"According to the Brazilian Federal Revenue, the company's current status is {stat}.")

    final_dossier = f"""ACTIONABLE DOMAIN:
{dom}

LEGAL INFO/NAME OF THE COMPANY:
CNPJ: {cnpj}
Fantasy Name: {fantasia}
Legal Name: {razao}

COMPANY DESCRIPTION/ABOUT:
{description}

COMPANY WEBSITE: 

CONTACT/ADDRESS INFORMATION:
Address: {addr} (Source: Federal Revenue)
Phone: {phones_str}
Email: {emails_str} (Source: Official Records)

KEY PERSONNEL:
{partners_block}
SOCIAL MEDIA:
{social_str}

OBSERVATIONS:
"""

    with col2:
        st.subheader("Final Structured Dossier")
        st.code(final_dossier, language="markdown")
        st.info("Copy the text using the icon in the top-right of the box above.")
