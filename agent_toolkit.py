import requests
import json
import os
from urllib.parse import urlparse
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_aws import AmazonKendraRetriever
import time

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
    Uses the search endpoint as HubSpot does not support direct lookup by email in the path.
    Args:
        email: The email address of the contact to retrieve
    Returns:
        JSON string containing contact details or error message
    """
    try:
        url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
        data = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "email",
                            "operator": "EQ",
                            "value": email
                        }
                    ]
                }
            ],
            "properties": ["email", "firstname", "lastname", "company", "phone"],
            "limit": 1
        }
        response = requests.post(url, headers=HEADERS, json=data)
        if response.status_code == 200:
            results = response.json().get("results", [])
            if results:
                return json.dumps({
                    "status": "success",
                    "message": results[0]
                })
            else:
                return json.dumps({
                    "status": "failed",
                    "message": f"No contact found for email: {email}"
                })
        else:
            return json.dumps({
                "status": "failed",
                "message": f"Error retrieving contact: {response.status_code} - {response.text}"
            })
    except Exception as e:
        return json.dumps({
            "status": "failed",
            "message": f"Error: {str(e)}"
        })


@tool
def create_support_ticket(subject: str, description: str, priority: str) -> str:
    """
    Create a support ticket in HubSpot for a contact.
    Associates the ticket with the contact using the associations field.
    Args:
        contact_id: HubSpot contact ID
        subject: Ticket subject line
        description: Detailed description of the issue
        priority: Ticket priority (LOW, MEDIUM, HIGH)
    Returns:
        JSON string with ticket details or error message
    """
    try:
        url = "https://api.hubapi.com/crm/v3/objects/tickets"
        data = {
            "properties": {
                "hs_ticket_priority": priority.upper(),
                "subject": subject,
                "content": description,
                "hs_pipeline_stage": "1"  # Default to 'New' stage; adjust as needed
            },
        }
        response = requests.post(url, headers=HEADERS, json=data)
        if response.status_code == 201:
            return json.dumps({
                "status": "success",
                "message": response.json()
            })
        else:
            return json.dumps({
                "status": "failed",
                "message": f"Error creating ticket: {response.status_code} - {response.text}"
            })
    except Exception as e:
        return json.dumps({
            "status": "failed",
            "message": f"Error: {str(e)}"
        })


@tool
def log_call_activity(contact_id: str, call_duration: int, call_outcome: str, notes: str) -> str:
    """
    Log a customer service call as an activity in HubSpot.
    Adds required hs_timestamp property.
    Args:
        contact_id: HubSpot contact ID
        call_duration: Duration of call in seconds
        call_outcome: Outcome of the call (COMPLETED, NO_ANSWER, BUSY, etc.)
        notes: Call notes and summary
    Returns:
        JSON string with activity details or error message
    """
    try:
        url = "https://api.hubapi.com/crm/v3/objects/calls"
        data = {
            "properties": {
                "hs_call_duration": str(call_duration),
                "hs_call_status": call_outcome.upper(),
                "hs_call_body": notes,
                "hs_call_direction": "INBOUND",
                "hs_timestamp": str(int(time.time() * 1000))  # Current time in ms
            },
            "associations": [
                {
                    "to": {"id": contact_id},
                    "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 194}]
                }
            ]
        }
        response = requests.post(url, headers=HEADERS, json=data)
        if response.status_code == 201:
            return json.dumps({
                "status": "success",
                "message": response.json()
            })
        else:
            return json.dumps({
                "status": "failed",
                "message": f"Error logging call: {response.status_code} - {response.text}"
            })
    except Exception as e:
        return json.dumps({
            "status": "failed",
            "message": f"Error: {str(e)}"
        })


@tool
def update_contact_property(contact_id: str, property_name: str, property_value: str) -> str:
    """
    Update a specific property of a contact in HubSpot.
    
    Args:
        contact_id: HubSpot contact ID
        property_name: Name of the property to update
        property_value: New value for the property
        
    Returns:
        Success message or error message
    """
    try:
        url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
        
        data = {
            "properties": {
                property_name: property_value
            }
        }
        
        response = requests.patch(url, headers=HEADERS, json=data)
        
        if response.status_code == 200:
            return json.dumps({
                "status": "success",
                "message": f"Successfully updated {property_name} to {property_value}"
            })
        else:
            return json.dumps({
                "status": "failed",
                "message": f"Error updating contact: {response.status_code} - {response.text}"
            })
            
    except Exception as e:
        return json.dumps({
            "status": "failed",
            "message": f"Error: {str(e)}"
        })


@tool
def get_contact_deals(contact_id: str) -> str:
    """
    Retrieve all deals associated with a contact, returning deal summaries.
    Args:
        contact_id: HubSpot contact ID
    Returns:
        JSON string containing a list of deal summaries or error message
    """
    try:
        url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}/associations/deals"
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            return json.dumps({
                "status": "failed",
                "message": f"Error retrieving deals: {response.status_code} - {response.text}"
            })
        deals_data = response.json().get("results", [])
        deal_summaries = []
        for deal in deals_data:
            deal_id = deal.get("id")
            if not deal_id:
                continue
            # Fetch deal details
            deal_url = f"https://api.hubapi.com/crm/v3/objects/deals/{deal_id}?properties=dealname,amount,dealstage,closedate"
            deal_resp = requests.get(deal_url, headers=HEADERS)
            if deal_resp.status_code == 200:
                deal_info = deal_resp.json()
                properties = deal_info.get("properties", {})
                deal_summaries.append({
                    "id": deal_id,
                    "name": properties.get("dealname"),
                    "amount": properties.get("amount"),
                    "stage": properties.get("dealstage"),
                    "close_date": properties.get("closedate")
                })
            else:
                deal_summaries.append({
                    "id": deal_id,
                    "error": f"Could not fetch details: {deal_resp.status_code}"
                })
        return json.dumps({
            "status": "success",
            "message": deal_summaries
        })
    except Exception as e:
        return json.dumps({
            "status": "failed",
            "message": f"Error: {str(e)}"
        })


@tool
def search_contacts_by_company(company_name: str) -> str:
    """
    Search for contacts by company name in HubSpot.
    
    Args:
        company_name: Name of the company to search for
        
    Returns:
        JSON string containing matching contacts or error message
    """
    try:
        url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
        
        data = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "company",
                            "operator": "CONTAINS_TOKEN",
                            "value": company_name
                        }
                    ]
                }
            ],
            "properties": ["email", "firstname", "lastname", "company", "phone"],
            "limit": 10
        }
        
        response = requests.post(url, headers=HEADERS, json=data)
        
        if response.status_code == 200:
            return json.dumps({
                "status": "success",
                "message": response.json()
            })
        else:
            return json.dumps({
                "status": "failed",
                "message": f"Error searching contacts: {response.status_code} - {response.text}"
            })
            
    except Exception as e:
        return json.dumps({
            "status": "failed",
            "message": f"Error: {str(e)}"
        })


@tool
def get_contact_timeline(contact_id: str) -> str:
    """
    Retrieve the activity timeline for a contact.
    
    Args:
        contact_id: HubSpot contact ID
        
    Returns:
        JSON string containing timeline activities or error message
    """
    try:
        url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}/associations/calls"
        
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code == 200:
            return json.dumps({
                "status": "success",
                "message": response.json()
            })
        else:
            return json.dumps({
                "status": "failed",
                "message": f"Error retrieving timeline: {response.status_code} - {response.text}"
            })
            
    except Exception as e:
        return json.dumps({
            "status": "failed",
            "message": f"Error: {str(e)}"
        })


@tool
def send_email(subject: str, body: str) -> str:
    """
    Send an email with the given subject and body.
    
    Args:
        subject: Email subject line
        body: Email body content
        
    Returns:
        Confirmation message
    """
    return json.dumps({
        "status": "success",
        "message": "Email will be sent shortly"
    })


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
                "status": "success",
                "message": f"No results found for query: '{query}'",
                "sources": []
            })
        
        # Format results for agent consumption
        formatted_results = []
        sources = []
        for i, result in enumerate(results[:3], 1):  # Limit to top 5 results
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
            formatted_results.append(f"{i}. Source: {source}\nContent: {content}\n")
        
        return json.dumps({
            "status": "success",
            "message": "\n".join(formatted_results),
            "sources": list(set(sources))
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
    get_contact_timeline,
    send_email, # Suggested action to frontend
    search_company_manuals
]