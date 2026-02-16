import streamlit as st
import hashlib

def make_password_hash(password):
    """Create a hash of the password"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password():
    """Returns `True` if the user has entered the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets.get("dashboard_password", ""):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    # Return True if password already validated
    if st.session_state.get("password_correct", False):
        return True

    # Show password input
    st.markdown("## 🔐 Health Dashboard Login")
    st.text_input(
        "Password", 
        type="password", 
        on_change=password_entered, 
        key="password"
    )
    
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    
    return False
