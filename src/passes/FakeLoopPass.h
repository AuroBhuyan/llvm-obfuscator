#pragma once
#include <llvm/IR/Function.h>
#include <llvm/Pass.h>

struct FakeLoopPass : public llvm::FunctionPass {
    static char ID;
    FakeLoopPass() : FunctionPass(ID) {}
    bool runOnFunction(llvm::Function &F) override;
};

llvm::FunctionPass* createFakeLoopPass();