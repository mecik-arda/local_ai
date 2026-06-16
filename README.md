# local_ai

CyberPUF and LLM Model Local Management System.
This project serves as the main CLI and orchestration layer for managing CyberPUF and CyberPUF_LLM modules.

## Key Security Features (New Modules Integrated)
This orchestration layer dynamically toggles and configures the advanced security architectures implemented in the `CyberPUF_LLM` submodule.

1. **Hardware Attestation (TPM 2.0 & TEE Mock):**
   - Automatically validates host hardware integrity using TEE (Trusted Execution Environment) Docker enclaves (under `tee_docker/`) and simulated TPM 2.0 quotes prior to loading sensitive models.
2. **Post-Quantum Cryptography (PQC ML-KEM/Kyber):**
   - Implements hybrid quantum-resistant key encapsulation. Intercepts key derivation using Rust-based mock ML-KEM routines.
3. **Anti-Debugging & Watchdog Protection:**
   - Spawns background anti-debug tracers using Linux `ptrace` and `TracerPid` scanning. Terminates and zeroizes immediately if unauthorized hooks or debuggers (gdb, strace) are attached.
4. **Active WebSocket Telemetry:**
   - Transmits real-time security events, decrypted chunks status, and system logs to the Web Dashboard using secured channels.
5. **Layer-by-Layer Paging:**
   - Prevents dumping the entire model from memory. Cryptographic weights are sliced into custom paging chunks, decrypting only the active neural layers into memory on demand.

---

## Features Added Recently
- **TEE Docker Enclave:** Added a mock Trusted Execution Environment (Gramine/Intel SGX sim) structure under the `tee_docker/` directory for secure LLM deployment.
- **Hugging Face On-The-Fly Encryption:** You can now use the `/hf-indir <repo_id>` command in the CLI to download and encrypt models on the fly, directly outputting secure `.cpuf_llm` files.
- **FUSE & RAM-Disk Options:** Model loading strategies (FUSE Streaming vs Full RAM-Disk Extraction) are now dynamically managed via the `config.json` configuration file on a per-model basis.
- **Dynamic CLI Settings Toggles:** Settings menu expanded (options 1-12) to allow switching all 5 new security mechanisms directly from the terminal interface.

---

## Getting Started
Ensure you have the required Python environments (`ai_env`, `cpuf_env`) set up.

### Running the CLI Manager:
```bash
python3 local_ai.py
```

### Accessing Settings Menu:
Launch the CLI and type `/ayarlar` to configure:
- Hardware Attestation [ON/OFF]
- PQC / Post-Quantum Cryptography [ON/OFF]
- Anti-Debugging Tracers [ON/OFF]
- WebSocket Dashboard Telemetry [ON/OFF]
- Layer-by-Layer Paging [ON/OFF]
- Device selection (AUTO/CPU/GPU)

---

## 🚀 CyberPUF LLM Edition
This project integrates the advanced **CyberPUF LLM Edition**. If you are looking specifically for the LLM encryption wrapper, RAM-disk security module, and the hardware PUF simulated workflows for Large Language Models, you can find the complete source code and documentation inside the `CyberPUF_LLM` submodule.

To explore the LLM edition, navigate to:
[CyberPUF-LLM-Edition Repository](https://github.com/mecik-arda/CyberPUF-LLM-Edition)
