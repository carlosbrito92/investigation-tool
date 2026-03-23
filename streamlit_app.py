import streamlit as st
import re

# Page Config
st.set_page_config(page_title="Dossier Builder", layout="wide")

def validate(value, label):
    """Returns the value or a bold warning if missing."""
    if not value or value.strip() == "" or value == "N/A":
        return "**(MISSING " + label.upper() + " PLEASE UPDATE)**"
    return value.strip()

def extract_data(text):
    # Regex Patterns tailored to your example
    patterns = {
        "domain": r"(?:domain:|investigation is)\s+([a-z0-9.-]+)",
        "cnpj": r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}",
        "razao": r"Razão Social:\s+([^\n\r]+)",
        "founding_date": r"(?:Fundada em|Created on)\s+([\d/]+|[\d-]+)",
        "location": r"(?:Município:|Cidade:)\s+([^\n\r]+)",
        "activity": r"CNAE principal\s+[\d\-]+\s+-\s+([^,.\n\r]+)",
        "status": r"Situação:\s+(\w+)",
        "website": r"https?://(?:www\.)?[a-z0-9.-]+\.[a-z]{2,}(?:/[^\s]*)?",
        "fb": r"https://www.facebook.com/[^\s/\"']+",
        "ig": r"https://www.instagram.com/[^\s/\"']+",
        "li": r"https://www.linkedin.com/in/[^\s/\"']+"
    }
    
    res = {}
    for key, pat in patterns.items():
        match = re.search(pat, text, re.I)
        res[key] = match.group(1) if match and match.groups() else (match.group(0) if match else None)
    return res

# --- UI ---
st.title("🕵️ Internal Investigation Tool")
st.info("Paste your raw data below. The tool will structure it instantly.")

raw_input = st.text_area("Input (Whois, CNPJ, Social Media):", height=300)

if raw_input:
    data = extract_data(raw_input)
    
    # Process findings with your mandatory warning
    dom = validate(data['domain'], "Domain")
    cnpj = validate(data['cnpj'], "CNPJ")
    name = validate(data['razao'], "Company Name")
    date = validate(data['founding_date'], "Date")
    loc = validate(data['location'], "Location")
    act = validate(data['activity'], "Activity")
    stat = validate(data['status'], "Status")
    web = validate(data['website'], "Website")
    fb = validate(data['fb'], "Facebook")
    ig = validate(data['ig'], "Instagram")
    li = validate(data['li'], "LinkedIn")

    # Build the Standardized Description
    desc = (f"{name}, operating under the Corporate Taxpayer ID (CNPJ) {cnpj}, "
            f"was founded on {date}. The company's official registry name is {name}. "
            f"Located in the city of {loc}, its main area of activity is {act}. "
            f"According to the Brazilian Federal Revenue, the company's current status is {stat}.")

    # Final Dossier Construction
    final_dossier = f"""ACTIONABLE DOMAIN:
{dom}

LEGAL INFO/NAME OF THE COMPANY:
CNPJ {cnpj} - {name}

COMPANY DESCRIPTION/ABOUT:
{desc}

COMPANY WEBSITE:
{web}

CONTACT/ADDRESS INFORMATION:
** (MISSING ADDRESS PLEASE UPDATE) **

SOCIAL MEDIA:
Facebook: {fb}
Instagram: {ig}
LinkedIn: {li}

OBSERVATIONS:
** (MISSING OBSERVATION PLEASE UPDATE) **"""

    st.subheader("Generated Dossier")
    st.markdown("---")
    
    # Using st.code makes it one-click copyable in the browser
    st.code(final_dossier, language="markdown")
    
    st.success("Dossier generated! Use the copy icon in the top right of the black box above.")
