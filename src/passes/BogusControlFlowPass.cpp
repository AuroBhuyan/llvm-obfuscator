#include "BogusControlFlowPass.h"
#include "../ObfuscationConfig.h"

#include <llvm/IR/Function.h>
#include <llvm/IR/BasicBlock.h>
#include <llvm/IR/IRBuilder.h>
#include <llvm/IR/Instructions.h>
#include <llvm/IR/Verifier.h>
#include <llvm/IR/Constants.h>
#include <llvm/IR/Type.h>
#include <llvm/Pass.h>
#include <llvm/Support/raw_ostream.h>
#include <vector>

using namespace llvm;

// -------------------------------------------------------
// Helper: get a usable i32 value for opaque predicate
// Returns nullptr if none available
// -------------------------------------------------------
static Value* getUsableI32Value(Function &F, IRBuilder<> &Builder) {
    // Try function arguments first
    for (auto &Arg : F.args()) {
        if (Arg.getType()->isIntegerTy(32))
            return &Arg;
    }
    // Fallback: constant zero — always safe
    return ConstantInt::get(Type::getInt32Ty(F.getContext()), 0);
}

// -------------------------------------------------------
// BogusControlFlowPass::runOnFunction
// -------------------------------------------------------
bool BogusControlFlowPass::runOnFunction(Function &F) {
    uint32_t level = ObfuscationConfig::get().bogusCFLevel;
    if (level == 0 || F.isDeclaration() || F.empty())
        return false;

    LLVMContext &Ctx = F.getContext();
    bool modified = false;
    uint32_t inserted = 0;

    // Collect blocks to process upfront — avoid iterator invalidation
    std::vector<BasicBlock*> Blocks;
    for (auto &BB : F)
        Blocks.push_back(&BB);

    for (BasicBlock *BB : Blocks) {
        if (inserted >= level)
            break;

        // Need at least one non-terminator instruction to split safely
        Instruction *Term = BB->getTerminator();
        if (!Term)
            continue;

        // Skip exit blocks (return/unreachable — no successors)
        if (Term->getNumSuccessors() == 0)
            continue;

        // Find a safe split point: after the first non-PHI instruction
        Instruction *SplitPt = BB->getFirstNonPHI();
        if (!SplitPt || SplitPt == Term)
            continue;

        // ---- Build opaque predicate BEFORE splitting ----
        IRBuilder<> Builder(SplitPt);

        Value *Base = getUsableI32Value(F, Builder);
        // Opaque: (base + 10 - 10) == base  →  always true
        Value *Add  = Builder.CreateAdd(Base,
                        ConstantInt::get(Type::getInt32Ty(Ctx), 10),
                        "opq_add");
        Value *Sub  = Builder.CreateSub(Add,
                        ConstantInt::get(Type::getInt32Ty(Ctx), 10),
                        "opq_sub");
        Value *Cond = Builder.CreateICmpEQ(Sub, Base, "opq_cond");

        // ---- Split the block at SplitPt ----
        // BB            → code before SplitPt (now ends with unconditional br)
        // RealBlock     → SplitPt ... original terminator
        BasicBlock *RealBlock = BB->splitBasicBlock(SplitPt, "bogus_real");

        // Remove the auto-generated unconditional branch from BB
        BB->getTerminator()->eraseFromParent();

        // ---- Create fake dead block ----
        BasicBlock *FakeBlock = BasicBlock::Create(Ctx, "bogus_fake", &F);
        IRBuilder<> FakeB(FakeBlock);

        Type *RetTy = F.getReturnType();
        if (RetTy->isVoidTy()) {
            FakeB.CreateRetVoid();
        } else if (RetTy->isIntegerTy()) {
            FakeB.CreateRet(ConstantInt::get(RetTy, 0));
        } else if (RetTy->isPointerTy()) {
            FakeB.CreateRet(ConstantPointerNull::get(cast<PointerType>(RetTy)));
        } else {
            // Unsupported return type — abandon this block
            FakeBlock->eraseFromParent();
            // Re-attach BB to RealBlock
            IRBuilder<> Fix(BB);
            Fix.CreateBr(RealBlock);
            continue;
        }

        // ---- Insert conditional branch in BB ----
        IRBuilder<> TermB(BB);
        TermB.CreateCondBr(Cond, RealBlock, FakeBlock);

        modified = true;
        inserted++;

        outs() << "[BogusControlFlow] Inserted bogus branch #"
               << inserted << " in function: " << F.getName() << "\n";
    }

    if (modified) {
        std::string errStr;
        raw_string_ostream errOS(errStr);
        if (verifyFunction(F, &errOS)) {
            errs() << "[BogusControlFlow] WARNING: Function '"
                   << F.getName() << "' failed verification:\n"
                   << errStr << "\n";
        }
    }

    return modified;
}

char BogusControlFlowPass::ID = 0;

static RegisterPass<BogusControlFlowPass> X_Bogus(
    "bogusCF", "Phase4 Bogus Control Flow Pass", false, false
);

llvm::FunctionPass* createBogusControlFlowPass() {
    return new BogusControlFlowPass();
}