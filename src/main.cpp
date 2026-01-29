#include <llvm/IR/LLVMContext.h>
#include <llvm/IR/Module.h>
#include <llvm/IR/Function.h>
#include <llvm/IR/BasicBlock.h>
#include <llvm/IR/Instruction.h>
#include <llvm/IRReader/IRReader.h>
#include <llvm/Support/SourceMgr.h>
#include <llvm/Support/raw_ostream.h>
#include <cstring>

int main(int argc, char** argv){
    if(argc!=2){
    llvm::errs()<<"Usage: Obfuscator <input.ll>\n";
    return 1;
    }

llvm::LLVMContext context;
llvm::SMDiagnostic error;
//Loading the IR file
auto module = llvm::parseIRFile(argv[1],error,context);
//Handling Invalid IR
if(!module){
    error.print("obfuscator",llvm::errs());
    return 1;
}
//Counters
size_t funcCount = 0;
size_t bbCount = 0;
size_t instCount = 0;

for(const llvm::Function& F : *module){
    if(F.isDeclaration()) continue;
    funcCount++;

    for(const llvm::BasicBlock& BB : F){
        bbCount++;

        for(const llvm::Instruction& I : BB){
            instCount++;
        }
    }
}

llvm::outs() << "Functions: " << funcCount << "\n";
llvm::outs() << "BasicBlocks: " << bbCount << "\n";
llvm::outs() << "Instructions: " << instCount << "\n";

return 0;
}