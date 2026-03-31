import streamlit as st
import re
from datetime import datetime

# Page Config
st.set_page_config(page_title="Dossier Pro: Multi-Source v2", layout="wide")

# ============================================
# UTILITY FUNCTIONS
# ============================================

def validate(value, label):
    """Valida campo e retorna placeholder se vazio"""
    if not value or str(value).strip() in ["", "None", "N/A", "-", "None"]:
        return f"**(MISSING {label.upper()} PLEASE UPDATE)**"
    return str(value).strip()

def format_phone(phone):
    """Formata telefone com +55"""
    if not phone or phone.strip() in ["", "N/A", "-"]:
        return f"**(MISSING PHONE PLEASE UPDATE)**"
    phone = phone.strip()
    if not phone.startswith("+55"):
        phone = f"+55 {phone}"
    return phone

def extract_cnpj_from_text(text):
    """Extrai CNPJ de qualquer texto (Whois, Cadastro, etc)"""
    pattern = r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def extract_email_from_text(text):
    """Extrai primeiro email válido de texto"""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def extract_phone_from_text(text):
    """Extrai primeiro telefone válido de texto"""
    # Padrão brasileiro: (XX) XXXXX-XXXX ou (XX) XXXX-XXXX
    pattern = r'\(\d{2}\)\s*\d{4,5}-\d{4}'
    match = re.search(pattern, text)
    return match.group(0) if match else None

def get_website_or_fallback(website, facebook, instagram, linkedin, cadastro_link):
    """
    Regra de prioridade para COMPANY WEBSITE:
    1. Se tem website direto → usa
    2. Se não, usa primeiro social media (prioridade: fb > ig > li)
    3. Se não, usa link de cadastro
    4. Se não, vazio
    """
    if website and website.strip() not in ["", "N/A", "-"]:
        return website.strip()
    
    if facebook and facebook.strip() not in ["", "N/A", "-"]:
        return facebook.strip()
    
    if instagram and instagram.strip() not in ["", "N/A", "-"]:
        return instagram.strip()
    
    if linkedin and linkedin.strip() not in ["", "N/A", "-"]:
        return linkedin.strip()
    
    if cadastro_link and cadastro_link.strip() not in ["", "N/A", "-"]:
        return cadastro_link.strip()
    
    return ""

def get_partner_email_or_fallback(partner_email, whois_email, company_email):
    """
    Fallback para email do partner:
    1. Se tem email específico do partner → usa
    2. Se não, tenta email genérico da company
    3. Se não, tenta email do Whois
    4. Se não, vazio
    """
    if partner_email and partner_email.strip() not in ["", "N/A", "-"]:
        return partner_email.strip()
    
    if company_email and company_email.strip() not in ["", "N/A", "-"]:
        return company_email.strip()
    
    if whois_email and whois_email.strip() not in ["", "N/A", "-"]:
        return whois_email.strip()
    
    return ""

def extract_all_emails(whois_data, company_email=""):
    """
    Extrai TODOS os emails do texto (não só o primeiro)
    """
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = list(set(re.findall(pattern, whois_data)))
    
    # Adiciona email da company se não estiver vazio
    if company_email and company_email.strip() not in ["", "N/A", "-"]:
        emails.insert(0, company_email.strip())
    
    # Remove duplicatas mantendo ordem
    seen = set()
    unique_emails = []
    for email in emails:
        if email not in seen:
            seen.add(email)
            unique_emails.append(email)
    
    return unique_emails

def extract_all_phones(whois_data, company_phone=""):
    """
    Extrai TODOS os telefones do texto (não só o primeiro)
    """
    pattern = r'\(\d{2}\)\s*\d{4,5}-\d{4}'
    phones = list(set(re.findall(pattern, whois_data)))
    
    # Adiciona telefone da company se não estiver vazio
    if company_phone and company_phone.strip() not in ["", "N/A", "-"]:
        phones.insert(0, company_phone.strip())
    
    # Remove duplicatas mantendo ordem
    seen = set()
    unique_phones = []
    for phone in phones:
        if phone not in seen:
            seen.add(phone)
            unique_phones.append(phone)
    
    return unique_phones

def format_multiple_contacts(items, contact_type="email"):
    """
    Formata múltiplos emails/telefones com formatação apropriada
    """
    if not items or len(items) == 0:
        if contact_type == "email":
            return "**(MISSING EMAIL PLEASE UPDATE)**"
        else:
            return "**(MISSING PHONE PLEASE UPDATE)**"
    
    if contact_type == "phone":
        formatted = []
        for phone in items:
            phone = phone.strip()
            if phone and phone not in ["", "N/A", "-"]:
                if not phone.startswith("+55"):
                    phone = f"+55 {phone}"
                formatted.append(phone)
        
        if not formatted:
            return "**(MISSING PHONE PLEASE UPDATE)**"
        return " / ".join(formatted)
    
    else:  # email
        cleaned = [e.strip() for e in items if e.strip() not in ["", "N/A", "-"]]
        if not cleaned:
            return "**(MISSING EMAIL PLEASE UPDATE)**"
        return " / ".join(cleaned)

def detect_red_flags(domain_age_days, address_mismatch, whois_recent_change, observations):
    """
    Detecta red flags automáticas:
    - Domínio muito antigo mas empresa nova
    - Mudança recente no Whois
    - Inconsistência de endereço
    """
    flags = []
    
    if domain_age_days and domain_age_days > 1825:  # > 5 anos
        flags.append(f"⚠️ Domain age: {domain_age_days} days (~{domain_age_days//365} years)")
    
    if whois_recent_change:
        flags.append(f"⚠️ Recent Whois change: {whois_recent_change}")
    
    if address_mismatch:
        flags.append(f"⚠️ Address mismatch between sources")
    
    return flags

def generate_dossier(domain, cnpj, fantasia, razao, descricao, website, 
                     endereco, telefone, email, partner_name, partner_email,
                     facebook, instagram, linkedin, observations, source,
                     whois_data="", cadastro_link="", additional_emails="", additional_phones=""):
    """Gera o dossier com fallbacks e lógica automática"""
    
    # LÓGICA: Fallback para CNPJ se vazio
    if not cnpj or cnpj.strip() in ["", "N/A", "-"]:
        extracted_cnpj = extract_cnpj_from_text(whois_data)
        if extracted_cnpj:
            cnpj = extracted_cnpj
    
    # LÓGICA: Fallback para Partner Name (usar Owner do Whois)
    if not partner_name or partner_name.strip() in ["", "N/A", "-"]:
        owner_match = re.search(r'owner:\s+([^\n]+)', whois_data, re.I)
        if owner_match:
            partner_name = owner_match.group(1).strip()
    
    # LÓGICA: Website ou Social Media
    website = get_website_or_fallback(website, facebook, instagram, linkedin, cadastro_link)
    
    # LÓGICA: Extrair TODOS os emails (company + whois + adicionais)
    all_emails = extract_all_emails(whois_data, email)
    
    # Adicionar emails adicionais se fornecidos
    if additional_emails and additional_emails.strip():
        extra = [e.strip() for e in additional_emails.split(",")]
        all_emails.extend(extra)
    
    # Remover duplicatas
    all_emails = list(dict.fromkeys(all_emails))
    
    # LÓGICA: Extrair TODOS os telefones (company + whois + adicionais)
    all_phones = extract_all_phones(whois_data, telefone)
    
    # Adicionar telefones adicionais se fornecidos
    if additional_phones and additional_phones.strip():
        extra = [p.strip() for p in additional_phones.split(",")]
        all_phones.extend(extra)
    
    # Remover duplicatas
    all_phones = list(dict.fromkeys(all_phones))
    
    # LÓGICA: Partner Email com fallback
    whois_email = extract_email_from_text(whois_data)
    partner_email = get_partner_email_or_fallback(partner_email, whois_email, email)
    
    # Validações finais
    domain = validate(domain, "Domain")
    cnpj = validate(cnpj, "CNPJ")
    fantasia = validate(fantasia, "Fantasy Name")
    razao = validate(razao, "Legal Name")
    endereco = validate(endereco, "Address")
    
    # Formatar múltiplos telefones
    phones_str = format_multiple_contacts(all_phones, "phone")
    
    # Formatar múltiplos emails
    emails_str = format_multiple_contacts(all_emails, "email")
    if emails_str != "**(MISSING EMAIL PLEASE UPDATE)**":
        emails_str = f"{emails_str} (Source: {source})"
    
    # Descrição
    if not descricao or descricao.strip() in ["", "N/A", "-"]:
        if razao != f"**(MISSING LEGAL NAME PLEASE UPDATE)**":
            descricao = f"{razao}, operating under the Corporate Taxpayer ID (CNPJ) {cnpj}, is a company registered in Brazil."
        else:
            descricao = "**(MISSING DESCRIPTION PLEASE UPDATE)**"
    
    # Social Media
    socials = []
    if facebook and facebook.strip() not in ["", "N/A", "-"]:
        socials.append(facebook.strip())
    if instagram and instagram.strip() not in ["", "N/A", "-"]:
        socials.append(instagram.strip())
    if linkedin and linkedin.strip() not in ["", "N/A", "-"]:
        socials.append(linkedin.strip())
    
    social_str = "\n".join(socials) if socials else "**(MISSING SOCIAL MEDIA PLEASE UPDATE)**"
    
    # Partner Block
    if partner_name and partner_name.strip() not in ["", "N/A", "-"]:
        partner_email_display = partner_email if partner_email and partner_email.strip() not in ["", "N/A", "-"] else "**(MISSING EMAIL)**"
        partner_block = f"Partner: {partner_name.strip()} (Sócio-Administrador)\nEmail: {partner_email_display}\nSource: {source}"
    else:
        partner_block = "Partner: **(MISSING PARTNER PLEASE UPDATE)**\nEmail: **(MISSING EMAIL)**\nSource: **(MISSING SOURCE)**"
    
    # Website
    website_display = website if website else ""
    
    # Montar dossier
    dossier = f"""ACTIONABLE DOMAIN:
{domain}

LEGAL INFO/NAME OF THE COMPANY:
CNPJ: {cnpj}
Fantasy Name: {fantasia}
Legal Name: {razao}

COMPANY DESCRIPTION/ABOUT:
{descricao}

COMPANY WEBSITE:
{website_display}

CONTACT/ADDRESS INFORMATION:
Address: {endereco} (Source: {source})
Phone: {phones_str}
Email: {emails_str}

KEY PERSONNEL:
{partner_block}

SOCIAL MEDIA:
{social_str}

OBSERVATIONS:
{observations.strip() if observations else ''}
"""
    
    return dossier

# ============================================
# STREAMLIT INTERFACE
# ============================================

st.title("🕵️ Dossier Structure Tool v2 (Multi-Source)")
st.markdown("**Fill in the fields as you find the data. Smart fallbacks handle missing info automatically.**")

# Initialize session state
if 'form_data' not in st.session_state:
    st.session_state.form_data = {
        'domain': '', 'cnpj': '', 'fantasia': '', 'razao': '',
        'descricao': '', 'website': '', 'endereco': '', 'telefone': '',
        'email': '', 'partner_name': '', 'partner_email': '',
        'facebook': '', 'instagram': '', 'linkedin': '',
        'observations': '', 'source': 'General Source',
        'whois_data': '', 'cadastro_link': ''
    }

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    source = st.selectbox(
        "Source",
        ["General Source", "Registro.br", "DomainTools", "Informe Cadastral", "Cadastro Empresa"],
        key="source_select"
    )
    st.session_state.form_data['source'] = source
    
    if st.button("🗑️ Clear All Data", use_container_width=True):
        st.session_state.form_data = {
            'domain': '', 'cnpj': '', 'fantasia': '', 'razao': '',
            'descricao': '', 'website': '', 'endereco': '', 'telefone': '',
            'email': '', 'partner_name': '', 'partner_email': '',
            'facebook': '', 'instagram': '', 'linkedin': '',
            'observations': '', 'source': 'General Source',
            'whois_data': '', 'cadastro_link': ''
        }
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 📝 Raw Data (for auto-extraction)")
    st.markdown("Paste Whois or Cadastro data here for smart fallbacks")
    st.session_state.form_data['whois_data'] = st.text_area(
        "Whois / Cadastro Raw Data",
        value=st.session_state.form_data['whois_data'],
        height=150,
        placeholder="Paste whois or cadastro empresa data..."
    )
    
    st.session_state.form_data['cadastro_link'] = st.text_input(
        "Cadastro Empresa Link",
        value=st.session_state.form_data['cadastro_link'],
        placeholder="https://cadastroempresa.com.br/..."
    )

# Main form
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

st.session_state.form_data['descricao'] = st.text_area(
    "📄 Company Description/About",
    value=st.session_state.form_data['descricao'],
    placeholder="Company overview and main activities...",
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

st.markdown("**Additional Contacts** (separated by comma)")
col1, col2 = st.columns(2)
with col1:
    if 'additional_phones' not in st.session_state.form_data:
        st.session_state.form_data['additional_phones'] = ""
    st.session_state.form_data['additional_phones'] = st.text_input(
        "Additional Phones",
        value=st.session_state.form_data['additional_phones'],
        placeholder="e.g., (11) 98765-4321, (11) 3333-2222"
    )

with col2:
    if 'additional_emails' not in st.session_state.form_data:
        st.session_state.form_data['additional_emails'] = ""
    st.session_state.form_data['additional_emails'] = st.text_input(
        "Additional Emails",
        value=st.session_state.form_data['additional_emails'],
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
        placeholder="https://www.facebook.com/spportoessp/"
    )

with col2:
    st.session_state.form_data['instagram'] = st.text_input(
        "📷 Instagram",
        value=st.session_state.form_data['instagram'],
        placeholder="https://www.instagram.com/spportoes/"
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
    placeholder="E.g., Domain registrant mismatch, suspicious activity patterns, company match validated, etc.",
    height=120
)

st.markdown("---")

# Generate dossier
col_generate, col_copy = st.columns(2)

with col_generate:
    if st.button("✅ Generate Formatted Dossier", use_container_width=True, type="primary"):
        dossier = generate_dossier(
            st.session_state.form_data['domain'],
            st.session_state.form_data['cnpj'],
            st.session_state.form_data['fantasia'],
            st.session_state.form_data['razao'],
            st.session_state.form_data['descricao'],
            st.session_state.form_data['website'],
            st.session_state.form_data['endereco'],
            st.session_state.form_data['telefone'],
            st.session_state.form_data['email'],
            st.session_state.form_data['partner_name'],
            st.session_state.form_data['partner_email'],
            st.session_state.form_data['facebook'],
            st.session_state.form_data['instagram'],
            st.session_state.form_data['linkedin'],
            st.session_state.form_data['observations'],
            st.session_state.form_data['source'],
            st.session_state.form_data['whois_data'],
            st.session_state.form_data['cadastro_link'],
            st.session_state.form_data.get('additional_emails', ''),
            st.session_state.form_data.get('additional_phones', '')
        )
        
        st.session_state.dossier = dossier
        st.success("✅ Dossier Generated with Smart Fallbacks!")

with col_copy:
    if st.button("📋 Copy Output", use_container_width=True):
        if 'dossier' in st.session_state:
            st.info("⬆️ Select code below and Ctrl+C to copy")
        else:
            st.warning("Generate dossier first!")

# Output
if 'dossier' in st.session_state:
    st.markdown("### 📄 Formatted Dossier Output")
    st.code(st.session_state.dossier, language="text")
    
    # Stats
    col1, col2, col3 = st.columns(3)
    with col1:
        filled_fields = sum(1 for v in st.session_state.form_data.values() if v and v.strip() not in ["", "N/A", "-"])
        st.metric("Fields Filled", filled_fields)
    
    with col2:
        missing_critical = sum(1 for field in ['domain', 'cnpj', 'razao'] if not st.session_state.form_data.get(field, "").strip())
        st.metric("Critical Missing", missing_critical)
    
    with col3:
        st.metric("Source", st.session_state.form_data['source'])
