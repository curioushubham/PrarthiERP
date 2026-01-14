"""
Vendor Registration Module
Clean UI with AI Toggle and Document Storage
"""

import streamlit as st
import os
import re
import base64
from datetime import datetime
from database import SessionLocal, Vendor, VendorContact, get_next_vendor_code, log_action
from config import VENDOR_CATEGORIES, INDIAN_STATES

st.set_page_config(page_title="Vendor Registration", page_icon="🛒", layout="wide")

CREDENTIALS_PATH = r"C:\Users\Admin\Desktop\PrarthiERP\google_credentials.json"
DOCUMENTS_DIR = r"C:\Users\Admin\Desktop\PrarthiERP\documents"

# Ensure documents directory exists
os.makedirs(DOCUMENTS_DIR, exist_ok=True)

# Check login
if not st.session_state.get('authenticated'):
    st.error("Please login to access this module")
    st.stop()

user_role = st.session_state.user['role']
if user_role not in ["Purchase", "Accounts", "Management"]:
    st.error("Access denied. You don't have permission to access this module.")
    st.stop()

# Initialize session state
if 'v_step' not in st.session_state:
    st.session_state.v_step = 1
if 'v_data' not in st.session_state:
    st.session_state.v_data = {}
if 'v_done' not in st.session_state:
    st.session_state.v_done = False
if 'ai_extracted' not in st.session_state:
    st.session_state.ai_extracted = {}
if 'use_ai' not in st.session_state:
    st.session_state.use_ai = False


def extract_with_ai(file_bytes, file_type):
    """Extract data using AI"""
    try:
        from google.cloud import documentai_v1 as documentai
        from google.oauth2 import service_account
        
        if not os.path.exists(CREDENTIALS_PATH):
            return None, "AI service not configured"
        
        credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
        client = documentai.DocumentProcessorServiceClient(credentials=credentials)
        
        name = "projects/total-velocity-483817-r1/locations/us/processors/d669080ee0db5f05"
        
        mime_types = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'pdf': 'application/pdf'}
        mime_type = mime_types.get(file_type, 'application/pdf')
        
        raw_document = documentai.RawDocument(content=file_bytes, mime_type=mime_type)
        request = documentai.ProcessRequest(name=name, raw_document=raw_document)
        
        result = client.process_document(request=request)
        return result.document.text, None
        
    except Exception as e:
        return None, str(e)


def parse_gst_data(text):
    """Parse GST certificate text"""
    data = {
        'gstin': '', 'legal_name': '', 'trade_name': '', 'pan': '',
        'address': '', 'city': '', 'state': 'Maharashtra', 'pin_code': '',
        'email': '', 'phone': ''
    }
    
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    # GSTIN
    gstin_match = re.search(r'\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][0-9A-Z]Z[0-9A-Z])\b', text)
    if gstin_match:
        data['gstin'] = gstin_match.group(1)
        data['pan'] = data['gstin'][2:12]
    
    # Legal name
    for i, line in enumerate(lines):
        if 'legal name' in line.lower():
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and not re.match(r'^\d+\.?$', next_line):
                    data['legal_name'] = next_line
            break
    
    # Trade name
    for i, line in enumerate(lines):
        if 'trade name' in line.lower() and 'additional' not in line.lower():
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and not re.match(r'^\d+\.?$', next_line):
                    data['trade_name'] = next_line
            break
    
    # Email
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    if email_match:
        data['email'] = email_match.group(0).lower()
    
    # Phone
    phone_match = re.search(r'\b[6-9][0-9]{9}\b', text)
    if phone_match:
        data['phone'] = phone_match.group(0)
    
    # PIN
    pin_matches = re.findall(r'\b([1-9][0-9]{5})\b', text)
    if pin_matches:
        data['pin_code'] = pin_matches[-1]
    
    # State from GSTIN
    if data['gstin']:
        state_codes = {
            '01': 'Jammu and Kashmir', '02': 'Himachal Pradesh', '03': 'Punjab',
            '07': 'Delhi', '08': 'Rajasthan', '09': 'Uttar Pradesh',
            '24': 'Gujarat', '27': 'Maharashtra', '29': 'Karnataka',
            '32': 'Kerala', '33': 'Tamil Nadu', '36': 'Telangana'
        }
        data['state'] = state_codes.get(data['gstin'][:2], 'Maharashtra')
    
    if not data['trade_name'] and data['legal_name']:
        data['trade_name'] = data['legal_name']
    
    return data


def extract_pan_number(text):
    """Extract PAN from document"""
    match = re.search(r'\b([A-Z]{5}[0-9]{4}[A-Z])\b', text)
    return match.group(1) if match else None


def extract_bank_details(text):
    """Extract bank details from cheque"""
    data = {'bank_name': '', 'ifsc': '', 'account': ''}
    
    ifsc_match = re.search(r'\b([A-Z]{4}0[A-Z0-9]{6})\b', text)
    if ifsc_match:
        data['ifsc'] = ifsc_match.group(1)
        bank_prefixes = {
            'HDFC': 'HDFC Bank', 'ICIC': 'ICICI Bank', 'SBIN': 'State Bank of India',
            'AXIS': 'Axis Bank', 'KKBK': 'Kotak Mahindra Bank', 'PUNB': 'Punjab National Bank',
            'BARB': 'Bank of Baroda', 'CNRB': 'Canara Bank', 'UBIN': 'Union Bank of India'
        }
        data['bank_name'] = bank_prefixes.get(data['ifsc'][:4], '')
    
    acc_match = re.search(r'\b(\d{9,18})\b', text)
    if acc_match:
        data['account'] = acc_match.group(1)
    
    return data


def save_document(vendor_code, doc_type, file_bytes, file_ext):
    """Save document to folder and return path"""
    vendor_dir = os.path.join(DOCUMENTS_DIR, vendor_code)
    os.makedirs(vendor_dir, exist_ok=True)
    
    filename = f"{doc_type}.{file_ext}"
    filepath = os.path.join(vendor_dir, filename)
    
    with open(filepath, 'wb') as f:
        f.write(file_bytes)
    
    return filepath


def show_preview(file_bytes, file_type):
    """Show document preview"""
    if file_type in ['jpg', 'jpeg', 'png']:
        st.image(file_bytes, width=250)
    else:
        st.info("📄 PDF uploaded successfully")


# ============ SIDEBAR ============
with st.sidebar:
    st.markdown(f"**👤 {st.session_state.user['full_name']}**")
    st.caption(st.session_state.user['role'])


# ============ MAIN ============
st.title("🛒 Vendor Registration")

# Success screen
if st.session_state.v_done:
    st.balloons()
    st.success(f"""
    ### ✅ Vendor registered successfully
    
    **Code:** {st.session_state.v_data.get('vendor_code')}  
    **Name:** {st.session_state.v_data.get('trade_name')}
    """)
    
    if st.button("Register another vendor", type="primary"):
        st.session_state.v_step = 1
        st.session_state.v_data = {}
        st.session_state.v_done = False
        st.session_state.ai_extracted = {}
        st.session_state.use_ai = False
        st.rerun()
    st.stop()

# Progress
steps = ["GST certificate", "Basic information", "Contact and ratings", "Bank and documents"]
st.caption(f"Step {st.session_state.v_step} of 4: {steps[st.session_state.v_step - 1]}")
st.progress(st.session_state.v_step / 4)
st.markdown("---")

# ============ STEP 1: GST CERTIFICATE ============
if st.session_state.v_step == 1:
    st.subheader("📄 Upload GST certificate")
    
    # AI Toggle
    col1, col2 = st.columns([3, 1])
    with col2:
        use_ai = st.toggle("✨ Use AI to auto-fill", value=st.session_state.use_ai, 
                          help="AI will automatically extract details from your document")
        st.session_state.use_ai = use_ai
    
    uploaded = st.file_uploader("Select GST certificate", type=['pdf', 'jpg', 'jpeg', 'png'], 
                                label_visibility="collapsed")
    
    if uploaded:
        file_bytes = uploaded.read()
        file_type = uploaded.name.split('.')[-1].lower()
        
        st.session_state.v_data['gst_file'] = file_bytes
        st.session_state.v_data['gst_file_type'] = file_type
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.caption("Preview")
            show_preview(file_bytes, file_type)
        
        with col2:
            if st.session_state.use_ai and os.path.exists(CREDENTIALS_PATH):
                with st.spinner("Extracting details..."):
                    raw_text, error = extract_with_ai(file_bytes, file_type)
                    if raw_text:
                        extracted = parse_gst_data(raw_text)
                        extracted['raw_text'] = raw_text[:1000]
                        st.session_state.ai_extracted = extracted
                        st.success("✅ Details extracted successfully")
                        
                        st.text_input("GSTIN", value=extracted.get('gstin', ''), disabled=True)
                        st.text_input("Legal name", value=extracted.get('legal_name', ''), disabled=True)
                        st.text_input("Trade name", value=extracted.get('trade_name', ''), disabled=True)
                    else:
                        st.warning("Could not extract details. Please enter manually.")
                        st.session_state.ai_extracted = {}
            else:
                st.info("Upload complete. Click Next to enter details manually.")
                st.session_state.ai_extracted = {}
        
        if st.session_state.ai_extracted.get('raw_text'):
            with st.expander("View extracted text"):
                st.text(st.session_state.ai_extracted['raw_text'])
        
        st.markdown("---")
        if st.button("Next →", type="primary"):
            st.session_state.v_step = 2
            st.rerun()
    else:
        st.info("Please upload a GST certificate to continue, or skip to enter details manually.")
        if st.button("Skip and enter manually"):
            st.session_state.v_step = 2
            st.rerun()

# ============ STEP 2: BASIC INFORMATION ============
elif st.session_state.v_step == 2:
    st.subheader("📋 Basic information")
    
    extracted = st.session_state.ai_extracted or {}
    
    session = SessionLocal()
    vendor_code = get_next_vendor_code(session)
    session.close()
    
    st.info(f"Vendor code: **{vendor_code}** (auto-generated)")
    st.session_state.v_data['vendor_code'] = vendor_code
    
    col1, col2 = st.columns(2)
    with col1:
        gstin = st.text_input("GSTIN *", value=extracted.get('gstin', ''), max_chars=15)
        pan = st.text_input("PAN *", value=extracted.get('pan', ''), max_chars=10)
        legal_name = st.text_input("Legal name *", value=extracted.get('legal_name', ''))
        vendor_type = st.selectbox("Vendor type *", ["Material Supplier", "Service Provider", "Both"])
    
    with col2:
        trade_name = st.text_input("Trade name *", value=extracted.get('trade_name', ''))
        vendor_category = st.selectbox("Category *", VENDOR_CATEGORIES)
        company_email = st.text_input("Email *", value=extracted.get('email', ''))
        company_phone = st.text_input("Phone *", value=extracted.get('phone', ''), max_chars=10)
    
    st.markdown("##### Address")
    address = st.text_input("Address line 1 *", value=extracted.get('address', ''))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        city = st.text_input("City *", value=extracted.get('city', ''))
    with col2:
        state_val = extracted.get('state', 'Maharashtra')
        state_idx = INDIAN_STATES.index(state_val) if state_val in INDIAN_STATES else 10
        state = st.selectbox("State *", INDIAN_STATES, index=state_idx)
    with col3:
        pin = st.text_input("PIN code *", value=extracted.get('pin_code', ''), max_chars=6)
    
    st.session_state.v_data.update({
        'gstin': gstin, 'pan': pan, 'legal_name': legal_name, 'trade_name': trade_name,
        'vendor_type': vendor_type, 'vendor_category': vendor_category,
        'company_email': company_email, 'company_phone': company_phone,
        'address': address, 'city': city, 'state': state, 'pin': pin
    })
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back"):
            st.session_state.v_step = 1
            st.rerun()
    with col2:
        required = [gstin, pan, legal_name, trade_name, company_email, company_phone, address, city, pin]
        if all(required):
            if st.button("Next →", type="primary"):
                st.session_state.v_step = 3
                st.rerun()
        else:
            st.button("Next →", disabled=True)
            st.caption("Please fill all required fields")

# ============ STEP 3: CONTACT AND RATINGS ============
elif st.session_state.v_step == 3:
    st.subheader("👥 Contact person and ratings")
    
    st.markdown("##### Primary contact")
    col1, col2 = st.columns(2)
    with col1:
        p_name = st.text_input("Name *")
        p_mobile = st.text_input("Mobile *", max_chars=10)
    with col2:
        p_desig = st.text_input("Designation *")
        p_email = st.text_input("Email")
    
    st.markdown("##### Payment terms")
    col1, col2, col3 = st.columns(3)
    with col1:
        payment_terms = st.selectbox("Payment terms", ["30 Days", "45 Days", "60 Days", "90 Days", "Advance"])
    with col2:
        credit_days = st.number_input("Credit days", value=30, min_value=0)
    with col3:
        credit_limit = st.number_input("Credit limit (₹)", value=500000.0, min_value=0.0, step=10000.0)
    
    st.markdown("##### Vendor rating")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        r_del = st.slider("Delivery", 1.0, 5.0, 4.0, 0.5)
    with col2:
        r_qual = st.slider("Quality", 1.0, 5.0, 4.0, 0.5)
    with col3:
        r_price = st.slider("Pricing", 1.0, 5.0, 4.0, 0.5)
    with col4:
        r_overall = round((r_del + r_qual + r_price) / 3, 1)
        st.metric("Overall", f"⭐ {r_overall}")
    
    comments = st.text_area("Comments (optional)", height=80)
    
    st.session_state.v_data.update({
        'p_name': p_name, 'p_desig': p_desig, 'p_mobile': p_mobile, 'p_email': p_email,
        'payment_terms': payment_terms, 'credit_days': credit_days, 'credit_limit': credit_limit,
        'r_del': r_del, 'r_qual': r_qual, 'r_price': r_price, 'r_overall': r_overall,
        'comments': comments
    })
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back"):
            st.session_state.v_step = 2
            st.rerun()
    with col2:
        if p_name and p_desig and p_mobile:
            if st.button("Next →", type="primary"):
                st.session_state.v_step = 4
                st.rerun()
        else:
            st.button("Next →", disabled=True)
            st.caption("Please fill contact details")

# ============ STEP 4: BANK AND DOCUMENTS ============
elif st.session_state.v_step == 4:
    st.subheader("🏦 Bank details and documents")
    
    expected_pan = st.session_state.v_data.get('pan', '')
    
    # Bank details - Manual entry first
    st.markdown("##### Bank details (optional)")
    col1, col2 = st.columns(2)
    with col1:
        bank_name = st.text_input("Bank name", value=st.session_state.v_data.get('bank_name', ''))
        account = st.text_input("Account number", value=st.session_state.v_data.get('account', ''))
        ifsc = st.text_input("IFSC code", value=st.session_state.v_data.get('ifsc', ''), max_chars=11)
    with col2:
        branch = st.text_input("Branch", value=st.session_state.v_data.get('branch', ''))
        acc_type = st.selectbox("Account type", ["Current", "Savings"])
    
    st.markdown("---")
    
    # Document uploads
    st.markdown("##### Documents (optional)")
    st.caption("Upload documents for verification. AI can auto-fill details if enabled.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**PAN card**")
        use_ai_pan = st.checkbox("Use AI to verify PAN", key="ai_pan")
        pan_file = st.file_uploader("Upload PAN card", type=['pdf', 'jpg', 'jpeg', 'png'], 
                                    key="pan", label_visibility="collapsed")
        
        if pan_file:
            pan_bytes = pan_file.read()
            pan_type = pan_file.name.split('.')[-1].lower()
            st.session_state.v_data['pan_file'] = pan_bytes
            st.session_state.v_data['pan_file_type'] = pan_type
            
            show_preview(pan_bytes, pan_type)
            
            if use_ai_pan and os.path.exists(CREDENTIALS_PATH):
                with st.spinner("Verifying..."):
                    pan_text, _ = extract_with_ai(pan_bytes, pan_type)
                    if pan_text:
                        extracted_pan = extract_pan_number(pan_text)
                        if extracted_pan:
                            if extracted_pan == expected_pan:
                                st.success(f"✅ PAN verified: {extracted_pan}")
                            else:
                                st.error(f"❌ Mismatch: Expected {expected_pan}, found {extracted_pan}")
                        else:
                            st.warning("Could not extract PAN")
    
    with col2:
        st.markdown("**Bank document**")
        use_ai_bank = st.checkbox("Use AI to extract bank details", key="ai_bank")
        cheque_file = st.file_uploader("Upload cancelled cheque or bank statement", 
                                       type=['pdf', 'jpg', 'jpeg', 'png'], 
                                       key="cheque", label_visibility="collapsed")
        
        if cheque_file:
            cheque_bytes = cheque_file.read()
            cheque_type = cheque_file.name.split('.')[-1].lower()
            st.session_state.v_data['cheque_file'] = cheque_bytes
            st.session_state.v_data['cheque_file_type'] = cheque_type
            
            show_preview(cheque_bytes, cheque_type)
            
            if use_ai_bank and os.path.exists(CREDENTIALS_PATH):
                with st.spinner("Extracting..."):
                    cheque_text, _ = extract_with_ai(cheque_bytes, cheque_type)
                    if cheque_text:
                        bank_data = extract_bank_details(cheque_text)
                        if bank_data.get('ifsc'):
                            st.success("✅ Bank details extracted")
                            st.session_state.v_data['bank_name'] = bank_data.get('bank_name') or bank_name
                            st.session_state.v_data['ifsc'] = bank_data.get('ifsc') or ifsc
                            st.session_state.v_data['account'] = bank_data.get('account') or account
                            st.rerun()
    
    st.markdown("---")
    
    # MSME
    st.markdown("##### MSME registration (optional)")
    is_msme = st.checkbox("Vendor is MSME registered")
    msme_num = None
    if is_msme:
        msme_num = st.text_input("MSME/Udyam number", placeholder="UDYAM-XX-XX-XXXXXXX")
    
    status = st.radio("Vendor status", ["Active", "Inactive"], horizontal=True)
    
    st.session_state.v_data.update({
        'bank_name': bank_name, 'branch': branch, 'account': account,
        'ifsc': ifsc, 'acc_type': acc_type, 'is_msme': is_msme,
        'msme_num': msme_num, 'status': status
    })
    
    # Summary
    with st.expander("📋 Review details before submission"):
        d = st.session_state.v_data
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Basic**")
            st.write(f"Code: {d.get('vendor_code')}")
            st.write(f"Name: {d.get('trade_name')}")
            st.write(f"GSTIN: {d.get('gstin')}")
            st.write(f"PAN: {d.get('pan')}")
        with col2:
            st.markdown("**Contact**")
            st.write(f"Email: {d.get('company_email')}")
            st.write(f"Phone: {d.get('company_phone')}")
            st.write(f"City: {d.get('city')}")
        with col3:
            st.markdown("**Bank**")
            st.write(f"Bank: {bank_name or 'Not provided'}")
            st.write(f"IFSC: {ifsc or 'Not provided'}")
            st.write(f"Rating: ⭐ {d.get('r_overall')}")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back"):
            st.session_state.v_step = 3
            st.rerun()
    with col2:
        if st.button("✅ Submit", type="primary"):
            session = SessionLocal()
            try:
                d = st.session_state.v_data
                vendor_code = d['vendor_code']
                
                # Save documents
                doc_gst = doc_pan = doc_cheque = None
                
                if d.get('gst_file'):
                    doc_gst = save_document(vendor_code, 'gst_certificate', 
                                           d['gst_file'], d['gst_file_type'])
                if d.get('pan_file'):
                    doc_pan = save_document(vendor_code, 'pan_card', 
                                           d['pan_file'], d['pan_file_type'])
                if d.get('cheque_file'):
                    doc_cheque = save_document(vendor_code, 'bank_document', 
                                              d['cheque_file'], d['cheque_file_type'])
                
                # Create vendor
                vendor = Vendor(
                    vendor_code=vendor_code,
                    gstin=d.get('gstin'),
                    pan=d.get('pan'),
                    legal_name=d.get('legal_name'),
                    trade_name=d.get('trade_name'),
                    vendor_type=d.get('vendor_type'),
                    vendor_category=d.get('vendor_category'),
                    company_email=d.get('company_email'),
                    company_phone=d.get('company_phone'),
                    address_line1=d.get('address'),
                    city=d.get('city'),
                    state=d.get('state'),
                    pin_code=d.get('pin'),
                    bank_name=bank_name or None,
                    bank_branch=branch or None,
                    account_number=account or None,
                    ifsc_code=ifsc or None,
                    account_type=acc_type,
                    payment_terms=d.get('payment_terms'),
                    credit_days=d.get('credit_days'),
                    credit_limit=d.get('credit_limit'),
                    rating_delivery=d.get('r_del'),
                    rating_quality=d.get('r_qual'),
                    rating_pricing=d.get('r_price'),
                    rating_overall=d.get('r_overall'),
                    is_msme=is_msme,
                    msme_number=msme_num,
                    doc_gst_certificate=doc_gst,
                    doc_pan_card=doc_pan,
                    doc_cancelled_cheque=doc_cheque,
                    comments=d.get('comments'),
                    status=status,
                    created_by_id=st.session_state.user['id']
                )
                
                session.add(vendor)
                session.flush()
                
                # Add contact
                contact = VendorContact(
                    vendor_id=vendor.id,
                    contact_type="Primary",
                    name=d.get('p_name'),
                    designation=d.get('p_desig'),
                    mobile=d.get('p_mobile'),
                    email=d.get('p_email'),
                    is_primary=True
                )
                session.add(contact)
                
                log_action(session, st.session_state.user['id'], "CREATE",
                          "vendors", vendor.id, f"Registered vendor {vendor_code}")
                
                session.commit()
                st.session_state.v_done = True
                st.rerun()
                
            except Exception as e:
                session.rollback()
                st.error(f"Error: {e}")
            finally:
                session.close()
