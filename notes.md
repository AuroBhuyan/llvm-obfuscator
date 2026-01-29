# 🧱 LLVM Obfuscator — Phase 0 (WSL)

## **Tracking / Contract Document**

Below is a **clean compilation of Phase 0**, split into **two parts**, so **future phases can reference it without re-reading setup steps**.

> No hand-waving. No redundancy.

---

## **Consolidated Phase Record**

---

## PART 1️⃣ — High-level explanation

### 🎯 Objective of Phase 0

Phase 0 exists to **eliminate environment uncertainty**.

Before touching LLVM IR, passes, or obfuscation logic, we must guarantee that:

* The compiler pipeline works
* LLVM headers & libraries are usable
* We can build **LLVM-linked C++ tools**
* Our build system is reproducible

> Phase 0 **does not implement obfuscation**.
> It only proves that the **toolchain contract is satisfied**.

---

### 🧠 Why WSL (Linux Subsystem)

We chose **WSL + Ubuntu 22.04 LTS** instead of:

* Native Windows (higher friction with LLVM)
* Dual boot (risk + operational overhead)

WSL provides:

* Real Linux ABI
* Native `clang`, `llvm-config`, `opt`
* Zero disk risk
* Seamless VS Code integration

Crucially:

> **Anything built in WSL behaves the same as native Linux**, so later phases remain valid.

---

### 🔩 What Phase 0 established

#### 1. A real Linux execution environment

* Linux filesystem
* Linux linker
* Linux package manager
* Linux LLVM toolchain

> No emulation. No fake layers.

---

#### 2. A verified LLVM frontend

We explicitly proved that:

* `clang` can emit LLVM IR
* The IR is readable and correct
* The frontend → IR stage works end-to-end

This is foundational for **IR-level obfuscation**.

---

#### 3. A C++ program that links against LLVM

This is the **most important proof** in Phase 0.

We confirmed:

* LLVM headers are discoverable
* LLVM libraries link correctly
* Namespaces (`llvm::`) resolve
* The binary runs successfully

> Without this, **writing LLVM passes is impossible**.

---

#### 4. A reproducible build system (CMake)

CMake is configured to:

* Discover LLVM via `LLVMConfig.cmake`
* Pull correct include paths
* Link required LLVM components

This guarantees:

* Deterministic builds
* Easy extension in later phases
* No hardcoded hacks

---

#### 5. A minimal CLI contract (`--help`)

A basic `--help` option was added to:

* Establish a command-line interface pattern
* Prepare for future flags (`--input`, `--passes`, etc.)
* Lock in a **tool-style architecture**

This avoids refactors later.

---

### ✅ Why Phase 0 is complete

Phase 0 is done because all of the following are **provably true**:

* Can we generate LLVM IR? → **YES**
* Can we include LLVM headers in C++? → **YES**
* Can we link LLVM libraries? → **YES**
* Can we build via CMake? → **YES**
* Can we run a Linux LLVM tool from VS Code? → **YES**

> Nothing else belongs in Phase 0.

---

## PART 2️⃣ — Technical environment & tools

> **Canonical reference for all future phases**

---

### 🖥️ Host System

* **Host OS**: Windows
* **Linux layer**: WSL 2
* **Linux distro**: Ubuntu **22.04 LTS (Jammy)**

---

### 🧩 Editor & Integration

* **VS Code**: Windows installation
* **Extension**: Remote – WSL
* **Execution model**:

  * UI on Windows
  * Compiler, linker, filesystem on Linux

---

### 🔧 Toolchain Versions (locked)

| Tool         | Version         | Notes                            |
| ------------ | --------------- | -------------------------------- |
| Ubuntu       | 22.04 LTS       | Supported until 2027             |
| LLVM         | 17.x            | Installed via LLVM official repo |
| Clang        | 17.x            | LLVM frontend                    |
| llvm-config  | 17.x            | Used by CMake                    |
| CMake        | ≥ 3.15          | Required for LLVMConfig          |
| GCC / linker | build-essential | Used indirectly                  |
| Shell        | bash            | Default WSL shell                |

---

### 📦 LLVM installation source

* **Repository**: `apt.llvm.org`
* **Reasoning**:

  * Ubuntu repo ships LLVM 14 only
  * LLVM 17 aligns with modern APIs
  * Reduces API drift in later phases

---

### 📁 Project layout (baseline — frozen)

```
llvm-obfuscator/
├── src/
│   └── main.cpp
├── build/
└── CMakeLists.txt
```

> This structure will be **extended**, never replaced.

---

### 🧪 Verified capabilities

* `clang-17 -emit-llvm` → works
* `llvm-config-17` → works
* CMake locates LLVM via `LLVM_DIR`
* Binary links against LLVM `support` component
* Executable runs inside WSL
* `--help` CLI path works

---

### 📜 Phase 0 Output Artifact

* **Binary**: `obfuscator`
* **Behavior**:

  * Runs successfully
  * Prints help text
  * Proves LLVM linkage

> This binary is the **handoff artifact** to Phase 1.

---

## 🔒 Phase Boundary (Non‑negotiable)

Phase 0 guarantees:

> **“We can now safely write LLVM‑dependent logic without debugging the environment.”**

Anything involving:

* IR parsing
* Modules
* Passes
* Transformations

❌ **Does not belong to Phase 0**
✅ **Begins in Phase 1**

---

## ⏭️ Next Phase

**Phase 1 — IR‑level foundations**

* Load IR
* Walk `Module` / `Function` / `BasicBlock`
* Print, inspect, and minimally modify IR (no obfuscation yet)

Trigger phrase:

> **“Phase 1 — start with reading IR”**
LLVM IR hierarchy:

Module
 └── Function
      └── BasicBlock
           └── Instruction
