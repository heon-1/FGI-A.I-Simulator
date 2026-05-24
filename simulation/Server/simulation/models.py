from django.db import models
import uuid

class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Project(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey('users.Organization', on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, help_text="The prompt or context for this project")
    
    def __str__(self):
        return self.title

class Persona(TimestampedModel):
    id = models.CharField(max_length=100, primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='personas')
    name = models.CharField(max_length=100)
    # ... (rest of Persona fields)

    age = models.IntegerField()
    gender = models.CharField(max_length=20, blank=True)
    segment = models.CharField(max_length=100, blank=True)
    background = models.TextField(blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    household_size = models.IntegerField(default=1)
    income_monthly = models.IntegerField(default=0)
    spend_monthly = models.IntegerField(default=0)
    
    # JSON fields for flexible data
    spend_breakdown = models.JSONField(default=dict, blank=True)
    traits = models.JSONField(default=dict, blank=True)
    goals = models.JSONField(default=list, blank=True)
    pains = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"{self.name} ({self.id})"

class Questionnaire(TimestampedModel):
    id = models.CharField(max_length=100, primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='questionnaires')
    title = models.CharField(max_length=200)
    instructions = models.TextField(blank=True)
    questions = models.JSONField(default=list) 

    def __str__(self):
        return self.title

class Scenario(TimestampedModel):
    id = models.CharField(max_length=100, primary_key=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='scenarios')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    context = models.TextField(blank=True)
    constraints = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.title

class SimulationSession(TimestampedModel):
    """
    Records a simulation run (Individual or FGI)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sessions')
    mode = models.CharField(max_length=20, choices=[('individual', 'Individual'), ('fgi', 'FGI')])
    
    scenario = models.ForeignKey(Scenario, on_delete=models.SET_NULL, null=True, blank=True)
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.SET_NULL, null=True, blank=True)
    
    personas = models.JSONField(default=list)
    transcript = models.JSONField(default=dict)
    summary = models.TextField(blank=True)
    tags = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"[{self.mode}] {self.id} ({self.created_at})"

class JourneyMap(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='journey_maps')
    goal = models.CharField(max_length=200)
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)
    
    steps = models.JSONField(default=list)
    source_sessions = models.ManyToManyField(SimulationSession, blank=True)

    def __str__(self):
        return f"Journey: {self.goal} - {self.persona.name}"
