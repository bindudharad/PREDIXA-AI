# AGENT_DESIGN.md

## Agent Architecture and Decision Process

This document details the prediction agent architecture.

## Agent Overview

The Prediction Agent coordinates specialized sub-agents into unified decisions.
It is a deterministic, rule-based coordinator - NOT an LLM agent.

`
                 PREDICTION AGENT
                       |
       +---------------+---------------+
       |               |               |
       v               v               v
Technical Agent   News Agent      Risk Agent
       |               |               |
       v               v               v
XGBoost + SHAP   FinBERT + Rules  Hard Constraints
       +---------------+---------------+
                       |
                       v
               Decision Engine
                       |
                       v
            Final Decision + Explanation
`

## Sub-Agent Specifications

### Technical Agent
**Input**: Technical features (price, technical, volatility, market-relative, regime)
**Model**: XGBoost (production version)
**Output**: 
- Probabilities [P(DOWN), P(SIDEWAYS), P(UP)]
- Confidence (entropy-based)
- Direction: -1/0/+1
- Strength: max_prob - 0.333
- Top SHAP features (positive/negative)

### News Agent
**Input**: News features (sentiment, count, ratios, credibility)
**Model**: Rule-based on FinBERT sentiment
**Output**:
- Probabilities based on sentiment direction
- Confidence = credibility * (1 - sentiment_std)
- Direction: -1/0/+1
- Strength: sentiment magnitude * ratio

### Risk Agent
**Input**: Portfolio state, risk limits, prediction context
**Model**: Hard constraint checker (deterministic)
**Output**:
- Allowed: boolean
- Max position %: calculated from limits
- Constraints violated: list
- Veto reason: string (if not allowed)

## Decision Engine

### Signal Combination
`python
# Confidence-weighted combination
tech_weight = 0.6 * technical.confidence
news_weight = 0.2 * news.confidence
total_weight = tech_weight + news_weight

combined_probs = (tech_weight * tech_probs + news_weight * news_probs) / total_weight
`

### Conflict Detection
- If technical.direction == +1 AND news.direction == -1 AND both confidence > 0.6: CONFLICT
- If technical.direction == -1 AND news.direction == +1 AND both confidence > 0.6: CONFLICT
- Result: NO_TRADE

### No-Trade Conditions
1. Risk agent veto (hard limits reached)
2. Max probability < 0.40
3. Confidence < 0.55 (both agents)
4. Conflict detected
5. Risk agent allows zero position size

### Position Sizing
`python
if direction != 0 and allowed:
    expected_return = combined_probs[UP]*0.02 + combined_probs[DOWN]*(-0.02)
    avg_confidence = (tech_conf + news_conf) / 2
    edge = abs(expected_return)
    size = max_pos * avg_confidence * min(edge / 0.02, 1.0)
    size = max(0, min(size, max_pos))
else:
    size = 0
`

## Explanation Generation

Every decision includes:
1. **Final prediction**: Class + probabilities + confidence
2. **Technical factors**: Top 3 positive/negative SHAP features
3. **News factors**: Sentiment, count, credibility
4. **Risk factors**: Constraints checked (all OK or violations)
5. **Conflict**: Whether detected
6. **Position sizing rationale**: Formula with values

## Agent Configuration

`yaml
technical_weight: 0.6
news_weight: 0.2
risk_weight: 0.2
min_confidence: 0.55
min_max_prob: 0.40
conflict_confidence_threshold: 0.6
max_position_pct: 0.05
max_sector_pct: 0.30
max_gross_exposure: 1.0
max_drawdown_pct: 0.20
`

## Key Principles

1. **Risk Agent has veto power**: Hard constraints cannot be overridden
2. **Confidence-weighted**: More confident agents have more influence
3. **Explicit conflict handling**: Conflicting signals = no trade
4. **No-trade default**: When uncertain, don't trade
5. **Full audit trail**: Every decision logged with all agent inputs
6. **Quantitative over qualitative**: LLM only for natural language (v2+)

## LLM Integration (v2+)

If LLM is used:
- ONLY for generating natural language explanations
- NEVER for making trading decisions
- NEVER for overriding risk limits
- ALWAYS with human review for high-stakes decisions
- Prompt includes: decision, all agent outputs, SHAP values
