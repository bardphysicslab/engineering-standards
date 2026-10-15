# Bard web policy and service guidance

## Authority and applicability

The [original Bard web application and hosting requirements](web-application-and-hosting-requirements.pdf), revised February 26, 2025, is the written institutional source. Preserve its exact wording and conditions; this companion document does not replace it. PDF SHA-256: `0ceed5a82e1b4a9afeed7508ceb876f26ebb1fc5ccf752fad34131e08f5c39c6`.

The maintainer directed on October 13, 2026 that these requirements apply to **current and future BardBox and Bard Physics Lab projects wherever applicable**, including RKC Monitor, CESH and Beaker. Consult the PDF during planning, implementation, hosting and release review. Preserve required, recommended, ideal and conditional provisions. Confirm uncertain applicability for internal tools with Bard IT/PR. For existing projects, assess and record gaps, evidence and scoped remediation in their authoritative GitHub tracker; filing this policy does not certify compliance.

Before recommending hosting, email, messaging, SMS, authentication or monitoring, read this guidance and the PDF. Evaluate Bard's existing services first, verify access and suitability, and explain a concrete integration or operational reason for another provider. Meeting suggestions do not override written policy or finalize a provider, authentication method or migration. Changing infrastructure requires its own authorization.

These documents have one maintained home in `bardphysicslab/engineering-standards`. Other repositories and chat project instructions should link here, rather than maintain policy copies. Chat source copies, if needed, are read-only snapshots and must identify this authoritative location.

## October 13, 2026 meeting reference

The following reflects the maintainer's supplied notes from the conversation with Bard CIO David Brangaitis. Service capabilities, access and operational arrangements remain to be verified.

For BardBox and Bard Physics Lab projects, consider Bard’s existing services before recommending new vendors. Regroup should be the first SMS option evaluated before Twilio, provided it supports the project's integration and delivery needs. These preferences reflect the user's conversation with Bard CIO David Brangaitis on October 13, 2026; they are separate from the written hosting requirements.

### Bard services and contacts

| Service or person | Role | Guidance for future projects |
| - | - | - |
| Regroup | Bard's SMS gateway; David suggested it as an alternative to Twilio. | Evaluate first for SMS. Confirm API access, automated transactional alerts, delivery reporting, costs, and escalation suitability. |
| Jacob Testa | Manages Regroup. | Coordinate Regroup access and integration with him. |
| Google Chat | Security monitors Google messaging on a signed-in computer; David proposed webhooks. | Use an incoming webhook in a space Security monitors. Security or a space administrator provides the URL to the application team. Confirm overnight monitoring, acknowledgement, and escalation for freezer alerts. |
| Mailgun | Outgoing email service discussed by David. | Coordinate sender authorization and relay configuration with Bard IT before choosing another email provider. |
| Postfix | Mail transport software discussed alongside Mailgun. | Can serve as the application's relay to Mailgun; confirm the actual approved arrangement. |
| Linode | Hosting provider Bard uses and knows. | Include in hosting comparisons. Existing operational familiarity is relevant. |
| Google Cloud Platform or GCP | David proposed it for the RKC server. | Include in hosting comparisons; it is not a finalized hosting decision for all BardBox projects. |
| Hetzner | Current CESH hosting provider. | CESH may move as part of the broader hosting decision; no migration authorized or completed by this reference. |
| CAS, SAML, Google authentication | Sign-in methods Bard IT is familiar with. | Coordinate the appropriate institutional SSO integration before choosing a separate identity provider. No specific method selected. |
| Bard IT and Cloudflare | IT controls DNS and can provide Cloudflare origin certificates under the written policy. | Coordinate domains, DNS, proxy setup, certificates, sender permissions, and access requirements. |
| David Brangaitis | Bard CIO; maintainer of the web application and hosting requirements. | Institutional IT contact: [dbrangaitis@bard.edu](mailto:dbrangaitis@bard.edu). |
| Automated Logic WebCTRL | Building automation system operated at Bard by B&G, with Eastern Heating and Cooling as vendor, per David’s October 13 message. | Possible consumer of BardBox sensor data while B&G retains its existing dashboard; interface, compatibility, access, cost and support arrangements remain unverified. No integration selected or authorized. |
| AVTECH environment monitors | Environmental monitoring products supplied as a reference. | Reference only; procurement or adoption has not been established. |

Twilio is the alternative being compared with Regroup, not a recorded Bard service. Bard use of Zabbix has not been confirmed; an earlier chat interpretation should not be treated as evidence.

### Hosting and alert details to confirm

A static outbound IP is allowlisted in the existing Linode arrangement discussed with David. Confirm who maintains that allowlist and which service it protects before changing hosting. David also said a Bard public IP brings a system into Bard audit scope; coordinate the applicable scope with IT.

For after-hours freezer incidents, define detection thresholds, notification recipients, acknowledgement deadlines, and escalation ownership. A Google Chat webhook delivers a message to a space; it does not establish that someone has acted on it.

### BardBox development baseline

The user directed that Bard's web application and hosting requirements apply across BardBox, beyond RKC. The supplied PDF was revised February 26, 2025. Preserve the distinction between required, recommended, ideal, and conditional provisions.

Apply the policy to planning, implementation, hosting, and release review. Key provisions include IT/PR vendor and hosting disclosure before contracts; development access for security and accessibility review before launch; an ongoing support contract and redundant Bard-associated credential custody; Bard-managed DNS; HTTPS even in development, TLS 1.2 or newer and security headers; minimal exposed ports; current software; critical patches within 24 hours and noncritical updates within two months; applicable Cloudflare requirements; IT-authorized bard.edu senders; no bulk/spam or direct inbound email; form spam prevention and restrictions on sensitive/PII collection; accessibility, consent, privacy, branding, and authorized media requirements.

Use the PDF for exact wording and conditions. Clarify applicability to internal tools with Bard IT/PR, especially the stated shared-server restriction, identity/form data requirements, and the unspecified WCAG version/conformance target. Hosting and notification suggestions above do not override the written policy.


## WebCTRL clarification and possible integration — October 15, 2026

Source: David’s October 13 message, supplied by the maintainer as a screenshot
on October 15, identifies the pictured WebCTRL output as operated by B&G with
vendor Eastern Heating and Cooling, and shared for awareness. This confirms
use at Bard; it does not establish freezer coverage or an integration offer.

In the October 15 discussion, the maintainer explored BardBox supplying
potentially lower-cost temperature sensors and their readings to B&G while
B&G keeps WebCTRL as its dashboard. Conceptually, a BardBox instance could
expose a data interface that WebCTRL consumes directly or through an adapter.
The comparison with CESH supplying data to JustAir is architectural only;
it does not establish matching protocols or existing WebCTRL compatibility.

This is a possibility, not an implemented API, selected architecture or
commitment from B&G or its vendor. Bard’s installed WebCTRL version and
supported interfaces, authentication, data mapping, operational ownership,
reliability requirements, integration costs and overall savings are not yet
established. No procurement, sensor deployment or integration is authorized.
Project/platform-specific implementation decisions belong in their owning
repositories if this exploration proceeds; this section records shared IT
context only.

## Continuation and consolidation

Scope, verification and remaining work: [engineering-standards issue #5](https://github.com/bardphysicslab/engineering-standards/issues/5). Existing-project compliance assessments remain subsequent scoped tasks. No hosting, notification, SSO or hardware change is performed by this consolidation.
