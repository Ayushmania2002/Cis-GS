# Security Policy

## Supported Versions

Only the latest stable release receives security fixes.
Older versions are not actively patched.

| Version | Supported |
|---------|-----------|
| 1.3.x (latest) | ✅ Yes |
| 1.2.x | ❌ No |
| < 1.2 | ❌ No |

---

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub Issues.**

If you discover a security vulnerability in Cis-GS, please report it
responsibly by emailing:

**ayushmania2002@gmail.com**

Include the following in your report:

- A clear description of the vulnerability
- Steps to reproduce the issue
- The version of Cis-GS affected
- Any potential impact you have identified
- Optional: a suggested fix or patch

You will receive an acknowledgement within **72 hours** and a resolution
timeline within **7 days**. We will keep you informed throughout the process
and credit you in the release notes unless you prefer to remain anonymous.

---

## Security Scope

Cis-GS is a **locally executed desktop and CLI application** — it does not
run a web server, does not collect user data, and does not transmit genomic
sequences to any external service.

### In scope

- Vulnerabilities in Cis-GS source code that could allow arbitrary code
  execution, privilege escalation, or data exfiltration
- Malicious FASTA, GFF3, CSV, or MEME input files that could cause
  unexpected code execution or path traversal
- Insecure handling of file paths, temporary files, or user-supplied data
- Issues in the packaged Windows `.exe` build that introduce attack surface
  beyond the Python source

### Out of scope

- Vulnerabilities in third-party dependencies (BioPython, PyQt5, pandas,
  etc.) — please report those to the respective upstream projects
- Issues requiring physical access to the user's machine
- Denial-of-service via very large genome files (expected behaviour for a
  genome-scale tool)
- NCBI / KEGG REST API availability or security (controlled by NCBI / KEGG)

---

## External Network Connections

Cis-GS makes outbound connections only when the user explicitly requests:

| Feature | External service | Data sent |
|---|---|---|
| NCBI genome fetch | `api.ncbi.nlm.nih.gov` | Assembly accession / organism name |
| KEGG enrichment | `rest.kegg.jp` | KEGG organism code |
| Gene-ID conversion | `mygene.info` | Gene IDs (anonymised batch) |
| PlantTFDB / AnimalTFDB import | `planttfdb.gao-lab.org` | Species code |

No genomic sequences, expression data, or local file contents are ever
transmitted externally.

---

## Dependency Security

We recommend running Cis-GS in a dedicated virtual environment and keeping
dependencies up to date:

```bash
pip install --upgrade cis-gs
```

To audit installed dependencies for known CVEs:

```bash
pip install pip-audit
pip-audit
```

---

## Disclosure Policy

We follow a **coordinated disclosure** model:

1. Vulnerability reported privately
2. Fix developed and tested
3. Patched release published
4. Vulnerability publicly disclosed in the release notes (with credit)

We aim for a maximum of **30 days** from report to public disclosure for
critical issues, and **90 days** for low-severity issues.

---

## Contact

| Channel | Address |
|---|---|
| Security reports | ayushmania2002@gmail.com |
| General issues | [GitHub Issues](https://github.com/Ayushmania2002/Cis-GS/issues) |
| Documentation | https://ayushmania2002.github.io/Cis-GS/ |

*Cis-GS is developed at the Plant Signaling Lab, IISER Tirupati.*
