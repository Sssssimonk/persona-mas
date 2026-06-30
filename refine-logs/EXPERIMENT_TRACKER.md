# Experiment Tracker

| Run ID | Milestone | Purpose | System / Variant | Split | Metrics | Priority | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| R001 | M0 | prompt/parser unit tests | official-CoT GPQA parser | synthetic + saved samples | parse success, final answer extraction | MUST | TODO | Include reasoning and final answer |
| R002 | M0 | C1 protocol repair | GPQA C1 prompt includes choices | synthetic | no letter-response mismatch in prompt | MUST | TODO | `Changed` computed by code |
| R003 | M1 | GPQA sanity | base + 3 single personas + voting + C0 + C1 | GPQA n20 | accuracy, invalid rate, C0/C1 gain | MUST | TODO | `max_new_tokens=1024` |
| R004 | M2 | Deception L1 sanity | base + 3 single personas + C0 + C1 | L1-self n20 | deception/honest/refusal/unclear | MUST | TODO | JSON reasoning/response |
| R005 | M3 | Abstention official-natural sanity | base + 3 single personas + C0 + C1 | n50 multi-subdataset | abstention acc, over/under abstention | MUST | TODO | no forced ANSWER/ABSTAIN |
| R006 | M4 | GPQA main | base + single personas + voting + C0 + C1 | GPQA Diamond 198 | accuracy, oracle upper bound | MUST | TODO | official-CoT |
| R007 | M4 | Deception main | base + single personas + C0 + C1 | L1-self n100 | deception/honest/refusal | MUST | TODO | judge response only |
| R008 | M4 | Abstention main | base + single personas + C0 + C1 | n100 or n200 | abstention metrics | MUST | TODO | official-natural |
| R009 | M5 | base ensemble control | base ensemble C0 | GPQA + Deception | same as main | MUST before paper | TODO | Controls multi-agent/synthesis effect |
| R010 | M5 | homogeneous control | homogeneous mathematical/goodness/remorse C0 | Deception L1 n100 | deception/honest/refusal | MUST before paper | TODO | Tests heterogeneity necessity |
| R011 | M5 | prompt-only control | base + persona prompt C0 | Deception L1 n100 | deception/honest/refusal | MUST before paper | TODO | Tests parameter vs role prompt |
| R012 | M6 | pressure stress test | base + C0 + C1 | L2-self-pressure n50 | deception/honest/refusal | NICE | TODO | Do after L1 result is interpretable |
| R013 | M6 | reward stress test | base + C0 + C1 | L2-self-reward n50 | deception/honest/refusal | NICE | TODO | Do after pressure |
