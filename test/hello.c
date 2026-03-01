#include <stdio.h>

int add(int a, int b) {
    return a + b;
}

int main() {
    int x = add(3, 4);
    printf("Result: %d\n", x);
    printf("Hello from obfuscator test!\n");
    return 0;
}
