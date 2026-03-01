#pragma once
#include <cstdint>

struct ObfuscationConfig {
    uint32_t bogusCFLevel   = 0;
    uint32_t stringObfLevel = 0;
    uint32_t fakeLoopsLevel = 0;
    uint32_t cycles         = 1;

    static ObfuscationConfig& get() {
        static ObfuscationConfig instance;
        return instance;
    }

private:
    ObfuscationConfig() = default;
};