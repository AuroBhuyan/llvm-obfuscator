#include "StringObfuscationPass.h"
#include "../ObfuscationConfig.h"

#include <llvm/IR/Module.h>
#include <llvm/IR/GlobalVariable.h>
#include <llvm/IR/Constants.h>
#include <llvm/IR/Type.h>
#include <llvm/Pass.h>
#include <llvm/Support/raw_ostream.h>
#include <vector>
#include <string>

using namespace llvm;

// -------------------------------------------------------
// StringObfuscationPass::runOnModule
//
// Iterates all global variables, finds ConstantDataArray
// string literals, XOR-encodes them in-place.
//
// NOTE: This intentionally breaks runtime string usage
// unless you also insert a decode stub. For the purposes
// of this project (IR obfuscation / static analysis
// resistance) encoding is the goal.
// -------------------------------------------------------
bool StringObfuscationPass::runOnModule(Module &M) {
    uint32_t level = ObfuscationConfig::get().stringObfLevel;
    if (level == 0)
        return false;

    LLVMContext &Ctx = M.getContext();
    bool modified = false;
    uint32_t count = 0;

    for (GlobalVariable &GV : M.globals()) {
        // Must be a constant with an initializer
        if (!GV.isConstant() || !GV.hasInitializer())
            continue;

        auto *CDA = dyn_cast<ConstantDataArray>(GV.getInitializer());
        if (!CDA || !CDA->isString())
            continue;

        StringRef orig = CDA->getAsString(); // includes null terminator
        if (orig.empty())
            continue;

        const char key = 0x55; // XOR key
        std::vector<uint8_t> enc(orig.size());
        for (size_t i = 0; i < orig.size(); i++)
            enc[i] = static_cast<uint8_t>(orig[i]) ^ static_cast<uint8_t>(key);

        // Build replacement constant
        Constant *NewInit = ConstantDataArray::get(
            Ctx, ArrayRef<uint8_t>(enc.data(), enc.size()));

        GV.setInitializer(NewInit);
        GV.setConstant(true);

        count++;
        modified = true;
        outs() << "[StringObf] Encoded global: " << GV.getName() << "\n";

        if (count >= level * 10) // limit scope by level
            break;
    }

    outs() << "[StringObf] Total strings encoded: " << count << "\n";
    return modified;
}

char StringObfuscationPass::ID = 0;

static RegisterPass<StringObfuscationPass> X_StringObf(
    "stringObf", "Phase5 String Obfuscation Pass", false, false
);

llvm::ModulePass* createStringObfuscationPass() {
    return new StringObfuscationPass();
}