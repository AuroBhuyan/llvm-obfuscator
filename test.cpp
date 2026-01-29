#include <iostream>
using namespace std;

int sub(int a,int b){
    return b-a;
}

int add(int a,int b){
    return a+b;
}

int main(){
    int a = 5; int b = 12;
    cout<<"Subtraction Result:"<<sub(a,b)<<"\n";
    cout<<"Addition Result:"<<add(a,b)<<"\n";
}
