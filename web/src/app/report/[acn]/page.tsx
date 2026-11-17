import ReportView from "@/components/report-view";
export default async function ReportPage({
  params,
}: {
  params: Promise<{ acn: string }>;
}) {
  const { acn } = await params;
  return <ReportView key={acn} acn={acn} />;
}
