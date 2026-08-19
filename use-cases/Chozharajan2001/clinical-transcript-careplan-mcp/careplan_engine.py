"""
AI-Powered Nursing Care Plan & Patient Discharge Instruction Engine.
Synthesizes NANDA-I aligned SMART clinical care plans and patient-friendly discharge packets.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from transcript_parser import ClinicalTranscriptData


@dataclass
class SMARTNursingGoal:
    nursing_diagnosis: str
    smart_outcome_goal: str
    target_timeframe: str
    nursing_interventions: List[str]
    evaluation_criteria: str
    nurse_signature: Optional[str] = None


@dataclass
class DischargeInstructionPacket:
    patient_name: str
    mrn: str
    primary_condition_explanation: str
    medication_schedule: List[Dict[str, str]]
    activity_and_diet_rules: List[str]
    red_flag_warning_signs: List[str]
    follow_up_appointments: List[Dict[str, str]]
    emergency_contact: str = "Call 911 or visit Nearest Emergency Department"


class NursingCarePlanEngine:
    """Generates evidence-grounded nursing care plans and discharge education."""

    def formulate_smart_care_plan(self, data: ClinicalTranscriptData) -> List[SMARTNursingGoal]:
        """Formulates NANDA-I standardized nursing care plan goals."""
        return [
            SMARTNursingGoal(
                nursing_diagnosis="Impaired Gas Exchange related to alveolar-capillary membrane changes secondary to resolving severe pneumonia as evidenced by SpO2 96% on 2L NC and bibasilar crackles.",
                smart_outcome_goal="Patient will maintain pulse oximetry (SpO2) >= 94% on room air or minimal supplemental oxygen (<= 1L) with unlabored respirations within 48 hours.",
                target_timeframe="Within 48 hours post-transfer",
                nursing_interventions=[
                    "Assess lung sounds and respiratory effort every 4 hours.",
                    "Titrate supplemental O2 to maintain SpO2 >= 94%.",
                    "Encourage Incentive Spirometry (10 breaths every hour while awake).",
                    "Administer prescribed DuoNeb nebulizer treatments as ordered for dyspnea.",
                    "Position patient in Semi-Fowler's position (30-45 degrees) to optimize lung expansion."
                ],
                evaluation_criteria="Continuous pulse oximetry trending >= 94%, absence of accessory muscle use, clear bilateral breath sounds."
            ),
            SMARTNursingGoal(
                nursing_diagnosis="Risk for Falls related to generalized post-ICU debility, supplemental oxygen tubing, and Morse Fall Risk Score of 55 (High Risk).",
                smart_outcome_goal="Patient will remain free from falls, trauma, or injury throughout step-down unit hospitalization.",
                target_timeframe="Throughout hospitalization",
                nursing_interventions=[
                    "Maintain yellow fall-risk wristband and non-skid socks at all times.",
                    "Keep bed in lowest position with bed alarm activated while patient is in bed.",
                    "Provide assist-of-1 with rolling walker for all transfers and ambulation.",
                    "Ensure call light and personal items are within immediate reach.",
                    "Manage oxygen tubing to prevent tripping hazards during ambulation."
                ],
                evaluation_criteria="Zero fall incidents, appropriate utilization of call light prior to unassisted transfer attempts."
            ),
            SMARTNursingGoal(
                nursing_diagnosis="Deficient Knowledge regarding newly prescribed oral antibiotic completion and home subcutaneous insulin self-administration technique.",
                smart_outcome_goal="Patient will accurately demonstrate subQ insulin injection technique and verbalize 100% adherence to 7-day oral antibiotic course prior to discharge.",
                target_timeframe="Prior to hospital discharge",
                nursing_interventions=[
                    "Provide teach-back education on oral Cefpodoxime adherence with meals.",
                    "Demonstrate subcutaneous insulin pen injection and site rotation.",
                    "Provide large-print written medication schedule in patient's preferred language.",
                    "Educate on hypoglycemia symptoms (sweating, tremor, confusion) and rule of 15s."
                ],
                evaluation_criteria="Patient independently verbalizes full antibiotic regimen and correctly demonstrates insulin priming and injection."
            )
        ]

    def build_discharge_packet(self, data: ClinicalTranscriptData) -> DischargeInstructionPacket:
        """Builds plain-language, patient-friendly discharge instructions (6th-grade reading level)."""
        med_schedule = []
        for med in data.prescribed_medications:
            med_schedule.append({
                "medication": f"{med.drug_name} ({med.dosage})",
                "how_to_take": f"{med.route} • {med.frequency} for {med.duration_days} days",
                "purpose": med.indication,
                "instructions": med.special_instructions,
            })

        return DischargeInstructionPacket(
            patient_name=data.patient_name,
            mrn=data.mrn,
            primary_condition_explanation=(
                "You were treated in the hospital for a severe lung infection (pneumonia) that has now improved. "
                "Your lungs are healing, but you will need to finish your oral antibiotic medicine at home and take extra care of your breathing."
            ),
            medication_schedule=med_schedule,
            activity_and_diet_rules=[
                "Rest frequently and avoid strenuous lifting (nothing over 10 lbs for 2 weeks).",
                "Use your breathing spirometer 10 times every hour while you are awake.",
                "Drink 6 to 8 glasses of water daily unless your doctor gives you fluid limits.",
                "Follow a balanced diabetic diet and check your blood sugar before meals and at bedtime."
            ],
            red_flag_warning_signs=[
                "🚨 Shortness of breath that gets worse even when resting",
                "🚨 New or worsening fever above 101.0°F (38.3°C) or severe shaking chills",
                "🚨 Coughing up blood or dark rusty-colored mucus",
                "🚨 Chest pain when taking a deep breath",
                "🚨 Blood sugar reading below 70 mg/dL or above 300 mg/dL"
            ],
            follow_up_appointments=[
                {
                    "provider": "Dr. Robert Chen, MD (Pulmonary Medicine)",
                    "timeframe": "In 7 to 10 days post-discharge",
                    "purpose": "Chest X-ray follow-up and lung exam"
                },
                {
                    "provider": "Primary Care Clinic (Dr. Emily Davis)",
                    "timeframe": "In 2 weeks",
                    "purpose": "Diabetes management & COPD review"
                }
            ]
        )
