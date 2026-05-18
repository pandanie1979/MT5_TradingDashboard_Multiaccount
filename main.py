# main.py - Streamlit entry point
import streamlit as st
import os
from datetime import datetime, timedelta

from tabs import tab_ea_attivi, tab_performance, tab_posizioni, tab_settings
from config import load_mt5_paths, discover_accounts_from_paths


def _ensure_basic_session_state(account_id: str):
    """
    Assicura che le chiavi session state base esistano SEMPRE.
    Evita KeyError nelle funzioni helper.
    """
    start_key = f"date_start_{account_id}"
    end_key = f"date_end_{account_id}"

    if start_key not in st.session_state:
        default_end = datetime.now().date()
        default_start = default_end - timedelta(days=30)
        st.session_state[start_key] = default_start
        st.session_state[end_key] = default_end
        st.session_state[f"basic_init_{account_id}"] = True


@st.cache_data
def load_css():
    """Load CSS with caching to avoid file read on every rerun."""
    try:
        with open("assets/style.css", "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def main():
    """Main application function"""

    st.set_page_config(
        page_title="MT5 Trading Dashboard",
        page_icon="\U0001f4ca",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    css = load_css()
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    st.title("MT5 Trading Dashboard")

    mt5_paths = load_mt5_paths()

    if not mt5_paths:
        st.error("Nessun percorso MT5 trovato. Configura accounts_config.json.")
        st.info(
            "Copia accounts_config.example.json in accounts_config.json "
            "e inserisci i percorsi MT5."
        )
        st.stop()

    all_accounts = discover_accounts_from_paths(mt5_paths)

    if not all_accounts:
        st.error("Nessun account trovato nei percorsi MT5 configurati.")
        st.info("Verifica che ci siano file CSV di trading nei percorsi MT5.")
        st.stop()

    account_ids = list(all_accounts.keys())
    selected_account = st.selectbox(
        "Seleziona Account:",
        account_ids,
        key="global_account_selector"
    )

    if not selected_account:
        st.stop()

    account_info = all_accounts[selected_account]
    account_path = account_info['path']

    _ensure_basic_session_state(selected_account)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Account", selected_account)
    with col2:
        st.metric("File Trading", account_info['trade_files'])
    with col3:
        st.metric("File EA Monitor", account_info['ea_files'])

    tab1, tab2, tab3, tab4 = st.tabs([
        "\U0001f4c8 Performance",
        "\U0001f4ca EA Attivi",
        "\U0001f4b0 Posizioni",
        "⚙️ Impostazioni"
    ])

    with tab1:
        try:
            tab_performance.render(selected_account, account_path, account_info)
        except Exception as e:
            st.error(f"Errore tab Performance: {e}")
            st.exception(e)

    with tab2:
        try:
            tab_ea_attivi.render(selected_account, account_path, account_info)
        except Exception as e:
            st.error(f"Errore tab EA Attivi: {e}")
            st.exception(e)

    with tab3:
        try:
            tab_posizioni.render(selected_account, account_path, account_info)
        except Exception as e:
            st.error(f"Errore tab Posizioni: {e}")
            st.exception(e)

    with tab4:
        try:
            accounts_data = {
                'all_accounts': all_accounts,
                'mt5_paths': mt5_paths,
                'selected_account': selected_account,
            }
            tab_settings.render(accounts_data)
        except Exception as e:
            st.error(f"Errore tab Impostazioni: {e}")
            st.exception(e)


def initialize_session_state_for_account(account_id, trades_data=None):
    """
    Inizializza le chiavi session state necessarie per un account
    """
    start_key = f"date_start_{account_id}"
    end_key = f"date_end_{account_id}"

    if start_key not in st.session_state or end_key not in st.session_state:

        if trades_data is not None and not trades_data.empty:
            data_start = trades_data['OpenDatetime'].min().date()
            data_end = trades_data['OpenDatetime'].max().date()

            default_end = min(datetime.now().date(), data_end)
            default_start = max(data_start, default_end - timedelta(days=30))
        else:
            default_end = datetime.now().date()
            default_start = default_end - timedelta(days=30)

        st.session_state[start_key] = default_start
        st.session_state[end_key] = default_end

    user_modified_key = f"period_user_set_{account_id}"
    if user_modified_key not in st.session_state:
        st.session_state[user_modified_key] = "auto_default"


if __name__ == "__main__":
    main()
