"""A deterministic compilation, never a substitute for a validated analysis."""


def partial_report(steps):
    completed = [step for step in steps if step.get("status") == "completed"
                 and step.get("output") and step.get("key") != "writer"]
    if not completed:
        return ""
    return "\n\n".join([
        "# Tutkimuksen osatulokset",
        "Loppuraportti ei valmistunut. Tämä on automaattinen kooste valmistuneista "
        "välituloksista, ei hyväksytty loppuanalyysi. Väitteet voivat olla puutteellisia "
        "tai ristiriitaisia. Löydetyt toimijat eivät muodosta kattavaa markkinakartoitusta.",
        *[f"## {step['label']}\n\n{step['output']}" for step in completed],
    ])
