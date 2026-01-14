"""
Database Models and Configuration
Prarthi ERP System
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database setup
DATABASE_URL = "sqlite:///./data/prarthi_erp.db"

# Ensure data directory exists
os.makedirs("./data", exist_ok=True)
os.makedirs("./documents", exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============ USER MODEL ============
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100))
    role = Column(String(50), nullable=False)
    department = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)


# ============ VENDOR MODEL ============
class Vendor(Base):
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, index=True)
    vendor_code = Column(String(20), unique=True, nullable=False)
    
    # Statutory
    gstin = Column(String(15))
    pan = Column(String(10))
    legal_name = Column(String(200))
    trade_name = Column(String(200))
    
    # Classification
    vendor_type = Column(String(50))
    vendor_category = Column(String(100))
    
    # Contact
    company_email = Column(String(100))
    company_phone = Column(String(15))
    website = Column(String(200))
    
    # Address
    address_line1 = Column(String(250))
    address_line2 = Column(String(250))
    city = Column(String(100))
    state = Column(String(100))
    pin_code = Column(String(10))
    country = Column(String(50), default="India")
    
    # Bank details
    bank_name = Column(String(100))
    bank_branch = Column(String(100))
    account_number = Column(String(30))
    ifsc_code = Column(String(15))
    account_type = Column(String(20))
    
    # Credit terms
    payment_terms = Column(String(50))
    credit_days = Column(Integer, default=30)
    credit_limit = Column(Float, default=0)
    
    # Ratings
    rating_delivery = Column(Float, default=0)
    rating_quality = Column(Float, default=0)
    rating_pricing = Column(Float, default=0)
    rating_overall = Column(Float, default=0)
    
    # MSME
    is_msme = Column(Boolean, default=False)
    msme_number = Column(String(50))
    msme_category = Column(String(20))
    
    # Documents - File paths
    doc_gst_certificate = Column(String(500))
    doc_pan_card = Column(String(500))
    doc_cancelled_cheque = Column(String(500))
    doc_msme_certificate = Column(String(500))
    
    # Status
    status = Column(String(20), default="Active")
    comments = Column(Text)
    
    # Audit
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_by_id = Column(Integer, ForeignKey("users.id"))
    modified_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    contacts = relationship("VendorContact", back_populates="vendor")


class VendorContact(Base):
    __tablename__ = "vendor_contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    contact_type = Column(String(50))
    name = Column(String(100))
    designation = Column(String(100))
    mobile = Column(String(15))
    email = Column(String(100))
    is_primary = Column(Boolean, default=False)
    
    vendor = relationship("Vendor", back_populates="contacts")


# ============ AUDIT LOG ============
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(50))
    table_name = Column(String(50))
    record_id = Column(Integer)
    details = Column(Text)
    ip_address = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)


# ============ HELPER FUNCTIONS ============
def get_next_vendor_code(session):
    """Generate next vendor code like V-0001, V-0002, etc."""
    last_vendor = session.query(Vendor).order_by(Vendor.id.desc()).first()
    if last_vendor:
        last_num = int(last_vendor.vendor_code.split('-')[1])
        return f"V-{str(last_num + 1).zfill(4)}"
    return "V-0001"


def log_action(session, user_id, action, table_name, record_id, details=""):
    """Log an action to audit trail"""
    log = AuditLog(
        user_id=user_id,
        action=action,
        table_name=table_name,
        record_id=record_id,
        details=details
    )
    session.add(log)


def init_db():
    """Initialize database and create default users"""
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    
    # Check if users exist
    if session.query(User).count() == 0:
        import bcrypt
        
        default_users = [
            {"username": "admin", "password": "Admin@123", "full_name": "System Administrator", "role": "Management", "department": "Admin"},
            {"username": "purchase_user", "password": "Purchase@123", "full_name": "Purchase Team", "role": "Purchase", "department": "Procurement"},
            {"username": "accounts_user", "password": "Accounts@123", "full_name": "Accounts Team", "role": "Accounts", "department": "Finance"},
            {"username": "stores_user", "password": "Stores@123", "full_name": "Stores Team", "role": "Stores", "department": "Warehouse"},
        ]
        
        for user_data in default_users:
            password_hash = bcrypt.hashpw(user_data["password"].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user = User(
                username=user_data["username"],
                password_hash=password_hash,
                full_name=user_data["full_name"],
                role=user_data["role"],
                department=user_data["department"]
            )
            session.add(user)
        
        session.commit()
    
    session.close()


# Initialize on import
init_db()
