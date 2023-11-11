#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <zlib.h>

int main() {
    char buf[512];
    ssize_t bytes_read;
    memset(buf, 0, 512);
    bytes_read = read(STDIN_FILENO, buf, 2048);

    if(bytes_read == -1) {
        // Handle read error
        fprintf(stderr, "Error reading from stdin\n");
        return 1;
    } else if(bytes_read == 0) {
        // Handle EOF scenario, maybe not necessarily an error depending on context
        fprintf(stderr, "EOF or no data read from stdin\n");
        return 1;
    }

    // Remove newline character if read included it
    buf[strcspn(buf, "\n")] = 0;

    uLong crc = crc32(0L, Z_NULL, 0);
    crc = crc32(crc, (const unsigned char*)buf, strlen(buf));

    printf("%lX", crc); // Removed the newline character from the output

    return 0;
}