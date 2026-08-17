export default function DiffView({ diff }: { diff: string }) {
  const lines = diff.split("\n");

  return (
    <pre className="text-xs sm:text-[13px] font-mono leading-relaxed overflow-x-auto rounded-xl bg-black/40 border border-line p-4">
      {lines.map((line, i) => {
        let cls = "text-muted";
        if (line.startsWith("+") && !line.startsWith("+++")) cls = "diff-line-add block px-1 -mx-1 rounded";
        else if (line.startsWith("-") && !line.startsWith("---")) cls = "diff-line-del block px-1 -mx-1 rounded";
        else if (line.startsWith("@@")) cls = "diff-line-hunk block";
        else if (line.startsWith("+++") || line.startsWith("---")) cls = "text-ink block";

        return (
          <span key={i} className={cls}>
            {line || " "}
            {"\n"}
          </span>
        );
      })}
    </pre>
  );
}
