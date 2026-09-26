const states = { pending: "Odottaa", running: "Työskentelee", completed: "Valmis", failed: "Keskeytyi" };

export default function AgentProgress({ job }) {
  const steps = job.steps || [];
  const done = steps.filter(step => step.status === "completed").length;
  const finished = job.status === "completed";
  const value = finished ? 100 : Math.min(95, Math.round(done / (steps.length || 5) * 100));
  const current = steps.find(step => step.status === "running");
  const message = finished ? "Tutkimus on valmis" : job.status === "failed" ? "Tutkimus keskeytyi"
    : current ? `${current.label} työskentelee` : done === steps.length && done ? "Tallennetaan raporttia…" : "Valmistellaan seuraavaa työvaihetta…";
  return <section className="agent-progress" aria-label="Tutkimuksen edistyminen">
    <h2>Agentit työssä</h2>
    <p role="status">{message}</p>
    <progress max="100" value={value} aria-label="Valmistuneet tutkimusvaiheet" />
    <p className="field-help">{done} / {steps.length} vaihetta valmiina. Palkki kuvaa työvaiheita, ei jäljellä olevaa aikaa.</p>
    <ol>{steps.map(step => <li key={step.key} className={`agent-step ${step.status}`} aria-current={step.status === "running" ? "step" : undefined}>
      <span className={`agent-step-icon ${step.status === "running" && job.status === "running" ? "robot-working" : ""}`} aria-hidden="true">{step.status === "completed" ? "✓" : step.status === "running" ? "🤖" : step.status === "failed" ? "!" : "○"}</span>
      <div><strong>{step.label}</strong><small>{step.description}</small></div><span className="agent-state">{states[step.status]}</span>
    </li>)}</ol>
  </section>;
}
