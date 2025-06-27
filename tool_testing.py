"""
Tool Testing Script for Agent Toolkit

This script tests all tools in agent_toolkit.py with dummy data to verify functionality.
"""

import json
from dotenv import load_dotenv
from agent_toolkit import (
    get_contact_by_email,
    create_support_ticket,
    log_call_activity,
    update_contact_property,
    get_contact_deals,
    search_contacts_by_company,
    get_contact_timeline,
    send_email,
    search_company_manuals
)

# Load environment variables
load_dotenv()

def test_tool(tool_name, tool_func, test_data):
    """Test a single tool with provided data"""
    print(f"\n{'='*60}")
    print(f"Testing: {tool_name}")
    print(f"{'='*60}")
    print(f"Input: {test_data}")
    print("-" * 60)
    
    try:
        result = tool_func.invoke(test_data)
        print(f"Output: {result}")
        
        # Try to parse as JSON to validate structure
        try:
            parsed = json.loads(result)
            status = parsed.get('status', 'unknown')
        except json.JSONDecodeError:
            print("Output is not valid JSON")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    
    print("-" * 60)

def run_all_tests():
    """Run tests for all tools with dummy data"""
    print("🧪 AGENT TOOLKIT TESTING")
    print("Testing all tools with dummy data...")
    
    # Test data for each tool
    test_cases = [
        {
            "name": "get_contact_by_email",
            "func": get_contact_by_email,
            "data": {"email": "bh@hubspot.com"}
        },
        {
            "name": "create_support_ticket", 
            "func": create_support_ticket,
            "data": {
                "subject": "Test Ticket - Login Issues",
                "description": "Customer cannot access their account after password reset",
                "priority": "HIGH"
            }
        },
        # {
        #     "name": "log_call_activity",
        #     "func": log_call_activity,
        #     "data": {
        #         "contact_id": "12345",
        #         "call_duration": 450,
        #         "call_outcome": "COMPLETED",
        #         "notes": "Helped customer resolve billing question and updated account preferences"
        #     }
        # },
        {
            "name": "update_contact_property",
            "func": update_contact_property,
            "data": {
                "contact_id": "149785901771",
                "property_name": "phone",
                "property_value": "+1-555-123-4567"
            }
        },
        {
            "name": "get_contact_deals",
            "func": get_contact_deals,
            "data": {"contact_id": "149785901771"}
        },
        {
            "name": "search_contacts_by_company",
            "func": search_contacts_by_company,
            "data": {"company_name": "HubSpot"}
        },
        {
            "name": "get_contact_timeline",
            "func": get_contact_timeline,
            "data": {"contact_id": "149785901771"}
        },
        {
            "name": "send_email",
            "func": send_email,
            "data": {
                "subject": "Follow-up: Your Support Request",
                "body": "Hi there! Thank you for contacting our support team. We've resolved your login issue and your account should now be accessible. Please let us know if you need any further assistance."
            }
        },
        {
            "name": "search_company_manuals",
            "func": search_company_manuals,
            "data": {"query": "password reset procedure"}
        }
    ]
    
    # Run tests for each tool
    for test_case in test_cases:
        test_tool(
            test_case["name"],
            test_case["func"], 
            test_case["data"]
        )
    
    print(f"\n{'='*60}")
    print("✅ All tool tests completed!")
    print(f"{'='*60}")

def test_single_tool(tool_name):
    """Test a specific tool by name"""
    tools_map = {
        "get_contact_by_email": (get_contact_by_email, {"email": "bh@hubspot.com"}),
        "create_support_ticket": (create_support_ticket, {
            "subject": "Test Ticket - Login Issues",
            "description": "Customer cannot access their account after password reset",
            "priority": "HIGH"
        }),
        "log_call_activity": (log_call_activity, {
            "contact_id": "149785901771",
            "call_duration": 450,
            "call_outcome": "COMPLETED",
            "notes": "Helped customer resolve billing question and updated account preferences"
        }),
        "update_contact_property": (update_contact_property, {
            "contact_id": "149785901771",
            "property_name": "phone",
            "property_value": "+1-555-123-4567"
        }),
        "get_contact_deals": (get_contact_deals, {"contact_id": "149785901771"}),
        "search_contacts_by_company": (search_contacts_by_company, {"company_name": "HubSpot"}),
        "get_contact_timeline": (get_contact_timeline, {"contact_id": "149785901771"}),
        "send_email": (send_email, {
            "subject": "Follow-up: Your Support Request",
            "body": "Hi there! Thank you for contacting our support team. We've resolved your login issue and your account should now be accessible. Please let us know if you need any further assistance."
        }),
        "search_company_manuals": (search_company_manuals, {"query": "password reset procedure"})
    }
    
    if tool_name in tools_map:
        func, data = tools_map[tool_name]
        test_tool(tool_name, func, data)
    else:
        print(f"❌ Tool '{tool_name}' not found!")
        print("Available tools:", list(tools_map.keys()))

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Test specific tool
        tool_name = sys.argv[1]
        print(f"🔧 Testing single tool: {tool_name}")
        test_single_tool(tool_name)
    else:
        # Test all tools
        run_all_tests()