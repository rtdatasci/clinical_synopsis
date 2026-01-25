
import streamlit as st
from scraper import ClinicalTrialsScraper, PubMedScraper
from supabase import create_client, Client
import os

# Initialize Supabase client
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception:
        return None

def main():
    st.set_page_config(page_title="Clinical Study Synopsis Generator", layout="wide")
    
    st.title("Clinical Study Synopsis Generator")
    st.markdown("""
    Generate clinical study synopses from **ClinicalTrials.gov** and find relevant **PubMed** articles.
    All searches are saved to a **Supabase** database.
    """)
    
    supabase = init_supabase()
    if not supabase:
        st.warning("Supabase credentials not found in secrets. History features will be disabled. Please check `.streamlit/secrets.toml`.")

    # Create tabs
    tab1, tab2 = st.tabs(["New Search", "Search Database"])
    
    # --- Tab 1: New Search ---
    with tab1:
        st.header("New Search")
        query = st.text_input("Drug Name or Condition (Search live data)", placeholder="e.g., pcsk9 inhibitor")
        
        if st.button("Generate Synopsis"):
            if not query:
                st.warning("Please enter a search term.")
                return
                
            with st.spinner(f"Searching for '{query}'..."):
                # 1. Search ClinicalTrials.gov
                ct_scraper = ClinicalTrialsScraper()
                studies = ct_scraper.search_studies(query)
                
                if not studies:
                    st.error("No studies found on ClinicalTrials.gov.")
                    return
                
                # Use the first study found
                first_study_id = studies[0]['protocolSection']['identificationModule']['nctId']
                st.success(f"Found {len(studies)} studies. Using the first result: **{first_study_id}**")
                
                # Get details and map to synopsis
                details = ct_scraper.get_study_details(first_study_id)
                synopsis_text = ""
                
                if details:
                    synopsis_text = ct_scraper.map_to_synopsis(details)
                    
                    st.subheader("Generated Synopsis")
                    with st.expander("View Rendered Synopsis", expanded=True):
                        st.markdown(synopsis_text)
                    
                    st.subheader("Copy Synopsis Markdown")
                    st.code(synopsis_text, language="markdown")
                    
                    # Log to Supabase (Deduplication)
                    if supabase:
                        try:
                            # Check if this query already exists (case-insensitive)
                            existing = supabase.table("searches").select("id").ilike("query", query).execute()
                            
                            data = {
                                "query": query,
                                "top_study_id": first_study_id,
                                "synopsis_text": synopsis_text,
                                "num_studies_found": len(studies),
                                "created_at": "now()" # Refresh timestamp on update
                            }
                            
                            if existing.data:
                                # Update existing record
                                record_id = existing.data[0]['id']
                                supabase.table("searches").update(data).eq("id", record_id).execute()
                                st.toast("Search history updated!", icon="🔄")
                            else:
                                # Insert new record
                                supabase.table("searches").insert(data).execute()
                                st.toast("Search saved to history!", icon="💾")
                        except Exception as e:
                            st.error(f"Failed to save to database: {e}")
                else:
                    st.error("Failed to fetch study details.")
                
                # 2. Search PubMed
                st.markdown("---")
                st.subheader("Additional Information (PubMed)")
                
                pm_scraper = PubMedScraper()
                pmids = pm_scraper.search_articles(f"{query} clinical trial")
                
                if pmids:
                    for pmid in pmids:
                        details = pm_scraper.get_article_details(pmid)
                        if details:
                            st.markdown(f"**{details.get('title', 'No Title')}**")
                            st.markdown(f"*Source:* {details.get('source', 'Unknown')} ({details.get('pubdate', 'N/A')}) | *PMID:* {pmid}")
                            st.markdown("---")
                else:
                    st.info("No PubMed articles found.")

    # --- Tab 2: Search Database ---
    with tab2:
        st.header("Search Database History")
        if not supabase:
            st.error("Supabase is not configured.")
        else:
            db_query = st.text_input("Filter saved searches by keyword", placeholder="e.g., aspirin")
            
            # Fetch latest searches
            try:
                query_builder = supabase.table("searches").select("*").order("created_at", desc=True)
                
                if db_query:
                    # Filter by query text
                    query_builder = query_builder.ilike("query", f"%{db_query}%")
                
                response = query_builder.execute()
                results = response.data
                
                if results:
                    st.write(f"Found {len(results)} saved searches.")
                    for row in results:
                        with st.expander(f"{row['created_at'][:19]} - {row['query']} (Study: {row['top_study_id']})"):
                            st.text_area("Synopsis", row['synopsis_text'], height=200, key=f"hist_{row['id']}")
                else:
                    st.info("No saved searches found matching your criteria.")
                    
            except Exception as e:
                st.error(f"Error fetching from database: {e}")

if __name__ == "__main__":
    main()
