import type { Status } from "@/lib/types";
export default function StatusBadge({ status }: { status: Status }) {
  return (
    <span data-testid="answer-status" className={`status status-${status}`}>
      {status.replaceAll("_", " ")}
    </span>
  );
}
