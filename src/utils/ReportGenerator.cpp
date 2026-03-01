#include "ReportGenerator.h"
#include <llvm/IR/Module.h>
#include <llvm/IR/Function.h>
#include <llvm/IR/BasicBlock.h>
#include <llvm/Support/raw_ostream.h>
#include <fstream>
#include <ctime>

using namespace llvm;

void generateReport(Module* M, const char* filename) {
    if (!M) return;

    size_t funcCount = 0;
    size_t bbCount   = 0;
    size_t instCount = 0;

    for (const auto &F : *M) {
        if (F.isDeclaration()) continue;
        funcCount++;
        for (const auto &BB : F) {
            bbCount++;
            instCount += BB.size();
        }
    }

    std::ofstream out(filename);
    if (!out.is_open()) {
        errs() << "[Report] Cannot open output file: " << filename << "\n";
        return;
    }

    // Timestamp
    std::time_t now = std::time(nullptr);
    char timebuf[64];
    std::strftime(timebuf, sizeof(timebuf), "%Y-%m-%d %H:%M:%S", std::localtime(&now));

    out << "=== LLVM Obfuscation Report ===\n";
    out << "Generated   : " << timebuf << "\n";
    out << "Module Name : " << M->getName().str() << "\n";
    out << "------------------------------\n";
    out << "Functions    : " << funcCount << "\n";
    out << "BasicBlocks  : " << bbCount   << "\n";
    out << "Instructions : " << instCount << "\n";
    out << "==============================\n";

    out.close();

    outs() << "[Report] Written to: " << filename << "\n";
}