/* Host regression tests exercise the actual firmware source with hardware stubs. */
#include <assert.h>
#include <stdio.h>
#include "../../src/pointing/pinchwing_dpi.c"

#if CONFIG_SHIELD_PINCHWING_DONGLE_RIGHT
static ssize_t read_result = sizeof(uint16_t);

static ssize_t read_setting(void *arg, void *value, size_t len) {
    if (read_result > 0) {
        memcpy(value, arg, len < (size_t)read_result ? len : (size_t)read_result);
    }
    return read_result;
}

static int load_cpi(uint16_t *cpi) {
    return registered_settings_set("cpi", sizeof(*cpi), read_setting, cpi);
}

static void reboot_right(void) {
    current_cpi = saved_cpi = 1600;
    confirmed = false;
    ready = false;
    driver_result = 0;
    writes = reports = applied_cpi = 0;
    save_work.schedules = announce_work.schedules = 0;
    dpi_init();
}

static void test_persistence(void) {
    reboot_right();
    assert(save_calls == 0);
    ready = true;
    announce(NULL);
    save_dpi(NULL);
    assert(applied_cpi == 1600 && save_calls == 0); /* No startup flash writes. */

    assert(pinchwing_dpi_adjust(true) == 0);
    assert(save_work.delay == 1000 && save_work.schedules == 1);
    assert(pinchwing_dpi_adjust(true) == 0);
    assert(save_work.delay == 1000 && save_work.schedules == 2);
    assert(save_calls == 0); /* Rapid changes reschedule a single deferred save. */
    save_dpi(NULL);
    assert(save_calls == 1 && flash_cpi == 2000);
    save_dpi(NULL);
    announce(NULL);
    assert(save_calls == 1); /* Heartbeats/duplicate work don't wear flash. */

    reboot_right();
    assert(load_cpi(&flash_cpi) == 0);
    assert(current_cpi == 2000 && !confirmed && writes == 0);
    announce(NULL);
    assert(reports == 0 && writes == 0);
    ready = true;
    driver_result = -EBUSY;
    announce(NULL);
    assert(!confirmed && reports == 0 && current_cpi == 2000);
    driver_result = 0;
    announce(NULL);
    assert(confirmed && applied_cpi == 2000 && last_report.data.input_event.value == 2000);
    assert(save_work.schedules == 0 && save_calls == 1);

    driver_result = -EIO;
    assert(pinchwing_dpi_adjust(true) == -EIO);
    assert(current_cpi == 2000 && save_work.schedules == 0);
    save_dpi(NULL);
    assert(flash_cpi == 2000 && save_calls == 1);
    driver_result = 0;
    assert(pinchwing_dpi_adjust(true) == 0);
    assert(pinchwing_dpi_adjust(false) == 0);
    save_dpi(NULL);
    assert(save_calls == 1); /* Returning to the saved value needs no write. */

    assert(pinchwing_dpi_adjust(false) == 0);
    save_result = -EIO;
    int previous_schedules = save_work.schedules;
    save_dpi(NULL);
    assert(saved_cpi == 2000 && flash_cpi == 2000 && current_cpi == 1800);
    assert(save_work.schedules == previous_schedules + 1 && save_work.delay == 1000);
    save_result = 0;
    save_dpi(NULL);
    assert(flash_cpi == 1800 && saved_cpi == 1800 && save_calls == 3);

    /* Every invalid record leaves the startup default intact. */
    reboot_right();
    uint16_t invalid[] = {0, 199, 201, 3400, UINT16_MAX};
    for (unsigned int i = 0; i < sizeof(invalid) / sizeof(invalid[0]); i++) {
        assert(load_cpi(&invalid[i]) == -EINVAL);
    }
    assert(registered_settings_set("cpi", 1, read_setting, &flash_cpi) == -EINVAL);
    assert(registered_settings_set("cpi", 0, read_setting, &flash_cpi) == -EINVAL);
    assert(registered_settings_set("cpi", 4, read_setting, &flash_cpi) == -EINVAL);
    assert(registered_settings_set("cpi/other", 2, read_setting, &flash_cpi) == -ENOENT);
    assert(registered_settings_set("other", 2, read_setting, &flash_cpi) == -ENOENT);
    read_result = -EIO;
    assert(load_cpi(&flash_cpi) == -EIO);
    read_result = 0;
    assert(load_cpi(&flash_cpi) == -EINVAL);
    read_result = 1;
    assert(load_cpi(&flash_cpi) == -EINVAL);
    read_result = sizeof(uint16_t);
    assert(current_cpi == 1600 && saved_cpi == 1600 && !confirmed);
    ready = true;
    announce(NULL);
    assert(applied_cpi == 1600);

    /* A late settings load must replace an already-confirmed startup default. */
    assert(load_cpi(&flash_cpi) == 0 && !confirmed);
    announce(NULL);
    assert(applied_cpi == 1800);
    uint16_t limits[] = {200, 3200};
    for (unsigned int i = 0; i < sizeof(limits) / sizeof(limits[0]); i++) {
        assert(load_cpi(&limits[i]) == 0);
        announce(NULL);
        assert(applied_cpi == limits[i]);
        previous_schedules = save_work.schedules;
        assert(pinchwing_dpi_adjust(i == 1) == 0);
        assert(save_work.schedules == previous_schedules);
    }
    puts("PASS: deferred saves, reboot restore, startup retries, flash failures and invalid settings");
}
#endif

int main(void) {
#if CONFIG_SHIELD_PINCHWING_DONGLE_RIGHT
    dpi_init();
    assert(scheduled_delay == 2000);
    ready = false;
    announce(NULL);
    assert(reports == 0 && writes == 0);
    ready = true;
    driver_result = -EBUSY; /* Device ready, but asynchronous sensor init is not. */
    announce(NULL);
    assert(reports == 0 && !confirmed);
    driver_result = 0;
    announce(NULL);
    assert(applied_cpi == 1600 && last_report.data.input_event.value == 1600);
    assert(last_report.type == ZMK_SPLIT_TRANSPORT_PERIPHERAL_EVENT_TYPE_INPUT_EVENT);
    assert(last_report.data.input_event.reg == 0);
    assert(last_report.data.input_event.type == INPUT_EV_MSC);
    assert(last_report.data.input_event.code == PINCHWING_INPUT_MSC_DPI);
    assert(!last_report.data.input_event.sync); /* Must not flush a mouse frame. */
    int previous_writes = writes;
    transport_result = -ENOTCONN;
    announce(NULL);
    transport_result = 0;
    announce(NULL);
    assert(writes == previous_writes && scheduled_delay == 2000);
    assert(pinchwing_dpi_adjust(true) == 0 && scheduled_delay == 0);
    announce(NULL);
    assert(applied_cpi == 1800 && last_report.data.input_event.value == 1800);
    driver_result = -EIO;
    assert(pinchwing_dpi_adjust(true) == -EIO);
    announce(NULL);
    assert(current_cpi == 1800 && last_report.data.input_event.value == 1800);
    driver_result = 0;
    for (int i = 0; i < 20; i++) assert(pinchwing_dpi_adjust(false) == 0);
    assert(current_cpi == 200);
    previous_writes = writes;
    assert(pinchwing_dpi_adjust(false) == 0 && writes == previous_writes);
    for (int i = 0; i < 20; i++) assert(pinchwing_dpi_adjust(true) == 0);
    assert(current_cpi == 3200);
    previous_writes = writes;
    assert(pinchwing_dpi_adjust(true) == 0 && writes == previous_writes);
    puts("PASS: sensor readiness, failures, limits, report isolation and reconnect retries");
    test_persistence();
#else
    assert(pinchwing_dpi_get() == 0);
    struct input_event event = {.type = INPUT_EV_MSC, .code = PINCHWING_INPUT_MSC_DPI,
                                .value = 3200};
    now = 100;
    receive_dpi(&event, NULL);
    assert(pinchwing_dpi_get() == 3200);
    now = 5099;
    assert(pinchwing_dpi_get() == 3200);
    now = 5100;
    assert(pinchwing_dpi_get() == 0);
    int invalid[] = {-200, 0, 199, 201, 3400};
    for (unsigned int i = 0; i < sizeof(invalid) / sizeof(invalid[0]); i++) {
        event.value = invalid[i];
        receive_dpi(&event, NULL);
        assert(pinchwing_dpi_get() == 0);
    }
    event.value = 1600;
    event.type = INPUT_EV_REL;
    receive_dpi(&event, NULL);
    assert(pinchwing_dpi_get() == 0); /* Optical movement is not DPI telemetry. */
    event.type = INPUT_EV_MSC;
    event.code++;
    receive_dpi(&event, NULL);
    assert(pinchwing_dpi_get() == 0);
    event.code = PINCHWING_INPUT_MSC_DPI;
    receive_dpi(&event, NULL);
    assert(pinchwing_dpi_get() == 1600); /* Right-half reboot/reconnect. */
    now = UINT32_MAX - 1000;
    receive_dpi(&event, NULL);
    now += 4999;
    assert(pinchwing_dpi_get() == 1600);
    now++;
    assert(pinchwing_dpi_get() == 0);
    puts("PASS: unknown/stale values, validation, reboot reports and timer wraparound");
#endif
    return 0;
}
