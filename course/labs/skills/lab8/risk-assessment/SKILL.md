---
name: risk-assessment
description: Assess release risk with clear severity, likelihood, blast radius, and mitigations.
---

# Risk Assessment Skill

## When To Use
- User asks whether a release is safe.
- User requests go/no-go recommendations.

## Workflow
1. Identify risks from the provided changes.
2. Score each risk:
- Severity: Low / Medium / High
- Likelihood: Low / Medium / High
- Blast Radius: narrow / moderate / broad
3. Propose mitigation and rollback plan for each High risk.
4. Provide an overall recommendation: Go, Go with guardrails, or No-Go.

## Output Table
| Risk | Severity | Likelihood | Blast Radius | Mitigation | Rollback |
|------|----------|------------|--------------|------------|----------|

## Quality Rules
- Explicitly call out assumptions.
- If data is missing, ask for it before giving high-confidence guidance.
