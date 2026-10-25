# Security Policy

## Supported versions

The latest release on `main` is supported; there are no versioned release
lines yet.

## Reporting a vulnerability

If you find a vulnerability or unsafe default in `rampwatch` itself, please open a
private security advisory on the GitHub repository (or open an issue describing the
problem at a high level if you cannot use advisories). We will acknowledge within
72 hours and coordinate a fix before public disclosure.

## Intended use

Loopback only unless --allow-public is passed explicitly. Request counts are bounded by the ramp plan; there are no flood, amplification, reflection or header-spoofing features.

## Secrets

`rampwatch` stores no credentials and requires none. Do not commit real tokens, cookies
or keys to the spec/example files in this repository; `.gitignore` excludes `.env`
and common key material.
