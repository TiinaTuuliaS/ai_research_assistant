// Stored agent payloads are internal data. Display their public text only.
export function stepText(output) {
  try {
    const data = JSON.parse(output);
    if (Array.isArray(data.accepted_findings)) {
      return data.accepted_findings.map(finding => [
        `### ${finding.title || "Havainto"}`, finding.summary,
        finding.source ? `[Lähde](${finding.source})` : "",
        Array.isArray(finding.limitations) ? finding.limitations.join(" ") : "",
      ].filter(Boolean).join("\n\n")).join("\n\n");
    }
    if (data.answer?.statement && Array.isArray(data.conclusions)) {
      const conclusions = [data.answer, ...data.conclusions].map(item =>
        [item.statement, item.uncertainty].filter(Boolean).join("\n\n"));
      const statuses = { shared: "Yhteinen ominaisuus", evidenced_difference: "Osoitettu ero", proposal: "Testattava ehdotus", unknown: "Ei vahvistettu" };
      const comparisons = (data.comparisons || []).map(item =>
        [`### ${item.competitor}: ${item.feature}`, statuses[item.status], item.limitation].filter(Boolean).join("\n\n"));
      return [...conclusions, ...comparisons,
        data.recommendation ? `### Suositus\n\n${data.recommendation}` : "",
        data.alternative ? `### Vaihtoehto\n\n${data.alternative}` : "",
        data.gaps?.length ? `### Tiedon puutteet\n\n${data.gaps.map(gap => `- ${gap}`).join("\n")}` : "",
      ].filter(Boolean).join("\n\n");
    }
  } catch { /* Existing Markdown outputs need no conversion. */ }
  return output;
}

export function compactCitations(result = "") {
  result = result || "";
  const heading = /^##\s+(?:Lähteet|Sources)\s*$/im.exec(result);
  const split = heading ? heading.index : result.length;
  const numbers = new Map();
  const link = /\[([^\]\n]+)\]\((https?:\/\/[^\s)]+)\)/g;
  const body = result.slice(0, split).replace(link, (_, title, url) => {
    if (!numbers.has(url)) numbers.set(url, numbers.size + 1);
    return `[${numbers.get(url)}](${url})`;
  });
  const sources = result.slice(split).replace(link, (_, title, url) =>
    `[${numbers.has(url) ? `${numbers.get(url)}. ` : ""}${title}](${url})`);
  return body + sources;
}
