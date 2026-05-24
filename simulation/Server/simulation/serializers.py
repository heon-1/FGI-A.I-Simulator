"""
Serializers for simulation API
"""
from rest_framework import serializers


class ProjectSerializer(serializers.Serializer):
    """Serializer for Project data"""
    id = serializers.UUIDField(read_only=True)
    organization_id = serializers.UUIDField()
    title = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

class PersonaSerializer(serializers.Serializer):
    """Serializer for Persona data"""
    id = serializers.CharField(required=False)
    project_id = serializers.UUIDField(required=False)
    name = serializers.CharField()
    age = serializers.IntegerField()
    gender = serializers.CharField(required=False, allow_blank=True)
    segment = serializers.CharField(required=False, allow_blank=True)
    background = serializers.CharField(required=False, allow_blank=True)
    occupation = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)
    household_size = serializers.IntegerField(required=False, default=1)
    income_monthly = serializers.IntegerField(required=False, default=0)
    spend_monthly = serializers.IntegerField(required=False, default=0)
    spend_breakdown = serializers.DictField(required=False, default=dict)
    traits = serializers.DictField(required=False, default=dict)
    goals = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    pains = serializers.ListField(child=serializers.CharField(), required=False, default=list)


class QuestionSerializer(serializers.Serializer):
    """Serializer for Question data"""
    id = serializers.CharField()
    text = serializers.CharField()
    kind = serializers.ChoiceField(choices=['open', 'scale', 'multi'], default='open')
    scale_min = serializers.IntegerField(required=False, allow_null=True)
    scale_max = serializers.IntegerField(required=False, allow_null=True)
    options = serializers.ListField(child=serializers.CharField(), required=False, default=list)


class QuestionnaireSerializer(serializers.Serializer):
    """Serializer for Questionnaire data"""
    id = serializers.CharField()
    project_id = serializers.UUIDField(required=False)
    title = serializers.CharField()
    instructions = serializers.CharField(required=False, allow_blank=True)
    questions = QuestionSerializer(many=True)


class ScenarioSerializer(serializers.Serializer):
    """Serializer for Scenario data"""
    id = serializers.CharField()
    project_id = serializers.UUIDField(required=False)
    title = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    context = serializers.CharField(required=False, allow_blank=True)


class UtteranceSerializer(serializers.Serializer):
    """Serializer for Utterance data"""
    turn = serializers.IntegerField()
    speaker = serializers.CharField()
    text = serializers.CharField()
    timestamp = serializers.CharField(required=False, allow_null=True)


class TranscriptSerializer(serializers.Serializer):
    """Serializer for Transcript data"""
    session_id = serializers.CharField()
    mode = serializers.CharField()
    utterances = UtteranceSerializer(many=True)


class JourneyStepSerializer(serializers.Serializer):
    """Serializer for JourneyStep data"""
    step = serializers.IntegerField()
    stage = serializers.CharField()
    action_label = serializers.CharField()
    rationale = serializers.CharField(required=False, allow_blank=True)
    expected_outcome = serializers.CharField(required=False, allow_blank=True)
    subtasks = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    inputs = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    outputs = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    system_touchpoints = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    success_metric = serializers.CharField(required=False, allow_blank=True)
    risks = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    mitigations = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    owner = serializers.CharField(required=False, allow_blank=True)
    eta = serializers.CharField(required=False, allow_blank=True)


class JourneyMapSerializer(serializers.Serializer):
    """Serializer for JourneyMap data"""
    goal = serializers.CharField()
    persona_id = serializers.CharField()
    persona_name = serializers.CharField()
    steps = JourneyStepSerializer(many=True)


# Request Serializers

class GeneratePersonaRequestSerializer(serializers.Serializer):
    """Request to generate personas from context"""
    project_id = serializers.UUIDField()
    context = serializers.CharField(help_text="Context for persona generation")
    count = serializers.IntegerField(default=1, min_value=1, max_value=10)


class IndividualInterviewRequestSerializer(serializers.Serializer):
    """Request to run individual interview"""
    project_id = serializers.UUIDField()
    persona = PersonaSerializer()
    questionnaire = QuestionnaireSerializer()
    max_questions = serializers.IntegerField(required=False, allow_null=True)


class FGIRequestSerializer(serializers.Serializer):
    """Request to run FGI simulation"""
    project_id = serializers.UUIDField()
    personas = PersonaSerializer(many=True)
    questionnaire = QuestionnaireSerializer()
    scenario = ScenarioSerializer(required=False, allow_null=True)
    max_rounds = serializers.IntegerField(default=3)


class JourneyRequestSerializer(serializers.Serializer):
    """Request to generate journey map"""
    project_id = serializers.UUIDField()
    goal = serializers.CharField()
    persona = PersonaSerializer()
    fgi_transcript = TranscriptSerializer(required=False, allow_null=True)
    individual_transcript = TranscriptSerializer(required=False, allow_null=True)
    max_context_chars = serializers.IntegerField(default=2000)


class GenerateQuestionnaireRequestSerializer(serializers.Serializer):
    """Request to generate questionnaire"""
    project_id = serializers.UUIDField()
    type = serializers.ChoiceField(choices=['fgi', 'individual'])
    topic = serializers.CharField()
    objective = serializers.CharField()
    target_audience = serializers.CharField()
    question_count = serializers.IntegerField(default=8)
    # Individual only
    include_scale = serializers.BooleanField(default=True)
    include_multi = serializers.BooleanField(default=True)
    # Optional context
    additional_context = serializers.CharField(required=False, allow_blank=True)
