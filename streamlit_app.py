import streamlit as st
import re
import json
import os
from datetime import datetime

# Page Config
st.set_page_config(page_title="Dossier Pro v5", layout="wide")

# ============================================
# CONSTANTS — TRANSLATIONS & DATA
# ============================================

STATUS_TRANSLATIONS = {
    # Situação Cadastral (Receita Federal / Cadastro Empresa)
    "ativa": "Active",
    "ativo": "Active",
    "baixada": "Closed",
    "baixado": "Closed",
    "inapta": "Inactive",
    "inapto": "Inactive",
    "suspensa": "Suspended",
    "suspenso": "Suspended",
    "nula": "Null",
    "nulo": "Null",
    "em liquidação": "In Liquidation",
    "em liquidacao": "In Liquidation",
    # Whois / Registro.br
    "publicado": "Published",
    "reservado": "Reserved",
    "expirado": "Expired",
    "cancelado": "Cancelled",
    "aguardando pagamento": "Awaiting Payment",
    "on hold": "On Hold",
}

ACTIVITY_HISTORY_FILE = "activities_history.json"

# ============================================
# ACTIVITY HISTORY — PERSISTENCE
# ============================================

def load_activity_history():
    if os.path.exists(ACTIVITY_HISTORY_FILE):
        try:
            with open(ACTIVITY_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_activity_to_history(activity: str):
    if not activity or not activity.strip():
        return
    history = load_activity_history()
    activity = activity.strip()
    if activity not in history:
        history.insert(0, activity)
        history = history[:100]  # cap at 100 entries
        try:
            with open(ACTIVITY_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

# ============================================
# UTILITY FUNCTIONS
# ============================================

def translate_status(value: str) -> str:
    """Translate known PT status values to English. Passes through unknown values unchanged."""
    if not value:
        return value
    normalized = value.strip().lower()
    return STATUS_TRANSLATIONS.get(normalized, value.strip())

def validate(value, label):
    if not value or str(value).strip() in ["", "None", "N/A", "-"]:
        return f"**(MISSING {label.upper()} PLEASE UPDATE)**"
    return str(value).strip()

def format_phone(phone):
    if not phone or phone.strip() in ["", "N/A", "-"]:
        return "**(MISSING PHONE PLEASE UPDATE)**"
    phone = phone.strip()
    if not phone.startswith("+55"):
        phone = f"+55 {phone}"
    return phone

def is_empty(value):
    return not value or str(value).strip() in ["", "None", "N/A", "-"]

def extract_cnpj(text):
    pattern = r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def extract_email(text):
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def extract_all_emails(text):
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return list(dict.fromkeys(re.findall(pattern, text)))

def extract_phone(text):
    # Requires parentheses around DDD to avoid matching CNPJs or dates
    pattern = r'\(\d{2}\)\s*\d{4,5}-\d{4}'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def extract_all_phones(text):
    pattern = r'\(\d{2}\)\s*\d{4,5}-\d{4}'
    return list(dict.fromkeys(re.findall(pattern, text)))

def extract_urls(text):
    pattern = r'https?://[^\s\"\'\)\]>]+'
    return re.findall(pattern, text)

def get_website_or_fallback(website, facebook, instagram, linkedin, cadastro_link):
    for val in [website, facebook, instagram, linkedin, cadastro_link]:
        if val and val.strip() not in ["", "N/A", "-"]:
            return val.strip()
    return ""

def get_partner_email_or_fallback(partner_email, whois_email, company_email):
    for val in [partner_email, company_email, whois_email]:
        if val and val.strip() not in ["", "N/A", "-"]:
            return val.strip()
    return ""

def extract_all_contacts(whois_data, company_email="", company_phone="",
                          additional_emails="", additional_phones=""):
    all_emails = extract_all_emails(whois_data)
    if not is_empty(company_email):
        all_emails = [company_email.strip()] + [e for e in all_emails if e != company_email.strip()]
    if additional_emails and additional_emails.strip():
        all_emails += [e.strip() for e in additional_emails.split(",") if e.strip()]
    all_emails = list(dict.fromkeys(all_emails))

    all_phones = extract_all_phones(whois_data)
    if not is_empty(company_phone):
        all_phones = [company_phone.strip()] + [p for p in all_phones if p != company_phone.strip()]
    if additional_phones and additional_phones.strip():
        all_phones += [p.strip() for p in additional_phones.split(",") if p.strip()]
    all_phones = list(dict.fromkeys(all_phones))

    return all_emails, all_phones

def format_multiple_contacts(items, contact_type="email"):
    placeholder = "**(MISSING EMAIL PLEASE UPDATE)**" if contact_type == "email" else "**(MISSING PHONE PLEASE UPDATE)**"
    if not items:
        return placeholder
    if contact_type == "phone":
        formatted = []
        for p in items:
            p = p.strip()
            if p and p not in ["", "N/A", "-"]:
                if not p.startswith("+55"):
                    p = f"+55 {p}"
                formatted.append(p)
        return " / ".join(formatted) if formatted else placeholder
    else:
        cleaned = [e.strip() for e in items if e.strip() not in ["", "N/A", "-"]]
        return " / ".join(cleaned) if cleaned else placeholder

def generate_description(razao, cnpj, foundation_date, location, main_activity, current_status):
    if is_empty(razao):
        return ""
    cnpj_str = cnpj if not is_empty(cnpj) else "N/A"
    foundation = foundation_date if not is_empty(foundation_date) else "N/A"
    location_str = location if not is_empty(location) else "N/A"
    activity_str = main_activity if not is_empty(main_activity) else "N/A"
    status_str = translate_status(current_status) if not is_empty(current_status) else "Active"

    return (
        f"{razao.strip()}, operating under the Corporate Taxpayer ID (CNPJ) {cnpj_str}, "
        f"was founded on {foundation}. The company's official registry name is {razao.strip()}. "
        f"Located in the city of {location_str}, its main area of activity is {activity_str}. "
        f"According to the Brazilian Federal Revenue, the company's current status is {status_str}."
    )

# ============================================
# SOURCE-SPECIFIC PARSERS
# ============================================

def parse_cadastro_empresa(text: str) -> dict:
    """
    Parses raw text copied from Cadastro Empresa pages.
    Handles multiple label formats found on cadastroempresa.com.br and similar.
    Returns a dict with field keys matching session_state form_data.
    """
    result = {}

    def find(patterns, txt=text):
        for pat in patterns:
            m = re.search(pat, txt, re.IGNORECASE | re.MULTILINE)
            if m:
                val = m.group(1).strip()
                if val and val not in ["-", "N/A", ""]:
                    return val
        return None

    # CNPJ
    cnpj = extract_cnpj(text)
    if cnpj:
        result["cnpj"] = cnpj

    # Razão Social / Legal Name
    razao = find([
        r"Raz[aã]o\s+Social[:\s]+([^\n\r]+)",
        r"Nome Empresarial[:\s]+([^\n\r]+)",
        r"Empresa[:\s]+([^\n\r]+)",
    ])
    if razao:
        result["razao"] = razao

    # Nome Fantasia
    fantasia = find([
        r"Nome\s+Fantasia[:\s]+([^\n\r]+)",
        r"Fantasia[:\s]+([^\n\r]+)",
    ])
    if fantasia and fantasia.lower() not in ["não informado", "nao informado", "-"]:
        result["fantasia"] = fantasia

    # Data de Abertura / Foundation Date
    foundation = find([
        r"Data\s+(?:de\s+)?Abertura[:\s]+(\d{2}/\d{2}/\d{4})",
        r"Abertura[:\s]+(\d{2}/\d{2}/\d{4})",
        r"Constitui[cç][aã]o[:\s]+(\d{2}/\d{2}/\d{4})",
        r"Fundada?[:\s]+(\d{2}/\d{2}/\d{4})",
        r"Data\s+de\s+In[ií]cio[:\s]+(\d{2}/\d{2}/\d{4})",
    ])
    if foundation:
        result["foundation_date"] = foundation

    # Município / City
    city = find([
        r"Munic[ií]pio[:\s]+([^\n\r\/,]+)",
        r"Cidade[:\s]+([^\n\r\/,]+)",
        r"Localidade[:\s]+([^\n\r\/,]+)",
    ])
    if city:
        result["location"] = city.strip()

    # CNAE / Atividade Principal
    # Labeled field first (most precise), then CNAE code inline, then prose fallback
    activity = find([
        r"CNAE/Atividade\s+Principal:\s*\n\s*[\d\.]+[-–]\d+/\d+\s*[-–]\s*([^\n\r]+)",
        r"Atividade\s+Principal[:\s]+([^\n\r]+)",
        r"CNAE\s+Principal[:\s]+[\d\.]+[-–][\d/]+\s*[-–]\s*([^\n\r]+)",
        r"CNAE[:\s]+[\d\.]+[-–][\d/]+\s*[-–]\s*([^\n\r]+)",
        r"atividade/CNAE\s+principal\s+[\d\.\-/]+\s*[-–]\s*([^,\.]+)",
    ])
    if activity:
        # Strip any leading CNAE code remnants (e.g. "7319-0/99 – ")
        activity = re.sub(r'^[\d\.\-/]+\s*[-–]\s*', '', activity).strip()
        # Strip trailing prose (e.g. ", conforme informações da Receita Federal")
        activity = re.split(r',\s+conforme\s+', activity)[0].strip().rstrip('.')
        result["main_activity"] = activity

    # Situação Cadastral / Status
    # Priority: standalone "Situação: Ativa" line BEFORE "Situação Cadastral"
    # (which is followed by a date, not a status word).
    status = find([
        r"^Situa[cç][aã]o:\s*(\w+)",
        r"No momento sua situa[cç][aã]o [eé]\s+(\w+)",
        r"sua situa[cç][aã]o [eé]\s+(\w+)",
        r"Status[:\s]+(\w+)",
    ])
    if status:
        result["current_status"] = translate_status(status)

    # Endereço
    address = find([
        r"Logradouro[:\s]+([^\n\r]+)",
        r"Endere[cç]o[:\s]+([^\n\r]+)",
    ])
    # Try to build a full address
    complemento = find([r"Complemento[:\s]+([^\n\r]+)"])
    bairro = find([r"Bairro[:\s]+([^\n\r]+)"])
    cep = find([r"CEP[:\s]+([\d\.\-]+)"])
    uf = find([r"\bUF[:\s]+([A-Z]{2})\b", r"Estado[:\s]+([A-Z]{2})\b"])
    if address:
        parts = [address]
        if complemento and complemento.lower() not in ["não informado", "nao informado", "-", ""]:
            parts.append(complemento)
        if bairro:
            parts.append(bairro)
        if city:
            parts.append(city.strip())
        if uf:
            parts.append(uf)
        if cep:
            parts.append(f"CEP {cep}")
        result["endereco"] = ", ".join(p.strip() for p in parts if p.strip())

    # Telefone
    phone = extract_phone(text)
    if phone:
        result["telefone"] = phone

    # Email
    email = extract_email(text)
    if email:
        result["email"] = email

    # Website
    website_match = find([
        r"Site[:\s]+(https?://[^\s]+)",
        r"Website[:\s]+(https?://[^\s]+)",
        r"Homepage[:\s]+(https?://[^\s]+)",
    ])
    if website_match:
        result["website"] = website_match

    return result


def parse_whois(text: str) -> dict:
    """
    Parses Registro.br / generic Whois output.
    Handles both NIC.br format and generic WHOIS formats.
    """
    result = {}

    def find_field(keys, txt=text):
        for key in keys:
            m = re.search(rf'^{key}:\s+(.+)$', txt, re.IGNORECASE | re.MULTILINE)
            if m:
                val = m.group(1).strip()
                if val and val not in ["-", "N/A", ""]:
                    return val
        return None

    # Owner / Razão Social
    owner = find_field(["owner", "org-name", "registrant", "registrant name"])
    if owner:
        result["razao"] = owner

    # CNPJ
    cnpj = extract_cnpj(text)
    if cnpj:
        result["cnpj"] = cnpj

    # Owner ID (for NIC.br, this is the handle)
    # Country
    country = find_field(["country"])

    # Contact email
    email = find_field(["e-mail", "email", "registrant email", "tech-email"])
    if not email:
        email = extract_email(text)
    if email:
        result["email"] = email

    # Phone
    phone = find_field(["phone", "registrant phone", "fax-no"])
    if not phone:
        phone = extract_phone(text)
    if phone:
        result["telefone"] = phone

    # Responsible person
    responsible = find_field(["responsible", "admin-c", "tech-c", "registrant name"])
    if responsible:
        result["partner_name"] = responsible

    # Created date
    created = find_field(["created", "creation date", "registered"])
    if created:
        # Normalize date if ISO format
        iso_match = re.match(r'(\d{4})-(\d{2})-(\d{2})', created)
        if iso_match:
            created = f"{iso_match.group(3)}/{iso_match.group(2)}/{iso_match.group(1)}"
        result["foundation_date"] = created

    # Domain
    domain = find_field(["domain", "domain name"])
    if domain:
        result["domain"] = domain.lower().strip()

    # Address
    address = find_field(["address", "registrant address", "street"])
    city = find_field(["city", "registrant city"])
    state = find_field(["state", "registrant state", "registrant state/province"])
    postal = find_field(["postal-code", "zip", "registrant postal code", "zipcode"])
    if address:
        parts = [address]
        if city:
            parts.append(city)
            result["location"] = city
        if state:
            parts.append(state)
        if postal:
            parts.append(postal)
        if country:
            parts.append(country)
        result["endereco"] = ", ".join(p.strip() for p in parts if p.strip())

    # Whois status
    status = find_field(["status", "domain status"])
    if status:
        result["current_status"] = translate_status(status)

    return result


def parse_social_media(text: str) -> dict:
    """
    Extracts useful fields from pasted Facebook, Instagram, Linktree,
    Bio.sites or any link aggregator page text.
    """
    result = {}

    # Email
    email = extract_email(text)
    if email:
        result["email"] = email

    # Phone
    phone = extract_phone(text)
    if phone:
        result["telefone"] = phone

    # Detect social URLs present in text
    urls = extract_urls(text)
    for url in urls:
        url_lower = url.lower()
        if "facebook.com" in url_lower and "instagram" not in url_lower:
            result.setdefault("facebook", url)
        elif "instagram.com" in url_lower:
            result.setdefault("instagram", url)
        elif "linkedin.com" in url_lower:
            result.setdefault("linkedin", url)
        elif not any(x in url_lower for x in ["facebook", "instagram", "linkedin",
                                                "linktree", "bio.site", "beacons",
                                                "linktr.ee", "bit.ly"]):
            result.setdefault("website", url)

    # Try to extract a display name / company name (first non-empty line often)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if lines:
        candidate = lines[0]
        # Only use if it looks like a name (not a URL or a long sentence)
        if len(candidate) < 80 and "http" not in candidate and "@" not in candidate:
            result["_display_name_hint"] = candidate

    return result


def parse_website(text: str) -> dict:
    """
    Extracts contacts from pasted website text (about page, footer, etc.)
    """
    result = {}

    all_emails = extract_all_emails(text)
    if all_emails:
        result["email"] = all_emails[0]
        if len(all_emails) > 1:
            result["additional_emails"] = ", ".join(all_emails[1:])

    all_phones = extract_all_phones(text)
    if all_phones:
        result["telefone"] = all_phones[0]
        if len(all_phones) > 1:
            result["additional_phones"] = ", ".join(all_phones[1:])

    urls = extract_urls(text)
    for url in urls:
        url_lower = url.lower()
        if "facebook.com" in url_lower:
            result.setdefault("facebook", url)
        elif "instagram.com" in url_lower:
            result.setdefault("instagram", url)
        elif "linkedin.com" in url_lower:
            result.setdefault("linkedin", url)

    return result

# ============================================
# APPLY EXTRACTED FIELDS → SESSION STATE
# (never overwrites existing non-empty values)
# ============================================

FIELD_LABELS = {
    "domain": "Domain",
    "cnpj": "CNPJ",
    "razao": "Legal Name",
    "fantasia": "Fantasy Name",
    "foundation_date": "Foundation Date",
    "location": "Location",
    "main_activity": "Main Activity",
    "current_status": "Current Status",
    "endereco": "Address",
    "telefone": "Phone",
    "email": "Email",
    "partner_name": "Partner Name",
    "partner_email": "Partner Email",
    "website": "Website",
    "facebook": "Facebook",
    "instagram": "Instagram",
    "linkedin": "LinkedIn",
    "additional_emails": "Additional Emails",
    "additional_phones": "Additional Phones",
}

def apply_extracted(extracted: dict, overwrite: bool = False) -> tuple[int, list]:
    """
    Merges extracted fields into session_state.form_data.
    Returns (count_filled, list_of_filled_labels).
    Never touches internal keys like _display_name_hint.
    """
    filled = []
    for key, value in extracted.items():
        if key.startswith("_"):
            continue
        if key not in st.session_state.form_data:
            continue
        current = st.session_state.form_data[key]
        if overwrite or is_empty(current):
            if value and str(value).strip():
                st.session_state.form_data[key] = str(value).strip()
                filled.append(FIELD_LABELS.get(key, key))
    return len(filled), filled

# ============================================
# DOSSIER GENERATOR
# ============================================

def generate_dossier(data: dict) -> str:
    d = data
    whois_data = d.get("whois_data", "")

    # Fallback: CNPJ from Whois
    cnpj = d.get("cnpj", "")
    if is_empty(cnpj):
        cnpj = extract_cnpj(whois_data) or ""

    # Fallback: Partner from Whois owner
    partner_name = d.get("partner_name", "")
    if is_empty(partner_name):
        m = re.search(r'owner:\s+([^\n]+)', whois_data, re.I)
        if m:
            partner_name = m.group(1).strip()

    # Website fallback
    website = get_website_or_fallback(
        d.get("website", ""), d.get("facebook", ""), d.get("instagram", ""),
        d.get("linkedin", ""), d.get("cadastro_link", "")
    )

    # Contacts
    all_emails, all_phones = extract_all_contacts(
        whois_data, d.get("email", ""), d.get("telefone", ""),
        d.get("additional_emails", ""), d.get("additional_phones", "")
    )

    whois_email = extract_email(whois_data)
    partner_email = get_partner_email_or_fallback(
        d.get("partner_email", ""), whois_email, d.get("email", "")
    )

    source = d.get("source", "General Source")
    razao = d.get("razao", "")
    fantasia = d.get("fantasia", "")
    observations = d.get("observations", "")

    # Validate core fields
    domain_v = validate(d.get("domain", ""), "Domain")
    cnpj_v = validate(cnpj, "CNPJ")
    fantasia_v = validate(fantasia, "Fantasy Name")
    razao_v = validate(razao, "Legal Name")
    endereco_v = validate(d.get("endereco", ""), "Address")

    phones_str = format_multiple_contacts(all_phones, "phone")
    emails_str = format_multiple_contacts(all_emails, "email")
    if emails_str != "**(MISSING EMAIL PLEASE UPDATE)**":
        emails_str = f"{emails_str} (Source: {source})"

    # Description
    descricao = d.get("descricao", "")
    if is_empty(descricao):
        if not is_empty(razao):
            descricao = generate_description(
                razao, cnpj, d.get("foundation_date", ""),
                d.get("location", ""), d.get("main_activity", ""),
                d.get("current_status", "")
            )
        else:
            descricao = "**(MISSING DESCRIPTION PLEASE UPDATE)**"

    # Social media
    socials = [v for k, v in [
        ("facebook", d.get("facebook", "")),
        ("instagram", d.get("instagram", "")),
        ("linkedin", d.get("linkedin", "")),
    ] if v and v.strip() not in ["", "N/A", "-"]]
    social_str = "\n".join(socials) if socials else "**(MISSING SOCIAL MEDIA PLEASE UPDATE)**"

    # Partner block
    if not is_empty(partner_name):
        partner_email_display = partner_email if not is_empty(partner_email) else "**(MISSING EMAIL)**"
        partner_block = (
            f"Partner: {partner_name.strip()} (Sócio-Administrador)\n"
            f"Email: {partner_email_display}\n"
            f"Source: {source}"
        )
    else:
        partner_block = (
            "Partner: **(MISSING PARTNER PLEASE UPDATE)**\n"
            "Email: **(MISSING EMAIL)**\n"
            "Source: **(MISSING SOURCE)**"
        )

    return f"""ACTIONABLE DOMAIN:
{domain_v}

LEGAL INFO/NAME OF THE COMPANY:
CNPJ: {cnpj_v}
Fantasy Name: {fantasia_v}
Legal Name: {razao_v}

COMPANY DESCRIPTION/ABOUT:
{descricao}

COMPANY WEBSITE:
{website if website else ''}

CONTACT/ADDRESS INFORMATION:
Address: {endereco_v} (Source: {source})
Phone: {phones_str}
Email: {emails_str}

KEY PERSONNEL:
{partner_block}

SOCIAL MEDIA:
{social_str}

OBSERVATIONS:
{observations.strip() if observations else ''}
"""

# ============================================
# SESSION STATE INIT
# ============================================

EMPTY_FORM = {
    'domain': '', 'cnpj': '', 'fantasia': '', 'razao': '',
    'descricao': '', 'website': '', 'endereco': '', 'telefone': '',
    'email': '', 'partner_name': '', 'partner_email': '',
    'facebook': '', 'instagram': '', 'linkedin': '',
    'observations': '', 'source': 'General Source',
    'whois_data': '', 'cadastro_link': '',
    'foundation_date': '', 'location': '', 'main_activity': '', 'current_status': '',
    'additional_phones': '', 'additional_emails': ''
}

if 'form_data' not in st.session_state:
    st.session_state.form_data = EMPTY_FORM.copy()

if 'autofill_feedback' not in st.session_state:
    st.session_state.autofill_feedback = None  # (source_label, count, fields_list)

# ============================================
# SIDEBAR
# ============================================

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    source = st.selectbox(
        "Source",
        ["General Source", "Registro.br", "DomainTools", "Informe Cadastral", "Cadastro Empresa"],
        key="source_select"
    )
    st.session_state.form_data['source'] = source

    if st.button("🗑️ Clear All Data", use_container_width=True):
        st.session_state.form_data = EMPTY_FORM.copy()
        st.session_state.autofill_feedback = None
        st.rerun()

    st.markdown("---")

    # ── AUTO-FILL POR FONTE ──────────────────────────
    st.markdown("### ⚡ Auto-Fill por Fonte")
    st.caption("Cole o raw data de cada fonte e clique em Extrair. Campos já preenchidos não são sobrescritos.")

    tab_cad, tab_whois, tab_social, tab_site = st.tabs(["🏢 Cadastro", "🌐 Whois", "📱 Social", "🔗 Website"])

    with tab_cad:
        cad_text = st.text_area(
            "Cole o texto do Cadastro Empresa",
            height=160,
            placeholder="Razão Social: ...\nCNPJ: ...\nAtividade Principal: ...",
            key="cad_raw"
        )
        overwrite_cad = st.checkbox("Sobrescrever campos existentes", key="ow_cad")
        if st.button("⚡ Extrair e Preencher", key="btn_cad", use_container_width=True):
            if cad_text.strip():
                extracted = parse_cadastro_empresa(cad_text)
                count, fields = apply_extracted(extracted, overwrite=overwrite_cad)
                st.session_state.autofill_feedback = ("Cadastro Empresa", count, fields)
                # Also store raw for fallback extraction in dossier
                st.session_state.form_data['whois_data'] += "\n" + cad_text
                st.rerun()
            else:
                st.warning("Cole o texto antes de extrair.")

    with tab_whois:
        whois_text = st.text_area(
            "Cole o output do Whois / Registro.br",
            height=160,
            placeholder="domain: example.com.br\nowner: ...\ne-mail: ...",
            key="whois_raw"
        )
        overwrite_whois = st.checkbox("Sobrescrever campos existentes", key="ow_whois")
        if st.button("⚡ Extrair e Preencher", key="btn_whois", use_container_width=True):
            if whois_text.strip():
                extracted = parse_whois(whois_text)
                count, fields = apply_extracted(extracted, overwrite=overwrite_whois)
                st.session_state.autofill_feedback = ("Whois / Registro.br", count, fields)
                st.session_state.form_data['whois_data'] += "\n" + whois_text
                st.rerun()
            else:
                st.warning("Cole o texto antes de extrair.")

    with tab_social:
        social_text = st.text_area(
            "Cole o texto da página social (Facebook, Instagram, Linktree...)",
            height=160,
            placeholder="Nome da empresa\nBio / descrição\nhttps://facebook.com/...",
            key="social_raw"
        )
        overwrite_social = st.checkbox("Sobrescrever campos existentes", key="ow_social")
        if st.button("⚡ Extrair e Preencher", key="btn_social", use_container_width=True):
            if social_text.strip():
                extracted = parse_social_media(social_text)
                hint = extracted.pop("_display_name_hint", None)
                count, fields = apply_extracted(extracted, overwrite=overwrite_social)
                st.session_state.autofill_feedback = ("Social Media", count, fields)
                if hint:
                    st.info(f"💡 Nome detectado: **{hint}** — verifique se é o Fantasia/Razão Social.")
                st.rerun()
            else:
                st.warning("Cole o texto antes de extrair.")

    with tab_site:
        site_text = st.text_area(
            "Cole o texto do website da empresa",
            height=160,
            placeholder="Texto da página Sobre, rodapé, página de contato...",
            key="site_raw"
        )
        overwrite_site = st.checkbox("Sobrescrever campos existentes", key="ow_site")
        if st.button("⚡ Extrair e Preencher", key="btn_site", use_container_width=True):
            if site_text.strip():
                extracted = parse_website(site_text)
                count, fields = apply_extracted(extracted, overwrite=overwrite_site)
                st.session_state.autofill_feedback = ("Website", count, fields)
                st.rerun()
            else:
                st.warning("Cole o texto antes de extrair.")

    # Feedback de auto-fill
    if st.session_state.autofill_feedback:
        label, count, fields = st.session_state.autofill_feedback
        if count > 0:
            st.success(f"✅ {count} campo(s) preenchido(s) de {label}:\n" + ", ".join(fields))
        else:
            st.warning(f"⚠️ Nenhum campo novo extraído de {label}. Verifique se o texto está correto.")

    st.markdown("---")
    st.markdown("### 📎 Links de Referência")
    st.session_state.form_data['cadastro_link'] = st.text_input(
        "Cadastro Empresa Link",
        value=st.session_state.form_data['cadastro_link'],
        placeholder="https://cadastroempresa.com.br/..."
    )

# ============================================
# MAIN FORM
# ============================================

st.title("🕵️ Dossier Structure Tool v5")
st.markdown("**Auto-fill por fonte · Autocomplete de atividade · Traduções PT→EN automáticas**")

# Auto-fill feedback banner (also shown in main area for visibility)
if st.session_state.autofill_feedback:
    label, count, fields = st.session_state.autofill_feedback
    if count > 0:
        st.info(f"⚡ Auto-fill de **{label}**: {count} campo(s) preenchido(s) — {', '.join(fields)}")

st.markdown("### 📋 Company Information")

col1, col2, col3 = st.columns(3)
with col1:
    st.session_state.form_data['domain'] = st.text_input(
        "🌐 Actionable Domain",
        value=st.session_state.form_data['domain'],
        placeholder="e.g., example.com.br"
    )
with col2:
    st.session_state.form_data['cnpj'] = st.text_input(
        "🆔 CNPJ",
        value=st.session_state.form_data['cnpj'],
        placeholder="e.g., 26.600.547/0001-11"
    )
with col3:
    st.session_state.form_data['website'] = st.text_input(
        "🔗 Website",
        value=st.session_state.form_data['website'],
        placeholder="e.g., https://example.com.br"
    )

col1, col2 = st.columns(2)
with col1:
    st.session_state.form_data['razao'] = st.text_input(
        "📝 Legal Name (Razão Social)",
        value=st.session_state.form_data['razao'],
        placeholder="e.g., Comercial de Ferragens LTDA"
    )
with col2:
    st.session_state.form_data['fantasia'] = st.text_input(
        "🏪 Fantasy Name (Nome Fantasia)",
        value=st.session_state.form_data['fantasia'],
        placeholder="e.g., SP Portões"
    )

st.markdown("**Company Registry Information** *(used for auto-generated description)*")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.session_state.form_data['foundation_date'] = st.text_input(
        "📅 Foundation Date",
        value=st.session_state.form_data.get('foundation_date', ''),
        placeholder="e.g., 24/11/2016"
    )
with col2:
    st.session_state.form_data['location'] = st.text_input(
        "📍 Location (City)",
        value=st.session_state.form_data.get('location', ''),
        placeholder="e.g., São Paulo"
    )
with col3:
    # ── MAIN ACTIVITY — AUTOCOMPLETE ─────────────────
    activity_history = load_activity_history()
    current_activity = st.session_state.form_data.get('main_activity', '')

    if activity_history:
        # Build options: always include current value and a "New..." sentinel
        NEW_SENTINEL = "✏️  Type a new activity..."
        options = [NEW_SENTINEL] + activity_history

        # Pre-select current value in list if it exists
        try:
            default_idx = activity_history.index(current_activity) + 1  # +1 for sentinel
        except ValueError:
            default_idx = 0  # Show sentinel (= new entry mode)

        selected = st.selectbox(
            "🏭 Main Activity",
            options=options,
            index=default_idx,
            key="activity_select"
        )

        if selected == NEW_SENTINEL or selected is None:
            new_activity = st.text_input(
                "Type new activity",
                value=current_activity if current_activity not in activity_history else "",
                placeholder="e.g., Installation of advertising panels",
                key="activity_new_input"
            )
            st.session_state.form_data['main_activity'] = new_activity
        else:
            st.session_state.form_data['main_activity'] = selected
    else:
        # No history yet — just a plain text input
        st.session_state.form_data['main_activity'] = st.text_input(
            "🏭 Main Activity",
            value=current_activity,
            placeholder="e.g., Installation of advertising panels",
            key="activity_plain"
        )

with col4:
    st.session_state.form_data['current_status'] = st.text_input(
        "✅ Current Status",
        value=st.session_state.form_data.get('current_status', ''),
        placeholder="e.g., Active"
    )

st.markdown("**Or paste description manually:**")
st.session_state.form_data['descricao'] = st.text_area(
    "📄 Company Description/About *(auto-generated if empty)*",
    value=st.session_state.form_data['descricao'],
    placeholder="Leave empty to auto-generate from registry info above...",
    height=80
)

st.markdown("### 📞 Contact Information")
col1, col2, col3 = st.columns(3)
with col1:
    st.session_state.form_data['telefone'] = st.text_input(
        "☎️ Main Phone",
        value=st.session_state.form_data['telefone'],
        placeholder="e.g., (11) 2211-8065"
    )
with col2:
    st.session_state.form_data['email'] = st.text_input(
        "📧 Main Email",
        value=st.session_state.form_data['email'],
        placeholder="e.g., vendas@example.com.br"
    )
with col3:
    st.session_state.form_data['endereco'] = st.text_input(
        "🏢 Address",
        value=st.session_state.form_data['endereco'],
        placeholder="Full address..."
    )

st.markdown("**Additional Contacts** *(separated by comma)*")
col1, col2 = st.columns(2)
with col1:
    st.session_state.form_data['additional_phones'] = st.text_input(
        "Additional Phones",
        value=st.session_state.form_data.get('additional_phones', ''),
        placeholder="e.g., (11) 98765-4321, (11) 3333-2222"
    )
with col2:
    st.session_state.form_data['additional_emails'] = st.text_input(
        "Additional Emails",
        value=st.session_state.form_data.get('additional_emails', ''),
        placeholder="e.g., suporte@example.com.br, info@example.com.br"
    )

st.markdown("### 👥 Key Personnel")
col1, col2 = st.columns(2)
with col1:
    st.session_state.form_data['partner_name'] = st.text_input(
        "Partner Name (Sócio-Administrador)",
        value=st.session_state.form_data['partner_name'],
        placeholder="e.g., Renato Moura Yassuda"
    )
with col2:
    st.session_state.form_data['partner_email'] = st.text_input(
        "Partner Email",
        value=st.session_state.form_data['partner_email'],
        placeholder="e.g., renato@example.com"
    )

st.markdown("### 📱 Social Media")
col1, col2, col3 = st.columns(3)
with col1:
    st.session_state.form_data['facebook'] = st.text_input(
        "📘 Facebook",
        value=st.session_state.form_data['facebook'],
        placeholder="https://www.facebook.com/example/"
    )
with col2:
    st.session_state.form_data['instagram'] = st.text_input(
        "📷 Instagram",
        value=st.session_state.form_data['instagram'],
        placeholder="https://www.instagram.com/example/"
    )
with col3:
    st.session_state.form_data['linkedin'] = st.text_input(
        "💼 LinkedIn",
        value=st.session_state.form_data['linkedin'],
        placeholder="https://www.linkedin.com/in/..."
    )

st.markdown("### 💡 Observations & Red Flags")
st.session_state.form_data['observations'] = st.text_area(
    "Add your insights, red flags, and observations here",
    value=st.session_state.form_data['observations'],
    placeholder="E.g., Domain registrant mismatch, suspicious activity patterns...",
    height=120
)

st.markdown("---")

# ── GENERATE ─────────────────────────────────────────
col_generate, col_copy = st.columns(2)

with col_generate:
    if st.button("✅ Generate Formatted Dossier", use_container_width=True, type="primary"):
        dossier = generate_dossier(st.session_state.form_data)
        st.session_state.dossier = dossier

        # Save activity to history
        activity_val = st.session_state.form_data.get('main_activity', '').strip()
        if activity_val:
            save_activity_to_history(activity_val)

        st.success("✅ Dossier gerado com sucesso!")

with col_copy:
    if st.button("📋 Copy Output", use_container_width=True):
        if 'dossier' in st.session_state:
            st.info("⬆️ Selecione o código abaixo e pressione Ctrl+C para copiar.")
        else:
            st.warning("Gere o dossier primeiro!")

# ── OUTPUT ───────────────────────────────────────────
if 'dossier' in st.session_state:
    st.markdown("### 📄 Formatted Dossier Output")
    st.code(st.session_state.dossier, language="text")

    col1, col2, col3 = st.columns(3)
    with col1:
        filled = sum(1 for v in st.session_state.form_data.values() if v and str(v).strip() not in ["", "N/A", "-"])
        st.metric("Fields Filled", filled)
    with col2:
        missing = sum(1 for f in ['domain', 'cnpj', 'razao'] if not st.session_state.form_data.get(f, "").strip())
        st.metric("Critical Missing", missing)
    with col3:
        st.metric("Source", st.session_state.form_data['source'])
