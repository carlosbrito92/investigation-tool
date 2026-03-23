import streamlit as st
import re

# Configuração da Página
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

def extract_by_source(text):
    res = {}
    
    # --- NOVO: REGISTRO.BR (Captura de texto grudado) ---
    if "registro.br" in text.lower():
        st.sidebar.success("Source: Registro.br")
        res["source_name"] = "Registro.br"
        res["domain"] = re.search(r"Domínio\s+([a-z0-9.-]+)", text, re.I)
        # Captura o Titular (para após a palavra 'Titular' até 'Documento')
        res["razao"] = re.search(r"Titular([A-Z][^0-9\n\r]+?)(?=Documento|$)", text)
        res["cnpj_cpf"] = re.search(r"Documento([\d\.\-\*]+)", text)
        # Email específico do Registro.br
        res["whois_email"] = re.search(r"Email([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", text)
        res["founding_date"] = re.search(r"Criado([\d/]{10})", text)
        res["status"] = re.search(r"Status(\w+)", text)

    # --- NOVO: DOMAINTOOLS ---
    elif "whois.domaintools.com" in text.lower() or "Whois Record for" in text:
        st.sidebar.success("Source: DomainTools")
        res["source_name"] = "DomainTools"
        res["domain"] = re.search(r"domain:\s+([a-z0-9.-]+)", text, re.I)
        res["razao"] = re.search(r"owner:\s+([^\n\r]+)", text, re.I)
        res["cnpj_cpf"] = re.search(r"ownerid:\s+([^\n\r]+)", text, re.I)
        res["founding_date"] = re.search(r"created:\s+([\d]{8})", text) # Formato YYYYMMDD
        res["status"] = re.search(r"status:\s+(\w+)", text)
        res["whois_email"] = re.search(r"e-mail:\s+([a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,})", text, re.I)

    # --- SOURCE: INFORME CADASTRAL ---
    elif "informecadastral.com.br" in text.lower():
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

    # --- SOURCE: CADASTRO EMPRESA ---
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

    # --- FALLBACK ---
    else:
        st.sidebar.warning("Source: General Source")
        res["source_name"] = "General Source"
        res["cnpj"] = re.search(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", text)
        res["razao"] = re.search(r"(?:Razão Social|owner):\s+([^\n\r]+)", text, re.I)
        res["founding_date"] = re.search(r"(?:Fundada em|Abertura|created|Criado):\s+([\d/]+|[\d]{8})", text, re.I)
        res["status"] = re.search(r"Situação|Status:\s+(\w+)", text, re.I)

    # Global Patterns
    res["emails"] = list(set(re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", text)))
    res["phones"] = list(set(re.findall(r"\(\d{2}\)\s\d{4,5}-\d{4}", text)))
    res["fb"] = re.search(r"https://www.facebook.com/[^\s/\"']+", text)
    res["ig"] = re.search(r"https://www.instagram.com/[^\s/\"']+", text)
    res["li"] = re.search(r"https://www.linkedin.com/in/[^\s/\"']+", text)

    cleaned = {}
    for k, v in res.items():
        if k in ["emails", "phones", "partners", "source_name"]:
            cleaned[k] = v
        else:
            cleaned[k] = v.group(1).strip() if v and v.groups() else (v.group(0).strip() if v else None)
    return cleaned

# --- INTERFACE ---
st.title("🕵️ Dossier Structure Tool (Multi-Source)")

if st.sidebar.button("🗑️ Clear All Data"):
    st.rerun()

raw_input = st.text_area("Paste research text here (Whois, CNPJ sites, etc.):", height=300)

if raw_input:
    data = extract_by_source(raw_input)
    
    # Validações
    dom = validate(data.get('domain'), "Domain")
    # Tenta CNPJ ou o Documento mascarado do Whois
    cnpj_display = data.get('cnpj') or data.get('cnpj_cpf')
    cnpj = validate(cnpj_display, "CNPJ/Document")
    razao = validate(data.get('razao'), "Legal Name")
    fantasia = validate(data.get('fantasia'), "Fantasy Name")
    date = validate(data.get('founding_date'), "Foundation Date")
    loc = validate(data.get('location'), "Location")
    act = validate(data.get('activity'), "Activity")
    stat = validate(data.get('status'), "Status")
    addr = validate(data.get('address'), "Address")
    
    phones = format_phone(data.get('phones'), data['source_name'])
    
    # Combina emails encontrados no texto com o email específico do Whois
    all_emails = data.get('emails', [])
    if data.get('whois_email'): all_emails.append(data['whois_email'])
    emails_str = " / ".join(list(set(all_emails))) if all_emails else "**(MISSING EMAIL PLEASE UPDATE)**"
    
    socials = [data.get('fb'), data.get('ig'), data.get('li')]
    social_str = "\n".join([s for s in socials if s]) if any(socials) else "**(MISSING SOCIAL MEDIA PLEASE UPDATE)**"

    # Partner Block
    partner_text = ""
    partners = data.get('partners', [])
    if not partners:
        # Se for Whois, o 'Titular' é o parceiro principal
        if data['source_name'] in ["Registro.br", "DomainTools"]:
            partners = [data.get('razao')]
    
    for p in partners:
        if p and p != "None":
            partner_text += f"Partner: {p.strip()} (Sócio-Administrador/Titular)\nEmail - **(CHECK PERSONAL EMAIL)**\nSource - {data['source_name']}\n\n"
    if not partner_text:
        partner_text = "Partner: **(MISSING PARTNER PLEASE UPDATE)**\nEmail - **(MISSING INFO)**\nSource - **(MISSING INFO)**"

    # Assemble Dossier
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
Address: {addr} (Source: {data['source_name']})
Phone: {phones}
Email: {emails_str} (Source: {data['source_name']})

KEY PERSONNEL:
{partner_text}
SOCIAL MEDIA:
{social_str}

OBSERVATIONS:
"""

    st.subheader(f"Formatted Result (Source: {data['source_name']})")
    st.code(dossier, language="markdown")
