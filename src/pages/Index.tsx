import { useState, useCallback } from "react";
import { CheckCircle, XCircle, FileJson, Terminal, Zap, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

interface ValidationResult {
  total_entries: number;
  passed: number;
  failed: number;
  violations: Array<{
    robot_id: string;
    rule_id: string;
    message: string;
    timestamp: string;
  }>;
}

const Index = () => {
  const [logFile, setLogFile] = useState<File | null>(null);
  const [rulesFile, setRulesFile] = useState<File | null>(null);
  const [result, setResult] = useState<ValidationResult | null>(null);
  const [isValidating, setIsValidating] = useState(false);

  const handleFileUpload = useCallback((
    e: React.ChangeEvent<HTMLInputElement>,
    setter: (file: File | null) => void
  ) => {
    const file = e.target.files?.[0] || null;
    setter(file);
    setResult(null);
  }, []);

  const loadSampleFiles = useCallback(async () => {
    try {
      const [logsRes, rulesRes] = await Promise.all([
        fetch("/samples/sample_logs.json"),
        fetch("/samples/sample_rules.json"),
      ]);
      const logsBlob = await logsRes.blob();
      const rulesBlob = await rulesRes.blob();
      setLogFile(new File([logsBlob], "sample_logs.json", { type: "application/json" }));
      setRulesFile(new File([rulesBlob], "sample_rules.json", { type: "application/json" }));
      setResult(null);
    } catch {
      console.error("Failed to load sample files");
    }
  }, []);

  const simulateValidation = useCallback(async () => {
    if (!logFile || !rulesFile) return;

    setIsValidating(true);

    // Simulate validation delay
    await new Promise((r) => setTimeout(r, 800));

    try {
      const logText = await logFile.text();
      const logs = JSON.parse(logText);
      const logEntries = Array.isArray(logs) ? logs : logs.logs || [];

      // Demo simulation: random pass/fail based on log data
      const violations: ValidationResult["violations"] = [];
      let passed = 0;
      let failed = 0;

      logEntries.forEach((entry: Record<string, unknown>) => {
        const battery = entry.battery_level as number;
        const speed = entry.speed as number;
        const moving = entry.movement_state === "moving";

        let hasFail = false;

        if (typeof battery === "number" && battery < 20) {
          hasFail = true;
          violations.push({
            robot_id: String(entry.robot_id || "unknown"),
            rule_id: "BATTERY_MIN",
            message: `Battery level ${battery}% below minimum 20%`,
            timestamp: String(entry.timestamp || new Date().toISOString()),
          });
        }

        if (typeof speed === "number" && speed > 10) {
          hasFail = true;
          violations.push({
            robot_id: String(entry.robot_id || "unknown"),
            rule_id: "SPEED_MAX",
            message: `Speed ${speed} exceeds maximum 10`,
            timestamp: String(entry.timestamp || new Date().toISOString()),
          });
        }

        if (moving && typeof battery === "number" && battery < 10) {
          hasFail = true;
          violations.push({
            robot_id: String(entry.robot_id || "unknown"),
            rule_id: "CRITICAL_MOVEMENT",
            message: "Movement detected with critical battery",
            timestamp: String(entry.timestamp || new Date().toISOString()),
          });
        }

        if (hasFail) failed++;
        else passed++;
      });

      setResult({
        total_entries: logEntries.length,
        passed,
        failed,
        violations,
      });
    } catch {
      setResult({
        total_entries: 0,
        passed: 0,
        failed: 1,
        violations: [{ robot_id: "-", rule_id: "PARSE_ERROR", message: "Invalid JSON format", timestamp: new Date().toISOString() }],
      });
    }

    setIsValidating(false);
  }, [logFile, rulesFile]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm">
        <div className="container mx-auto flex items-center gap-3 px-6 py-4">
          <Terminal className="h-6 w-6 text-primary" />
          <h1 className="text-xl font-semibold tracking-tight">System Log Validator</h1>
          <span className="ml-2 rounded bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
            Demo UI
          </span>
        </div>
      </header>

      <main className="container mx-auto px-6 py-12">
        {/* Hero */}
        <section className="mb-12 text-center">
          <h2 className="mb-3 text-3xl font-bold tracking-tight sm:text-4xl">
            Validate Robot Logs Against Safety Rules
          </h2>
          <p className="mx-auto max-w-xl text-muted-foreground">
            Upload your log file and JSON ruleset to validate entries in real-time.
            The core engine is Python CLI-based — this UI is for demo purposes.
          </p>
        </section>

        {/* Upload Cards */}
        <div className="mx-auto mb-10 grid max-w-2xl gap-6 sm:grid-cols-2">
          <UploadCard
            label="Log File"
            accept=".json,.jsonl"
            file={logFile}
            onChange={(e) => handleFileUpload(e, setLogFile)}
          />
          <UploadCard
            label="Rules JSON"
            accept=".json"
            file={rulesFile}
            onChange={(e) => handleFileUpload(e, setRulesFile)}
          />
        </div>

        {/* Action Buttons */}
        <div className="mb-12 flex flex-wrap justify-center gap-4">
          <Button variant="outline" onClick={loadSampleFiles} className="gap-2">
            <FileText className="h-4 w-4" />
            Use Sample Files
          </Button>
          <Button
            size="lg"
            disabled={!logFile || !rulesFile || isValidating}
            onClick={simulateValidation}
            className="gap-2"
          >
            <Zap className="h-4 w-4" />
            {isValidating ? "Validating..." : "Run Validation"}
          </Button>
        </div>

        {/* Results */}
        {result && (
          <section className="mx-auto max-w-3xl space-y-6">
            <div className="grid gap-4 sm:grid-cols-3">
              <StatCard label="Total Entries" value={result.total_entries} />
              <StatCard label="Passed" value={result.passed} variant="success" />
              <StatCard label="Failed" value={result.failed} variant="destructive" />
            </div>

            {result.violations.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">Violations</CardTitle>
                  <CardDescription>Recent rule violations detected</CardDescription>
                </CardHeader>
                <CardContent className="max-h-64 overflow-y-auto">
                  <ul className="space-y-2 text-sm">
                    {result.violations.slice(0, 20).map((v, i) => (
                      <li key={i} className="flex items-start gap-2 rounded border border-border bg-muted/40 p-2">
                        <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
                        <div>
                          <span className="font-medium">{v.rule_id}</span>
                          <span className="mx-1 text-muted-foreground">·</span>
                          <span className="text-muted-foreground">{v.robot_id}</span>
                          <p className="text-muted-foreground">{v.message}</p>
                        </div>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </section>
        )}
      </main>

      <footer className="mt-auto border-t border-border py-6 text-center text-sm text-muted-foreground">
        Run the full CLI: <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">python -m src.cli -i logs.json -r rules.json</code>
      </footer>
    </div>
  );
};

/* ---------- Sub-components ---------- */

function UploadCard({
  label,
  accept,
  file,
  onChange,
}: {
  label: string;
  accept: string;
  file: File | null;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
}) {
  return (
    <Card className="relative overflow-hidden">
      <label className="block cursor-pointer p-6 text-center transition hover:bg-muted/30">
        <input type="file" accept={accept} onChange={onChange} className="sr-only" />
        <FileJson className="mx-auto mb-2 h-8 w-8 text-primary" />
        <p className="font-medium">{label}</p>
        {file ? (
          <p className="mt-1 truncate text-sm text-muted-foreground">{file.name}</p>
        ) : (
          <p className="mt-1 text-sm text-muted-foreground">Click to upload</p>
        )}
      </label>
      {file && (
        <CheckCircle className="absolute right-3 top-3 h-5 w-5 text-primary" />
      )}
    </Card>
  );
}

function StatCard({
  label,
  value,
  variant,
}: {
  label: string;
  value: number;
  variant?: "success" | "destructive";
}) {
  const color =
    variant === "success"
      ? "text-green-500"
      : variant === "destructive"
      ? "text-destructive"
      : "text-foreground";

  return (
    <Card className="p-4 text-center">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className={`text-3xl font-bold ${color}`}>{value}</p>
    </Card>
  );
}

export default Index;
