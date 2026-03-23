import streamlit as st
import re

# Configuração da Página
st.set_page_config(page_title="Dossier Pro: Multi-Source", layout="wide")

def validate(value, label):
    """Retorna o valor ou o aviso em negrito se estiver faltando."""
    if not value or str(value).strip() in ["", "None", "N/A", "-", "None"]:
        return f"**(MISSING {label.upper()} PLEASE UPDATE)**"
    return str(value).strip()

def format_phone(phone_list):
    """Adiciona +55 a todos os números encontrados."""
    if not phone_list:
        return f"**(MISSING PHONE PLEASE UPDATE)**"
    unique_phones = list(set(phone_list))
    return " / ".join([f"+55 {p.strip()}" for p in unique_phones])

def extract_by_source(text):
    res = {}
    
    # --- SOURCE 1: INFORME CADASTRAL ---
    if "informecadastral.com.br" in text.lower():
        st.sidebar.success("Source: Informe Cadastral")
        res["source_name"] = "Informe Cadastral"
        res["cnpj"] = re.search(r"CNPJ:\s+(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", text)
        res["razao"] = re.search(r"Razão Social:\s+([^\n\r]+)", text)
        res["fantasia"] = re.search(r"Nome Fantasia:\s+([^\n\r]+)", text)
        res["founding_date"] = re.search(r"Data de Abertura:\s+([\d/]+)", text)
        res["status"] = re.search(r"Situação Cadastral:\s+(\w+)", text)
        res["location"] = re.search(r"Município:\s+([^\n\r]+)", text)
        res["activity"] = re.search(r"Atividade Principal:\s+[\d\.-]+\s+-\s+([^,.\n\r]+)", text)
        res["address"] = re.search(r"Logradouro:\s+([^\n\r]+)", text)
        res["partners"] = re.findall(r"Sócio-Administrador\s+([A-Z\s]{5,})", text)

    # --- SOURCE 2: CADASTRO EMPRESA ---
    elif "cadastroempresa.com.br" in text.lower():
        st.sidebar.success("Source: Cadastro Empresa")
        res["source_name"] = "Cadastro Empresa"
        res["cnpj"] = re.search(r"CNPJ:\s+(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", text)
        res["razao"] = re.search(r"Razão Social:\s+([^\n\r]+)", text)
        res["fantasia"] = re.search(r"Nome Fantasia:\s+([^\n\r]+)", text)
        res["founding_date"] = re.search(r"Data de Abertura:\s+([\d/]+)", text)
        res["status"] = re.search(r"Situação:\s+(\w+)", text)
        res["location"] = re.search(r"Município:\s+([^\n\r]+)", text)
        res["activity"] = re.search(r"CNAE/Atividade Principal:\s+[\d\-]+\s+-\s+([^,.\n\r]+)", text)
        res["address"] = re.search(r"Endereço completo:\s+([^\n\r]+)", text)
        res["partners"] = re.findall(r"(?:Sócio-Administrador|Sócio):\s+([^\n\r]+)", text)

    # --- FALLBACK: GENERAL REGEX ---
    else:
        st.sidebar.warning("Source: General/Unknown")
        res["source_name"] = "General Source"
        res["cnpj"] = re.search(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", text)
        res["razao"] = re.search(r"(?:Razão Social|owner):\s+([^\n\r]+)", text, re.I)
        res["fantasia"] = re.search(r"Nome Fantasia:\s+([^\n\r]+)", text, re.I)
        res["founding_date"] = re.search(r"(?:Fundada em|Abertura|created):\s+([\d/]+|[\d]{8})", text, re.I)
        res["status"] = re.search(r"Situação:\s+(\w+)", text, re.I)
        res["location"] = re.search(r"(?:Município|Cidade):\s+([^\n\r]+)", text, re.I)
        res["activity"] = re.search(r"(?:CNAE|Atividade):\s+([^\n\r]+)", text, re.I)
        res["address"] = re.search(r"(?:Logradouro|Address):\s+([^\n\r]+)", text, re.I)
        res["partners"] = re.findall(r"(?:Sócio|Administrador):\s+([^\n\r]+)", text, re.I)

    # --- GLOBAL EXTRACTIONS ---
    res["domain"] = re.search(r"(?:domain:|investigation is)\s+([a-z0-9.-]+)", text, re.I)
    res["emails"] = list(set(re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", text)))
    res["phones"] = list(set(re.findall(r"\(\d{2}\)\s\d{4,5}-\d{4}", text)))
    res["fb"] = re.search(r"https://www.facebook.com/[^\s/\"']+", text)
    res["ig"] = re.search(r"https://www.instagram.com/[^\s/\"']+", text)
    res["li"] = re.search(r"https://www.linkedin.com/in/[^\s/\"']+", text)

    # Limpeza dos objetos Match
    cleaned = {}
    for k, v in res.items():
        if k in ["emails", "phones", "partners", "source_name"]:
            cleaned[k] = v
        else:
            cleaned[k] = v.group(1).strip() if v and v.groups() else (v.group(0).strip() if v else None)
    return cleaned

# --- UI ---
st.title("🕵️ Dossier Structure Tool")

raw_input = st.text_area("Paste research text here:", height=300)

if raw_input:
    data = extract_by_source(raw_input)
    
    # Validações
    dom = validate(data.get('domain'), "Domain")
    cnpj = validate(data.get('cnpj'), "CNPJ")
    razao = validate(data.get('razao'), "Legal Name")
    fantasia = validate(data.get('fantasia'), "Fantasy Name")
    date = validate(data.get('founding_date'), "Foundation Date")
    loc = validate(data.get('location'), "Location")
    act = validate(data.get('activity'), "Activity")
    stat = validate(data.get('status'), "Status")
    addr = validate(data.get('address'), "Address")
    
    # Telefones e Emails com fonte
    phones = format_phone(data.get('phones'))
    emails = " / ".join(data.get('emails')) if data.get('emails') else "**(MISSING EMAIL PLEASE UPDATE)**"
    
    # Redes Sociais
    socials = [data.get('fb'), data.get('ig'), data.get('li')]
    social_str = "\n".join([s for s in socials if s]) if any(socials) else "**(MISSING SOCIAL MEDIA PLEASE UPDATE)**"

    # Bloco de Sócios
    partner_text = ""
    if not data.get('partners'):
        partner_text = "Partner: **(MISSING PARTNER PLEASE UPDATE)**\nEmail - **(MISSING INFO)**\nSource - **(MISSING INFO)**"
    else:
        for p in data['partners']:
            partner_text += f"Partner: {p.strip()} (Sócio-Administrador)\nEmail - **(CHECK PERSONAL EMAIL)**\nSource - {data['source_name']}\n\n"

    # Montagem do ABOUT com a fonte do telefone
    phone_source = f"(Source: {data['source_name']})" if data.get('phones') else ""
    about = (f"{razao}, operating under the Corporate Taxpayer ID (CNPJ) {cnpj}, "
             f"was founded on {date}. The company's official registry name is {razao}. "
             f"Located in the city of {loc}, its main area of activity is {act}. "
             f"According to the Brazilian Federal Revenue, the company's current status is {stat}. "
             f"Contact Phone: {phones} {phone_source}.")

    # Template Final
    dossier = f"""ACTIONABLE DOMAIN:
{dom}

LEGAL INFO/NAME OF THE COMPANY:
CNPJ: {cnpj}
Fantasy Name: {fantasia}
Legal Name: {razao}

COMPANY DESCRIPTION/ABOUT:
{about}

COMPANY WEBSITE: 

CONTACT/ADDRESS INFORMATION:
Address: {addr} (Source: {data['source_name']})
Phone: {phones}
Email: {emails} (Source: {data['source_name']})

KEY PERSONNEL:
{partner_text}
SOCIAL MEDIA:
{social_str}

OBSERVATIONS:
"""

    st.subheader(f"Formatted Result (via {data['source_name']})")
    st.code(dossier, language="markdown")
    
    if st.button("Clear Data"):
        st.rerun()
