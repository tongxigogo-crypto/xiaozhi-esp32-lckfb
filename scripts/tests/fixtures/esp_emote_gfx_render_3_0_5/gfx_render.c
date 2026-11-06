/*
 * SPDX-FileCopyrightText: 2025-2026 Espressif Systems (Shanghai) CO LTD
 *
 * SPDX-License-Identifier: Apache-2.0
 */

void gfx_render_draw_child_objects(gfx_disp_t *disp, const gfx_draw_ctx_t *ctx)
{
    if (disp == NULL || disp->child_list == NULL || ctx == NULL) {
        return;
    }

    gfx_obj_child_t *child_node = disp->child_list;

    while (child_node != NULL) {
        gfx_obj_t *obj = (gfx_obj_t *)child_node->src;

        if (!obj->state.is_visible) {
            child_node = child_node->next;
            continue;
        }

        if (obj->vfunc.draw) {
            obj->vfunc.draw(obj, ctx);
        }

        child_node = child_node->next;
    }
}
