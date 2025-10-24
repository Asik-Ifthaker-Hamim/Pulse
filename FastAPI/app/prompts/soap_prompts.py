SOAP_TEMPLATE = """
You are an AI assistant generating a SOAP note and prescription draft from a consultation.

Conversation:
---
{dialogue}
---

**First, format the main output strictly as:**
**SOAP Note**
Subjective: ...
Objective: ...
Assessment: ...
Plan: ...

**Draft Prescription**
Medication: [Medication Name 1]
Dosage: [e.g., 500mg]
Frequency: [e.g., twice daily]
Route: [e.g., Oral]
Duration: [e.g., 7 days]
Instructions: [e.g., Take with food]

Medication: [Medication Name 2, if applicable]
Dosage: ...
Frequency: ...
... (continue for all medications)

---
**Second, after the main output above, provide a separate list of all medication names mentioned in the prescription section, formatted exactly like this:**
MEDICATION_LIST: [Medication Name 1], [Medication Name 2], ...
"""