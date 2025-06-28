from pydantic import BaseModel, Field
from typing import List, Literal

class Sentiment(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Sentiment score, integer from 0 (negative) to 100 (positive)")
    label: Literal["Positive", "Neutral", "Negative"] = Field(..., description="Sentiment category label based on score")

class Satisfaction(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Customer satisfaction score, 0 (least) to 100 (most)")
    prediction: Literal["Satisfied", "Neutral", "Dissatisfied"] = Field(..., description="Predicted satisfaction category from score")

class Emotion(BaseModel):
    emotion: str = Field(..., description="Identified emotion, e.g., 'frustration' or 'relief'")
    intensity: int = Field(..., ge=0, le=100, description="Intensity of emotion on a scale from 0 to 100")

class CallMetrics(BaseModel):
    duration: str = Field(..., description="Total call duration in MM:SS format")
    agentTalkTime: int = Field(..., ge=0, le=100, description="Percentage of total call time spoken by agent")
    customerTalkTime: int = Field(..., ge=0, le=100, description="Percentage of total call time spoken by customer")
    holdTime: int = Field(..., ge=0, le=100, description="Percentage of total call time spent on hold or waiting")

class IssueResolution(BaseModel):
    resolved: bool = Field(..., description="Whether the customer's issue was resolved during this call")
    category: str = Field(..., description="Issue category, e.g., 'login-issue' or 'billing'")
    resolutionTimeMinutes: int = Field(..., ge=0, description="Minutes elapsed from call start to resolution")
    escalationRisk: int = Field(..., ge=0, le=100, description="Likelihood (0-100) that the call will require escalation or follow-up")

class AgentPerformance(BaseModel):
    professionalismScore: int = Field(..., ge=0, le=100, description="Agent professionalism rating from 0 to 100")
    empathyScore: int = Field(..., ge=0, le=100, description="Agent empathy rating from 0 to 100")
    knowledgeScore: int = Field(..., ge=0, le=100, description="Agent knowledge rating from 0 to 100")
    avgResponseLatencySeconds: int = Field(..., ge=0, description="Median response latency by agent in seconds")

class MemoryBox(BaseModel):
    deliverables: List[str] = Field(..., description="Key deliverables or outcomes from the call to remember")
    improvementAreas: List[str] = Field(..., description="Areas for agent improvement or focus next time")

class AnalyticsOutput(BaseModel):
    sentiment: Sentiment = Field(..., description="Overall call sentiment metrics")
    satisfaction: Satisfaction = Field(..., description="Overall customer satisfaction metrics")
    emotions: List[Emotion] = Field(..., description="Top detected emotions and their intensities")
    callMetrics: CallMetrics = Field(..., description="Key call performance metrics")
    issueResolution: IssueResolution = Field(..., description="Issue resolution details for this call")
    agentPerformance: AgentPerformance = Field(..., description="Agent effectiveness metrics")
    keyInsights: List[str] = Field(..., description="Top 3 takeaways or insights from this call")
    actionItems: List[str] = Field(..., description="Up to 3 actionable next steps for agent or team")
    tags: List[str] = Field(..., description="Relevant tags for categorization or drill-down analysis")
    memory: MemoryBox = Field(..., description="Memory box for next-call coaching and reasoning")
