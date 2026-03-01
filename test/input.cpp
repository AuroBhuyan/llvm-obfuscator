#include <stdio.h>
#include <string.h>

int secret_key = 42;

int compute(int a, int b) {
    if (a > b) {
        return a * b + secret_key;
    } else {
        return a + b - secret_key;
    }
}

int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

int main() {
    printf("compute(10, 5)  = %d\n", compute(10, 5));
    printf("compute(3, 9)   = %d\n", compute(3, 9));
    printf("factorial(6)    = %d\n", factorial(6));
    printf("Secret key      = %d\n", secret_key);
    return 0;
}
