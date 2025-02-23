#include <raylib.h>
#include <raymath.h>
#define Rectangle WindowsRectangle
#define CloseWindow WindowsCloseWindow
#define ShowCursor WindowsShowCursor
#include <windows.h>
#undef Rectangle
#undef CloseWindow
#undef ShowCursor
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <process.h>

// Window interface
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
    HMODULE dllHandle; // To track which DLL this window came from
    char dllPath[260]; // Store DLL path for reloading
};

// Event types
enum { EVENT_MOUSE_CLICK = 1 };

// Message structure
typedef struct {
    int targetId;
    int senderId;
    char message[256];
} Message;

typedef struct {
    char entries[10][260];
    int count;
    int capacity;
} MessageQueue;

// Global state
static Camera2D camera;
static Window **windows = NULL;
static int windowCount = 0;
static int windowCapacity = 0;
static int nextWindowId = 0;
static Message *messageQueue = NULL;
static int messageCount = 0;
static int messageCapacity = 0;
static HANDLE reloadMutex;
static MessageQueue reloadQueue = {0}; // Simple queue for DLL paths to reload

// Persistent memory per window (fixed size: 1KB)
#define PERSISTENT_MEMORY_SIZE 1024

// Function declarations
void addWindow(Window *window);
void removeWindow(int index);
void sendMessage(int targetId, int senderId, const char *message);
void processMessages(void);
void reloadDll(const char *dllPath);

// Directory monitoring thread
static unsigned __stdcall directoryMonitorThread(void *arg) {
    char *dllDir = (char *)arg;
    HANDLE dirHandle = CreateFile(dllDir, FILE_LIST_DIRECTORY,
                                  FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                                  NULL, OPEN_EXISTING, FILE_FLAG_BACKUP_SEMANTICS, NULL);
    if (dirHandle == INVALID_HANDLE_VALUE) return 1;

    char buffer[1024];
    DWORD bytesReturned;
    FILE_NOTIFY_INFORMATION *fni;

    while (true) {
        if (!ReadDirectoryChangesW(dirHandle, buffer, sizeof(buffer), FALSE,
                                   FILE_NOTIFY_CHANGE_LAST_WRITE, &bytesReturned,
                                   NULL, NULL)) {
            break;
        }

        fni = (FILE_NOTIFY_INFORMATION *)buffer;
        while (true) {
            wchar_t *fileName = fni->FileName;
            int len = fni->FileNameLength / sizeof(wchar_t);
            char dllPath[260];
            sprintf(dllPath, "%s\\", dllDir);
            int dirLen = strlen(dllPath);
            for (int i = 0; i < len && i < 259 - dirLen; i++) {
                dllPath[dirLen + i] = (char)fileName[i];
            }
            dllPath[dirLen + len] = '\0';

            if (strstr(dllPath, ".dll") != NULL) {
                WaitForSingleObject(reloadMutex, INFINITE);
                // Add to reload queue (simplified: assumes single entry for demo)
                strcpy(reloadQueue.entries[reloadQueue.count++], dllPath);
                ReleaseMutex(reloadMutex);
            }

            if (fni->NextEntryOffset == 0) break;
            fni = (FILE_NOTIFY_INFORMATION *)((char *)fni + fni->NextEntryOffset);
        }
    }
    CloseHandle(dirHandle);
    free(dllDir);
    return 0;
}

// Load a window from a DLL
Window *loadWindowFromDll(const char *dllPath, float x, float y) {
    HMODULE dll = LoadLibrary(dllPath);
    if (!dll) return NULL;

    typedef Window *(*CreateWindowFunc)(int id, void *persistentMemory);
    CreateWindowFunc createWindow = (CreateWindowFunc)GetProcAddress(dll, "createWindow");
    if (!createWindow) {
        FreeLibrary(dll);
        return NULL;
    }

    int id = nextWindowId++;
    void *persistentMemory = malloc(PERSISTENT_MEMORY_SIZE);
    if (!persistentMemory) {
        FreeLibrary(dll);
        return NULL;
    }
    Window *window = createWindow(id, persistentMemory);
    if (window) {
        window->x = x;
        window->y = y;
        window->width = 200;
        window->height = 200;
        window->dllHandle = dll;
        strcpy(window->dllPath, dllPath);
        addWindow(window);
    } else {
        free(persistentMemory);
        FreeLibrary(dll);
    }
    return window;
}

int
main(void) {
    SetConfigFlags(FLAG_MSAA_4X_HINT);

    // Initialize raylib
    InitWindow(1280, 720, "Infinite Canvas");
    SetWindowState(FLAG_WINDOW_RESIZABLE);
    MaximizeWindow();
    SetTargetFPS(144);

    // Initialize camera
    camera.target = (Vector2){0, 0};
    camera.offset = (Vector2){GetScreenWidth() / 2.0f, GetScreenHeight() / 2.0f};
    camera.rotation = 0.0f;
    camera.zoom = 1.0f;

    // Initialize reload mutex and queue
    reloadMutex = CreateMutex(NULL, FALSE, NULL);
    reloadQueue.capacity = 10;

    // Start directory monitoring thread
    char *dllDir = strdup("dlls"); // Directory containing DLLs
    HANDLE thread = (HANDLE)_beginthreadex(NULL, 0, directoryMonitorThread, dllDir, 0, NULL);

    // Load initial window (e.g., tixy.dll)
    loadWindowFromDll("dlls\\tixy.dll", 0, 0);

    while (!WindowShouldClose()) {
        // Camera controls: panning and zooming
        if (IsMouseButtonDown(MOUSE_BUTTON_LEFT)) {
            Vector2 delta = GetMouseDelta();
            delta = Vector2Scale(delta, -1.0f / camera.zoom);
            camera.target = Vector2Add(camera.target, delta);
        }
        float wheel = GetMouseWheelMove();
        if (wheel != 0) {
            Vector2 mouseWorld = GetScreenToWorld2D(GetMousePosition(), camera);
            camera.offset = GetMousePosition();
            camera.target = mouseWorld;
            camera.zoom += wheel * 0.25f;
            if (camera.zoom < 0.01f) camera.zoom = 0.01f;
            if (camera.zoom > 100.0f) camera.zoom = 100.0f;
        }

        // Handle mouse click events
        if (IsMouseButtonPressed(MOUSE_BUTTON_LEFT)) {
            Vector2 mouseWorld = GetScreenToWorld2D(GetMousePosition(), camera);
            for (int i = 0; i < windowCount; i++) {
                Window *w = windows[i];
                if (mouseWorld.x >= w->x && mouseWorld.x < w->x + w->width &&
                    mouseWorld.y >= w->y && mouseWorld.y < w->y + w->height) {
                    float localX = mouseWorld.x - w->x;
                    float localY = mouseWorld.y - w->y;
                    w->handleEvent(w, EVENT_MOUSE_CLICK, localX, localY);
                    break;
                }
            }
        }

        // Handle DLL reloads
        WaitForSingleObject(reloadMutex, INFINITE);
        for (int i = 0; i < reloadQueue.count; i++) {
            reloadDll(reloadQueue.entries[i]);
        }
        reloadQueue.count = 0;
        ReleaseMutex(reloadMutex);

        // Process messages
        processMessages();

        // Render
        BeginDrawing();
        ClearBackground(RAYWHITE);
        BeginMode2D(camera);
        for (int i = 0; i < windowCount; i++) {
            Window *w = windows[i];
            w->render(w, w->x, w->y, w->width, w->height);
        }
        EndMode2D();
        EndDrawing();
    }

    //HideWindow();
    ShowWindow(GetActiveWindow(), SW_HIDE);  // Hide using Windows API

    // Cleanup
    puts("cleanup");
    for (int i = 0; i < windowCount; i++) {
        puts("cleanup window");
        windows[i]->destroy(windows[i]);
        free(windows[i]->persistentMemory);
        FreeLibrary(windows[i]->dllHandle);
        free(windows[i]);
    }
    puts("free");
    free(windows);
    puts("free");
    free(messageQueue);
    puts("free");
    free(reloadQueue.entries);
    puts("close handle");
    CloseHandle(reloadMutex);
    puts("close handle");
    CloseHandle(thread);
    puts("close window");
    CloseWindow();
    puts("done");
    return 0;
}

void addWindow(Window *window) {
    if (windowCount >= windowCapacity) {
        windowCapacity = windowCapacity ? windowCapacity * 2 : 10;
        windows = realloc(windows, windowCapacity * sizeof(Window *));
    }
    windows[windowCount++] = window;
}

void removeWindow(int index) {
    if (index < 0 || index >= windowCount) return;
    memmove(&windows[index], &windows[index + 1], (windowCount - index - 1) * sizeof(Window *));
    windowCount--;
}

void sendMessage(int targetId, int senderId, const char *message) {
    if (messageCount >= messageCapacity) {
        messageCapacity = messageCapacity ? messageCapacity * 2 : 10;
        messageQueue = realloc(messageQueue, messageCapacity * sizeof(Message));
    }
    Message *m = &messageQueue[messageCount++];
    m->targetId = targetId;
    m->senderId = senderId;
    strncpy(m->message, message, 255);
    m->message[255] = '\0';
}

void processMessages(void) {
    for (int i = 0; i < messageCount; i++) {
        Message *m = &messageQueue[i];
        for (int j = 0; j < windowCount; j++) {
            if (windows[j]->id == m->targetId) {
                windows[j]->handleMessage(windows[j], m->senderId, m->message);
                break;
            }
        }
    }
    messageCount = 0;
}

void reloadDll(const char *dllPath) {
    for (int i = 0; i < windowCount; ) {
        Window *w = windows[i];
        if (strcmp(w->dllPath, dllPath) == 0) {
            int id = w->id;
            void *persistentMemory = w->persistentMemory;
            float x = w->x, y = w->y;
            w->destroy(w);
            FreeLibrary(w->dllHandle);
            free(w);
            removeWindow(i);

            HMODULE newDll = LoadLibrary(dllPath);
            if (newDll) {
                typedef Window *(*CreateWindowFunc)(int id, void *persistentMemory);
                CreateWindowFunc createWindow = (CreateWindowFunc)GetProcAddress(newDll, "createWindow");
                if (createWindow) {
                    Window *newWindow = createWindow(id, persistentMemory);
                    if (newWindow) {
                        newWindow->x = x;
                        newWindow->y = y;
                        newWindow->width = 200;
                        newWindow->height = 200;
                        newWindow->dllHandle = newDll;
                        strcpy(newWindow->dllPath, dllPath);
                        addWindow(newWindow);
                    } else {
                        FreeLibrary(newDll);
                    }
                } else {
                    FreeLibrary(newDll);
                }
            }
        } else {
            i++;
        }
    }
}
