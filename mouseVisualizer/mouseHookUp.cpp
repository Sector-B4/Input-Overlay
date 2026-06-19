#include <windows.h>
#include <iostream>

HHOOK g_hMouseHook = NULL;

LRESULT CALLBACK LowLevelMouseProc(int nCode, WPARAM wParam, LPARAM lParam) {
    if (nCode >= 0) {
        MSLLHOOKSTRUCT* pMouseStruct = (MSLLHOOKSTRUCT*)lParam;
        if (pMouseStruct != nullptr) {
            switch (wParam) {
                case WM_LBUTTONDOWN:
                    std::cerr << "M_L_1\n"; fflush(stderr);
                    break;
                case WM_LBUTTONUP:
                    std::cerr << "M_L_0\n"; fflush(stderr);
                    break;
                case WM_RBUTTONDOWN:
                    std::cerr << "M_R_1\n"; fflush(stderr);
                    break;
                case WM_RBUTTONUP:
                    std::cerr << "M_R_0\n"; fflush(stderr);
                    break;
                case WM_MBUTTONDOWN:
                    std::cerr << "M_M_1\n"; fflush(stderr);
                    break;
                case WM_MBUTTONUP:
                    std::cerr << "M_M_0\n"; fflush(stderr);
                    break;
                case WM_MOUSEWHEEL: {
                    short wheelDelta = HIWORD(pMouseStruct->mouseData);
                    if (wheelDelta > 0) {
                        std::cerr << "M_W_UP\n"; fflush(stderr);
                    } else if (wheelDelta < 0) {
                        std::cerr << "M_W_DOWN\n"; fflush(stderr);
                    }
                    break;
                }
            }
        }
    }
    return CallNextHookEx(g_hMouseHook, nCode, wParam, lParam);
}

int main() {
    // Force standard streams to turn off internal caching completely
    std::setvbuf(stdout, NULL, _IONBF, 0);
    std::setvbuf(stderr, NULL, _IONBF, 0);

    g_hMouseHook = SetWindowsHookEx(WH_MOUSE_LL, LowLevelMouseProc, GetModuleHandle(NULL), 0);
    if (!g_hMouseHook) return 1;

    MSG msg;
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    UnhookWindowsHookEx(g_hMouseHook);
    return 0;
}