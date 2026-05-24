
import json
from simulation.models import Project
from simulation.services.gemini_client import get_gemini_client
from simulation.services.persona_service import PersonaService

class ProjectService:
    @staticmethod
    def initialize_project_from_prompt(project: Project, prompt: str):
        """
        Analyzes the prompt to set a title and generate initial personas.
        """
        client = get_gemini_client()
        
        # 1. Generate Title and Summary
        meta_prompt = f"""
        Analyze the following user research project prompt and generate a short, catchy title (max 50 chars).
        
        Prompt: {prompt}
        
        Return JSON: {{ "title": "..." }}
        """
        try:
            response = client.generate(meta_prompt)
            # Simple cleanup if markdown code blocks are returned
            response = response.replace("```json", "").replace("```", "").strip()
            data = json.loads(response)
            project.title = data.get("title", "New Project")
            project.save()
        except Exception as e:
            print(f"Error generating title: {e}")
            project.title = prompt[:20] + "..."
            project.save()

        # 2. Generate Personas
        # Reuse PersonaService logic but formatted for this flow
        # We'll generate 3 initial personas
        try:
            persona_prompt = PersonaService.generate_persona_prompt(prompt)
            persona_prompt += "\n\nGenerate 3 distinct personas based on this context. Return as a JSON list."
            
            # This might need more robust parsing depending on how PersonaService works, 
            # but let's assume we can loop and create them.
            # actually PersonaService.generate_persona_prompt returns a string prompt for ONE persona usually.
            # Let's simple loop 3 times or ask for a list.
            
            # Let's just generate 3 personas one by one or in batch. 
            # For speed, let's try batch or just 2.
            
            # We will use the existing Persona creation logic via API flow or direct model creation?
            # Direct model creation is better here.
            
            # Let's defer to the view or calling the generate_persona implementation logic 
            # but simpler:
            
            pass 
            # I will actually implement the loop in the view or here. 
            # Let's implement a helper here.
            
            personas_json = client.generate(f"""
            Based on this project context: "{prompt}"
            
            Create 3 detailed user personas for UX research.
            Return a JSON object with a key "personas" containing a list of 3 persona objects.
            Each persona must have: name, age, gender, occupation, segment, background, goals (list), pains (list), traits (dict).
            """)
            
            personas_json = personas_json.replace("```json", "").replace("```", "").strip()
            # find first { and last }
            start = personas_json.find("{")
            end = personas_json.rfind("}")
            if start != -1 and end != -1:
                data = json.loads(personas_json[start:end+1])
                for i, p_data in enumerate(data.get('personas', [])):
                    from simulation.models import Persona
                    Persona.objects.create(
                        id=f"{project.id}_p{i+1}",
                        project=project,
                        name=p_data.get('name', 'Unknown'),
                        age=p_data.get('age', 30),
                        gender=p_data.get('gender', ''),
                        occupation=p_data.get('occupation', ''),
                        segment=p_data.get('segment', ''),
                        background=p_data.get('background', ''),
                        goals=p_data.get('goals', []),
                        pains=p_data.get('pains', []),
                        traits=p_data.get('traits', {})
                    )
                    
        except Exception as e:
            print(f"Error generating personas: {e}")

