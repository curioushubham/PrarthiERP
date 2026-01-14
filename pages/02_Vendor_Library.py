"""
Vendor Library - Wide Table with Horizontal Scroll
"""

import streamlit as st
import pandas as pd
import os
import base64
from datetime import datetime
from database import SessionLocal, Vendor, VendorContact
from io import BytesIO

st.set_page_config(page_title="Vendor Library", page_icon="📚", layout="wide")

# Check login
if not st.session_state.get('authenticated'):
    st.error("Please login to access this module")
    st.stop()

DOCUMENTS_DIR = r"C:\Users\Admin\Desktop\PrarthiERP\documents"


def generate_vendor_pdf(vendor):
    """Generate PDF for a vendor"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.units import inch
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
        elements = []
        styles = getSampleStyleSheet()
        
        elements.append(Paragraph(f"Vendor: {vendor.vendor_code} - {vendor.trade_name}", styles['Heading1']))
        elements.append(Spacer(1, 20))
        
        data = [
            ["Field", "Value"],
            ["Vendor code", vendor.vendor_code or ""],
            ["Trade name", vendor.trade_name or ""],
            ["Legal name", vendor.legal_name or ""],
            ["GSTIN", vendor.gstin or ""],
            ["PAN", vendor.pan or ""],
            ["Category", vendor.vendor_category or ""],
            ["Type", vendor.vendor_type or ""],
            ["Email", vendor.company_email or ""],
            ["Phone", vendor.company_phone or ""],
            ["Address", vendor.address_line1 or ""],
            ["City", vendor.city or ""],
            ["State", vendor.state or ""],
            ["PIN code", vendor.pin_code or ""],
            ["Bank name", vendor.bank_name or "Not provided"],
            ["Branch", vendor.bank_branch or ""],
            ["Account number", vendor.account_number or ""],
            ["IFSC code", vendor.ifsc_code or ""],
            ["Payment terms", vendor.payment_terms or ""],
            ["Credit days", str(vendor.credit_days or "")],
            ["Credit limit", f"₹{vendor.credit_limit:,.0f}" if vendor.credit_limit else ""],
            ["Rating", f"{vendor.rating_overall or 0}/5"],
            ["Status", vendor.status or ""],
            ["MSME", vendor.msme_number if vendor.is_msme else "No"],
        ]
        
        table = Table(data, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, 1), (0, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('PADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(table)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
    except:
        return None


# ============ MAIN ============
st.title("📚 Vendor Library")

session = SessionLocal()
vendors = session.query(Vendor).order_by(Vendor.created_at.desc()).all()

# Stats row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total vendors", len(vendors))
col2.metric("Active", len([v for v in vendors if v.status == "Active"]))
col3.metric("Inactive", len([v for v in vendors if v.status == "Inactive"]))
col4.metric("MSME registered", len([v for v in vendors if v.is_msme]))

st.markdown("---")

# Filters
col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
with col1:
    search = st.text_input("Search", placeholder="Search by name, GSTIN, code...", label_visibility="collapsed")
with col2:
    status_filter = st.selectbox("Status", ["All", "Active", "Inactive"], label_visibility="collapsed")
with col3:
    categories = ["All"] + list(set([v.vendor_category for v in vendors if v.vendor_category]))
    category_filter = st.selectbox("Category", categories, label_visibility="collapsed")
with col4:
    col_a, col_b = st.columns(2)
    export_selected = col_a.button("📥 Export selected")
    export_all = col_b.button("📄 Export all")

# Filter logic
filtered = vendors
if search:
    s = search.lower()
    filtered = [v for v in filtered if s in (v.trade_name or '').lower() or 
                s in (v.legal_name or '').lower() or s in (v.gstin or '').lower() or 
                s in (v.vendor_code or '').lower()]
if status_filter != "All":
    filtered = [v for v in filtered if v.status == status_filter]
if category_filter != "All":
    filtered = [v for v in filtered if v.vendor_category == category_filter]

st.caption(f"Showing {len(filtered)} of {len(vendors)} vendors")

# Build dataframe for display
if filtered:
    # Create data for table
    table_data = []
    for v in filtered:
        table_data.append({
            "Code": v.vendor_code,
            "Vendor name": v.trade_name or v.legal_name,
            "Legal name": v.legal_name,
            "GSTIN": v.gstin,
            "PAN": v.pan,
            "Category": v.vendor_category,
            "Type": v.vendor_type,
            "City": v.city,
            "State": v.state,
            "Phone": v.company_phone,
            "Email": v.company_email,
            "Bank": v.bank_name or "-",
            "Account": v.account_number or "-",
            "IFSC": v.ifsc_code or "-",
            "Credit limit": f"₹{v.credit_limit:,.0f}" if v.credit_limit else "-",
            "Credit days": v.credit_days,
            "Payment terms": v.payment_terms,
            "Rating": f"⭐ {v.rating_overall or 0}",
            "Status": v.status,
            "MSME": "Yes" if v.is_msme else "No",
        })
    
    df = pd.DataFrame(table_data)
    
    # Display with horizontal scroll
    st.markdown("""
    <style>
    .vendor-table-container {
        width: 100%;
        overflow-x: auto;
        margin: 10px 0;
    }
    .vendor-table-container table {
        width: max-content;
        min-width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Use st.dataframe with horizontal scroll
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=400,
        column_config={
            "Code": st.column_config.TextColumn("Code", width="small"),
            "Vendor name": st.column_config.TextColumn("Vendor name", width="medium"),
            "Legal name": st.column_config.TextColumn("Legal name", width="medium"),
            "GSTIN": st.column_config.TextColumn("GSTIN", width="medium"),
            "PAN": st.column_config.TextColumn("PAN", width="small"),
            "Category": st.column_config.TextColumn("Category", width="medium"),
            "Type": st.column_config.TextColumn("Type", width="small"),
            "City": st.column_config.TextColumn("City", width="small"),
            "State": st.column_config.TextColumn("State", width="small"),
            "Phone": st.column_config.TextColumn("Phone", width="small"),
            "Email": st.column_config.TextColumn("Email", width="medium"),
            "Bank": st.column_config.TextColumn("Bank", width="medium"),
            "Account": st.column_config.TextColumn("Account", width="medium"),
            "IFSC": st.column_config.TextColumn("IFSC", width="small"),
            "Credit limit": st.column_config.TextColumn("Credit limit", width="small"),
            "Credit days": st.column_config.NumberColumn("Credit days", width="small"),
            "Payment terms": st.column_config.TextColumn("Payment terms", width="small"),
            "Rating": st.column_config.TextColumn("Rating", width="small"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "MSME": st.column_config.TextColumn("MSME", width="small"),
        }
    )
    
    st.markdown("---")
    
    # Action buttons for each vendor
    st.subheader("Vendor actions")
    
    selected_vendor = st.selectbox(
        "Select vendor for actions",
        options=[f"{v.vendor_code} - {v.trade_name}" for v in filtered],
        label_visibility="collapsed",
        placeholder="Select a vendor to view details, documents or download PDF..."
    )
    
    if selected_vendor:
        vendor_code = selected_vendor.split(" - ")[0]
        vendor = next((v for v in filtered if v.vendor_code == vendor_code), None)
        
        if vendor:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("👁️ View full details", use_container_width=True):
                    st.session_state['show_vendor_detail'] = vendor.id
            
            with col2:
                if st.button("📎 View documents", use_container_width=True):
                    st.session_state['show_vendor_docs'] = vendor.id
            
            with col3:
                pdf_data = generate_vendor_pdf(vendor)
                if pdf_data:
                    st.download_button(
                        "📄 Download PDF",
                        pdf_data,
                        f"{vendor.vendor_code}.pdf",
                        "application/pdf",
                        use_container_width=True
                    )
                else:
                    st.button("📄 Download PDF", disabled=True, use_container_width=True)
                    st.caption("Install reportlab for PDF")
            
            # Show details popup
            if st.session_state.get('show_vendor_detail') == vendor.id:
                with st.expander(f"📋 Full details: {vendor.trade_name}", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("**Company information**")
                        st.write(f"Code: {vendor.vendor_code}")
                        st.write(f"Legal name: {vendor.legal_name}")
                        st.write(f"Trade name: {vendor.trade_name}")
                        st.write(f"Type: {vendor.vendor_type}")
                        st.write(f"Category: {vendor.vendor_category}")
                        st.write(f"GSTIN: {vendor.gstin}")
                        st.write(f"PAN: {vendor.pan}")
                        if vendor.is_msme:
                            st.write(f"MSME: {vendor.msme_number}")
                    
                    with col2:
                        st.markdown("**Contact information**")
                        st.write(f"Email: {vendor.company_email}")
                        st.write(f"Phone: {vendor.company_phone}")
                        st.write(f"Address: {vendor.address_line1}")
                        st.write(f"City: {vendor.city}")
                        st.write(f"State: {vendor.state}")
                        st.write(f"PIN: {vendor.pin_code}")
                        
                        contacts = session.query(VendorContact).filter_by(vendor_id=vendor.id).all()
                        if contacts:
                            st.markdown("**Contact person**")
                            for c in contacts:
                                st.write(f"{c.name} ({c.designation})")
                                st.write(f"📞 {c.mobile}")
                    
                    with col3:
                        st.markdown("**Bank information**")
                        st.write(f"Bank: {vendor.bank_name or 'Not provided'}")
                        st.write(f"Branch: {vendor.bank_branch or '-'}")
                        st.write(f"Account: {vendor.account_number or '-'}")
                        st.write(f"IFSC: {vendor.ifsc_code or '-'}")
                        st.write(f"Type: {vendor.account_type or '-'}")
                        
                        st.markdown("**Payment terms**")
                        st.write(f"Terms: {vendor.payment_terms}")
                        st.write(f"Credit days: {vendor.credit_days}")
                        st.write(f"Credit limit: ₹{vendor.credit_limit:,.0f}" if vendor.credit_limit else "Not set")
                        
                        st.markdown("**Ratings**")
                        st.write(f"Delivery: {'⭐' * int(vendor.rating_delivery or 0)}")
                        st.write(f"Quality: {'⭐' * int(vendor.rating_quality or 0)}")
                        st.write(f"Pricing: {'⭐' * int(vendor.rating_pricing or 0)}")
                        st.write(f"Overall: {'⭐' * int(vendor.rating_overall or 0)}")
                    
                    if st.button("Close details"):
                        st.session_state['show_vendor_detail'] = None
                        st.rerun()
            
            # Show documents popup
            if st.session_state.get('show_vendor_docs') == vendor.id:
                with st.expander(f"📎 Documents: {vendor.trade_name}", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("**GST certificate**")
                        if vendor.doc_gst_certificate and os.path.exists(vendor.doc_gst_certificate):
                            ext = vendor.doc_gst_certificate.split('.')[-1].lower()
                            with open(vendor.doc_gst_certificate, 'rb') as f:
                                file_bytes = f.read()
                            if ext in ['jpg', 'jpeg', 'png']:
                                st.image(file_bytes, width=200)
                            else:
                                b64 = base64.b64encode(file_bytes).decode()
                                st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="GST_Certificate.pdf">📥 Download GST certificate</a>', unsafe_allow_html=True)
                        else:
                            st.caption("Not uploaded")
                    
                    with col2:
                        st.markdown("**PAN card**")
                        if vendor.doc_pan_card and os.path.exists(vendor.doc_pan_card):
                            ext = vendor.doc_pan_card.split('.')[-1].lower()
                            with open(vendor.doc_pan_card, 'rb') as f:
                                file_bytes = f.read()
                            if ext in ['jpg', 'jpeg', 'png']:
                                st.image(file_bytes, width=200)
                            else:
                                b64 = base64.b64encode(file_bytes).decode()
                                st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="PAN_Card.pdf">📥 Download PAN card</a>', unsafe_allow_html=True)
                        else:
                            st.caption("Not uploaded")
                    
                    with col3:
                        st.markdown("**Bank document**")
                        if vendor.doc_cancelled_cheque and os.path.exists(vendor.doc_cancelled_cheque):
                            ext = vendor.doc_cancelled_cheque.split('.')[-1].lower()
                            with open(vendor.doc_cancelled_cheque, 'rb') as f:
                                file_bytes = f.read()
                            if ext in ['jpg', 'jpeg', 'png']:
                                st.image(file_bytes, width=200)
                            else:
                                b64 = base64.b64encode(file_bytes).decode()
                                st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="Bank_Document.pdf">📥 Download bank document</a>', unsafe_allow_html=True)
                        else:
                            st.caption("Not uploaded")
                    
                    if st.button("Close documents"):
                        st.session_state['show_vendor_docs'] = None
                        st.rerun()

    # Export all as CSV
    if export_all:
        csv = df.to_csv(index=False)
        st.download_button(
            "⬇️ Download CSV",
            csv,
            "vendors_export.csv",
            "text/csv"
        )

else:
    st.info("No vendors found. Register your first vendor to get started.")

session.close()

st.markdown("---")
st.caption("💡 Tip: Scroll the table horizontally to see all columns. Select a vendor below for more actions.")
