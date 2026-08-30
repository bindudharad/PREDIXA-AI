# 15_PREDICTION_AGENT.md

## Prediction Agent Architecture

This document designs the agent layer that coordinates specialized models into unified decisions.

## Agent Overview

`mermaid
flowchart TD
    subgraph Inputs [Inputs]
        I1[Live Features Price/Technical/Vol]
        I2[News Features Sentiment/Volume]
        I3[Risk Features Portfolio/Positions]
        I4[Market Context Regime/Vol/VIX]
    end
    
    subgraph Agents [Specialized Agents]
        A1[Technical Agent XGBoost + Rules]
        A2[News Agent FinBERT + Aggregation]
        A3[Risk Agent Constraints + Limits]
    end
    
    subgraph Decision [Decision Engine]
        D1[Signal Aggregation Weighted Voting]
        D2[Conflict Resolution Veto Logic]
        D3[No-Trade Conditions]
        D4[Position Sizing]
    end
    
    subgraph Output [Outputs]
        O1[Final Prediction Probabilities + Confidence]
        O2[Explanation SHAP + Reasoning]
        O3[Action Trade/No-Trade + Size]
        O4[Audit Trail Full Decision Log]
    end
    
    I1 --> A1
    I2 --> A2
    I3 --> A3
    I4 --> A1
    I4 --> A2
    I4 --> A3
    
    A1 --> D1
    A2 --> D1
    A3 --> D1
    
    D1 --> D2
    D2 --> D3
    D3 --> D4
    D4 --> O1
    D4 --> O2
    D4 --> O3
    D4 --> O4
`

---

## Agent Responsibilities

### Technical Agent
`python
class TechnicalAgent:
    def __init__(self, model, feature_names, config):
        self.model = model
        self.feature_names = feature_names
        self.config = config
    
    def analyze(self, features):
        probs = self.model.predict_proba(features[self.feature_names])
        confidence = compute_confidence(probs, method='entropy')
        predicted_class = probs.argmax(axis=1)
        
        direction_map = {2: 1, 1: 0, 0: -1}
        direction = direction_map[predicted_class[0]]
        
        max_prob = probs.max(axis=1)[0]
        strength = max_prob - 0.333
        
        shap_values = self._get_shap(features[self.feature_names])
        top_features = self._get_top_features(shap_values, self.feature_names)
        
        return AgentSignal(
            agent='technical',
            probabilities=probs[0],
            confidence=confidence[0],
            direction=direction,
            strength=strength,
            key_features=top_features,
            metadata={'model_version': self.model.version}
        )
`

### News Agent
`python
class NewsAgent:
    def __init__(self, sentiment_model, config):
        self.sentiment_model = sentiment_model
        self.config = config
    
    def analyze(self, news_features):
        sentiment = news_features['sentiment_mean_5d'].values[0]
        sentiment_std = news_features['sentiment_std_5d'].values[0]
        pos_ratio = news_features['positive_ratio_5d'].values[0]
        neg_ratio = news_features['negative_ratio_5d'].values[0]
        news_count = news_features['news_count_5d'].values[0]
        credibility = news_features['source_credibility_weighted'].values[0]
        
        if news_count == 0:
            return AgentSignal(
                agent='news',
                probabilities=[0.33, 0.34, 0.33],
                confidence=0.1,
                direction=0,
                strength=0,
                key_features=[('no_news', 0)],
                metadata={'news_count': 0}
            )
        
        confidence = credibility * (1 - sentiment_std)
        
        if sentiment > 0.1 and pos_ratio > 0.6:
            direction = 1
            strength = sentiment * pos_ratio
            probs = [0.5 + strength*0.3, 0.3, 0.2 - strength*0.3]
        elif sentiment < -0.1 and neg_ratio > 0.6:
            direction = -1
            strength = abs(sentiment) * neg_ratio
            probs = [0.2 - strength*0.3, 0.3, 0.5 + strength*0.3]
        else:
            direction = 0
            strength = 0
            probs = [0.3, 0.4, 0.3]
        
        probs = np.array(probs)
        probs = probs / probs.sum()
        
        return AgentSignal(
            agent='news',
            probabilities=probs,
            confidence=confidence,
            direction=direction,
            strength=strength,
            key_features=[
                ('sentiment_mean', sentiment),
                ('pos_ratio', pos_ratio),
                ('credibility', credibility)
            ],
            metadata={'news_count': news_count}
        )
`

### Risk Agent
`python
class RiskAgent:
    def __init__(self, portfolio, risk_limits, config):
        self.portfolio = portfolio
        self.risk_limits = risk_limits
        self.config = config
    
    def analyze(self, prediction, context):
        constraints = []
        veto_reason = None
        allowed = True
        
        current_exposure = self.portfolio.gross_exposure
        if current_exposure >= self.risk_limits.max_gross_exposure:
            constraints.append('max_gross_exposure')
            allowed = False
            veto_reason = 'Portfolio gross exposure limit reached'
        
        symbol = context.symbol
        current_position = self.portfolio.get_position(symbol)
        if current_position and abs(current_position.pct) >= self.risk_limits.max_position_pct:
            constraints.append('max_position_pct')
            allowed = False
            veto_reason = 'Position limit reached for ' + symbol
        
        sector = context.sector
        sector_exposure = self.portfolio.get_sector_exposure(sector)
        if sector_exposure >= self.risk_limits.max_sector_pct:
            constraints.append('max_sector_pct')
            allowed = False
            veto_reason = 'Sector limit reached for ' + sector
        
        current_dd = self.portfolio.current_drawdown
        if current_dd <= -self.risk_limits.max_drawdown_pct:
            constraints.append('max_drawdown')
            allowed = False
            veto_reason = 'Max drawdown limit reached'
        
        if prediction.confidence < self.config.min_confidence:
            constraints.append('low_confidence')
            allowed = False
            veto_reason = 'Model confidence below threshold'
        
        if allowed:
            max_pos = min(
                self.risk_limits.max_position_pct,
                self.risk_limits.max_gross_exposure - current_exposure,
                self.risk_limits.max_sector_pct - sector_exposure
            )
            max_pos = max(0, max_pos)
        else:
            max_pos = 0
        
        return RiskSignal(
            allowed=allowed,
            max_position_pct=max_pos,
            constraints=constraints,
            veto_reason=veto_reason,
            current_drawdown=current_dd,
            current_exposure=current_exposure
        )
`

---

## Decision Engine

### Signal Aggregation
`python
class DecisionEngine:
    def __init__(self, config):
        self.config = config
        self.weights = {
            'technical': 0.6,
            'news': 0.2,
            'risk': 0.2
        }
    
    def decide(self, technical, news, risk):
        if not risk.allowed:
            return Decision(
                action='NO_TRADE',
                reason=risk.veto_reason,
                probabilities=[0, 0, 0],
                confidence=0,
                position_size=0,
                agents={'technical': technical, 'news': news, 'risk': risk}
            )
        
        tech_probs = np.array(technical.probabilities)
        news_probs = np.array(news.probabilities)
        
        tech_weight = self.weights['technical'] * technical.confidence
        news_weight = self.weights['news'] * news.confidence
        total_weight = tech_weight + news_weight
        
        if total_weight == 0:
            combined_probs = np.array([0.33, 0.34, 0.33])
        else:
            combined_probs = (tech_weight * tech_probs + news_weight * news_probs) / total_weight
        
        conflict = self._detect_conflict(technical, news)
        no_trade_reason = self._check_no_trade(combined_probs, technical, news, risk, conflict)
        if no_trade_reason:
            return Decision(
                action='NO_TRADE',
                reason=no_trade_reason,
                probabilities=combined_probs.tolist(),
                confidence=max(technical.confidence, news.confidence),
                position_size=0,
                agents={'technical': technical, 'news': news, 'risk': risk}
            )
        
        predicted_class = combined_probs.argmax()
        direction_map = {2: 1, 1: 0, 0: -1}
        final_direction = direction_map[predicted_class]
        
        position_size = self._calculate_position_size(
            combined_probs, technical.confidence, news.confidence, 
            risk.max_position_pct, final_direction
        )
        
        return Decision(
            action='TRADE' if position_size > 0 else 'NO_TRADE',
            reason='OK' if position_size > 0 else 'Position size zero',
            probabilities=combined_probs.tolist(),
            confidence=(tech_weight * technical.confidence + news_weight * news.confidence) / total_weight if total_weight > 0 else 0,
            position_size=position_size,
            direction=final_direction,
            agents={'technical': technical, 'news': news, 'risk': risk}
        )
    
    def _detect_conflict(self, technical, news):
        tech_dir = technical.direction
        news_dir = news.direction
        
        if tech_dir == 1 and news_dir == -1 and technical.confidence > 0.6 and news.confidence > 0.6:
            return True
        if tech_dir == -1 and news_dir == 1 and technical.confidence > 0.6 and news.confidence > 0.6:
            return True
        return False
    
    def _check_no_trade(self, probs, technical, news, risk, conflict):
        if probs.max() < self.config.min_max_prob:
            return 'Max probability below threshold'
        if conflict:
            return 'Conflicting technical and news signals'
        if technical.confidence < self.config.min_confidence and news.confidence < self.config.min_confidence:
            return 'Both agents low confidence'
        if risk.max_position_pct <= 0:
            return 'Risk limits allow zero position'
        return None
    
    def _calculate_position_size(self, probs, tech_conf, news_conf, max_pos, direction):
        if direction == 0:
            return 0
        
        expected_return = probs[2] * 0.02 + probs[0] * (-0.02)
        avg_confidence = (tech_conf + news_conf) / 2
        edge = abs(expected_return)
        size = max_pos * avg_confidence * min(edge / 0.02, 1.0)
        return max(0, min(size, max_pos))
`

---

## Decision Flow

`mermaid
flowchart TD
    A[Receive Prediction Request] --> B[Technical Agent Analysis]
    A --> C[News Agent Analysis]
    A --> D[Risk Agent Analysis]
    
    B --> E[Decision Engine]
    C --> E
    D --> E
    
    E --> F{Risk Veto?}
    F -->|Yes| G[NO_TRADE: Risk Reason]
    F -->|No| H[Combine Signals]
    
    H --> I{Conflict Detected?}
    I -->|Yes| J[NO_TRADE: Conflict]
    I -->|No| K[Check No-Trade Conditions]
    
    K --> L{No-Trade?}
    L -->|Yes| M[NO_TRADE: Condition]
    L -->|No| N[Calculate Position Size]
    
    N --> O{Size > 0?}
    O -->|Yes| P[TRADE: Direction + Size]
    O -->|No| Q[NO_TRADE: Zero Size]
    
    G --> R[Log Decision]
    J --> R
    M --> R
    P --> R
    Q --> R
    
    R --> S[Return Decision + Explanation]
`

---

## Explainability

Every decision must be explainable:

`python
@dataclass
class Explanation:
    decision: Decision
    technical_factors: List[Tuple[str, float]]
    news_factors: List[Tuple[str, float]]
    risk_factors: List[str]
    conflict_detected: bool
    no_trade_reason: Optional[str]
    position_sizing_rationale: str
    
    def to_natural_language(self):
        lines = [
            'Decision: ' + self.decision.action,
            'Direction: ' + ('UP' if self.decision.direction == 1 else 'DOWN' if self.decision.direction == -1 else 'SIDEWAYS'),
            'Confidence: ' + str(self.decision.confidence),
            'Position Size: ' + str(self.decision.position_size),
            ''
        ]
        
        if self.decision.action == 'TRADE':
            lines.append('Supporting Factors:')
            for feat, val in self.technical_factors[:3]:
                lines.append('  + ' + feat + ': ' + str(val))
            for feat, val in self.news_factors[:2]:
                lines.append('  + ' + feat + ': ' + str(val))
            
            lines.append('')
            lines.append('Risk Checks:')
            for rf in self.risk_factors:
                lines.append('  - ' + rf + ': OK')
        else:
            lines.append('Reason: ' + str(self.no_trade_reason))
            if self.conflict_detected:
                lines.append('  - Conflicting signals detected')
        
        return '
'.join(lines)
`

---

## Agent Configuration

`python
@dataclass
class AgentConfig:
    technical_weight: float = 0.6
    news_weight: float = 0.2
    risk_weight: float = 0.2
    min_confidence: float = 0.55
    min_max_prob: float = 0.40
    conflict_confidence_threshold: float = 0.6
    max_position_pct: float = 0.05
    max_sector_pct: float = 0.30
    max_gross_exposure: float = 1.0
    max_drawdown_pct: float = 0.20
    sizing_method: str = 'confidence_weighted'
    kelly_fraction_cap: float = 0.25
`

---

## Key Principles

1. Risk Agent Has Veto Power: Hard constraints cannot be overridden by other agents
2. Confidence-Weighted Combination: More confident agents have more influence
3. Explicit Conflict Handling: Conflicting signals trigger no-trade
4. No-Trade Default: When uncertain, do not trade
5. Full Audit Trail: Every decision logged with all agent inputs
6. Quantitative Over Qualitative: LLM reasoning supplements, never replaces, quantitative signals

---

## Agent vs LLM

The agent is NOT an LLM-based agent. It is a deterministic, rule-based coordinator of quantitative models.

If LLM is used (v2+):
- Only for generating natural language explanations
- Never for making trading decisions
- Never for overriding risk limits
- Always with human review for high-stakes decisions

---

## Summary

| Component | Implementation |
|-----------|----------------|
| Technical Agent | XGBoost + SHAP |
| News Agent | Rule-based + FinBERT sentiment |
| Risk Agent | Hard constraint checker |
| Decision Engine | Weighted combination + veto logic |
| Conflict Resolution | No-trade on strong disagreement |
| No-Trade Conditions | Low confidence, low prob, conflict, risk veto |
| Position Sizing | Confidence-weighted, risk-limited |
| Explainability | SHAP + rule trace |
| LLM Role | Explanation generation only (v2+) |