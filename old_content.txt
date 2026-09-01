# 16_EXPLAINABILITY.md

## Explainability System Design

This document designs the explanation system for every prediction.

## Core Principle

Explanations must reflect actual model inputs and computations, not post-hoc rationalizations.

## Explanation Requirements

For every prediction, provide:
1. Prediction: UP/DOWN/SIDEWAYS with probabilities
2. Confidence: Entropy-based confidence score
3. Major Positive Factors: Top features pushing toward predicted class
4. Major Negative Factors: Top features pushing away
5. Model Contribution: How each ensemble member voted
6. Agent Reasoning: Technical/News/Risk agent outputs
7. Risk Checks: Which constraints passed/failed

---

## SHAP-Based Explanations

### Tree SHAP (XGBoost, LightGBM, RF)

`python
import shap

class SHAPExplainer:
    def __init__(self, model, feature_names):
        self.explainer = shap.TreeExplainer(model)
        self.feature_names = feature_names
        self.model = model
    
    def explain(self, X, top_k=10):
        shap_values = self.explainer.shap_values(X[self.feature_names])
        probs = self.model.predict_proba(X[self.feature_names])
        predicted_class = probs.argmax(axis=1)
        
        explanations = []
        for i in range(len(X)):
            pred_class = predicted_class[i]
            class_shap = shap_values[pred_class][i]
            
            feature_importance = list(zip(self.feature_names, class_shap, X[self.feature_names].iloc[i]))
            feature_importance.sort(key=lambda x: abs(x[1]), reverse=True)
            
            positive = [(f, v, val) for f, v, val in feature_importance if v > 0][:top_k]
            negative = [(f, v, val) for f, v, val in feature_importance if v < 0][:top_k]
            
            explanations.append({
                'predicted_class': pred_class,
                'positive_factors': [
                    {'feature': f, 'shap_value': float(v), 'feature_value': float(val)}
                    for f, v, val in positive
                ],
                'negative_factors': [
                    {'feature': f, 'shap_value': float(v), 'feature_value': float(val)}
                    for f, v, val in negative
                ],
                'base_value': float(self.explainer.expected_value[pred_class]),
                'prediction_value': float(self.explainer.expected_value[pred_class] + class_shap.sum()),
            })
        return explanations
`

### Linear Model Coefficients (Logistic Regression)

`python
class LinearExplainer:
    def __init__(self, model, feature_names):
        self.model = model
        self.feature_names = feature_names
        self.coefficients = model.coef_
    
    def explain(self, X, top_k=10):
        explanations = []
        probs = self.model.predict_proba(X[self.feature_names])
        predicted_class = probs.argmax(axis=1)
        
        for i in range(len(X)):
            pred_class = predicted_class[i]
            coefs = self.coefficients[pred_class]
            feature_vals = X[self.feature_names].iloc[i].values
            
            contributions = coefs * feature_vals
            feature_importance = list(zip(self.feature_names, contributions, feature_vals))
            feature_importance.sort(key=lambda x: abs(x[1]), reverse=True)
            
            positive = [(f, v, val) for f, v, val in feature_importance if v > 0][:top_k]
            negative = [(f, v, val) for f, v, val in feature_importance if v < 0][:top_k]
            
            explanations.append({
                'predicted_class': pred_class,
                'positive_factors': [{'feature': f, 'contribution': float(v), 'feature_value': float(val)} for f, v, val in positive],
                'negative_factors': [{'feature': f, 'contribution': float(v), 'feature_value': float(val)} for f, v, val in negative],
                'intercept': float(self.model.intercept_[pred_class]),
            })
        return explanations
`

---

## Ensemble Explanations

### Model Contribution Breakdown

`python
class EnsembleExplainer:
    def __init__(self, ensemble, base_explainers):
        self.ensemble = ensemble
        self.base_explainers = base_explainers
        self.weights = ensemble.weights
    
    def explain(self, X):
        ens_probs = self.ensemble.predict_proba(X)
        predicted_class = ens_probs.argmax(axis=1)[0]
        ens_confidence = compute_confidence(ens_probs)[0]
        
        model_contributions = {}
        for name, model in self.ensemble.models.items():
            probs = model.predict_proba(X)
            weight = self.weights[name]
            model_contributions[name] = {
                'weight': weight,
                'probabilities': probs[0].tolist(),
                'predicted_class': probs.argmax(axis=1)[0],
                'confidence': compute_confidence(probs)[0],
                'contribution_to_ensemble': weight * probs[0][predicted_class],
            }
        
        primary_name = max(self.weights.items(), key=lambda x: x[1])[0]
        primary_explainer = self.base_explainers[primary_name]
        shap_explanation = primary_explainer.explain(X)[0]
        
        return {
            'ensemble_probabilities': ens_probs[0].tolist(),
            'predicted_class': predicted_class,
            'ensemble_confidence': ens_confidence,
            'model_contributions': model_contributions,
            'shap_explanation': shap_explanation,
            'primary_model': primary_name,
        }
`

---

## Agent Explanations

### Decision Trace

`python
class AgentExplainer:
    def __init__(self, decision_engine):
        self.decision_engine = decision_engine
    
    def explain_decision(self, decision):
        tech = decision.agents['technical']
        news = decision.agents['news']
        risk = decision.agents['risk']
        
        return {
            'final_decision': {
                'action': decision.action,
                'direction': decision.direction,
                'probabilities': {
                    'UP': decision.probabilities[2],
                    'SIDEWAYS': decision.probabilities[1],
                    'DOWN': decision.probabilities[0],
                },
                'confidence': decision.confidence,
                'position_size': decision.position_size,
            },
            'technical_agent': {
                'direction': 'UP' if tech.direction == 1 else 'DOWN' if tech.direction == -1 else 'SIDEWAYS',
                'confidence': tech.confidence,
                'strength': tech.strength,
                'top_positive_factors': tech.key_features[:5],
                'model_version': tech.metadata.get('model_version'),
            },
            'news_agent': {
                'direction': 'UP' if news.direction == 1 else 'DOWN' if news.direction == -1 else 'SIDEWAYS',
                'confidence': news.confidence,
                'strength': news.strength,
                'key_factors': news.key_features,
                'news_count': news.metadata.get('news_count'),
            },
            'risk_agent': {
                'allowed': risk.allowed,
                'max_position_pct': risk.max_position_pct,
                'active_constraints': risk.constraints,
                'veto_reason': risk.veto_reason,
                'current_drawdown': risk.current_drawdown,
            },
            'decision_logic': {
                'risk_veto': not risk.allowed,
                'conflict_detected': getattr(decision, 'conflict_detected', False),
                'no_trade_reason': decision.reason if decision.action == 'NO_TRADE' else None,
                'position_sizing_rationale': self._sizing_rationale(decision),
            },
        }
    
    def _sizing_rationale(self, decision):
        if decision.position_size == 0:
            return 'No position: ' + (decision.reason or 'zero size')
        return 'Position sized at ' + str(decision.position_size) + ' based on confidence ' + str(decision.confidence) + ' and risk limit ' + str(decision.agents['risk'].max_position_pct)
`