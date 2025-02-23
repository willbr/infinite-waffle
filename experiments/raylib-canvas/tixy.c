#include <raylib.h>
#define Rectangle WindowsRectangle
#define CloseWindow WindowsCloseWindow
#define ShowCursor WindowsShowCursor
#include <windows.h>
#undef Rectangle
#undef CloseWindow
#undef ShowCursor
#include <math.h>  // For sin and sqrt

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
    float time;  // Tracks animation time
} TixyWindowData;

void render(Window *window, float x, float y, float width, float height) {
    TixyWindowData *data = (TixyWindowData *)window->persistentMemory;
    data->time += GetFrameTime();  // Increment time based on frame delta

    // Grid settings: 16x16 to mimic tixy.land
    const int gridSize = 16;
    float cellWidth = width / gridSize;
    float cellHeight = height / gridSize;
    float radius = cellWidth / 2.0f - 1.0f;  // Slightly smaller than half cell width for spacing

    // Draw grid with circles
    for (int i = 0; i < gridSize; i++) {
        for (int j = 0; j < gridSize; j++) {
            // Map i, j to x, y coordinates (0 to 15 range, like tixy.land)
            float gridX = (float)i;
            float gridY = (float)j;

            // Calculate the formula: sin(t - sqrt((x - 7.5)^2 + (y - 6)^2))
            float distance = sqrtf(powf(gridX - 7.5f, 2) + powf(gridY - 6.0f, 2));
            float value = sinf(data->time - distance);

            // Map sin result (-1 to 1) to color intensity (0 to 255)
            unsigned char intensity = (unsigned char)((value + 1.0f) * 0.5f * 255.0f);  // 0 to 255

            // Draw a circle for each cell, centered in the grid position
            Color color = { intensity, intensity, intensity, 255 };  // Grayscale
            float centerX = x + i * cellWidth + cellWidth / 2.0f;
            float centerY = y + j * cellHeight + cellHeight / 2.0f;
            DrawCircle(centerX, centerY, radius, color);
        }
    }
}

void handleEvent(Window *window, int type, float x, float y) {
    // Example: Reset time on click (optional)
    if (type == 1) { // EVENT_MOUSE_CLICK
        TixyWindowData *data = (TixyWindowData *)window->persistentMemory;
        data->time = 0.0f;  // Reset animation
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
    data->time = 0.0f;  // Initialize time

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
