#pragma once
#include <llvm/IR/Function.h>
#include <llvm/Pass.h>

struct BogusControlFlowPass : public llvm::FunctionPass {
    static char ID;
    BogusControlFlowPass() : FunctionPass(ID) {}
    bool runOnFunction(llvm::Function &F) override;
};

llvm::FunctionPass* createBogusControlFlowPass();