<h1 align="center"><strong>System Log Validator</strong></h1>

<h3 align="center">Python CLI–First Safety Rule Validation Engine</h3>

<p align="center">
🔗 <a href="https://system-log-validator.vercel.app/">System Log Validator</a>
</p>

<p>
<strong>System Log Validator</strong> is a Python CLI-first tool for validating robot and system logs against configurable safety rules defined in JSON.  
It processes logs in a streaming manner, generates real-time alerts for violations, and produces structured PASS/FAIL reports. A minimal web UI is included for demo purposes.
</p>

<h3><strong>Features</strong></h3>

- **Streaming validation** to process logs line-by-line without loading entire files into memory  
- **JSON-based rule engine** with extensible operators and conditional rules  
- **Real-time alerts** for safety violations during validation  
- **Detailed JSON reports** with per-robot PASS/FAIL status and violation summaries  
- **Demo UI** for quick validation and visualization (core logic remains CLI-based)

<h3><strong>Tech Stack</strong></h3>

- **Python 3.x** (CLI-first backend)  
- **Custom JSON Rule Engine**  
- **Streaming Log Processing**  
- **React (TypeScript)** — demo UI only  
- **Tailwind CSS & shadcn/ui**  
- **Vercel Deployment** (UI)

<p align="center">
 <img width="1907" height="858" alt="image" src="https://github.com/user-attachments/assets/869628e0-b30a-4731-8d72-06242c32782a" />
</p>
