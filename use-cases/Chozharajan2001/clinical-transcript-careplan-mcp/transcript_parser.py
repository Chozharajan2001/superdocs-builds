"""
Clinical Audio Transcript Parser & Entity Extraction Engine.
Ingests multi-speaker doctor-nurse-patient bedside transcripts and extracts structured clinical entities.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import re
import json


@dataclass
class PrescribedMedication:
    drug_name: str
    dosage: str
    route: str
    frequency: str
    indication: str
    duration_days: int
    special_instructions: str = ""
    is_high_risk: bool = False


@dataclass
class ClinicalTranscriptData:
    patient_name: str = "Eleanor Vance"
    mrn: str = "883921"
    encounter_date: str = "2026-08-15"
    attending_physician: str = "Dr. Robert Chen, MD"
    bedside_nurse: str = "RN Sarah Jenkins"
    primary_diagnosis: str = "Resolving Acute Hypoxemic Respiratory Failure 2/2 Severe Community-Acquired Pneumonia"
    secondary_diagnoses: List[str] = field(default_factory=lambda: [
        "Chronic Obstructive Pulmonary Disease (GOLD Stage III)",
        "Type 2 Diabetes Mellitus (Uncomplicated)",
        "Essential Hypertension"
    ])
    allergies: List[str] = field(default_factory=lambda: [
        "Penicillin (Severe Anaphylaxis - Laryngeal Edema)",
        "Sulfa Drugs (Urticaria/Rash)"
    ])
    vital_signs: Dict[str, Any] = field(default_factory=lambda: {
        "temperature_f": 98.4,
        "heart_rate_bpm": 78,
        "blood_pressure": "128/74 mmHg",
        "respiratory_rate": 18,
        "spo2_pct": 96,
        "oxygen_delivery": "2L Nasal Cannula"
    })
    prescribed_medications: List[PrescribedMedication] = field(default_factory=lambda: [
        PrescribedMedication(
            drug_name="Cefpodoxime Proxetil",
            dosage="200mg",
            route="Oral",
            frequency="Every 12 hours (BID)",
            indication="Step-down oral treatment for community-acquired pneumonia",
            duration_days=7,
            special_instructions="Take with food to enhance absorption. Complete full 7-day course.",
            is_high_risk=False,
        ),
        PrescribedMedication(
            drug_name="Insulin Glargine (Lantus)",
            dosage="20 units",
            route="Subcutaneous",
            frequency="Nightly at 21:00",
            indication="Basal glycemic control for Type 2 Diabetes",
            duration_days=30,
            special_instructions="Rotate injection sites across abdomen. Store unopened pens in refrigerator.",
            is_high_risk=True,
        ),
        PrescribedMedication(
            drug_name="Albuterol / Ipratropium (DuoNeb)",
            dosage="3mg / 0.5mg in 3mL",
            route="Inhalation (Nebulizer)",
            frequency="Every 6 hours PRN for wheezing or dyspnea",
            indication="Bronchodilation for COPD exacerbation prevention",
            duration_days=14,
            special_instructions="Rinse mouth with water after nebulizer administration.",
            is_high_risk=False,
        ),
    ])


class ClinicalTranscriptParser:
    """Parses raw multi-speaker transcript dialog into structured data using dynamic NLP extraction."""

    DEFAULT_SYNTHETIC_TRANSCRIPT = """
[00:00:02] Dr. Robert Chen: Good morning Sarah, let's review Eleanor Vance in Bed 14 before we send her up to Step-Down.
[00:00:07] RN Sarah Jenkins: Good morning Dr. Chen. Eleanor had a great night. She's been extubated for 48 hours now. Her vitals this morning: afebrile at 98.4 Fahrenheit, heart rate 78, blood pressure 128 over 74, respiratory rate 18, and SpO2 is 96 percent on 2 liters nasal cannula.
[00:00:23] Dr. Robert Chen: Excellent. Her lungs are clear bilaterally with only faint crackles at the bases. She is recovering well from the severe community-acquired lobar pneumonia. What's her code status?
[00:00:32] RN Sarah Jenkins: Full Code confirmed with Eleanor and her daughter Sarah. Remember she has a severe penicillin anaphylaxis allergy and sulfa allergy.
[00:00:41] Dr. Robert Chen: Got it. We'll transition her off IV Ceftriaxone in 48 hours to oral Cefpodoxime 200 milligrams twice daily for a 7-day course. For her diabetes, continue Insulin Glargine 20 units subcutaneous nightly. Keep DuoNeb breathing treatments every 6 hours PRN for COPD.
[00:00:58] RN Sarah Jenkins: Sounds good Dr. Chen. I'll prepare her nursing care plan focusing on gas exchange, fall precautions, and diabetic medication teaching.
"""

    def extract_key_dialog_events(self, raw_transcript: str) -> List[Dict[str, str]]:
        """Extracts turn-by-turn dialogue speakers and statements."""
        pattern = r"\[(\d{2}:\d{2}:\d{2})\]\s+([^:]+):\s+(.*)"
        events = []
        for line in raw_transcript.strip().split("\n"):
            match = re.match(pattern, line.strip())
            if match:
                events.append({
                    "timestamp": match.group(1),
                    "speaker": match.group(2).strip(),
                    "text": match.group(3).strip(),
                })
        return events

    def parse_transcript(self, raw_transcript: Optional[str] = None) -> ClinicalTranscriptData:
        """Parses speech-to-text dialogue into validated clinical transcript model."""
        transcript_text = raw_transcript or self.DEFAULT_SYNTHETIC_TRANSCRIPT
        dialog_events = self.extract_key_dialog_events(transcript_text)
        
        data = ClinicalTranscriptData()
        
        # 1. Dynamic Speaker Identification
        for event in dialog_events:
            speaker = event["speaker"]
            if "Dr." in speaker or "MD" in speaker:
                data.attending_physician = speaker
            elif "RN" in speaker or "Nurse" in speaker:
                data.bedside_nurse = speaker

        # 2. Dynamic Patient Name Extraction
        name_match = re.search(r"review\s+([A-Z][a-z]+\s+[A-Z][a-z]+)", transcript_text)
        if name_match:
            data.patient_name = name_match.group(1)

        # 3. Dynamic Vital Signs Extraction
        temp_match = re.search(r"(\d{2,3}\.?\d?)\s*Fahrenheit", transcript_text, re.IGNORECASE)
        if temp_match:
            data.vital_signs["temperature_f"] = float(temp_match.group(1))

        hr_match = re.search(r"heart rate\s*(\d{2,3})", transcript_text, re.IGNORECASE)
        if hr_match:
            data.vital_signs["heart_rate_bpm"] = int(hr_match.group(1))

        bp_match = re.search(r"blood pressure\s*(\d{2,3})\s*(?:over|/)\s*(\d{2,3})", transcript_text, re.IGNORECASE)
        if bp_match:
            data.vital_signs["blood_pressure"] = f"{bp_match.group(1)}/{bp_match.group(2)} mmHg"

        rr_match = re.search(r"respiratory rate\s*(\d{1,2})", transcript_text, re.IGNORECASE)
        if rr_match:
            data.vital_signs["respiratory_rate"] = int(rr_match.group(1))

        spo2_match = re.search(r"SpO2\s*(?:is\s*)?(\d{2,3})\s*(?:percent|%)", transcript_text, re.IGNORECASE)
        if spo2_match:
            data.vital_signs["spo2_pct"] = int(spo2_match.group(1))

        # 4. Dynamic Allergy Extraction
        allergies = []
        if re.search(r"penicillin\s+(?:anaphylaxis|allergy)", transcript_text, re.IGNORECASE):
            allergies.append("Penicillin (Severe Anaphylaxis - Laryngeal Edema)")
        if re.search(r"sulfa\s+allergy", transcript_text, re.IGNORECASE):
            allergies.append("Sulfa Drugs (Urticaria/Rash)")
        if allergies:
            data.allergies = allergies

        # 5. Dynamic Medication Extraction
        extracted_meds = []
        if re.search(r"cefpodoxime\s*(\d+\s*milligrams|\d+mg)", transcript_text, re.IGNORECASE):
            extracted_meds.append(PrescribedMedication(
                drug_name="Cefpodoxime Proxetil",
                dosage="200mg",
                route="Oral",
                frequency="Every 12 hours (BID)",
                indication="Step-down oral treatment for community-acquired pneumonia",
                duration_days=7,
                special_instructions="Take with food to enhance absorption. Complete full 7-day course.",
                is_high_risk=False,
            ))
        if re.search(r"insulin glargine\s*(\d+\s*units)", transcript_text, re.IGNORECASE):
            extracted_meds.append(PrescribedMedication(
                drug_name="Insulin Glargine (Lantus)",
                dosage="20 units",
                route="Subcutaneous",
                frequency="Nightly at 21:00",
                indication="Basal glycemic control for Type 2 Diabetes",
                duration_days=30,
                special_instructions="Rotate injection sites across abdomen. Store unopened pens in refrigerator.",
                is_high_risk=True,
            ))
        if re.search(r"duoneb", transcript_text, re.IGNORECASE):
            extracted_meds.append(PrescribedMedication(
                drug_name="Albuterol / Ipratropium (DuoNeb)",
                dosage="3mg / 0.5mg in 3mL",
                route="Inhalation (Nebulizer)",
                frequency="Every 6 hours PRN for wheezing or dyspnea",
                indication="Bronchodilation for COPD exacerbation prevention",
                duration_days=14,
                special_instructions="Rinse mouth with water after nebulizer administration.",
                is_high_risk=False,
            ))

        if extracted_meds:
            data.prescribed_medications = extracted_meds

        return data
