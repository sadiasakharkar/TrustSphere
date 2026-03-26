def take_action(model_results, severity):
    actions = []

    high_risk_models = [name for name, score in model_results.items() if float(score) > 0.6]

    if severity == "HIGH":
        actions.extend([
            "Escalate to SOC analyst",
            "Quarantine suspicious email",
            "Block sender and embedded domains"
        ])
    elif severity == "MEDIUM":
        actions.extend([
            "Flag email for analyst review",
            "Warn recipient before interaction"
        ])
    else:
        actions.append("Log event for monitoring")

    if high_risk_models:
        actions.append(f"Triggered models: {', '.join(high_risk_models)}")

    return actions
