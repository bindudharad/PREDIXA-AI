--- 
## Natural Language Explanations 
### Template-Based Generation 
```python 
class NaturalLanguageExplainer: 
    def __init__(self): 
        self.templates = { 
            \"UP\": { 
                \"strong\": \"The model predicts a strong upward move with {prob}% probability. Key drivers: {pos_factors}.\" 
                \"moderate\": \"The model indicates a moderate upward bias ({prob}% probability). Supporting factors: {pos_factors}. Caution: {neg_factors}.\" 
                \"weak\": \"The model shows a slight upward tendency ({prob}% probability). However, opposing factors include: {neg_factors}.\" 
            }, 
            \"DOWN\": { 
                \"strong\": \"The model predicts a strong downward move with {prob}% probability. Key drivers: {neg_factors}.\" 
                \"moderate\": \"The model indicates a moderate downward bias ({prob}% probability). Supporting factors: {neg_factors}. Caution: {pos_factors}.\" 
                \"weak\": \"The model shows a slight downward tendency ({prob}% probability). However, opposing factors include: {pos_factors}.\" 
            }, 
            \"SIDEWAYS\": { 
                \"strong\": \"The model predicts range-bound trading with {prob}% probability. Market lacks clear directional catalysts.\" 
                \"moderate\": \"The model suggests sideways consolidation ({prob}% probability). Mixed signals from {pos_factors} and {neg_factors}.\" 
                \"weak\": \"The model is uncertain with highest probability on SIDEWAYS ({prob}%). Conflicting signals dominate.\" 
            } 
        } 
    def generate(self, explanation): 
        pred_class = explanation[\"predicted_class\"] 
        prob = max(explanation[\"ensemble_probabilities\"]) * 100 
        pos_factors = [f[\"feature\"] for f in explanation[\"shap_explanation\"][\"positive_factors\"][:3]] 
        neg_factors = [f[\"feature\"] for f in explanation[\"shap_explanation\"][\"negative_factors\"][:3]] 
        pos_str = \", \".join(pos_factors) if pos_factors else \"none identified\" 
        neg_str = \", \".join(neg_factors) if neg_factors else \"none identified\" 
        class_map = {2: \"UP\", 1: \"SIDEWAYS\", 0: \"DOWN\"} 
        direction = class_map.get(pred_class, \"SIDEWAYS\") 
        if prob 
            strength = \"strong\" 
        elif prob 
            strength = \"moderate\" 
        else: 
            strength = \"weak\" 
        template = self.templates[direction][strength] 
        return template.format(prob=round(prob, 1), pos_factors=pos_str, neg_factors=neg_str) 
``` 
 
--- 
## Explanation Output Format 
### API Response JSON 
```json 
{ 
{
  "symbol": "AAPL",
  "timestamp": "2025-01-15T09:30:00Z",
  "model_version": "model_v042",
  "prediction": {
    "direction": "UP",
    "probabilities": {
      "UP": 0.68,
      "SIDEWAYS": 0.21,
      "DOWN": 0.11
    },
    "confidence": 0.72,
    "expected_return": 0.023
  },
  "explanation": {
    "positive_factors": [
      {
        "feature": "momentum_20d",
        "shap_value": 0.15,
        "feature_value": 0.08,
        "description": "Strong 20-day price momentum"
      },
      {
        "feature": "rsi_14",
        "shap_value": 0.09,
        "feature_value": 62.3,
        "description": "RSI in bullish territory"
      },
      {
        "feature": "relative_strength_spy",
        "shap_value": 0.07,
        "feature_value": 1.15,
        "description": "Outperforming S&P 500"
      }
    ],
    "negative_factors": [
      {
        "feature": "atr_14",
        "shap_value": -0.06,
        "feature_value": 2.45,
        "description": "Elevated volatility"
      },
      {
        "feature": "sector_trend",
        "shap_value": -0.04,
        "feature_value": -0.02,
        "description": "Weak sector performance"
      }
    ],
    "model_contributions": {
      "xgboost": {
        "weight": 0.4,
        "probabilities": [
          0.12,
          0.22,
          0.66
        ],
        "predicted_class": "UP"
      },
      "lightgbm": {
        "weight": 0.35,
        "probabilities": [
          0.1,
          0.18,
          0.72
        ],
        "predicted_class": "UP"
      },
      "logistic_regression": {
        "weight": 0.25,
        "probabilities": [
          0.15,
          0.25,
          0.6
        ],
        "predicted_class": "UP"
      }
    },
    "agent_analysis": {
      "technical": {
        "direction": "UP",
        "confidence": 0.75,
        "strength": 0.68
      },
      "news": {
        "direction": "SIDEWAYS",
        "confidence": 0.45,
        "strength": 0.12
      },
      "risk": {
        "allowed": true,
        "max_position_pct": 0.05,
        "active_constraints": []
      }
    },
    "natural_language": "The model predicts a strong upward move with 68.0% probability. Key drivers: momentum_20d, rsi_14, relative_strength_spy.",
    "explanation_quality": {
      "shap_coverage": 0.89,
      "stability_score": 0.92,
      "consistency_check": "PASSED"
    }
  }
}``` 
 
--- 
## Dashboard Explanation View 
### UI Components 
1. **Prediction Card**: Shows direction, probabilities (bar chart), confidence gauge 
2. **Factor Waterfall**: Horizontal bar chart of SHAP values (green/red) 
3. **Model Agreement Matrix**: Heatmap of model vs prediction 
4. **Agent Panel**: Three cards for Technical/News/Risk with verdict 
5. **Natural Language Summary**: Plain-text explanation 
6. **Historical Accuracy**: Rolling accuracy for this symbol/model 
 
### Mermaid Diagram 
```mermaid 
graph TD 
    A[Prediction Request] -- Ensemble] 
    B -- Explainer] 
    B -- Explainer] 
    C -- Ranking] 
    D -- Trace] 
    E -- Language Generator] 
    F --
    G -- Response] 
    H -- Components] 
    I -- Card] 
    I -- Waterfall] 
    I -- Agreement] 
    I -- Panel] 
    I -- Summary] 
``` 
 
--- 
## Explanation Quality Checks 
### Validation Rules 
```python 
class ExplanationValidator: 
    def __init__(self): 
        self.min_shap_coverage = 0.8 
        self.max_stability_threshold = 0.15 
    def validate(self, explanation, symbol, model_version): 
        checks = {} 
        # SHAP coverage 
        shap_exp = explanation[\"shap_explanation\"] 
        total_shap = sum(abs(f[\"shap_value\"]) for f in shap_exp[\"positive_factors\"] + shap_exp[\"negative_factors\"]) 
        pred_diff = abs(shap_exp[\"prediction_value\"] - shap_exp[\"base_value\"]) 
        coverage = total_shap / pred_diff if pred_diff  else 1.0 
        checks[\"shap_coverage\"] = {\"value\": coverage, \"passed\": coverage 
        # Stability 
        recent = self._get_recent_explanations(symbol, model_version, n=10) 
        if recent: 
            stability = self._compute_stability(shap_exp, recent) 
