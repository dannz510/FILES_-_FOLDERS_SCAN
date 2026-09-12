# 🛡️ AppScan — Automated Security & Vulnerability Analysis Tool

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://www.microsoft.com/windows)

**AppScan** is an automated application security analysis tool designed to scan source code, identify potential security weaknesses, and detect vulnerable or outdated dependencies.

It provides a lightweight workflow for developers who want to perform basic security checks during application development without relying entirely on external security platforms.

---

## ⚡ Features

| Feature                      | Description                                                                                                              |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| 🔍 **SAST**                  | Performs static source-code analysis to identify potentially weak or insecure logic.                                     |
| 📦 **Dependency Analysis**   | Checks project dependencies for outdated packages and known security vulnerabilities such as CVEs.                       |
| 🚀 **Standalone Executable** | Supports packaging the application into a Windows `.exe` executable that can run without a separate Python installation. |
| 📊 **Detailed Reporting**    | Generates structured scan results for easier analysis and review.                                                        |

---

## 🏗️ Architecture

AppScan is organized around a simple scanning workflow:

```text
      Source Code
           │
           ▼
┌─────────────────────┐
│      AppScan        │
│                     │
│  ┌───────────────┐  │
│  │ Source Scanner│  │
│  └───────┬───────┘  │
│          │          │
│  ┌───────▼───────┐  │
│  │  Dependency   │  │
│  │    Checker    │  │
│  └───────┬───────┘  │
│          │          │
│  ┌───────▼───────┐  │
│  │    Report     │  │
│  │   Generator   │  │
│  └───────────────┘  │
└──────────┬──────────┘
           │
           ▼
     Scan Results
```

---

## 📂 Project Structure

```text
appscan/
├── dist/               # Compiled application and binary distribution
├── build/              # Temporary PyInstaller build artifacts
├── src/                # Main application source code
├── requirements.txt    # Python dependencies
├── app.py              # Application entry point
└── README.md            # Project documentation
```

> `dist/` and `build/` are generated directories and normally should not be committed to source control.

---

## 🛠️ Installation

### System Requirements

* **Python:** 3.9 or newer
* **Operating System:** Windows, Linux, or macOS
* **Git:** Recommended for cloning the repository

### Clone the Repository

```powershell
git clone https://github.com/dannz510/appscan.git
cd appscan
```

### Create a Virtual Environment

#### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🚀 Usage

### Run from Source

Start AppScan directly from the Python source code:

```bash
python app.py
```

---

## 📦 Build a Standalone Executable

AppScan can be packaged using **PyInstaller**.

```bash
pyinstaller --noconfirm --onedir --windowed app.py
```

After a successful build, the generated application will typically be available at:

```text
dist/
└── appscan/
    └── appscan.exe
```

The standalone executable can then be distributed to supported Windows systems without requiring users to manually install Python and the project dependencies.

---

## 📋 Dependencies

Project dependencies are maintained in:

```text
requirements.txt
```

Install them with:

```bash
pip install -r requirements.txt
```

To regenerate the dependency list automatically using `pipreqs`:

```bash
python -m pipreqs.pipreqs . \
    --encoding=utf-8-sig \
    --ignore dist,build,venv \
    --force
```

### Why `pipreqs`?

`pipreqs` analyzes the Python source code and generates a dependency list based on packages actually imported by the project, helping keep `requirements.txt` cleaner than blindly exporting the entire Python environment.

---

## 🔎 Security Scanning Workflow

A typical AppScan workflow can be represented as:

```text
1. Load Project
       │
       ▼
2. Discover Source Files
       │
       ▼
3. Analyze Source Code
       │
       ▼
4. Inspect Dependencies
       │
       ▼
5. Identify Potential Issues
       │
       ▼
6. Generate Report
       │
       ▼
7. Review Findings
```

The exact checks and findings depend on the scanners and rules implemented in the current version of AppScan.

---

## 🧪 Development

For development, activate the virtual environment before working on the project:

```bash
python -m venv venv
```

Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

Linux / macOS:

```bash
source venv/bin/activate
```

Then install the required packages:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python app.py
```

---

## 🧹 Project Maintenance

Before committing changes, it is recommended to keep generated files out of the repository:

```text
build/
dist/
venv/
.venv/
__pycache__/
```

A typical `.gitignore` should therefore exclude these directories.

---

## 📊 Reporting

AppScan is designed to provide structured security findings that can help developers:

* Identify potentially insecure source-code patterns.
* Review dependency-related security risks.
* Prioritize findings for further investigation.
* Track security issues during development.
* Produce readable scan results for review.

> **Important:** Automated security scanners can produce false positives and false negatives. Scan results should be manually reviewed before treating a finding as a confirmed vulnerability.

---

## ⚠️ Disclaimer

AppScan is intended for **authorized security analysis, defensive development, and educational purposes**.

Only scan applications, source code, and systems that you own or have explicit permission to analyze.

The tool should not be used to gain unauthorized access to systems, applications, networks, or data.

---

## 🤝 Contributing

Contributions, bug reports, feature requests, and improvements are welcome.

A typical contribution workflow is:

```bash
git checkout -b feature/your-feature
```

Make your changes, test them, and then create a pull request.

When contributing, please keep the codebase clean, document significant changes, and avoid committing generated build artifacts.

---

## 📌 Roadmap

Potential future improvements include:

* [ ] Expanded SAST rules
* [ ] Improved dependency vulnerability detection
* [ ] CVE database integration
* [ ] Severity classification
* [ ] HTML / JSON / CSV reporting
* [ ] Improved false-positive filtering
* [ ] Configurable scanning rules
* [ ] CI/CD integration
* [ ] Cross-platform executable builds
* [ ] Security scan history and comparison

---

## 📜 License

AppScan is distributed under the **MIT License**.

See the [`LICENSE`](LICENSE) file for the complete license text.

---

## 👤 Author

**Dannz**

GitHub: [@dannz510](https://github.com/dannz510)

---

<div align="center">

### 🛡️ AppScan

**Scan smarter. Find risks earlier. Build more securely.**

</div>
