#include "mos/core/kernel.hpp"
#include "mos/core/cognitive_state.hpp"
#include "mos/translation/knowledge_base.hpp"
#include "mos/translation/colibri_kernel.hpp"
#include <iostream>
#include <string>
#include <vector>
#include <memory>
#define NOMINMAX
#include <Windows.h>
#include <io.h>
#include <fcntl.h>
#include <cstdint>

using namespace mos;

uint32_t compute_crc32(const uint8_t* buf, size_t len) {
    uint32_t crc = 0xFFFFFFFF;
    for (size_t i = 0; i < len; i++) {
        crc ^= buf[i];
        for (int j = 0; j < 8; j++) {
            crc = (crc >> 1) ^ (0xEDB88320 & (-(crc & 1)));
        }
    }
    return ~crc;
}

void set_color(int color_code) {
    SetConsoleTextAttribute(GetStdHandle(STD_OUTPUT_HANDLE), color_code);
}

void run_ipc_server() {
    // Force stdin to binary mode to prevent Windows newline corruption
    _setmode(_fileno(stdin), _O_BINARY);
    
    // Initialize OS Kernel dependencies
    auto kb = std::make_shared<translation::KnowledgeBase>("mos_brain_ipc.db");
    mos::translation::ColibriKernel::ColibriConfig config;
    config.host = "api.groq.com";
    config.port = 443;
    config.model_name = "llama-3.1-8b-instant";
    auto llm = std::make_shared<mos::translation::ColibriKernel>(config);
    
    core::CognitiveState state;

    // E7. The assembly record is the one artefact the registry calls impossible
    // to recover later, so where it lands must not depend on the caller's
    // working directory. communicator.py sets MOS_ASSEMBLY_LOG to the same path
    // assembly_log.py reads; an empty value is the explicit opt-out.
    core::KernelConfig kernel_config;
    if (const char* log_path = std::getenv("MOS_ASSEMBLY_LOG")) {
        kernel_config.assembly_log_path = log_path;
    }
    std::cerr << "[C++ Engine] E7 assembly log: "
              << (kernel_config.assembly_log_path.empty()
                      ? std::string("DISABLED")
                      : kernel_config.assembly_log_path)
              << "\n";

    core::OSKernel kernel(state, kernel_config);
    kernel.set_knowledge_base(kb);
    kernel.set_llm(llm);

    set_color(11);
    std::cerr << "[C++ Engine] IPC Server listening on standard input...\n";
    set_color(15);

    while (true) {
        uint32_t size = 0;
        uint32_t expected_crc = 0;
        if (!std::cin.read(reinterpret_cast<char*>(&size), sizeof(size))) break;
        if (!std::cin.read(reinterpret_cast<char*>(&expected_crc), sizeof(expected_crc))) break;

        if (size == 0 || size > 1024 * 1024 * 10) {
            std::cerr << "[C++ Engine] Invalid payload size: " << size << "\n";
            continue;
        }

        std::vector<uint8_t> buffer(size);
        if (!std::cin.read(reinterpret_cast<char*>(buffer.data()), size)) {
            break; // Stream failed
        }

        uint32_t actual_crc = compute_crc32(buffer.data(), size);
        if (actual_crc != expected_crc) {
            std::cerr << "[C++ Engine] CRC32 mismatch (expected " << expected_crc << ", got " << actual_crc << "). Dropping corrupt payload.\n";
            continue;
        }

        std::cerr << "[C++ Engine] Received FlatBuffer payload (" << size << " bytes, valid CRC32).\n";
        kernel.execute_dag(buffer.data(), size);
    }
}

int main(int argc, char** argv) {
    SetConsoleOutputCP(CP_UTF8);

    if (argc > 1 && std::string(argv[1]) == "--ipc-server") {
        run_ipc_server();
        return 0;
    }

    set_color(11);
    std::cout << "TATIANA C++ Engine. Run Python Communicator or use --ipc-server.\n";
    set_color(15);
    return 0;
}
