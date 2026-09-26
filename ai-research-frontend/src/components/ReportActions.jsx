import { useState } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import ReactMarkdown from "react-markdown";
import { reportText } from "./ResearchReport";

export default function ReportActions({ topic, result, steps = [] }) {
  const [status, setStatus] = useState("");
  const [sharing, setSharing] = useState(false);
  const text = `${topic}\n\n${reportText(result, steps)}`;
  const excerpt = `${topic}\n\nOte tutkimusraportista:\n${result.slice(0, 1200)}${result.length > 1200 ? "\n[Ote päättyy tähän.]" : ""}\n\nKoko raportin voi toimittaa erillisenä PDF-tiedostona.`;

  const pdf = () => {
    const popup = window.open("", "_blank", "width=900,height=750");
    if (!popup) { setStatus("Salli ponnahdusikkuna PDF-tallennusta varten."); return; }
    popup.opener = null;
    popup.document.write('<!doctype html><html lang="fi"><head><meta charset="utf-8"><title>Tutkimusraportti</title><style>@page{size:A4;margin:18mm}body{font:11pt/1.55 Arial,sans-serif;color:#222;max-width:760px;margin:24px auto;padding:0 16px}h1{font-size:22pt}h2{font-size:16pt;color:#3e0f8d}h3{font-size:13pt}h1,h2,h3{break-after:avoid}a{color:#3e0f8d;overflow-wrap:anywhere}pre{white-space:pre-wrap}img{max-width:100%}table{width:100%;border-collapse:collapse}td,th{padding:6px;border:1px solid #ddd}@media print{body{margin:0;padding:0;max-width:none}}</style></head><body></body></html>');
    popup.document.close();
    popup.document.title = topic;
    popup.document.body.innerHTML = renderToStaticMarkup(<article><h1>{topic}</h1><p>AI Markkinatutkimusassistentti · Tekoälyn tuottama raportti</p><ReactMarkdown>{reportText(result, steps)}</ReactMarkdown></article>);
    popup.focus();
    popup.print();
    setStatus("Valitse tulostusikkunassa kohteeksi Tallenna PDF-muodossa. Mukana ovat agenttien näkemykset, loppuraportti ja lähteet.");
  };
  const copy = async () => {
    try { await navigator.clipboard.writeText(text); setStatus("Koko raportti kopioitu."); }
    catch { setStatus("Kopiointi ei onnistunut. Voit ladata raportin TXT-tiedostona."); }
  };
  const share = async () => {
    setSharing(true);
    if (!navigator.share) return;
    try { await navigator.share({ title: topic, text }); }
    catch (error) { if (error.name !== "AbortError") setStatus("Laitteen jakaminen ei onnistunut. Käytä alla olevia vaihtoehtoja."); }
  };
  const download = () => {
    const url = URL.createObjectURL(new Blob([text], { type: "text/plain;charset=utf-8" }));
    const link = document.createElement("a");
    link.href = url; link.download = `${topic.replace(/[<>:"/\\|?*]/g, "_").slice(0, 100) || "raportti"}.txt`;
    link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  return <div className="report-actions">
    <div className="actions">
      <button type="button" className="button primary" onClick={pdf}>Tallenna PDF</button>
      <button type="button" className="button subtle" onClick={share}>Jaa raportti</button>
      <button type="button" className="button subtle" onClick={download}>Lataa TXT</button>
      <button type="button" className="button subtle" onClick={copy}>Kopioi raportti</button>
    </div>
    {sharing && <div className="share-options" aria-label="Jakamisen vaihtoehdot">
      <p>Sähköposti ja WhatsApp avaavat viestiluonnoksen, jossa on lyhyt ote. Voit liittää tallennetun PDF:n itse tai kopioida koko raportin.</p>
      <div className="actions"><a className="button subtle" href={`mailto:?subject=${encodeURIComponent(topic)}&body=${encodeURIComponent(excerpt)}`}>Sähköposti</a>
        <a className="button subtle" href={`https://wa.me/?text=${encodeURIComponent(excerpt)}`} target="_blank" rel="noopener noreferrer">WhatsApp</a>
        <button type="button" className="button subtle" onClick={() => setSharing(false)}>Sulje jakovaihtoehdot</button></div>
    </div>}
    {status && <p role="status">{status}</p>}
  </div>;
}
