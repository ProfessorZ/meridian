This directory defines the high-level concepts, business logic, and architecture of this project using markdown. It is managed by [lat.md](https://www.npmjs.com/package/lat.md) — a tool that anchors source code to these definitions. Install the `lat` command with `npm i -g lat.md` and run `lat --help`.

- [[meridian]] — project overview, architecture, and entry points
- [[polling-loop]] — core async event loop orchestrating IP detection and DNS updates
- [[ip-detection]] — multi-source fallback strategy for public IPv4/IPv6 discovery
- [[provider-system]] — plugin architecture and registry for DNS providers
- [[route53-provider]] — AWS Route53 DNS implementation with credential refresh
- [[authentication]] — certificate-based AWS IAM Roles Anywhere credential acquisition
- [[configuration]] — layered YAML + env var config loading with Pydantic validation
- [[data-models]] — Pydantic v2 models for config, state, and DNS records
- [[web-panel]] — optional FastAPI monitoring dashboard
- [[state-management]] — JSON file persistence for IP change detection
- [[docker-deployment]] — multi-arch container build and compose services
- [[limitations]] — known gaps between architecture and implementation that drive the feature-completeness effort
- [[roadmap]] — planned work, items addressed in the current milestone, and explicitly deferred capabilities
- [[tests]] — executable test specifications anchored to code via `@lat:` references (require-code-mention enabled)
