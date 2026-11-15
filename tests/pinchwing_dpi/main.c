/* Host regression tests exercise the actual firmware source with hardware stubs. */
#include <assert.h>
#include <stdio.h>
#include "../../src/pointing/pinchwing_dpi.c"

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
