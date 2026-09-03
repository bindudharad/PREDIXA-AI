---
## Natural Language Explanations
### Template-Based Generation
```pythonclass NaturalLanguageExplainer:    def __init__(self):        self.templates = {            "UP": {                "strong": "The model predicts a strong upward move with {prob}% probability. Key drivers: {pos_factors}."                "moderate": "The model indicates a moderate upward bias ({prob}% probability). Supporting factors: {pos_factors}. Caution: {neg_factors}."