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


llvm::outs()<<"LLVM Status 1\n";
return 0;
}