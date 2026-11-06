/* Host-only SDK/log shim; upstream decoder remains byte-identical. */
#include <stdio.h>
#include <stdlib.h>
#include "gfx_eaf_dec.h"
#include "core/gfx_log.h"
bool gfx_log_should_output(gfx_log_module_t module, gfx_log_level_t level) { return false; }
void gfx_log_write(gfx_log_module_t module, gfx_log_level_t level, const char *tag, const char *format, ...) {}
int main(int argc, char **argv) {
    if (argc != 2) return 2;
    FILE *f = fopen(argv[1], "rb");
    if (!f) return 3;
    fseek(f, 0, SEEK_END); long length = ftell(f); rewind(f);
    if (length < 24) return 4;
    unsigned char *data = malloc(length);
    if (!data || fread(data, 1, length, f) != (size_t)length) return 5;
    fclose(f);
    eaf_dec_handle_t handle = NULL;
    if (eaf_dec_init(data, length, &handle) != ESP_OK) return 6;
    for (int i = 0; i < eaf_dec_get_total_frames(handle); ++i) {
        eaf_dec_header_t header = {0};
        if (eaf_dec_get_frame_info(handle, i, &header) != EAF_DEC_TYPE_VALID) return 7;
        uint32_t size = (uint32_t)header.width * header.height * 2;
        eaf_dec_free_header(&header);
        unsigned char *out = calloc(1, size);
        if (!out) return 8;
        if (eaf_dec_decode_frame(handle, i, out, size, false) != ESP_OK) return 9;
        if (fwrite(&size, sizeof(size), 1, stdout) != 1 || fwrite(out, 1, size, stdout) != size) return 10;
        free(out);
    }
    eaf_dec_deinit(handle);
    free(data);
    return 0;
}
