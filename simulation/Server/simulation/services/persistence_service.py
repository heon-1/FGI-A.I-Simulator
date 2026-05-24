"""
Persistence Service for saving simulation data to Database
"""
import uuid
from django.shortcuts import get_object_or_404
from users.models import Organization, OrganizationMember
from simulation.models import (
    Persona as PersonaModel,
    Questionnaire as QuestionnaireModel,
    Scenario as ScenarioModel,
    SimulationSession as SessionModel,
    JourneyMap as JourneyMapModel
)
from simulation.types import (
    Persona as PydanticPersona,
    Questionnaire as PydanticQuestionnaire,
    Scenario as PydanticScenario,
    Transcript as PydanticTranscript,
    JourneyMap as PydanticJourneyMap
)

class PersistenceService:
    @staticmethod
    def validate_access(user, organization_id: str):
        """Check if user is a member of the organization"""
        # Convert UUID string to object if needed
        org_id = str(organization_id)
        
        # Check membership
        exists = OrganizationMember.objects.filter(
            user__id=user.id,
            organization__id=org_id
        ).exists()
        
        if not exists:
            raise PermissionError("User is not a member of this organization")
            
        return Organization.objects.get(id=org_id)

    @staticmethod
    def save_personas(org, personas_data: list[dict]) -> list[PersonaModel]:
        """Save generated personas"""
        saved = []
        for p_data in personas_data:
            # Ensure ID
            if 'id' not in p_data:
                p_data['id'] = f"p_{uuid.uuid4().hex[:8]}"
                
            # Create or update
            persona, _ = PersonaModel.objects.update_or_create(
                id=p_data['id'],
                organization=org,
                defaults={
                    'name': p_data['name'],
                    'age': p_data['age'],
                    'gender': p_data.get('gender', ''),
                    'segment': p_data.get('segment', ''),
                    'background': p_data.get('background', ''),
                    'occupation': p_data.get('occupation', ''),
                    'location': p_data.get('location', ''),
                    'household_size': p_data.get('household_size', 1),
                    'income_monthly': p_data.get('income_monthly', 0),
                    'spend_monthly': p_data.get('spend_monthly', 0),
                    'spend_breakdown': p_data.get('spend_breakdown', {}),
                    'traits': p_data.get('traits', {}),
                    'goals': p_data.get('goals', []),
                    'pains': p_data.get('pains', [])
                }
            )
            saved.append(persona)
        return saved

    @staticmethod
    def save_questionnaire(org, questionnaire_data: dict) -> QuestionnaireModel:
        """Save questionnaire"""
        q, _ = QuestionnaireModel.objects.update_or_create(
            id=questionnaire_data['id'],
            organization=org,
            defaults={
                'title': questionnaire_data['title'],
                'instructions': questionnaire_data.get('instructions', ''),
                'questions': questionnaire_data['questions']
            }
        )
        return q

    @staticmethod
    def save_session(org, mode: str, transcript, questionnaire_data, personas_data, scenario_data=None):
        """Save simulation session"""
        
        # Ensure related models exist
        q_model = PersistenceService.save_questionnaire(org, questionnaire_data)
        
        scenario_model = None
        if scenario_data:
            scenario_model, _ = ScenarioModel.objects.update_or_create(
                id=scenario_data['id'],
                organization=org,
                defaults={
                    'title': scenario_data['title'],
                    'description': scenario_data.get('description', ''),
                    'context': scenario_data.get('context', ''),
                    'constraints': scenario_data.get('constraints', [])
                }
            )
        
        PersistenceService.save_personas(org, personas_data if isinstance(personas_data, list) else [personas_data])
        
        # Create session
        session = SessionModel.objects.create(
            organization=org,
            mode=mode,
            questionnaire=q_model,
            scenario=scenario_model,
            personas=[p['id'] for p in (personas_data if isinstance(personas_data, list) else [personas_data])],
            transcript=transcript.dict() if hasattr(transcript, 'dict') else transcript
        )
        return session
    
    @staticmethod
    def save_journey_map(org, journey_data: dict, source_transcript=None):
        """Save journey map"""
        persona_data = {
            'id': journey_data['persona_id'],
            'name': journey_data['persona_name']
        }
        # Ideally persona should already exist, but minimal save here
        # (Assuming persona creation happened before or passed fully)
        # For simplicity, we assume PersonaModel exists or we link by ID only if strict
        # But JourneyMapModel requires ForeignKey to PersonaModel.
        
        try:
            persona = PersonaModel.objects.get(id=journey_data['persona_id'], organization=org)
        except PersonaModel.DoesNotExist:
            # Create minimal if missing (edge case)
            persona = PersonaModel.objects.create(
                id=journey_data['persona_id'],
                organization=org,
                name=journey_data['persona_name'],
                age=0 # Dummy
            )

        journey = JourneyMapModel.objects.create(
            organization=org,
            goal=journey_data['goal'],
            persona=persona,
            steps=journey_data['steps']
        )
        
        # Link source session if provided (not implemented fully in serializer yet)
        return journey
