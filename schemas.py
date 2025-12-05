from pydantic import BaseModel, Field


class CodeRequest(BaseModel):
    code: str


class FeedbackRequest(BaseModel):
    function_name: str
    code: str
    explanation: str
    rating: int  # 1 or -1


class CodeIssue(BaseModel):
    issue_type: str = Field(
        ...,
        description="Category of the issue, e.g., 'Time Complexity', 'Security', 'Redundant Logic', 'Naming Convention'",
    )
    severity: str = Field(..., description="Critical, High, Medium, or Low")
    line_number: int = Field(
        ...,
        description="The specific line number where the issue is found (approximate)",
    )
    description: str = Field(
        ...,
        description="A concise explanation of why this is bad logic",
    )
    fix_suggestion: str = Field(
        ...,
        description="A short snippet showing how to fix it (if applicable)",
    )


class CodeSenseiAnalysis(BaseModel):
    complexity_estimate: str = Field(
        ...,
        description="The Big O time complexity (e.g., O(n), O(n^2))",
    )
    plain_english_explanation: str = Field(
        ...,
        description="A simple summary of what this code block does, for a Junior Dev.",
    )
    issues: list[CodeIssue] = Field(
        default_factory=list,
        description="A list of specific bad practices found in the code.",
    )
    quality_score: int = Field(
        ...,
        description="A generic score from 1-10 (10 being perfect code)",
    )
