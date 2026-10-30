# Retrieve the preserved resources later

The files in this kit are instructions and verification records. The large models, datasets and source archives stay on the remote services listed in the index.

Open **free-recovery-index.md** for the current working links and outstanding gaps. You can browse the copies and download individual files through those links. For the private GenBio copy, sign into your **hellnahbru** Hugging Face account.

When you have an external drive, extract this kit onto it. Keep the JSON files beside `restore-backups.py`.

To list available recovery plans without downloading anything, open Terminal in the extracted folder and run:

```bash
python3 restore-backups.py --list
```

Choose the exact repository identifier printed in the list. For example, this only previews the Ghidra recovery plan:

```bash
python3 restore-backups.py --resource nationalsecurityagency/ghidra
```

To download, replace the example drive path with the path to your actual external drive:

```bash
python3 restore-backups.py --resource nationalsecurityagency/ghidra --destination "/Volumes/My External Drive/Frameo/Ghidra" --download
```

Downloads go directly to the chosen folder. Model and dataset files resume where the host supports it and receive a full checksum check. Small generated source archives restart after an interruption; if their packaging changes, the helper verifies every source file against the pinned Git tree. It does not extract archives or run the downloaded programs. Large model or dataset restores can take substantial time; choose individual resources you want to retrieve.

`recovery-manifest.json` records pinned revisions, file lists, checksums, current recovery locations and unavailable destinations. `recovery-verification.json` records which files were fully read and which large files received bounded checks. Historical PMC snapshots, alternative OpenMidnight models, and exact originals are labeled separately.

The Internet Archive source-upload item was removed and is excluded from current recovery plans. Public GitHub forks and Software Heritage bundles provide source recovery where verified. The saved remote copies remain usable without this computer being on; finishing any still-pending copy jobs requires the computer and its internet connection.

## Historical PMC torrent

`PMC-June-2025.torrent` is a small map to an existing June 2025 snapshot: 1,826 files totaling 347,357,315,508 bytes (347 GB). It is not the full current PMC collection. On 30 October 2026, a peer advertised all pieces and a complete 1,835,444-byte piece passed its SHA1 checksum. This proves a working retrieval sample, not that all 347 GB were downloaded or that peers will always remain available.

When your external drive is connected, install the free, open-source [Transmission](https://transmissionbt.com/download), open this torrent file, and choose a folder on that drive **before starting the download**. Select only the files you want if you do not need the whole snapshot. Transmission checks the torrent's piece hashes during download. Do not start it with the computer's internal disk selected. Allow additional drive space if you later unpack the downloaded archives.

The torrent info hash is `0ebccd3ed026006064e90e5287d330d7c3d48c5e`. The kit preserves the complete torrent metadata and its SHA256 in the manifest, so its original webpage is not needed. The Python downloader does not start torrent downloads. The 84 GB May 2020 snapshot offers a separate HTTPS recovery route listed in the index.

## Reconstructing DeepInfer

Its main source archive leaves submodules empty. The recovery manifest records 14 required dependency archives, some used in more than one folder. The downloader labels the plan incomplete and refuses to start the full restore until every required archive has a verified recovery location.

Once the complete set is available, unpack the main archive into a new folder on the external drive. Unpack each dependency archive separately and place the **contents inside its archive root folder** at the relative paths below. Do not substitute a newer revision or run `git submodule update` against the originals; that would depend on the live repositories. The main fork archive and each dependency archive have already been matched to their pinned Git trees. This preserves source files, not a prebuilt executable or a tested machine-specific development environment.

| Repository and pinned revision | Location inside the main DeepInfer folder |
| --- | --- |
| deepseek-ai/DeepEP `f6aa38fe06cd4a0489e7730365d4e0114970a2f3` | `vendor/DeepEP` |
| deepseek-ai/DeepEP-Ascend `3b25377d04b24fc6154698ded78a2bcb2c59afff` | `vendor/DeepEP-Ascend` |
| deepseek-ai/DeepGEMM `1fc9c66975ee322d628b3288534ca0e9ce12a64d` | `vendor/DeepGEMM` |
| deepseek-ai/DeepGEMM-Ascend `3a35326271b069b8b5bf1a754435acd6cc91575b` | `vendor/DeepGEMM-Ascend` |
| deepseek-ai/DeepSelect `bfa4507d935f17ebfc3d0f00ff7d3c9a4d0e5c18` | `vendor/DeepSelect` |
| deepseek-ai/FlashMLA `2e5429fc5653bab6e081f09477126f731882a6a9` | `vendor/FlashMLA` |
| deepseek-ai/DeepJIT `cba802df081985141eeee36803685775c183a047` | `vendor/DeepEP/third-party/deep_jit` |
| deepseek-ai/clangd-ascend `f407eca30e07e647ce2e556f9b08e145b65362c7` | `vendor/DeepEP-Ascend/third-party/clangd-ascend`, `vendor/DeepGEMM-Ascend/third-party/clangd-ascend` |
| deepseek-ai/DeepJIT `65f513952b8771408a19202f65e36398522db6db` | `vendor/DeepEP-Ascend/third-party/deep_jit`, `vendor/DeepGEMM-Ascend/third-party/deep-jit` |
| NVIDIA/cutlass `f3fde58372d33e9a5650ba7b80fc48b3b49d40c8` | `vendor/DeepGEMM/third-party/cutlass` |
| deepseek-ai/DeepJIT `2efdab421e1cfb17fe8bc20e11ca72aa6d0e6c43` | `vendor/DeepGEMM/third-party/deep_jit` |
| Neargye/magic_enum `b233b96e49d371bad00300f59b5ba581100b8745` | `vendor/DeepGEMM-Ascend/third-party/magic_enum` |
| NVIDIA/cutlass `ae6bccf341fb4410241f696ba06873023d5ce4ed` | `vendor/DeepSelect/csrc/3rdparty/cutlass` |
| NVIDIA/cutlass `4faf1a1568cf1e4ad8ff71846a13e16f2a6a6f6b` | `vendor/FlashMLA/csrc/3rdparty/cutlass` |
