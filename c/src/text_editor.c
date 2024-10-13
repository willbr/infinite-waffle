#include "raylib.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

// Maximum number of lines and line length
#define MAX_LINES 1000
#define MAX_LINE_LENGTH 1024

typedef struct {
    char* lines[MAX_LINES];
    int lineCount;
    int cursorX;
    int cursorY;
} TextBuffer;

// Function to initialize the text buffer
void InitTextBuffer(TextBuffer* tb) {
    tb->lineCount = 1;
    tb->lines[0] = (char*)malloc(MAX_LINE_LENGTH);
    tb->lines[0][0] = '\0';
    tb->cursorX = 0;
    tb->cursorY = 0;
}

// Function to free the text buffer
void FreeTextBuffer(TextBuffer* tb) {
    for(int i = 0; i < tb->lineCount; i++) {
        free(tb->lines[i]);
    }
}

// Function to insert a character at the cursor position
void InsertChar(TextBuffer* tb, char c) {
    char* line = tb->lines[tb->cursorY];
    int len = (int)strlen(line);
    if(len >= MAX_LINE_LENGTH - 1) return; // Prevent overflow

    // Shift characters to the right
    for(int i = len; i >= tb->cursorX; i--) {
        line[i+1] = line[i];
    }
    line[tb->cursorX] = c;
    tb->cursorX++;
}

// Function to handle backspace
void Backspace(TextBuffer* tb) {
    if(tb->cursorX > 0) {
        char* line = tb->lines[tb->cursorY];
        int len = (int)strlen(line);
        for(int i = tb->cursorX - 1; i < len; i++) {
            line[i] = line[i+1];
        }
        tb->cursorX--;
    }
    else if(tb->cursorY > 0) {
        // Merge with previous line
        int prevLen = (int)strlen(tb->lines[tb->cursorY - 1]);
        if(tb->lineCount < MAX_LINES) {
            strcat(tb->lines[tb->cursorY - 1], tb->lines[tb->cursorY]);
            free(tb->lines[tb->cursorY]);
            for(int i = tb->cursorY; i < tb->lineCount -1; i++) {
                tb->lines[i] = tb->lines[i+1];
            }
            tb->lineCount--;
            tb->cursorY--;
            tb->cursorX = prevLen;
        }
    }
}

// Function to insert a new line
void InsertNewLine(TextBuffer* tb) {
    if(tb->lineCount >= MAX_LINES) return;

    // Create a new line
    tb->lines[tb->lineCount] = (char*)malloc(MAX_LINE_LENGTH);
    tb->lines[tb->lineCount][0] = '\0';

    // Split the current line
    char* current = tb->lines[tb->cursorY];
    strcpy(tb->lines[tb->lineCount], current + tb->cursorX);
    current[tb->cursorX] = '\0';

    tb->lineCount++;
    tb->cursorY++;
    tb->cursorX = 0;
}

// Function to save the text buffer to a file
void SaveToFile(TextBuffer* tb, const char* filename) {
    FILE* fp = fopen(filename, "w");
    if(fp) {
        for(int i = 0; i < tb->lineCount; i++) {
            fprintf(fp, "%s\n", tb->lines[i]);
        }
        fclose(fp);
    }
    else {
        printf("Failed to save file.\n");
    }
}

// Function to load the text buffer from a file
void LoadFromFile(TextBuffer* tb, const char* filename) {
    FILE* fp = fopen(filename, "r");
    if(fp) {
        // Free existing lines
        for(int i = 0; i < tb->lineCount; i++) {
            free(tb->lines[i]);
        }

        tb->lineCount = 0;
        char buffer[MAX_LINE_LENGTH];
        while(fgets(buffer, sizeof(buffer), fp) && tb->lineCount < MAX_LINES) {
            // Remove newline characters
            buffer[strcspn(buffer, "\r\n")] = 0;
            tb->lines[tb->lineCount] = (char*)malloc(MAX_LINE_LENGTH);
            strcpy(tb->lines[tb->lineCount], buffer);
            tb->lineCount++;
        }
        fclose(fp);
        tb->cursorY = tb->cursorX = 0;
    }
    else {
        printf("Failed to load file.\n");
    }
}

int main(void)
{
    // Initialization
    const int screenWidth = 800;
    const int screenHeight = 600;

    InitWindow(screenWidth, screenHeight, "Basic Text Editor - raylib");

    // Initialize text buffer
    TextBuffer tb;
    InitTextBuffer(&tb);

    // Font settings
    int fontSize = 20;
    int lineHeight = fontSize + 4;
    int margin = 10;

    // Cursor blink settings
    float cursorTimer = 0.0f;
    bool cursorVisible = true;
    float blinkInterval = 0.5f;

    // Key repeat settings
    float keyRepeatDelay = 0.2f; // Delay in seconds for repeat
    float keyRepeatTimer = 0.0f;
    bool backspaceHeld = false;

    SetTargetFPS(144);

    while (!WindowShouldClose())
    {
        // Handle input within key repeat logic
        keyRepeatTimer += GetFrameTime();
        if (keyRepeatTimer >= keyRepeatDelay) {
            if(IsKeyDown(KEY_ENTER)) {
                InsertNewLine(&tb);
                keyRepeatTimer = 0.0f;
            }
            else if(IsKeyDown(KEY_BACKSPACE)) {
                Backspace(&tb);
                backspaceHeld = true;
                keyRepeatTimer = 0.0f; // Reset timer for backspace key
            }

            if(IsKeyDown(KEY_RIGHT)) {
                if(tb.cursorX < strlen(tb.lines[tb.cursorY])) {
                    tb.cursorX++;
                }
                else if(tb.cursorY < tb.lineCount -1) {
                    tb.cursorY++;
                    tb.cursorX = 0;
                }
                keyRepeatTimer = 0.0f;
            }
            if(IsKeyDown(KEY_LEFT)) {
                if(tb.cursorX > 0) {
                    tb.cursorX--;
                }
                else if(tb.cursorY > 0) {
                    tb.cursorY--;
                    tb.cursorX = (int)strlen(tb.lines[tb.cursorY]);
                }
                keyRepeatTimer = 0.0f;
            }
            if(IsKeyDown(KEY_DOWN)) {
                if(tb.cursorY < tb.lineCount -1) {
                    tb.cursorY++;
                    if(tb.cursorX > strlen(tb.lines[tb.cursorY]))
                        tb.cursorX = (int)strlen(tb.lines[tb.cursorY]);
                }
                keyRepeatTimer = 0.0f;
            }
            if(IsKeyDown(KEY_UP)) {
                if(tb.cursorY > 0) {
                    tb.cursorY--;
                    if(tb.cursorX > strlen(tb.lines[tb.cursorY]))
                        tb.cursorX = (int)strlen(tb.lines[tb.cursorY]);
                }
                keyRepeatTimer = 0.0f;
            }
        }

        if (IsKeyReleased(KEY_BACKSPACE)) {
            backspaceHeld = false;
        }

        // Handle character input with shift key support for capital letters and special characters
        int key = GetCharPressed();
        if(key >= 32 && key <= 126) { // Printable characters
            if(IsKeyDown(KEY_LEFT_SHIFT) || IsKeyDown(KEY_RIGHT_SHIFT)) {
                if(key >= 'a' && key <= 'z') {
                    key = toupper(key); // Convert to uppercase
                }
                else {
                    switch (key) {
                        case '1': key = '!'; break;
                        case '2': key = '@'; break;
                        case '3': key = '#'; break;
                        case '4': key = '$'; break;
                        case '5': key = '%'; break;
                        case '6': key = '^'; break;
                        case '7': key = '&'; break;
                        case '8': key = '*'; break;
                        case '9': key = '('; break;
                        case '0': key = ')'; break;
                        case '-': key = '_'; break;
                        case '=': key = '+'; break;
                        case '[': key = '{'; break;
                        case ']': key = '}'; break;
                        case ';': key = ':'; break;
                        case '\\': key = '|'; break;
                        case ',': key = '<'; break;
                        case '.': key = '>'; break;
                        case '/': key = '?'; break;
                        case '\'': key = '"'; break;
                    }
                }
            }
            InsertChar(&tb, (char)key);
        }

        // Handle save/load with shortcuts
        if(IsKeyDown(KEY_LEFT_CONTROL) || IsKeyDown(KEY_RIGHT_CONTROL)) {
            if(IsKeyPressed(KEY_S)) {
                SaveToFile(&tb, "output.txt");
            }
            if(IsKeyPressed(KEY_O)) {
                LoadFromFile(&tb, "output.txt");
            }
        }

        // Update cursor blink
        cursorTimer += GetFrameTime();
        if(cursorTimer >= blinkInterval) {
            cursorTimer = 0.0f;
            cursorVisible = !cursorVisible;
        }

        // Draw
        BeginDrawing();
            ClearBackground(RAYWHITE);

            // Draw text
            for(int i = 0; i < tb.lineCount; i++) {
                DrawText(tb.lines[i], margin, margin + i * lineHeight, fontSize, BLACK);
            }

            // Draw cursor
            if(cursorVisible) {
                // Calculate cursor position
                int cursorXPos = margin + MeasureText(tb.lines[tb.cursorY], fontSize) * (tb.cursorX);
                int cursorYPos = margin + tb.cursorY * lineHeight;

                // Adjust cursorXPos based on character width
                // To improve cursor placement accuracy
                if(tb.cursorX > 0) {
                    char temp = tb.lines[tb.cursorY][tb.cursorX];
                    char temp2 = tb.lines[tb.cursorY][tb.cursorX - 1];
                    tb.lines[tb.cursorY][tb.cursorX] = '\0';
                    cursorXPos = margin + MeasureText(tb.lines[tb.cursorY], fontSize);
                    tb.lines[tb.cursorY][tb.cursorX] = temp;
                }

                DrawLine(cursorXPos, cursorYPos, cursorXPos, cursorYPos + fontSize, BLACK);
            }

            // Instruction
            DrawText("CTRL+S to Save, CTRL+O to Load", margin, screenHeight - 30, 10, DARKGRAY);
        EndDrawing();
    }

    // De-Initialization
    FreeTextBuffer(&tb);
    CloseWindow();

    return 0;
}
