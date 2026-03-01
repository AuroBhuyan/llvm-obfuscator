#include <cstdint>
#include <cstdlib>
#include <string>
#include <iostream>

#include <llvm/IR/LLVMContext.h>
#include <llvm/IR/Module.h>
#include <llvm/IR/Verifier.h>
#include <llvm/IRReader/IRReader.h>
#include <llvm/IR/LegacyPassManager.h>
#include <llvm/Support/SourceMgr.h>
#include <llvm/Support/raw_ostream.h>
#include <llvm/Support/FileSystem.h>

#include "ObfuscationConfig.h"
#include "passes/BogusControlFlowPass.h"
#include "passes/StringObfuscationPass.h"
#include "passes/FakeLoopPass.h"
#include "utils/ReportGenerator.h"

using namespace llvm;

// -------------------------------------------------------
// Print usage
// -------------------------------------------------------
static void printUsage(const char* prog) {
    errs() << "\nUsage: " << prog
           << " <input.ll> <bogusCF 0-5> <stringObf 0-3>"
              " <fakeLoops 0-5> [cycles=1]\n";
    errs() << "Example: ./" << prog
           << " input.ll 3 1 2 1\n\n";
}

// -------------------------------------------------------
// main
// -------------------------------------------------------
int main(int argc, char** argv) {

    if (argc < 5) {
        printUsage(argv[0]);
        return 1;
    }

    // ---- Parse arguments ----
    const std::string filename = argv[1];
    uint32_t bogusCF   = static_cast<uint32_t>(std::stoul(argv[2]));
    uint32_t stringObf = static_cast<uint32_t>(std::stoul(argv[3]));
    uint32_t fakeLoops = static_cast<uint32_t>(std::stoul(argv[4]));
    uint32_t cycles    = (argc > 5) ? static_cast<uint32_t>(std::stoul(argv[5])) : 1;

    // ---- Validate ranges ----
    auto validateRange = [](uint32_t val, uint32_t maxVal, const char* name) {
        if (val > maxVal) {
            errs() << "[Config] Invalid value for " << name
                   << ": " << val << " (max " << maxVal << ")\n";
            std::exit(1);
        }
    };
    validateRange(bogusCF,   5, "bogusCF");
    validateRange(stringObf, 3, "stringObf");
    validateRange(fakeLoops, 5, "fakeLoops");
    validateRange(cycles,   10, "cycles");

    // ---- Populate config ----
    auto &cfg = ObfuscationConfig::get();
    cfg.bogusCFLevel   = bogusCF;
    cfg.stringObfLevel = stringObf;
    cfg.fakeLoopsLevel = fakeLoops;
    cfg.cycles         = cycles;

    outs() << "\n=== Obfuscation Configuration ===\n";
    outs() << "  Input file       : " << filename        << "\n";
    outs() << "  Bogus CF Level   : " << cfg.bogusCFLevel   << "\n";
    outs() << "  String Obf Level : " << cfg.stringObfLevel << "\n";
    outs() << "  Fake Loops Level : " << cfg.fakeLoopsLevel << "\n";
    outs() << "  Cycles           : " << cfg.cycles         << "\n";
    outs() << "=================================\n\n";

    // ---- Load LLVM IR ----
    LLVMContext Context;
    SMDiagnostic ParseErr;
    std::unique_ptr<Module> M = parseIRFile(filename, ParseErr, Context);
    if (!M) {
        ParseErr.print(argv[0], errs());
        return 1;
    }

    outs() << "[Phase1] IR loaded: " << filename << "\n";

    // ---- Print initial stats ----
    {
        size_t funcCount = 0, bbCount = 0, instCount = 0;
        for (const auto &F : *M) {
            if (F.isDeclaration()) continue;
            funcCount++;
            for (const auto &BB : F) {
                bbCount++;
                instCount += BB.size();
            }
        }
        outs() << "[Phase1] Functions   : " << funcCount << "\n";
        outs() << "[Phase1] BasicBlocks : " << bbCount   << "\n";
        outs() << "[Phase1] Instructions: " << instCount << "\n\n";
    }

    // ---- Run String Obfuscation (Module Pass) first ----
    if (cfg.stringObfLevel > 0) {
        outs() << "[Phase5] Running String Obfuscation...\n";
        legacy::PassManager MPM;
        MPM.add(createStringObfuscationPass());
        MPM.run(*M);
    }

    // ---- Run Function Passes (Bogus CF + Fake Loops) per cycle ----
    if (cfg.bogusCFLevel > 0 || cfg.fakeLoopsLevel > 0) {
        legacy::FunctionPassManager FPM(M.get());

        if (cfg.bogusCFLevel   > 0) FPM.add(createBogusControlFlowPass());
        if (cfg.fakeLoopsLevel > 0) FPM.add(createFakeLoopPass());

        FPM.doInitialization();
        for (uint32_t cycle = 0; cycle < cfg.cycles; cycle++) {
            outs() << "\n=== Obfuscation Cycle " << (cycle + 1)
                   << " / " << cfg.cycles << " ===\n";
            for (auto &F : *M)
                if (!F.isDeclaration())
                    FPM.run(F);
        }
        FPM.doFinalization();
    }

    // ---- Verify final module ----
    {
        std::string verifyErr;
        raw_string_ostream verifyOS(verifyErr);
        if (verifyModule(*M, &verifyOS)) {
            errs() << "\n[Verify] Module verification FAILED:\n"
                   << verifyErr << "\n";
            return 1;
        }
        outs() << "\n[Verify] Module is valid.\n";
    }

    // ---- Print post-obfuscation stats ----
    {
        size_t funcCount = 0, bbCount = 0, instCount = 0;
        for (const auto &F : *M) {
            if (F.isDeclaration()) continue;
            funcCount++;
            for (const auto &BB : F) {
                bbCount++;
                instCount += BB.size();
            }
        }
        outs() << "[Stats] Post-obfuscation:\n";
        outs() << "  Functions   : " << funcCount << "\n";
        outs() << "  BasicBlocks : " << bbCount   << "\n";
        outs() << "  Instructions: " << instCount << "\n\n";
    }

    // ---- Write obfuscated IR ----
    {
        std::error_code EC;
        raw_fd_ostream outFile("obf.ll", EC, sys::fs::OF_Text);
        if (EC) {
            errs() << "[Output] Cannot write obf.ll: " << EC.message() << "\n";
            return 1;
        }
        M->print(outFile, nullptr);
        outs() << "[Output] Obfuscated IR written to: obf.ll\n";
    }

    // ---- Generate report ----
    generateReport(M.get(), "report.txt");

    outs() << "\n=== Obfuscation Complete ===\n";
    return 0;
}