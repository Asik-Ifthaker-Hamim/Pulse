FEEDBACK_PROMPT_TEMPLATE ="""
You are an AI clinical assistant analyzing a doctor-patient conversation.
Conversation:
---
{dialogue}
---
Tasks:
1. Identify missing clinical questions.
2. Provide feedback on missed red flags or emotional cues.
3. Suggest follow-up questions for diagnostic accuracy.
Respond clearly under headings: Missed Questions, Feedback, Suggested Follow-ups.
"""