"""
Prarthi ERP System
Main Application Entry Point
"""

import streamlit as st
import bcrypt
from datetime import datetime
from database import SessionLocal, User, init_db

st.set_page_config(
    page_title="Prarthi ERP",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
init_db()

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1rem;
        color: #888;
        margin-top: 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .welcome-box {
        background: #1E1E2E;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #1E88E5;
    }
</style>
""", unsafe_allow_html=True)


def verify_password(plain_password, hashed_password):
    """Verify password against hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def login_user(username, password):
    """Authenticate user"""
    session = SessionLocal()
    user = session.query(User).filter(User.username == username).first()
    
    if user and verify_password(password, user.password_hash):
        # Update last login
        user.last_login = datetime.utcnow()
        session.commit()
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'full_name': user.full_name,
            'role': user.role,
            'department': user.department
        }
        session.close()
        return user_data
    
    session.close()
    return None


# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None


# ============ LOGIN PAGE ============
if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("")
        st.markdown("")
        st.markdown('<p class="main-header">🏢 Prarthi ERP</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Enterprise Resource Planning System</p>', unsafe_allow_html=True)
        st.markdown("---")
        
        with st.form("login_form"):
            st.subheader("Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
            
            if submitted:
                if username and password:
                    user = login_user(username, password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.warning("Please enter username and password")
        
        st.markdown("---")
        with st.expander("Demo credentials"):
            st.code("""
Purchase: purchase_user / Purchase@123
Accounts: accounts_user / Accounts@123
Admin: admin / Admin@123
            """)

# ============ DASHBOARD ============
else:
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.user['full_name']}")
        st.caption(f"{st.session_state.user['role']} • {st.session_state.user['department']}")
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.rerun()
    
    # Main content
    st.markdown('<p class="main-header">🏢 Prarthi ERP</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Enterprise Resource Planning System</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Welcome box
    st.markdown(f"""
    <div class="welcome-box">
        <h3>Welcome back, {st.session_state.user['full_name']}!</h3>
        <p>Role: {st.session_state.user['role']} | Department: {st.session_state.user['department']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("")
    
    # Quick stats
    session = SessionLocal()
    from database import Vendor
    
    total_vendors = session.query(Vendor).count()
    active_vendors = session.query(Vendor).filter(Vendor.status == "Active").count()
    session.close()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total vendors", total_vendors)
    with col2:
        st.metric("Active vendors", active_vendors)
    with col3:
        st.metric("Pending POs", "0")
    with col4:
        st.metric("Today's MRV", "0")
    
    st.markdown("---")
    
    # Quick actions based on role
    st.subheader("Quick actions")
    
    role = st.session_state.user['role']
    
    if role in ["Purchase", "Management"]:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            #### 🛒 Procurement
            - Register new vendor
            - View vendor library
            - Create purchase order
            """)
    
    if role in ["Accounts", "Management"]:
        col1, col2, col3 = st.columns(3)
        with col2 if role == "Management" else col1:
            st.markdown("""
            #### 💼 Accounts
            - Verify vendor details
            - Payment processing
            - Invoice management
            """)
    
    if role in ["Stores", "Management"]:
        col1, col2, col3 = st.columns(3)
        with col3 if role == "Management" else col1:
            st.markdown("""
            #### 📦 Stores
            - Material receipt
            - Stock management
            - Issue materials
            """)
    
    st.markdown("---")
    st.caption(f"© 2026 Prarthi Bhambere Limited. Last login: {datetime.now().strftime('%d %b %Y, %H:%M')}")
