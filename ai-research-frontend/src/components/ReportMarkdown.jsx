import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const components = {
  table: ({ node, ...props }) => <div className="report-table-scroll" role="region" aria-label="Raportin taulukko" tabIndex={0}>
    <table {...props} />
  </div>,
};

export default function ReportMarkdown({ children }) {
  return <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>{children}</ReactMarkdown>;
}
