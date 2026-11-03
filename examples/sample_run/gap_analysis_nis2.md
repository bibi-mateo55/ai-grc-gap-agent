# Gap analysis — CloudNova (fictional) vs NIS2

> ⚠️ **AI-assisted draft. Every finding must be validated by a qualified analyst before use.** Sample output: these assessments were hand-written to illustrate the agent's output format and were replayed through the same validation guardrails. They were not produced by a live AI run.

**Framework:** Directive (EU) 2022/2555 (NIS2) — cybersecurity risk-management, governance and reporting obligations  
**Organisation:** European SME (~45 employees) providing a multi-tenant B2B project-management SaaS platform hosted on AWS (single region). Processes customer personal data and documents. In scope of GDPR and NIS2 as a digital service provider.  
**Run:** 2026-11-03 · mode: `offline demo (no AI)`

## Summary

| Metric | Value |
|---|---|
| Controls assessed | 12 / 12 |
| ✅ Implemented | 0 |
| 🟡 Partial | 6 |
| ❌ Not implemented | 6 |
| ➖ N/A | 0 |
| **Compliance score** (implemented = 1, partial = 0.5) | **25.0%** |
| Findings flagged for human review | 1 |
| Assessments rejected by guardrails during the run | 0 |

> ✅ **Coverage check passed:** every control in scope was assessed.

## Executive summary (sample, hand-written)

CloudNova is at an early maturity stage for NIS2. Technical basics exist (SSO with MFA for staff, TLS, CloudTrail, daily snapshots), but governance, incident management and reporting are largely missing. The three most urgent gaps are: (1) no incident response or NIS2 reporting process, so the 24h/72h deadlines would be missed; (2) no MFA on the AWS root account and shared admin credentials; (3) no approved security policy or management-body oversight, which NIS2 makes a personal accountability issue for leadership.

## Prioritised gaps

| Priority | Control | Status | Gap | Recommendation | Related risks |
|---|---|---|---|---|---|
| HIGH | **NIS2-20** Governance: management body accountability | ❌ Not implemented | Management body neither approves nor oversees cybersecurity measures and has no training. | Have the board formally approve the security policy and risk treatment plan, add a quarterly cyber-risk agenda item, and schedule NIS2 training for all directors. | R-06 |
| HIGH | **NIS2-21b** Incident handling | ❌ Not implemented | No incident response plan, defined roles or detection capability. | Write an incident response plan with roles and severity levels, configure security alerts on CloudTrail/CloudWatch, and run a tabletop exercise. | R-01, R-04 |
| HIGH | **NIS2-21i** HR security, access control and asset management | ❌ Not implemented | Access control, HR security and asset management do not meet basic requirements. | Remove shared accounts, apply least privilege in AWS IAM, introduce an offboarding checklist with same-day access removal, and run quarterly access reviews. | R-07, R-13, R-15 |
| HIGH | **NIS2-23** Incident reporting obligations | ❌ Not implemented | No process to classify significant incidents and notify the authority within NIS2 deadlines. | Add a reporting annex to the incident plan with significance criteria, the competent CSIRT contact and templates for the 24h warning, 72h notification and one-month final report. | R-06 |
| HIGH | **NIS2-21a** Risk analysis and information system security policies | 🟡 Partial | Risk analysis is not formalised, approved or tied to a complete asset inventory. | Approve the risk register with a treatment plan and owners, finalise the security policy, and extend the inventory to cloud resources and data stores. | R-15 |
| HIGH | **NIS2-21c** Business continuity and crisis management | 🟡 Partial | Backups are untested and there is no continuity, DR or crisis-management plan. | Define RPO/RTO, perform and document a quarterly restore test, and write a DR plan covering a full AWS region outage. | R-09, R-14 |
| HIGH | **NIS2-21e** Secure acquisition, development and maintenance; vulnerability handling | 🟡 Partial | Secure development and vulnerability handling are not systematic. | Add SAST and dependency scanning to CI/CD, adopt a vulnerability scanner with patch SLAs, retest the 2024 pentest findings and publish a vulnerability disclosure contact. | R-03, R-05 |
| HIGH | **NIS2-21j** Multi-factor authentication and secured communications | 🟡 Partial | MFA is missing on the most privileged account and for customers; no secured emergency communications. | Enable MFA on the AWS root account immediately, offer MFA to customer users, and set up an out-of-band emergency contact channel. | R-01, R-12 |
| MEDIUM | **NIS2-21d** Supply chain security | ❌ Not implemented | No supplier security assessment, contractual clauses or list of critical suppliers. | Identify critical suppliers, send a short security questionnaire, and add security and incident-notification clauses to contracts. | R-05 |
| MEDIUM | **NIS2-21f** Effectiveness assessment of security measures | ❌ Not implemented | No way to measure whether security measures are effective. | Define 5–8 security KPIs (e.g. MFA coverage, patch latency, restore-test success) and plan an annual internal audit. | — |
| MEDIUM | **NIS2-21g** Cyber hygiene and security training | 🟡 Partial | Training is one-off and cyber hygiene does not cover all devices. | Introduce annual training with phishing simulations, extend MDM to 100% of devices used for work (including contractors) and deploy EDR. | R-01, R-04, R-16 |
| MEDIUM | **NIS2-21h** Cryptography and encryption | 🟡 Partial | Encryption is applied inconsistently and not governed by a policy. | Write a short cryptography policy, enforce default encryption on all S3 buckets and review KMS key rotation settings. | R-02 |

## Full assessment

| Control | Status | Evidence | Rationale | Confidence |
|---|---|---|---|---|
| **NIS2-20** Governance: management body accountability | ❌ Not implemented | E-01, E-02 | No approved security policy (E-01) and the board has not discussed cyber risk or received training in 12 months (E-02). | high |
| **NIS2-21a** Risk analysis and information system security policies | 🟡 Partial | E-01, E-03, E-04 | A first ISO 27005 risk register exists (E-03) but it is not approved, the security guideline is an unapproved draft (E-01) and the asset inventory is incomplete (E-04). | high |
| **NIS2-21b** Incident handling | ❌ Not implemented | E-15, E-16 | Incidents are handled ad hoc in Slack with no plan or roles (E-16); logs exist but are not reviewed and no security alerts are configured (E-15). | high |
| **NIS2-21c** Business continuity and crisis management | 🟡 Partial | E-11, E-17 | Daily snapshots and a multi-AZ database exist (E-11, E-17), but restores were never tested, RPO/RTO are undefined and there is no DR plan for a region outage. | high |
| **NIS2-21d** Supply chain security | ❌ Not implemented | E-20 | Suppliers are selected on price and features only, with no security assessment or clauses (E-20). | high |
| **NIS2-21e** Secure acquisition, development and maintenance; vulnerability handling | 🟡 Partial | E-12, E-13, E-14 | Peer review on pull requests and a 2024 pentest exist (E-12, E-13), but there is no SAST/DAST, no dependency scanning, irregular patching and no vulnerability scanner (E-14). | high |
| **NIS2-21f** Effectiveness assessment of security measures | ❌ Not implemented | E-24 | No security metrics are tracked and no internal audit has been performed (E-24). | high |
| **NIS2-21g** Cyber hygiene and security training | 🟡 Partial | E-18, E-19 | Onboarding includes a short security video (E-19) and most laptops are managed and encrypted (E-18), but there is no refresher training, no phishing simulation, no EDR and contractor devices are unmanaged. | medium 🔍 |
| **NIS2-21h** Cryptography and encryption | 🟡 Partial | E-10, E-22 | TLS 1.2+ and KMS-managed keys are in place (E-22), but not all S3 buckets are encrypted (E-10) and there is no cryptography policy. | high |
| **NIS2-21i** HR security, access control and asset management | ❌ Not implemented | E-04, E-05, E-07, E-08 | Shared admin accounts and AdministratorAccess roles (E-05), no offboarding (E-07), no access reviews (E-08) and an incomplete asset inventory (E-04). | high |
| **NIS2-21j** Multi-factor authentication and secured communications | 🟡 Partial | E-05, E-06, E-09, E-23 | MFA is enforced for staff Google Workspace/SSO (E-06), but not on the AWS root account (E-05), not offered to customers (E-09), and there is no emergency communication channel (E-23). | high |
| **NIS2-23** Incident reporting obligations | ❌ Not implemented | E-16, E-21 | The team is not aware of the 24h/72h NIS2 deadlines (E-16) and there is no breach-notification procedure (E-21). | high |

🔍 = flagged for human review (confidence below *high*, or marked not applicable).

## Evidence referenced

- **E-01** (Interview with CEO): There is no formally approved information security policy. The CTO wrote a draft security guideline in 2025 that was never approved by management.
- **E-02** (Board minutes Q2): The board has not discussed cybersecurity risk in the last 12 months. No board member has received cybersecurity training.
- **E-03** (Risk register (iso27005-risk-register project)): A first information-security risk register (16 risks, ISO 27005 method) was produced this year. It has not yet been formally approved or linked to a treatment plan.
- **E-04** (IT spreadsheet): A spreadsheet lists laptops and SaaS subscriptions, but cloud resources, data stores and asset owners are not recorded. Last updated eight months ago.
- **E-05** (AWS IAM export): The AWS root account has no MFA enabled. Two engineers share one administrator IAM user. Several IAM roles have AdministratorAccess attached.
- **E-06** (Google Workspace admin console): MFA is enforced for all employee Google Workspace accounts, which are used as SSO for most internal tools.
- **E-07** (HR / IT interview): There is no offboarding checklist. Access removal for leavers depends on the CTO remembering; one former contractor still had GitHub access three months after leaving.
- **E-08** (Interview with CTO): No periodic access reviews are performed for AWS, GitHub or the production database.
- **E-09** (Product documentation): Customer users log in with email and password (minimum 8 characters). MFA is not offered to customers.
- **E-10** (AWS Config / S3 inventory): One S3 bucket containing exported customer reports was publicly readable until last month. Default encryption is enabled on the production database but not on all S3 buckets. No CSPM tool is used.
- **E-11** (Architecture diagram): The platform runs in a single AWS region with a multi-AZ database. There is no documented disaster-recovery plan for a full region outage.
- **E-12** (GitHub repository settings): Pull requests require one reviewer before merging to main. There is no SAST, DAST or dependency scanning in the CI/CD pipeline. No secure-coding guideline exists.
- **E-13** (Pentest report (2024)): One external penetration test was performed in 2024; two high findings (IDOR and missing rate limiting) are recorded as fixed but were never retested.
- **E-14** (Interview with DevOps engineer): Container images are rebuilt monthly. OS patches on the two remaining EC2 instances are applied manually and irregularly. No vulnerability scanner is in place.
- **E-15** (AWS console): AWS CloudTrail is enabled in the main region and logs are kept for 90 days. Application logs go to CloudWatch, but nobody reviews them and no alerts are configured for security events.
- **E-16** (Interview with CTO): There is no written incident response plan or defined roles. Incidents are handled ad hoc in a Slack channel. The team is not aware of the NIS2 24h/72h reporting deadlines.
- **E-17** (AWS Backup console): Automated daily database snapshots are kept for 14 days. A restore has never been tested and RPO/RTO targets are not defined.
- **E-18** (MDM report): About 70% of company laptops are enrolled in MDM with full-disk encryption enforced. Contractors use personal devices without controls. Built-in antivirus is used; there is no EDR.
- **E-19** (HR records): New employees watch a 20-minute security video during onboarding. There is no annual refresher or phishing simulation.
- **E-20** (Procurement interview): Suppliers are chosen on price and features. No security questionnaire or contractual security clauses are used, except AWS standard terms. There is no list of critical suppliers.
- **E-21** (Website / legal): A privacy policy is published and a data processing agreement template exists for customers. No DPO is appointed, there is no record of processing activities and no breach-notification procedure.
- **E-22** (Interview with CTO): TLS 1.2+ is enforced on all public endpoints. Encryption keys are managed by AWS KMS with default settings. There is no written cryptography policy.
- **E-23** (Interview with CEO): Internal communication uses Slack and Google Meet with SSO. There is no out-of-band emergency communication channel if Google Workspace or Slack is unavailable.
- **E-24** (Interview with CTO): No security metrics or KPIs are tracked and no internal audit of security controls has been performed.
