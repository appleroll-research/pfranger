# PromptForest Ranger

PromptForest Ranger (or **PFRanger**) is a CLI tool for auditing LLM prompts for injection attacks and jailbreaks. It leverages the PromptForest ensemble engine to scan datasets and generate comprehensive and accurate HTML reports, mitigating the problem of high-certainty false positives.

![PFRanger Report Preview](assets/report-preview.png)

## Intended Use Cases

We intend this tool to be a swiss army knife: it should be used for multiple situations regarding unsafe prompts. Here are some, but not all, of the ways to use PFRanger:

1.  **Processing Unsafe Datasets**
    Huge datasets may contain prompts that weaken a model, making it more vulnerable to jailbreak attempts. PFRanger can mitigate this issue before you feed it to your model.

2.  **Auditing Datasets**
    Feeding potentially dangerous datasets into AI model with highly privileged abilities may produce catastrophic results. PFRanger helps by giving you an overview of the dataset's security.

## Key Features

*   **Works Offline**: All data stays on your computer.
*   **Accurate and Reliable**: PFRanger utilises the PromptForest engine, which provides responses that are not only accurate, but also calibrated and reliable. PromptForest uses a strategically selected ensemble of small models using soft weighted model voting.
*   **Fast**: Startup latency of ~3s and an average request rate of 27 prompts/s on a consumer GPU with optimal parallelization.
*   **Informative**: Supports a large number of input and output file types. Also outputs a shareable HTML file to help you analyse the data.

## How it Works

PromptForest automatically handles all model downloading on first run. Downloading takes around 3GB disk space and around a minute to download on consumer network download speeds.
