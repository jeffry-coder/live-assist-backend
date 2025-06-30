from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from agent_toolkit import TOOLKIT
import json
from logging import getLogger
from typing import Literal

logger = getLogger(__name__)

class AiTip(BaseModel):
    tag: Literal["Urgent", "Suggestion", "Info"] = Field(description="Tag for the AI tip")
    content: str = Field(description="Content of the AI tip")

class ToolCall(BaseModel):
    name: str = Field(description="Name of the tool called")
    input: str = Field(description="Input parameters passed to the tool")
    output: str = Field(description="Output or result from the tool call")
    status: str = Field(description="Status of the tool call: success or failed")

class Output(BaseModel):
    aiTips: list[AiTip] = Field(description="List of AI tips")

class Agent:
    def __init__(self, model_name="gpt-4o-2024-08-06"):
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """
You are *LiveCallInsights*, an AI assistant monitoring a live customer service call. 
Analyze the current window of the conversation, in reference to the call history and past call summary if provided.
Use available tools to conduct CRM operations, search company manuals, and suggest email communications when appropriate. 
These tools run silently. Only use the insights to sharpen AI tips. 

- NEVER call the same tool twice with the same input.
- NEVER create AI tips that repeat the same tag *and* message (or close paraphrase) from earlier windows.

Example of violation (DON'T DO THIS):
Window 2: {{ "tag": "Suggestion", "content": "Customer mentioned slow dashboard—consider offering troubleshooting steps." }}
Window 4: {{ "tag": "Suggestion", "content": "Customer said dashboard is slow—maybe offer help." }}

Content of the AI tips should not be more than one sentence. Keep it concise. 
The conversation may not contain direct instructions to invoke tools. You should infer the need for tools from the conversation.

## When to use tools

### 📇 get_contact_by_email

**When:**  
Customer provides or implies their email or identity.

**Trigger example:**  
> "Hi, this is Sarah from sarah@bigco.com"

---

### 🎫 create_support_ticket

**When:**  
Customer reports a product issue, service failure, or recurring problem.

**Trigger example:**  
> "My dashboard hasn't worked all week"

---

### 🛠 update_contact_property

**When:**  
Customer provides new or updated personal info.

**Trigger example:**  
> "I changed my phone number—it’s 555-1234 now"

---

### 💼 get_contact_deals

**When:**  
Customer asks about pricing, deals, trials, or renewals.

**Trigger example:**  
> "I think my trial ends next week. What are my options?"

---

### 🏢 search_contacts_by_company

**When:**  
Customer gives company name but not their email.

**Trigger example:**  
> "I'm Tom from Globex Corp."

---

### 📩 send_email

**When:**  
Customer requests confirmation, follow-up, or can’t stay on the call.

**Trigger example:**  
> "Just email me the instructions, I’m heading into a meeting"

---

### 📘 search_company_manuals

**When:**  
Customer asks about internal policy, product instructions, or process.

**Trigger example:**  
> "What’s the refund policy for digital purchases?"

## Example Output
```json
{{
  "aiTips": [
    {{
      "tag": "Urgent",
      "content": "Customer has mentioned billing issues three times in the last 10 minutes—consider escalating to billing specialist."
    }},
    {{
      "tag": "Suggestion", 
      "content": "Customer is using 90 percent of their current plan capacity—good opportunity to discuss upgrade options."
    }}
  ]
}}
```
            """)
            ,("user", "Please analyze this conversation:\n{transcript}")
        ])
        
        model = ChatOpenAI(model=model_name, temperature=0.0)
        self.agent = create_react_agent(model, TOOLKIT, response_format=Output)
    
    def extract_tool_calls_from_trace(self, model_trace) -> list[ToolCall]:
        """Extract tool calls from the model trace with consistent IO handling"""
        tool_calls = []
        
        if 'messages' not in model_trace:
            return tool_calls
        
        messages = model_trace['messages']
        
        for i, message in enumerate(messages):
            # Check if this is an AIMessage with tool calls
            if (hasattr(message, 'tool_calls') and 
                message.tool_calls and 
                len(message.tool_calls) > 0):
                
                for tool_call in message.tool_calls:
                    tool_response = ""
                    status = "success"
                    
                    # Look for the corresponding ToolMessage
                    if i + 1 < len(messages):
                        next_msg = messages[i + 1]
                        if (hasattr(next_msg, 'tool_call_id') and 
                            next_msg.tool_call_id == tool_call['id']):
                            
                            tool_response = json.loads(next_msg.content)
                            status = tool_response['status']
                            if tool_call['name'] == 'search_company_manuals' and status == 'success':
                                message = tool_response['sources']
                            else:
                                message = tool_response['message']
                    
                    # Ensure consistent input format
                    tool_input = tool_call.get('args', {})
                    tool_calls.append(ToolCall(
                        name=tool_call['name'],
                        input=json.dumps(tool_input),
                        output=json.dumps(message),
                        status=status
                    ))
        
        return tool_calls
    
    def analyze_transcript(self, conversation) -> tuple[Output, list[ToolCall]]:          
        formatted_prompt = self.prompt_template.format_messages(transcript=json.dumps(conversation))
        
        logger.info('Invoking agent')
        response = self.agent.invoke({"messages": formatted_prompt})
        
        # Extract tool calls from the trace
        tool_calls = self.extract_tool_calls_from_trace(response)
        
        return response['structured_response'].aiTips, tool_calls

def main(conversation: list):
    agent = Agent()
    ai_tips, tool_calls = agent.analyze_transcript(conversation)
    return ai_tips, tool_calls

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    def roleplay_simulation():
        print("=== Customer Service Call Simulation ===")
        print("Type 'quit' to exit the simulation")
        print("Enter dialogue for both agent and customer\n")
        
        call_history = []
        
        while True:
            # Get agent input
            agent_input = input("Agent: ").strip()
            if agent_input.lower() == 'quit':
                break
                
            # Get customer input
            customer_input = input("Customer: ").strip()
            if customer_input.lower() == 'quit':
                break
            
            # Add current turns to conversation
            call_history.extend([
                {"speaker": "customer support", "transcript": agent_input},
                {"speaker": "client", "transcript": customer_input}
            ])
            
            # Analyze the transcript
            print("\n🤖 Analyzing conversation...")

            ai_tips, tool_calls = main(call_history)
            
            print("\n📋 AI Tips:")
            if ai_tips:
                for tip in ai_tips:
                    print(f"   {tip.tag}: {tip.content}")
            else:
                print("   No new insights at this time")
            
            print("\n🔧 Tool Calls:")
            if tool_calls:
                for tool_call in tool_calls:
                    print(f"   {tool_call.name} ({tool_call.status})")
                    print(f"     Input: {tool_call.input}")
                    print(f"     Output: {tool_call.output}")
            else:
                print("   No tools were invoked")
            
            # Add AI response to chat history to prevent duplicate responses
            ai_response_entry = {
                "speaker": "ai_assistant",
                "aiTips": [{"tag": tip.tag, "content": tip.content} for tip in ai_tips],
                "toolCalls": [{"name": tc.name, "input": tc.input, "output": tc.output, "status": tc.status} for tc in tool_calls]
            }
            call_history.append(ai_response_entry)
            
            print("\n" + "="*50)
    
    roleplay_simulation()