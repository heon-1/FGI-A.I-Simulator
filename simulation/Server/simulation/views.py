"""
Simulation API Views
"""
import json
from django.http import StreamingHttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action

from simulation.serializers import (
    PersonaSerializer,
    QuestionnaireSerializer,
    GeneratePersonaRequestSerializer,
    IndividualInterviewRequestSerializer,
    FGIRequestSerializer,
    JourneyRequestSerializer,
    GenerateQuestionnaireRequestSerializer,
    ProjectSerializer,
)
from simulation.models import Project, Persona as PersonaModel
from simulation.types import Persona, Questionnaire, Scenario, Transcript
from simulation.services import (
    PersonaService,
    IndividualInterviewService,
    FGIService,
    JourneyMapService,
    get_gemini_client,
)
from simulation.services.questionnaire_service import QuestionnaireService
from simulation.services.persistence_service import PersistenceService
from simulation.services.project_service import ProjectService


from simulation.services.persistence_service import PersistenceService


# ==================== Project Endpoints ====================

class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for calculating Projects.
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filter projects by user's organization membership
        # Assuming request.user.email maps to UserProfile.email
        email = self.request.user.email
        return Project.objects.filter(organization__members__email=email)

    def perform_create(self, serializer):
        # Auto-assign organization if possible, but it is required in serializer
        project = serializer.save()
        
        # If created with a prompt/description, initialize content
        if project.description and len(project.description) > 10:
            # Run in background ideally, but for MVP sync is fine
            try:
                ProjectService.initialize_project_from_prompt(project, project.description)
            except Exception as e:
                print(f"Failed to auto-init project: {e}")

# ... (existing views) ...

# ==================== Questionnaire Endpoints ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_questionnaire(request):
    """Validate questionnaire data"""
    serializer = QuestionnaireSerializer(data=request.data)
    if serializer.is_valid():
        return Response({
            'success': True,
            'data': {'valid': True, 'questionnaire': serializer.validated_data}
        })
    return Response({
        'success': False,
        'error': {'valid': False, 'errors': serializer.errors}
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_questionnaire(request):
    """Generate questionnaire using AI"""
    serializer = GenerateQuestionnaireRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    service = QuestionnaireService()
    
    try:
        if data['type'] == 'fgi':
            questionnaire = service.generate_fgi_questionnaire(
                topic=data['topic'],
                objective=data['objective'],
                target_audience=data['target_audience'],
                question_count=data['question_count'],
                additional_context=data.get('additional_context')
            )
        else:  # individual
            questionnaire = service.generate_individual_questionnaire(
                topic=data['topic'],
                objective=data['objective'],
                target_audience=data['target_audience'],
                question_count=data['question_count'],
                include_scale_questions=data['include_scale'],
                include_multi_questions=data['include_multi'],
                additional_context=data.get('additional_context')
            )
        
        return Response({
            'success': True,
            'data': {
                'questionnaire': questionnaire.model_dump()
            }
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': f"Failed to generate questionnaire: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== Persona Endpoints ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_persona(request):
    """Validate persona data"""
    serializer = PersonaSerializer(data=request.data)
    if serializer.is_valid():
        return Response({
            'success': True,
            'data': {'valid': True, 'persona': serializer.validated_data}
        })
    return Response({
        'success': False,
        'error': {'valid': False, 'errors': serializer.errors}
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_persona(request):
    """Generate persona(s) from context using AI"""
    serializer = GeneratePersonaRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    context = serializer.validated_data['context']
    count = serializer.validated_data.get('count', 1)
    
    client = get_gemini_client()
    personas = []
    
    for i in range(count):
        prompt = PersonaService.generate_persona_prompt(context)
        if count > 1:
            prompt += f"\n\n이것은 {count}개 중 {i+1}번째 페르소나입니다. 다양성을 고려하세요."
        
        response = client.generate(prompt)
        
        try:
            import orjson
            persona_data = orjson.loads(response)
            # Ensure unique ID
            if 'id' not in persona_data or not persona_data['id']:
                persona_data['id'] = f"p_gen_{i+1:02d}"
            personas.append(persona_data)
        except Exception as e:
            # Try to extract JSON from response
            start = response.find("{")
            end = response.rfind("}")
            if start != -1 and end != -1:
                try:
                    persona_data = orjson.loads(response[start:end+1])
                    if 'id' not in persona_data:
                        persona_data['id'] = f"p_gen_{i+1:02d}"
                    personas.append(persona_data)
                except:
                    pass
    
    return Response({
        'success': True,
        'data': {'personas': personas}
    })


# ==================== Individual Interview Endpoints ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_individual_interview(request):
    """Run individual interview simulation"""
    serializer = IndividualInterviewRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    persona = Persona(**data['persona'])
    questionnaire = Questionnaire(**data['questionnaire'])
    max_questions = data.get('max_questions')
    
    service = IndividualInterviewService()
    transcript = service.run_interview(persona, questionnaire, max_questions)
    
    return Response({
        'success': True,
        'data': {
            'transcript': transcript.to_dict()
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_individual_interview_stream(request):
    """Run individual interview with streaming response"""
    serializer = IndividualInterviewRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    persona = Persona(**data['persona'])
    questionnaire = Questionnaire(**data['questionnaire'])
    max_questions = data.get('max_questions')
    
    service = IndividualInterviewService()
    
    def event_stream():
        for event in service.run_interview_stream(persona, questionnaire, max_questions):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    
    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


# ==================== FGI Endpoints ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_fgi(request):
    """Run FGI simulation"""
    serializer = FGIRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    personas = [Persona(**p) for p in data['personas']]
    questionnaire = Questionnaire(**data['questionnaire'])
    scenario = Scenario(**data['scenario']) if data.get('scenario') else None
    max_rounds = data.get('max_rounds', 3)
    
    service = FGIService()
    transcript = service.run_fgi(personas, questionnaire, scenario, max_rounds)
    
    return Response({
        'success': True,
        'data': {
            'transcript': transcript.to_dict()
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def run_fgi_stream(request):
    """Run FGI with streaming response"""
    serializer = FGIRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    personas = [Persona(**p) for p in data['personas']]
    questionnaire = Questionnaire(**data['questionnaire'])
    scenario = Scenario(**data['scenario']) if data.get('scenario') else None
    max_rounds = data.get('max_rounds', 3)
    
    service = FGIService()
    
    def event_stream():
        for event in service.run_fgi_stream(personas, questionnaire, scenario, max_rounds):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    
    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


# ==================== Journey Map Endpoints ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_journey_map(request):
    """Generate journey map for a persona"""
    serializer = JourneyRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    goal = data['goal']
    persona = Persona(**data['persona'])
    
    # Convert transcript data if provided
    fgi_transcript = None
    if data.get('fgi_transcript'):
        fgi_transcript = Transcript(**data['fgi_transcript'])
    
    individual_transcript = None
    if data.get('individual_transcript'):
        individual_transcript = Transcript(**data['individual_transcript'])
    
    max_context_chars = data.get('max_context_chars', 2000)
    
    service = JourneyMapService()
    journey = service.simulate_journey(
        goal, persona, fgi_transcript, individual_transcript, max_context_chars
    )
    
    return Response({
        'success': True,
        'data': {
            'journey_map': journey.model_dump()
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_journey_map_stream(request):
    """Generate journey map with streaming response"""
    serializer = JourneyRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    goal = data['goal']
    persona = Persona(**data['persona'])
    
    fgi_transcript = None
    if data.get('fgi_transcript'):
        fgi_transcript = Transcript(**data['fgi_transcript'])
    
    individual_transcript = None
    if data.get('individual_transcript'):
        individual_transcript = Transcript(**data['individual_transcript'])
    
    max_context_chars = data.get('max_context_chars', 2000)
    
    service = JourneyMapService()
    
    def event_stream():
        for event in service.simulate_journey_stream(
            goal, persona, fgi_transcript, individual_transcript, max_context_chars
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    
    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def journey_to_csv(request):
    """Convert journey map to CSV format"""
    journey_data = request.data.get('journey_map')
    if not journey_data:
        return Response({
            'success': False,
            'error': 'journey_map is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    from simulation.types import JourneyMap
    journey = JourneyMap(**journey_data)
    
    service = JourneyMapService()
    rows = service.journey_to_csv_rows(journey)
    
    return Response({
        'success': True,
        'data': {'rows': rows}
    })



