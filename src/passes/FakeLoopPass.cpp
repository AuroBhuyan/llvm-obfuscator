#include "FakeLoopPass.h"
#include "../ObfuscationConfig.h"

#include <llvm/IR/Function.h>
#include <llvm/IR/BasicBlock.h>
#include <llvm/IR/Instructions.h>
#include <llvm/IR/InstrTypes.h>
#include <llvm/IR/Constants.h>
#include <llvm/IR/Type.h>
#include <llvm/Pass.h>
#include <llvm/Support/raw_ostream.h>

using namespace llvm;

// -------------------------------------------------------
// FakeLoopPass::runOnFunction
// Inserts harmless junk arithmetic at the top of each
// function to inflate IR size and confuse decompilers.
// Uses raw instruction constructors (not IRBuilder) to
// guarantee typed-pointer IR compatible with LLVM 14.
// -------------------------------------------------------
bool FakeLoopPass::runOnFunction(Function &F) {
    uint32_t level = ObfuscationConfig::get().fakeLoopsLevel;
    if (level == 0 || F.isDeclaration() || F.empty())
        return false;

    LLVMContext &Ctx = F.getContext();
    uint32_t inserted = 0;

    // Insert point: first non-alloca, non-PHI instruction in entry block
    BasicBlock &EntryBB = F.getEntryBlock();
    Instruction *InsertPt = &*EntryBB.getFirstInsertionPt();
    if (!InsertPt)
        return false;

    Type *I32Ty = Type::getInt32Ty(Ctx);

    while (inserted < level) {
        // ── Create alloca in the entry block ──
        // Explicitly use typed pointer (i32*) — required for LLVM 14.
        // We insert the alloca at the very start of the entry block so it
        // dominates all uses, then do the store/load right after.
        AllocaInst *Tmp = new AllocaInst(
            I32Ty,          // element type
            0,              // address space 0
            nullptr,        // array size (nullptr = 1 element)
            "junk_alloca",
            // Insert at the very first position of the entry block
            &*F.getEntryBlock().getFirstInsertionPt()
        );

        // Store a constant into the alloca
        Value *JunkVal = ConstantInt::get(I32Ty, 0x1337 + inserted);
        new StoreInst(JunkVal, Tmp, InsertPt);

        // Load it back (explicit element type = i32, ptr = Tmp)
        LoadInst *Loaded = new LoadInst(I32Ty, Tmp, "junk_load", InsertPt);

        // Harmless arithmetic — inflates IR without changing semantics
        BinaryOperator *Added = BinaryOperator::CreateAdd(
            Loaded,
            ConstantInt::get(I32Ty, inserted + 7),
            "junk_add", InsertPt);
        BinaryOperator *Xored = BinaryOperator::CreateXor(
            Added,
            ConstantInt::get(I32Ty, 0xDEAD),
            "junk_xor", InsertPt);

        // Store result back so it isn't trivially dead
        new StoreInst(Xored, Tmp, InsertPt);

        inserted++;
        outs() << "[FakeLoop] Inserted junk block #" << inserted
               << " in function: " << F.getName() << "\n";
    }

    return inserted > 0;
}

char FakeLoopPass::ID = 0;

static RegisterPass<FakeLoopPass> X_FakeLoop(
    "fakeLoop", "Phase6 Fake Loop & Junk Logic Pass", false, false
);

llvm::FunctionPass* createFakeLoopPass() {
    return new FakeLoopPass();
}