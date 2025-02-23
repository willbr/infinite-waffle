#include <raylib.h>
#define Rectangle WindowsRectangle
#define CloseWindow WindowsCloseWindow
#define ShowCursor WindowsShowCursor
#include <windows.h>
#undef Rectangle
#undef CloseWindow
#undef ShowCursor

// Window interface (must match main.c)
typedef struct Window Window;

typedef void (*RenderFunc)(Window *window, float x, float y, float width, float height);
typedef void (*EventFunc)(Window *window, int type, float x, float y);
typedef void (*MessageFunc)(Window *window, int senderId, const char *message);
typedef void (*DestroyFunc)(Window *window);

struct Window {
    int id;
    void *persistentMemory;
    RenderFunc render;
    EventFunc handleEvent;
    MessageFunc handleMessage;
    DestroyFunc destroy;
    float x, y, width, height;
    void *dllHandle; // Not used here
    char dllPath[260]; // Not used here
};

// Persistent data for tixy window
typedef struct {
    Color color;
} TixyWindowData;

void render(Window *window, float x, float y, float width, float height) {
    TixyWindowData *data = (TixyWindowData *)window->persistentMemory;
    DrawRectangle(x, y, width, height, data->color);
}

void handleEvent(Window *window, int type, float x, float y) {
    // Example: Change color on click
    if (type == 1) { // EVENT_MOUSE_CLICK
        TixyWindowData *data = (TixyWindowData *)window->persistentMemory;
        data->color = (Color){rand() % 256, rand() % 256, rand() % 256, 255};
    }
}

void handleMessage(Window *window, int senderId, const char *message) {
    // Not implemented for simplicity
}

void destroy(Window *window) {
    // No additional cleanup needed; persistentMemory is managed by main app
}

// DLL export
__declspec(dllexport) Window *createWindow(int id, void *persistentMemory) {
    Window *window = malloc(sizeof(Window));
    if (!window) return NULL;

    TixyWindowData *data = (TixyWindowData *)persistentMemory;
    if (data->color.r == 0 && data->color.g == 0 && data->color.b == 0 && data->color.a == 0) {
        data->color = RED; // Initialize color if unset
    }

    window->id = id;
    window->persistentMemory = persistentMemory;
    window->render = render;
    window->handleEvent = handleEvent;
    window->handleMessage = handleMessage;
    window->destroy = destroy;
    return window;
}

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpvReserved) {
    return TRUE;
}
