"use client";

import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";

interface AnalysisReportProps {
  content: string;
}

export function AnalysisReport({ content }: AnalysisReportProps) {
  if (!content) {
    return <p className="text-sm text-muted-foreground">暂无分析报告</p>;
  }

  return (
    <div className="prose prose-sm max-w-none">
      <ReactMarkdown rehypePlugins={[rehypeSanitize]}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
