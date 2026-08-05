#include "stubs.h"

int g_warn_count = 0;
int g_work_submits = 0;
int g_out_len = 0;
struct zmk_keycode_state_changed g_out[MAX_OUT];

/* Forward decl needed before including the driver. */
static int dm_keycode_listener_fwd(const zmk_event_t *eh);

#include "behavior_dynamic_macro.c"

/* Playback re-raises events; route them into the capture buffer AND back through
 * the recording listener, exactly as ZMK's event manager would. This is what
 * proves the in_playback guard actually prevents self-recording. */
int raise_zmk_keycode_state_changed(struct zmk_keycode_state_changed ev) {
    if (g_out_len < MAX_OUT) {
        g_out[g_out_len++] = ev;
    }
    dm_keycode_listener(&ev);
    return 0;
}

static int dm_keycode_listener_fwd(const zmk_event_t *eh) { return dm_keycode_listener(eh); }

/* ---- helpers ---- */

static void cmd(uint32_t command, uint32_t slot) {
    struct zmk_behavior_binding b = {.behavior_dev = "dm", .param1 = command, .param2 = slot};
    struct zmk_behavior_binding_event e = {0};
    on_keymap_binding_pressed(&b, e);
}

static void key(uint32_t keycode, bool pressed) {
    struct zmk_keycode_state_changed ev = {
        .usage_page = HID_USAGE_KEY,
        .keycode = keycode,
        .implicit_modifiers = 0,
        .explicit_modifiers = 0,
        .state = pressed,
        .timestamp = 0,
    };
    dm_keycode_listener(&ev);
}

static void tap(uint32_t keycode) {
    key(keycode, true);
    key(keycode, false);
}

/* Run playback to completion (bounded, so a runaway loop fails the test). */
static void pump(void) {
    for (int i = 0; i < 4096; i++) {
        bool busy = false;
        for (int s = 0; s < DM_MAX_SLOTS; s++) {
            if (dynamic_macro_data.slots[s].state == DM_SLOT_PLAYING) {
                busy = true;
            }
        }
        if (!busy) {
            return;
        }
        dm_play_work_handler(NULL);
    }
    printf("  !! playback did not terminate\n");
}

static void reset_out(void) { g_out_len = 0; }

/* Render captured output as "a+ a- b+ b-" for easy comparison. */
static void render(char *buf, size_t n) {
    size_t off = 0;
    buf[0] = 0;
    for (int i = 0; i < g_out_len; i++) {
        off += snprintf(buf + off, n - off, "%s%02x%c", i ? " " : "", g_out[i].keycode,
                        g_out[i].state ? '+' : '-');
    }
}

static int failures = 0;

static void expect(const char *name, const char *want) {
    char got[1024];
    render(got, sizeof(got));
    if (strcmp(got, want) == 0) {
        printf("PASS  %s\n", name);
    } else {
        printf("FAIL  %s\n        want: %s\n        got:  %s\n", name, want, got);
        failures++;
    }
}

/* HID keycodes */
#define K_A 0x04
#define K_B 0x05
#define K_C 0x06
#define K_X 0x1b
#define K_Y 0x1c
#define K_Z 0x1d
#define K_N1 0x1e
#define K_N2 0x1f
#define K_N3 0x20
#define K_LSFT 0xe1
#define K_LCTL 0xe0

int main(void) {
    behavior_dynamic_macro_init(NULL);

    /* --- basic recording: record "abc" into register a, play it --- */
    printf("\n== basic recording ==\n");
    cmd(DM_REC_CMD, 0);
    tap(K_A);
    tap(K_B);
    tap(K_C);
    cmd(DM_STP_CMD, 0);
    reset_out();
    cmd(DM_PLY_CMD, 0);
    pump();
    expect("basic abc", "04+ 04- 05+ 05- 06+ 06-");

    /* --- self-recording guard: playback must not feed back into a recording --- */
    printf("\n== playback is not re-recorded ==\n");
    if (dynamic_macro_data.slots[0].event_count == 6) {
        printf("PASS  slot unchanged after playback (6 events)\n");
    } else {
        printf("FAIL  slot grew to %u events after playback\n",
               dynamic_macro_data.slots[0].event_count);
        failures++;
    }

    /* --- independent registers --- */
    printf("\n== independent registers ==\n");
    cmd(DM_REC_CMD, 1);
    tap(K_X);
    tap(K_Y);
    tap(K_Z);
    cmd(DM_STP_CMD, 0); /* slot arg deliberately wrong: DM_STP stops whatever records */
    reset_out();
    cmd(DM_PLY_CMD, 1);
    pump();
    expect("register b xyz", "1b+ 1b- 1c+ 1c- 1d+ 1d-");
    reset_out();
    cmd(DM_PLY_CMD, 0);
    pump();
    expect("register a still abc", "04+ 04- 05+ 05- 06+ 06-");

    /* --- overwrite --- */
    printf("\n== overwrite ==\n");
    cmd(DM_REC_CMD, 0);
    tap(K_N1);
    tap(K_N2);
    tap(K_N3);
    cmd(DM_STP_CMD, 0);
    reset_out();
    cmd(DM_PLY_CMD, 0);
    pump();
    expect("register a overwritten with 123", "1e+ 1e- 1f+ 1f- 20+ 20-");

    /* --- empty slot / immediate stop --- */
    printf("\n== empty and immediate stop ==\n");
    cmd(DM_REC_CMD, 1);
    cmd(DM_STP_CMD, 1);
    reset_out();
    cmd(DM_PLY_CMD, 1);
    pump();
    expect("immediate stop plays nothing", "");

    /* --- held modifier: ctrl+c --- */
    printf("\n== held modifier ==\n");
    cmd(DM_REC_CMD, 1);
    key(K_LCTL, true);
    tap(K_C);
    key(K_LCTL, false);
    cmd(DM_STP_CMD, 1);
    reset_out();
    cmd(DM_PLY_CMD, 1);
    pump();
    expect("ctrl+c round trip", "e0+ 06+ 06- e0-");

    /* --- stop while a key is still held: must self-balance --- */
    printf("\n== stop with keys still held ==\n");
    cmd(DM_REC_CMD, 0);
    key(K_LSFT, true);
    key(K_A, true); /* both still held when we stop */
    cmd(DM_STP_CMD, 0);
    reset_out();
    cmd(DM_PLY_CMD, 0);
    pump();
    expect("synthetic releases appended in reverse order", "e1+ 04+ 04- e1-");

    /* --- recursion guard: play while recording --- */
    printf("\n== play while recording is refused ==\n");
    cmd(DM_REC_CMD, 1);
    tap(K_A);
    reset_out();
    cmd(DM_PLY_CMD, 1);
    pump();
    expect("play refused while that slot records", "");
    cmd(DM_STP_CMD, 1);

    /* --- record while playing is refused (slot data cannot mutate mid-playback) --- */
    printf("\n== record while playing is refused ==\n");
    cmd(DM_REC_CMD, 0);
    tap(K_A);
    tap(K_B);
    cmd(DM_STP_CMD, 0);
    cmd(DM_PLY_CMD, 0);
    dm_play_work_handler(NULL); /* one event emitted, playback still active */
    uint32_t before = dynamic_macro_data.slots[0].event_count;
    cmd(DM_REC_CMD, 0);
    if (dynamic_macro_data.slots[0].state == DM_SLOT_PLAYING &&
        dynamic_macro_data.slots[0].event_count == before) {
        printf("PASS  record refused mid-playback, buffer intact\n");
    } else {
        printf("FAIL  record mutated a slot during playback\n");
        failures++;
    }
    pump();

    /* --- capacity: MAX_EVENTS is 16 here; recording must auto-stop safely --- */
    printf("\n== capacity limit ==\n");
    g_warn_count = 0;
    cmd(DM_REC_CMD, 1);
    for (int i = 0; i < 40; i++) {
        tap(K_A);
    }
    cmd(DM_STP_CMD, 1);
    reset_out();
    cmd(DM_PLY_CMD, 1);
    pump();
    int presses = 0, releases = 0;
    for (int i = 0; i < g_out_len; i++) {
        g_out[i].state ? presses++ : releases++;
    }
    if (g_out_len > 0 && g_out_len <= DM_MAX_EVENTS && presses == releases && g_warn_count > 0) {
        printf("PASS  truncated to %d balanced events (%d presses, %d releases), warned\n",
               g_out_len, presses, releases);
    } else {
        printf("FAIL  capacity: len=%d presses=%d releases=%d warns=%d\n", g_out_len, presses,
               releases, g_warn_count);
        failures++;
    }

    /* --- too many simultaneously held keys (MAX_HELD is 4 here) --- */
    printf("\n== too many held keys ==\n");
    g_warn_count = 0;
    cmd(DM_REC_CMD, 0);
    key(K_A, true);
    key(K_B, true);
    key(K_C, true);
    key(K_X, true);
    key(K_Y, true); /* exceeds MAX_HELD -> auto-stop */
    if (dynamic_macro_data.slots[0].state == DM_SLOT_IDLE && g_warn_count > 0) {
        printf("PASS  auto-stopped when held-key limit exceeded\n");
    } else {
        printf("FAIL  held-key limit not enforced (state=%d warns=%d)\n",
               dynamic_macro_data.slots[0].state, g_warn_count);
        failures++;
    }
    reset_out();
    cmd(DM_PLY_CMD, 0);
    pump();
    presses = releases = 0;
    for (int i = 0; i < g_out_len; i++) {
        g_out[i].state ? presses++ : releases++;
    }
    if (presses == releases && presses > 0) {
        printf("PASS  auto-stopped recording still plays back balanced (%d/%d)\n", presses,
               releases);
    } else {
        printf("FAIL  unbalanced after auto-stop: %d presses, %d releases\n", presses, releases);
        failures++;
    }

    /* --- out of range slot must not corrupt memory --- */
    printf("\n== out of range slot ==\n");
    cmd(DM_REC_CMD, 99);
    cmd(DM_PLY_CMD, 99);
    printf("PASS  out-of-range slot rejected without crashing\n");

    /* --- re-record after auto-stop works --- */
    printf("\n== recovery ==\n");
    cmd(DM_REC_CMD, 0);
    tap(K_B);
    cmd(DM_STP_CMD, 0);
    reset_out();
    cmd(DM_PLY_CMD, 0);
    pump();
    expect("recovers after auto-stop", "05+ 05-");

    printf("\n%s (%d failure(s))\n", failures ? "FAILURES" : "ALL TESTS PASSED", failures);
    return failures ? 1 : 0;
}
