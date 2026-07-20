# Task79 Local Validation

Status: **PASS_COMPLETE_WITH_RECORDED_PROVIDER_MISSINGNESS**

- Checks passed: `14/14`
- New external judgments pending: `0/1200`

| Check | Pass | Detail |
|---|---:|---|
| preflight_status | yes | `"PASS"` |
| preflight_device | yes | `"AMD Radeon RX 9070 XT"` |
| fixed_weight_hash | yes | `[{"bytes": 2235829648, "path": "model.safetensors", "sha256": "a33a153b2493bff6be06af6921e69de9c0d0bb6ff06fe5bbb68670ba8d980ae2"}]` |
| segment_audit_status | yes | `"PASS"` |
| segment_content_not_truncated | yes | `{"dropped": 0, "max_content_tokens": 511}` |
| formal_compression_complete | yes | `{"rows": 600, "status": "COMPLETE"}` |
| compression_structure | yes | `{"empty_outputs": 0, "order_failures": 0}` |
| fixed_sample_and_answers | yes | `{"answers": 1200, "counts": {"dense_llmlingua2_matched_sent_mmr": 300, "dense_sent_mmr_r0.85_l0.70": 300, "intentroute_llmlingua2_matched_sent_mmr_seed19": 300, "intentweight_sent_mmr_r0.85_l0.70_seed19": 300}, "sample_rows": 300}` |
| judgment_keys_unique | yes | `{"unique": 3593, "valid": 3593}` |
| deepseek_complete | yes | `{"deepseek-v4-flash": 1200, "glm-5.2": 1200, "minimax-m3": 1193}` |
| execution_manifest_matches | yes | `"COMPLETE_TASK79_NEW_ENDPOINT_JUDGING_WITH_RECORDED_LEGACY_MISSINGNESS"` |
| external_handoff_complete | yes | `{"expected_responses": 1200, "requests": 600}` |
| external_gap_explicit | yes | `{"analysis_status": "COMPLETE_PRIMARY_THREE_JUDGE_WITH_RECORDED_LEGACY_MISSINGNESS", "external_pending": 0, "new_external_coverage": {"glm-5.2": 600, "minimax-m3": 600}}` |
| rocm_environment_lock | yes | `{"actual_lock": "059c40cce6bdf037bf81f3d83d2ec5be8eaec796dc891aa67ee82b3a2bfdc316", "recorded_lock": "059c40cce6bdf037bf81f3d83d2ec5be8eaec796dc891aa67ee82b3a2bfdc316"}` |
