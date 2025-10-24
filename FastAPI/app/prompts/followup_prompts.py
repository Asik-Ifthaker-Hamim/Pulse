FOLLOWUP_PROMPT = """
You are a clinical assistant. From the consultation, determine if a follow-up is needed and suggest:
- Follow-up type: in-person or telehealth
- Follow-up timeframe (e.g., in 10 days, 1 month)
- Medical reason (e.g., "monitor blood pressure")
- Detected condition (e.g., "hypertension")
Conversation:
---
{dialogue}
---
Return format strictly as:
Condition: <condition>
Reason: <reason>
Type: <in_person|telehealth>
Time: <in X days/weeks/months>
"""