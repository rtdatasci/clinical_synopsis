import requests
import json
import time

class ClinicalTrialsScraper:
    BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

    def search_studies(self, query, page_size=5):
        """
        Search for studies on ClinicalTrials.gov.
        """
        params = {
            "query.term": query,
            "pageSize": page_size,
            "format": "json"
        }
        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('studies', [])
        except requests.exceptions.RequestException as e:
            print(f"Error searching ClinicalTrials.gov: {e}")
            return []

    def get_study_details(self, nct_id):
        """
        Fetch full study details by NCT ID.
        """
        url = f"{self.BASE_URL}/{nct_id}"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching details for {nct_id}: {e}")
            return None

    def map_to_synopsis(self, study_data):
        """
        Map study data to the detailed synopsis format.
        """
        protocol = study_data.get('protocolSection', {})
        id_module = protocol.get('identificationModule', {})
        status_module = protocol.get('statusModule', {})
        sponsor_module = protocol.get('sponsorCollaboratorsModule', {})
        desc_module = protocol.get('descriptionModule', {})
        design_module = protocol.get('designModule', {})
        eligibility_module = protocol.get('eligibilityModule', {})
        outcomes_module = protocol.get('outcomesModule', {})
        
        # Helper to safely get list strings
        def get_list(data_list):
            return ", ".join(data_list) if data_list else "N/A"

        # Extracting Outcomes
        primary_outcomes = outcomes_module.get('primaryOutcomes', [])
        secondary_outcomes = outcomes_module.get('secondaryOutcomes', [])
        
        primary_text = ""
        for outcome in primary_outcomes:
            primary_text += f"*   {outcome.get('measure')}: {outcome.get('description', '')}\n"
            
        secondary_text = ""
        for outcome in secondary_outcomes:
            secondary_text += f"*   {outcome.get('measure')}: {outcome.get('description', '')}\n"

        # Safe extraction
        nct_id = id_module.get('nctId', 'N/A')
        title = id_module.get('officialTitle') or id_module.get('briefTitle', 'N/A')
        phases = get_list(design_module.get('phases', []))
        sponsor = sponsor_module.get('leadSponsor', {}).get('name', 'N/A')
        intervention = "N/A"
        if 'interventions' in protocol.get('armsInterventionsModule', {}):
            intervention = ", ".join([i.get('name') for i in protocol['armsInterventionsModule']['interventions']])
        
        enrollment = design_module.get('enrollmentInfo', {}).get('count', 'N/A')
        enrollment_type = design_module.get('enrollmentInfo', {}).get('type', '')
        
        eligibility_criteria = eligibility_module.get('eligibilityCriteria', 'N/A')
        min_age = eligibility_module.get('minimumAge', 'N/A')
        
        # Formatting as per SYNOPSIS_TEMPLATE.md
        synopsis_text = f"""# Clinical Study Synopsis

**Name of Sponsor/Company:** {sponsor}
**Name of Investigational Product:** {intervention}
**Name of Active Ingredient:** {intervention}
**Protocol Number:** {nct_id}
**Phase:** {phases}
**Study centers:** Multi-site, multi-regional (Assumed)
**Study Title:** {title}

## Objectives

### Primary
{primary_text if primary_text else "*   N/A"}

### Secondary
{secondary_text if secondary_text else "*   N/A"}

## Methodology
**Design:** {design_module.get('studyType', 'N/A')}
**Allocation:** {design_module.get('designInfo', {}).get('allocation', 'N/A')}
**Intervention Model:** {design_module.get('designInfo', {}).get('interventionModel', 'N/A')}
**Primary Purpose:** {design_module.get('designInfo', {}).get('primaryPurpose', 'N/A')}
**Masking:** {design_module.get('designInfo', {}).get('maskingInfo', {}).get('masking', 'N/A')}

**Brief Summary:**
{desc_module.get('briefSummary', 'N/A')}

**Number of participants (Planned):** {enrollment} ({enrollment_type})

## Diagnosis and Main Criteria for Eligibility

### Inclusion Criteria
*   Age >= {min_age}
*   (See below for full text)

### Exclusion Criteria
*   (See below for full text)

**Full Eligibility Criteria Text:**
{eligibility_criteria}
"""
        return synopsis_text

class PubMedScraper:
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    def search_articles(self, query, retmax=5):
        """
        Search for articles on PubMed.
        """
        url = f"{self.BASE_URL}esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": retmax
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('esearchresult', {}).get('idlist', [])
        except requests.exceptions.RequestException as e:
            print(f"Error searching PubMed: {e}")
            return []

    def get_article_details(self, pmid):
        """
        Fetch article details by PMID.
        """
        url = f"{self.BASE_URL}esummary.fcgi"
        params = {
            "db": "pubmed",
            "id": pmid,
            "retmode": "json"
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('result', {}).get(pmid, {})
        except requests.exceptions.RequestException as e:
            print(f"Error fetching details for PMID {pmid}: {e}")
            return None

def main():
    import sys
    # Force UTF-8 output for Windows consoles/redirection
    if sys.stdout.encoding.lower() != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except AttributeError:
            pass # Python < 3.7 or other environment

    print("--- Clinical Study Scraper ---")
    query = input("Enter drug name or condition (e.g., 'pcsk9 inhibitor'): ").strip()
    if not query:
        print("No input provided. Exiting.")
        return

    print(f"\nSearching for: {query}")

    print("\n--- ClinicalTrials.gov Search ---")
    ct_scraper = ClinicalTrialsScraper()
    studies = ct_scraper.search_studies(query)
    print(f"Found {len(studies)} studies.")
    
    if studies:
        first_study_id = studies[0]['protocolSection']['identificationModule']['nctId']
        print(f"Fetching details for {first_study_id}...")
        details = ct_scraper.get_study_details(first_study_id)
        synopsis_text = ct_scraper.map_to_synopsis(details)
        print("\n" + "="*40 + "\nGENERATED SYNOPSIS\n" + "="*40 + "\n")
        print(synopsis_text)
    
    # Additional Info (PubMed)
    print("\n" + "="*40 + "\nADDITIONAL INFORMATION (PubMed)\n" + "="*40 + "\n")
    print(f"Searching PubMed for '{query} clinical trial'...")
    pm_scraper = PubMedScraper()
    pmids = pm_scraper.search_articles(f"{query} clinical trial")
    
    if pmids:
        for pmid in pmids:
            details = pm_scraper.get_article_details(pmid)
            if details:
                print(f"*   **Title:** {details.get('title')}")
                print(f"    **Source:** {details.get('source')} ({details.get('pubdate')})")
                print(f"    **PMID:** {pmid}\n")
    else:
        print("No PubMed articles found.")

if __name__ == "__main__":
    main()
