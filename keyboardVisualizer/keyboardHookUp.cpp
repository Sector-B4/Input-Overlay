#include <iostream>
#include <windows.h>

// Global hook handle to keep track of our Windows injection hook
HHOOK hKeyboardHook = NULL;

// Low-level keyboard hook callback procedure
LRESULT CALLBACK KeyboardHookProc(int nCode, WPARAM wParam, LPARAM lParam) {
    // nCode >= 0 means there is a valid input event to process
    if (nCode >= 0) {
        // Cast the lParam pointer to read the raw virtual key code structure
        KBDLLHOOKSTRUCT* pKeyStruct = (KBDLLHOOKSTRUCT*)lParam;
        
        int vkCode = pKeyStruct->vkCode;
        int state = 0; // 0 = Key Release (WM_KEYUP / WM_SYSKEYUP)

        // Identify if the event is a key down action (normal or system Alt-combinations)
        if (wParam == WM_KEYDOWN || wParam == WM_SYSKEYDOWN) {
            state = 1; // 1 = Key Press
        }

        // Print the token token string straight to stderr for Python to instantly catch
        // Format: K_[Virtual_Key_Code]_[State] (e.g., K_87_1 for 'W' Key Down)
        std::cerr << "K_" << vkCode << "_" << state << std::endl;
    }
    
    // Always pass the event chain to the next running application hook in Windows
    return CallNextHookEx(hKeyboardHook, nCode, wParam, lParam);
}

int main() {
    // Set Windows hook to intercept global low-level keyboard events (WH_KEYBOARD_LL)
    hKeyboardHook = SetWindowsHookEx(WH_KEYBOARD_LL, KeyboardHookProc, NULL, 0);
    
    if (hKeyboardHook == NULL) {
        std::cout << "[Error] Failed to install low-level Win32 keyboard hook." << std::endl;
        return 1;
    }

    // Standard Win32 Message Loop to keep this background thread alive and capturing
    MSG msg;
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    // Clean up hook resources on close exit
    UnhookWindowsHookEx(hKeyboardHook);
    return 0;
}