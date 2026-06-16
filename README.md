# local_ai

CyberPUF and LLM Model Local Management System.
This project serves as the main CLI and orchestration layer for managing CyberPUF and CyberPUF_LLM modules.

## Features Added Recently
- **TEE Docker Enclave:** Added a mock Trusted Execution Environment (Gramine/Intel SGX sim) structure under the `tee_docker/` directory for secure LLM deployment.
- **Hugging Face On-The-Fly Encryption:** You can now use the `/hf-indir <repo_id>` command in the CLI to download and encrypt models on the fly, directly outputting secure `.cpuf_llm` files.
- **FUSE & RAM-Disk Options:** Model loading strategies (FUSE Streaming vs Full RAM-Disk Extraction) are now dynamically managed via the `config.json` configuration file on a per-model basis.

## Getting Started
Ensure you have the required Python environments (`ai_env`, `cpuf_env`) set up. 

Run the CLI:
```bash
python3 local_ai.py
```

## 🚀 CyberPUF LLM Edition
This project integrates the advanced **CyberPUF LLM Edition**. If you are looking specifically for the LLM encryption wrapper, RAM-disk security module, and the hardware PUF simulated workflows for Large Language Models, you can find the complete source code and documentation inside the `CyberPUF_LLM` submodule.

To explore the LLM edition, navigate to:
[CyberPUF-LLM-Edition Repository](https://github.com/mecik-arda/CyberPUF-LLM-Edition)
