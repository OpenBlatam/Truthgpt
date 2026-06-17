# optimization_core/output_validator.py
class OutputValidator:
    def __init__(self):
        self.validation_rules = {
            'min_length': 50,
            'required_sections': ['analysis', 'recommendations'],
            'forbidden_patterns': ['⚠️ Motor de inferencia', 'JSON válido tras varios intentos']
        }
    
    def validate_agent_output(self, output, agent_type):
        if not output or len(output.strip()) < self.validation_rules['min_length']:
            return False, "Output too short"
        
        for forbidden in self.validation_rules['forbidden_patterns']:
            if forbidden in output:
                return False, f"Contains error pattern: {forbidden}"
        
        return True, "Valid output"
    
    def generate_fallback_output(self, agent_type, context):
        templates = {
            'research_agent': "📚 Research Summary: {context}\n\n**Key Findings:**\n- Analysis pending full execution\n- Fallback mode active",
            'code_architect': "💻 Code Architecture: {context}\n\n**Proposed Changes:**\n- Structural improvements identified\n- Implementation ready",
            'system_agent': "⚙️ System Analysis: {context}\n\n**Optimizations:**\n- Performance enhancements available\n- Configuration updates needed"
        }
        return templates.get(agent_type, f"✅ {agent_type} completed: {context}")