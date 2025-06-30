import requests
import os
import json
from urllib.parse import urlparse
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_aws import AmazonKendraRetriever

# Load environment variables
load_dotenv()

# Global API key from environment
HUBSPOT_API_KEY = os.getenv('HUBSPOT_API_KEY')
AMAZON_KENDRA_INDEX_ID = os.getenv('AMAZON_KENDRA_INDEX_ID')

# Global headers for API requests
HEADERS = {
    "Authorization": f"Bearer {HUBSPOT_API_KEY}",
    "Content-Type": "application/json"
}

# Initialize Kendra retriever
kendra_retriever = AmazonKendraRetriever(
    index_id=AMAZON_KENDRA_INDEX_ID,
    min_score_confidence=0.5
)

@tool
def get_contact_by_email(email: str) -> str:
    """
    Retrieve contact information from HubSpot by email address.
    """
    try:
        url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
        payload = {
            "filterGroups": [{"filters": [{"propertyName": "email", "operator": "EQ", "value": email}]}],
            "properties": ["email", "firstname", "lastname", "company", "phone"],
            "limit": 1
        }
        resp = requests.post(url, headers=HEADERS, json=payload)
        if resp.status_code != 200:
            return json.dumps({"status": "failed", "message": f"Error retrieving contact (status {resp.status_code})."})
        data = resp.json().get('results', [])
        if not data:
            return json.dumps({"status": "failed", "message": f"No contact found for email: {email}."})
        c = data[0]['properties']
        fname = c.get('firstname', '<no first name>')
        lname = c.get('lastname', '<no last name>')
        comp = c.get('company', '<no company>')
        phone = c.get('phone', '<no phone>')
        msg = f"Found contact: {fname} {lname}, Email: {email}, Company: {comp}, Phone: {phone}."
        return json.dumps({"status": "success", "message": msg})
    except Exception as e:
        return json.dumps({"status": "failed", "message": f"Exception retrieving contact: {e}."})

@tool
def create_support_ticket(subject: str, description: str, priority: str) -> str:
    """
    Create a support ticket in HubSpot for a contact.
    """
    try:
        url = "https://api.hubapi.com/crm/v3/objects/tickets"
        payload = {"properties": {
            "subject": subject,
            "content": description,
            "hs_ticket_priority": priority.upper(),
            "hs_pipeline_stage": "1"
        }}
        resp = requests.post(url, headers=HEADERS, json=payload)
        if resp.status_code != 201:
            return json.dumps({"status": "failed", "message": f"Error creating ticket (status {resp.status_code})."})
        tid = resp.json().get('id', '<unknown>')
        return json.dumps({"status": "success", "message": f"Ticket created successfully with ID {tid}."})
    except Exception as e:
        return json.dumps({"status": "failed", "message": f"Exception creating ticket: {e}."})

@tool
def update_contact_property(contact_id: str, property_name: str, property_value: str) -> str:
    """
    Update a specific property of a contact in HubSpot.
    """
    try:
        url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
        payload = {"properties": {property_name: property_value}}
        resp = requests.patch(url, headers=HEADERS, json=payload)
        if resp.status_code != 200:
            return json.dumps({"status": "failed", "message": f"Error updating contact (status {resp.status_code})."})
        return json.dumps({"status": "success", "message": f"Updated {property_name} to '{property_value}' for contact {contact_id}."})
    except Exception as e:
        return json.dumps({"status": "failed", "message": f"Exception updating contact: {e}."})

@tool
def get_contact_deals(contact_id: str) -> str:
    """
    Retrieve all deals associated with a contact.
    """
    try:
        url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}/associations/deals"
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code != 200:
            return json.dumps({"status": "failed", "message": f"Error retrieving deals (status {resp.status_code})."})
        results = resp.json().get('results', [])
        if not results:
            return json.dumps({"status": "failed", "message": f"No deals found for contact {contact_id}."})
        summaries = []
        for d in results:
            did = d.get('id')
            deal_url = f"https://api.hubapi.com/crm/v3/objects/deals/{did}?properties=dealname,amount"
            dr = requests.get(deal_url, headers=HEADERS)
            if dr.status_code == 200:
                props = dr.json().get('properties', {})
                name = props.get('dealname', '<no name>')
                amt = props.get('amount', '<no amount>')
                summaries.append(f"{name} (${amt})")
        msg = f"Found {len(summaries)} deals: {', '.join(summaries)}."
        return json.dumps({"status": "success", "message": msg})
    except Exception as e:
        return json.dumps({"status": "failed", "message": f"Exception retrieving deals: {e}."})

@tool
def search_contacts_by_company(company_name: str) -> str:
    """
    Search for contacts by company name.
    """
    try:
        url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
        payload = {
            "filterGroups": [{"filters": [{"propertyName": "company", "operator": "CONTAINS_TOKEN", "value": company_name}]}],
            "properties": ["email", "firstname", "lastname"],
            "limit": 10
        }
        resp = requests.post(url, headers=HEADERS, json=payload)
        if resp.status_code != 200:
            return json.dumps({"status": "failed", "message": f"Error searching contacts (status {resp.status_code})."})
        results = resp.json().get('results', [])
        if not results:
            return json.dumps({"status": "failed", "message": f"No contacts found for company '{company_name}'."})
        contacts = [f"{c['properties'].get('firstname','')} {c['properties'].get('lastname','')} ({c['properties'].get('email','')})" for c in results]
        msg = f"Found {len(contacts)} contacts: {', '.join(contacts[:5])}."
        return json.dumps({"status": "success", "message": msg})
    except Exception as e:
        return json.dumps({"status": "failed", "message": f"Exception searching contacts: {e}."})

@tool
def send_email(subject: str, body: str) -> str:
    """
    Send an email with the given subject and body.
    """
    return json.dumps({"status": "success", "message": f"Email queued with subject '{subject}'."})

@tool
def search_company_manuals(query: str) -> str:
    """
    Search company manuals using Amazon Kendra to help with customer support solutions.
    
    Args:
        query: Search query for company manuals
        
    Returns:
        Search results from company manuals or error message
    """
    try:        
        # Invoke Kendra index directly for flexible result processing
        results = kendra_retriever.invoke(query)
        
        if not results:
            return json.dumps({
                "status": "failed",
                "message": f"No results found for query: '{query}'",
            })
        
        # Format results for agent consumption
        formatted_results = []
        sources = []
        for result in results[:3]:  # Limit to top 5 results
            content = result.page_content[:1000] if hasattr(result, 'page_content') else str(result)
            source = result.metadata.get('source', 'Unknown') if hasattr(result, 'metadata') else 'Unknown'
            # Extract filename from S3 URL without extension
            if source.startswith('https://'):
                # Parse URL to get the filename
                parsed_url = urlparse(source)
                filename = os.path.basename(parsed_url.path)
                # Remove file extension
                source = os.path.splitext(filename)[0]
            
            sources.append(source)
            formatted_results.append(content)
        
        return json.dumps({
            "status": "success",
            "message": "\n\n".join(formatted_results),
            "sources": "Read these documents: " + ", ".join(list(set(sources)))
        })
    
    except Exception as e:
        return json.dumps({
            "status": "failed",
            "message": f"Error searching company manuals: {str(e)}"
        })

# Toolkit constant containing all HubSpot tools
TOOLKIT = [
    get_contact_by_email,
    create_support_ticket,
    update_contact_property,
    get_contact_deals,
    search_contacts_by_company,
    send_email,
    search_company_manuals
]
