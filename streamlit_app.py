import streamlit as st
import re

# Page Config
st.set_page_config(page_title="Dossier Pro: Multi-Source", layout="wide")

def validate(value, label):
    if not value or str(value).strip() in ["", "None", "N/A", "-", "None"]:
        return f"**(MISSING {label.upper()} PLEASE UPDATE)**"
    return str(value).strip()

def format_phone(phone_list, source):
    if not phone_list:
        return f"**(MISSING PHONE PLEASE UPDATE)**"
    unique_phones = list(set(phone_list))
    formatted = " / ".join([f"+55 {p.strip()}" for p in unique_phones])
    return f"{formatted} (Source: {source})"

def get_match(pattern, text, group=1):
    """Função auxiliar para capturar texto sem dar erro de atributo."""
    match = re.search(pattern, text, re.I)
    if match:
        try:
            return match.group(group).strip()
        except IndexError:
            return match.group(0).strip()
    return None

def extract_by_source(text):
    res = {}
    
    # --- SOURCE 1: REGISTRO.BR ---
    if "registro.br" in text.lower():
        res["source_name"] = "Registro.br"
        res["domain"] = get_match(r"Domínio\s+([a-z0-9.-]+)", text)
        res["razao"] = get_match(r"Titular([A-Z][^0-9\n\r]+?)(?=Documento|$)", text)
        res["cnpj_cpf"] = get_match(r"Documento([\d\.\-\*]+)", text)
        res["whois_email"] = get_match(r"Email([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", text)
        res["founding_date"] = get_match(r"Criado([\d/]{10})", text)
        res["status"] = get_match(r"Status(\w+)", text)

    # --- SOURCE 2: DOMAINTOOLS ---
    elif "whois.domaintools.com" in text.lower() or "Whois Record for" in text:
        res["source_name"] = "DomainTools"
        res["domain"] = get_match(r"domain:\s+([a-z0-9.-]+)", text)
        res["razao"] = get_match(r"owner:\s+([^\n\r]+)", text)
        res["cnpj_cpf"] = get_match(r"ownerid:\s+([^\n\r]+)", text)
        res["founding_date"] = get_match(r"created:\s+([\d]{8})", text)
        res["status"] = get_match(r"status:\s+(\w+)", text)
        res["whois_email"] = get_match(r"e-mail:\s+([a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,})", text)

    # --- SOURCE 3: INFORME CADASTRAL ---
    elif "informecadastral.com.br" in text.lower():
        res["source_name"] = "Informe Cadastral"
        res["cnpj"] = get_match(r"CNPJ:\s+(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", text)
        res["razao"] = get_match(r"Razão Social:\s+([^\n\r]+)", text)
        res["fantasia"] = get_match(r"Nome Fantasia:\s+([^\n\r]+)", text)
        res["founding_date"] = get_match(r"Data de Abertura:\s+([\d/]+)", text)
        res["status"] = get_match(r"Situação Cadastral:\s+(\w+)", text)
        res["location"] = get_match(r"Município:\s+([^\n\r]+)", text)
        res["activity"] = get_match(r"Atividade Principal:\s+[\d\.-]+\s+-\s+([^,.\n\r]+)", text)
        res["address"] = get_match(r"Logradouro:\s+([^\n\r]+)", text)
        res["partners"] = re.findall(r"Sócio-Administrador\s+([A-Z\s]{5,})", text)

    # --- SOURCE 4: CADASTRO EMPRESA ---
    elif "cadastroempresa.com.br" in text.lower():
        res["source_name"] = "Cadastro Empresa"
        res["cnpj"] = get_match(r"CNPJ:\s+(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})", text)
        res["razao"] = get_match(r"Razão Social:\s+([^\n\r]+)", text)
        res["fantasia"] = get_match(r"Nome Fantasia:\s+([^\n\r]+)", text)
        res["founding_date"] = get_match(r"Data de Abertura:\s+([\d/]+)", text)
        res["status"] = get_match(r"Situação:\s+(\w+)", text)
        res["location"] = get_match(r"Município:\s+([^\n\r]+)", text)
        res["activity"] = get_match(r"CNAE/Atividade Principal:\s+[\d\-]+\s+-\s+([^,.\n\r]+)", text)
        res["address"] = get_match(r"Endereço completo:\s+([^\n\r]+)", text)
        res["partners"] = re.findall(r"(?:Sócio-Administrador|Sócio):\s+([^\n\r]+)", text)

    # --- FALLBACK ---
    else:
        res["source_name"] = "General Source"
        res["cnpj"] = get_match(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", text)
        res["razao"] = get_match(r"(?:Razão Social|owner|Titular):\s*([^\n\r]+)", text)
        res["founding_date"] = get_match(r"(?:Fundada em|Abertura|created|Criado):\s*([\d/]+|[\d]{8})", text)
        res["status"] = get_match(r"(?:Situação|Status):\s*(\w+)", text)

    # Global Patterns
    res["domain"] = res.get("domain") or get_match(r"(?:domain:|investigation is)\s+([a-z0-9.-]+)", text)
    res["emails"] = list(set(re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", text)))
    res["phones"] = list(set(re.findall(r"\(\d{2}\)\s\d{4,5}-\d{4}", text)))
    res["fb"] = get_match(r"https://www.facebook.com/[^\s/\"']+", text, 0)
    res["ig"] = get_match(r"https://www.instagram.com/[^\s/\"']+", text, 0)
    res["li"] = get_match(r"https://www.linkedin.com/in/[^\s/\"']+", text, 0)
    
    if "partners" not in res: res["partners"] = []
    
    return res

# --- INTERFACE ---
st.title("🕵️ Dossier Structure Tool (Multi-Source)")

if st.sidebar.button("🗑️ Clear All Data"):
    st.rerun()

raw_input = st.text_area("Paste research text here:", height=300)

if raw_input:
    data = extract_by_source(raw_input)
    source = data.get('source_name', 'General Source')
    st.sidebar.info(f"Detected: {source}")

    # Validações
    dom = validate(data.get('domain'), "Domain")
    cnpj = validate(data.get('cnpj') or data.get('cnpj_cpf'), "CNPJ/Document")
    razao = validate(data.get('razao'), "Legal Name")
    fantasia = validate(data.get('fantasia'), "Fantasy Name")
    date = validate(data.get('founding_date'), "Foundation Date")
    loc = validate(data.get('location'), "Location")
    act = validate(data.get('activity'), "Activity")
    stat = validate(data.get('status'), "Status")
    addr = validate(data.get('address'), "Address")
    
    phones = format_phone(data.get('phones'), source)
    
    all_emails = data.get('emails', [])
    if data.get('whois_email'): all_emails.append(data['whois_email'])
    emails_str = " / ".join(list(set(all_emails))) if all_emails else "**(MISSING EMAIL PLEASE UPDATE)**"
    
    socials = [data.get('fb'), data.get('ig'), data.get('li')]
    social_str = "\n".join([s for s in socials if s]) if any(socials) else "**(MISSING SOCIAL MEDIA PLEASE UPDATE)**"

    # Partner Block
    partner_text = ""
    partners = data.get('partners', [])
    if not partners and source in ["Registro.br", "DomainTools"]:
        partners = [data.get('razao')]
    
    for p in partners:
        if p:
            partner_text += f"Partner: {p.strip()} (Sócio-Administrador/Titular)\nEmail - **(CHECK PERSONAL EMAIL)**\nSource - {source}\n\n"
    if not partner_text:
        partner_text = "Partner: **(MISSING PARTNER PLEASE UPDATE)**\nEmail - **(MISSING INFO)**\nSource - **(MISSING INFO)**"

    about = (f"{razao}, operating under the Corporate Taxpayer ID (CNPJ) {cnpj}, "
             f"was founded on {date}. The company's official registry name is {razao}. "
             f"Located in the city of {loc}, its main area of activity is {act}. "
             f"According to the Brazilian Federal Revenue, the company's current status is {stat}.")

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
Address: {addr} (Source: {source})
Phone: {phones}
Email: {emails_str} (Source: {source})

KEY PERSONNEL:
{partner_text}
SOCIAL MEDIA:
{social_str}

OBSERVATIONS:
"""

    st.subheader(f"Formatted Result")
    st.code(dossier, language="markdown")
