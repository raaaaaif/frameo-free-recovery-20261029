# Remaining backup research — 30 October 2026

**The original OpenMidnight weights and a complete current PMC Open Access collection remain unresolved.** This report adds verified evidence and two small-scope Internet Archive deposits. It does not declare the whole task complete.

Checked 2026-10-30T07:30:25.872237+00:00. No public preservation requests were sent. No paid service was enabled. No bulk article, model, or archive payload was saved to this computer; transfer tests used memory.

## New recoverable copies

| Deposit | What was preserved | Verification |
| --- | --- | --- |
| [PMC6264737.1 article](https://archive.org/details/pmc6264737-complete-oa-snapshot-20261030) | One article's 12 original files: PDF, XML, text, metadata and eight figures | Entire archive retrieved independently from Internet Archive; archive SHA256 and all member checksums checked |
| [PMC inventory dated 29 October](https://archive.org/details/pmc-article-inventory-20261029) | All 11 compressed inventory CSVs and their manifest; 255,214,082 bytes | All 12 files fully retrieved independently and hashed |

The inventory is a list of files, **not the articles themselves**. The one-article deposit is a working memory-only transfer test, **not a collection backup**. Both are independent of NLM's live S3 files after retrieval.

Direct article archive: [PMC6264737.1-complete.tar.gz](https://archive.org/download/pmc6264737-complete-oa-snapshot-20261030/PMC6264737.1-complete.tar.gz). SHA256: `326ddb183c824efcaef09fa9f9b901a70e6206ae9cc9e41994eeeb23fe420da0`.

## PMC coverage and scale

The dated official inventory has 9,467,667 article-version entries representing 9,306,417 unique PMC identifiers. It includes multiple subsets, not only open-access articles.

Europe PMC's bulk OA metadata, last modified Mon, 26 Oct 2026 01:01:03 GMT, contains 3,265,307 unique eligible identifiers. 3,247,591 are present in both dated inventories. 6,058,826 official-inventory identifiers are absent from that bulk OA metadata. **That difference is not an OA missing-article count:** it includes differences in subset eligibility and publication/update timing. Identifier presence does not verify article files or versions.

The bulk metadata is also not a complete inventory of the live Europe PMC service. Four selected older identifiers absent from the bulk file (PMC139413, PMC193660, PMC308832 and PMC441500) yielded complete, correctly identified XML through the live API. Five selected recent NLM OA articles (PMC13716534–PMC13716538) had no live search result, and their XML requests returned HTTP 500 at the check time. These are observations of availability, not proof of permanent absence. Accordingly, neither the bulk-file omissions nor the live aggregate count is treated as a complete coverage measurement.

Separately, all 114 sampled OA articles could be read in full XML from Europe PMC. Their XML bytes differ from NLM's serialization. A supplementary-file sample had two complete files with MD5 values matching the NLM originals. These results establish working recovery routes for those samples; they cannot prove complete current coverage.

A deterministic sample of 128 official inventory entries produced an estimated **47.3 TB** for the OA original files, with an estimated standard error around 9.0 TB and substantial uncertainty from varying article sizes. This is an estimate, not a measured corpus total. The existing free Hugging Face allowance is insufficient for that estimate.

[NLM documents](https://pmc.ncbi.nlm.nih.gov/tools/cloud/) that existing article versions can change and, occasionally, be removed. Its daily inventory alone therefore cannot recover removed content. The [Europe PMC bulk directory](https://ftp.ebi.ac.uk/pub/databases/pmc/oa/) is an existing mirror, not a newly created immutable snapshot under this account.

Internet Archive accepted the memory-only transfer test. Extending it to tens of terabytes would require a long-running transfer and verification worker. A free remote worker sufficient for this full job was not established. [Hugging Face's current documentation](https://huggingface.co/docs/hub/spaces-overview) requires a paid personal plan for ordinary new compute Spaces. No paid plan, compute resource, or unbounded bulk-transfer job was started.

## Original OpenMidnight

The [official original repository](https://huggingface.co/SophontAI/OpenMidnight) remains gated. The main GitHub repository and all 26 public forks were checked for checkpoint files and release assets; none provided the original weights. Public derivative histories, author catalogs, paper deposits and other indexed mirrors did not yield an accessible original checkpoint.

The public OpenMidnight 1.1 and SPECTRA copies already preserved are different models. They are useful alternatives but cannot be represented as backups of either original checkpoint. The exact original filenames, sizes and SHA256 values are recorded in the [evidence file](remaining-backup-evidence.json).

## What remains unfulfilled

1. An accessible copy of the two original OpenMidnight checkpoint files, followed by verified independent preservation.
2. A complete copy of all current PMC OA article files, with a defined capture interval and file-level coverage and integrity verification.

No complete free solution satisfying both remaining requirements has been verified. The [main recovery index](https://github.com/raaaaaif/frameo-free-recovery-20261029) continues to distinguish existing mirrors, created copies, partial coverage and unresolved resources.
