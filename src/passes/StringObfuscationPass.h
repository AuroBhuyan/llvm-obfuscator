#pragma once
#include <llvm/IR/Module.h>
#include <llvm/Pass.h>

// This is a Module pass — strings are globals, not per-function
struct StringObfuscationPass : public llvm::ModulePass {
    static char ID;
    StringObfuscationPass() : ModulePass(ID) {}
    bool runOnModule(llvm::Module &M) override;
};

llvm::ModulePass* createStringObfuscationPass();