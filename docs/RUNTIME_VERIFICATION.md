# Local security, privacy, offline and performance checks

MSE-602 is a focused release smoke check of the local runtime and its trust
boundaries, not a comprehensive penetration test. The maintained
[runtime evidence](../artifacts/reports/runtime_smoke.json) and
[dependency evidence](../artifacts/reports/dependency_audit.json) contain actual
run timestamps and machine details.

## Observed behavior

- The API uses a fixed loopback listener. Foreign Host/Origin requests return
  400/403 before parsing; bodies over 512 KiB return 413 and queries over 4 KiB
  return 414. Allowed local origins receive structured error responses with
  no-store and nosniff headers, including early and unexpected failures.
- Pasted HTML stays text: the synthetic remote-image payload created no image
  element or external request. Input appeared in neither request URLs, browser
  storage nor captured API logs, including the controlled exception case.
- All six core workflows and both predictions worked with browser non-loopback
  requests denied and API Python internet sockets denied. A blocked test probe
  verified the API guard; the application made zero internet attempts. This
  uses interception/socket guards rather than disconnecting the operating system.
- Existing corpus and model artifact bytes remained identical. Runtime requests
  expose aggregate data and fixed local artifacts; no upload, training, raw-mail
  or arbitrary-path HTTP endpoint exists. Downloading remains a separate CLI.
- The model loader checks every artifact hash before deserialization. Checksums
  detect corruption; local joblib files must still come from a trusted source.

The review found an HTTP consistency defect: early bounded errors lacked the
ordinary safe headers, and unexpected errors lacked local CORS headers. The
fix preserves readable local errors and the no-store policy without allowing
foreign origins. Four regression cases now pass; the full backend/bootstrap
suite passes **401 tests**. Frontend lint and production build also pass.

## Measured performance

The API ran on Linux x86_64, kernel 7.3.4-1-cachyos,
13th Gen Intel(R) Core(TM) i5-13420H with 12 logical CPUs
in the process affinity set. Backend Python is pinned to 3.12.15; the HTTP
measurement client used 3.14.10. RAM was not measured.
Each series has three warmups then 30 sequential full HTTP requests; p95 is the
nearest-rank percentile. The prediction input was a 100-character
synthetic demonstration text, not an original corpus message.

| Operation | Observed p95 | Target | Result |
|---|---:|---:|---|
| Dual-model prediction | 0.0642 s | ≤3 s | Pass |
| Cached dataset summary | 0.0454 s | ≤5 s | Pass |

These timings describe this machine and input; cold startup, other machines,
concurrent load and all possible 50,000-character inputs are not benchmarked.
The maximum input boundary was exercised separately by critical acceptance.

## Dependency advisories and reproduction

At the recorded timestamp, `npm audit` reported zero known advisories for the
213 dependencies it counted. pip-audit 2.10.1 checked 33 installed Python
packages with zero known advisories and zero skips. Public advisory feeds can
change; these results do not prove the absence of vulnerabilities.

```bash
python3 scripts/dependency_check.py
python3 scripts/smoke_check.py --browser /absolute/path/to/trusted/chromium
```

Advisory lookup requires internet access. The runtime smoke command builds the
UI and manages its own loopback processes; stop an existing API first so the
network-guarded test process can own port 8000. Browser setup is described in
[UI verification](UI_VERIFICATION.md). Private marker strings and server logs
remain in ignored local test output; public reports contain only aggregate
outcomes, counts, timings and artifact identities.
