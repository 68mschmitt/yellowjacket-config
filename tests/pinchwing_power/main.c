/* Exercise real telemetry code, including USB/ADC races and disconnect expiry. */
#include <assert.h>
#include <stdio.h>
#include "../../src/pinchwing_power.c"

#if CONFIG_ZMK_SPLIT_ROLE_CENTRAL
#include "../../src/pointing/pinchwing_dpi.c"

static void dispatch(struct input_event *event) {
    struct test_input_callback *callbacks[] = {
        &callback_power_left, &callback_power_right, &callback_receive_dpi,
    };
    for (unsigned int i = 0; i < ARRAY_SIZE(callbacks); i++) {
        if (callbacks[i]->device == event->dev) {
            callbacks[i]->fn(event, callbacks[i]->user_data);
        }
    }
}
#endif

int main(void) {
#if !CONFIG_ZMK_SPLIT_ROLE_CENTRAL
    power_init();
    assert(scheduled_delay == PINCHWING_POWER_REPORT_MS);
    announce(NULL);
    assert(last_report.type == ZMK_SPLIT_TRANSPORT_PERIPHERAL_EVENT_TYPE_INPUT_EVENT);
    assert(last_report.data.input_event.reg == (CONFIG_SHIELD_PINCHWING_DONGLE_LEFT ? 1 : 0));
    assert(last_report.data.input_event.type == INPUT_EV_MSC);
    assert(last_report.data.input_event.code == PINCHWING_INPUT_MSC_POWER);
    assert(!last_report.data.input_event.sync);
    assert(last_report.data.input_event.value == 42);

    usb_present = true;
    battery_level = 100;
    int previous_samples = samples;
    announce(NULL);
    assert(last_report.data.input_event.value == PINCHWING_POWER_USB);
    assert(samples == previous_samples); /* Never interpret USB voltage as charge. */
    ready = false;
    announce(NULL);
    assert(last_report.data.input_event.value == PINCHWING_POWER_USB);
    ready = true;
    usb_present = false;
    battery_level = 43;
    announce(NULL);
    assert(last_report.data.input_event.value == 43); /* Fresh after unplug. */

    usb_during_sample = true;
    battery_level = 100;
    announce(NULL);
    assert(last_report.data.input_event.value == PINCHWING_POWER_USB);
    usb_during_sample = false;
    usb_present = false;
    sample_result = -EIO;
    announce(NULL);
    assert(last_report.data.input_event.value == PINCHWING_POWER_UNKNOWN);
    sample_result = 0;
    channel_result = -EIO;
    announce(NULL);
    assert(last_report.data.input_event.value == PINCHWING_POWER_UNKNOWN);
    channel_result = 0;
    ready = false;
    announce(NULL);
    assert(last_report.data.input_event.value == PINCHWING_POWER_UNKNOWN);
    ready = true;
    battery_level = 101;
    announce(NULL);
    assert(last_report.data.input_event.value == PINCHWING_POWER_UNKNOWN);
    battery_level = -1;
    announce(NULL);
    assert(last_report.data.input_event.value == PINCHWING_POWER_UNKNOWN);
    battery_level = 0;
    announce(NULL);
    assert(last_report.data.input_event.value == 0);

    transport_result = -ENOTCONN;
    announce(NULL);
    assert(scheduled_delay == PINCHWING_POWER_REPORT_MS);
    transport_result = 0;
    battery_level = 61;
    announce(NULL);
    assert(last_report.data.input_event.value == 61);
    puts("PASS: half identity, USB detection, fresh unplug samples, ADC races/failures and retries");
#else
    assert(pinchwing_power_get(0) == PINCHWING_POWER_UNKNOWN);
    assert(pinchwing_power_get(1) == PINCHWING_POWER_UNKNOWN);
    assert(pinchwing_power_get(2) == PINCHWING_POWER_UNKNOWN);
    struct input_event event = {.type = INPUT_EV_MSC, .code = PINCHWING_INPUT_MSC_POWER,
                                .value = PINCHWING_POWER_USB};
    now = 100;
    /* Exercise the actual callback registrations, independently of BLE slot order. */
    callback_power_right.fn(&event, callback_power_right.user_data);
    event.value = 42;
    callback_power_left.fn(&event, callback_power_left.user_data);
    assert(pinchwing_power_get(0) == 42);
    assert(pinchwing_power_get(1) == PINCHWING_POWER_USB);
    now = 5099;
    assert(pinchwing_power_get(1) == PINCHWING_POWER_USB);
    now++;
    assert(pinchwing_power_get(0) == PINCHWING_POWER_UNKNOWN);
    assert(pinchwing_power_get(1) == PINCHWING_POWER_UNKNOWN);

    int invalid[] = {-2, 102, 1000};
    for (unsigned int i = 0; i < ARRAY_SIZE(invalid); i++) {
        event.value = invalid[i];
        receive_power(&event, NULL);
        assert(pinchwing_power_get(0) == PINCHWING_POWER_UNKNOWN);
    }
    event.value = 50;
    event.type = INPUT_EV_REL;
    receive_power(&event, NULL);
    assert(pinchwing_power_get(0) == PINCHWING_POWER_UNKNOWN);
    event.type = INPUT_EV_MSC;
    event.code++;
    receive_power(&event, NULL);
    assert(pinchwing_power_get(0) == PINCHWING_POWER_UNKNOWN);
    event.code = PINCHWING_INPUT_MSC_POWER;
    receive_power(&event, (void *)2);
    assert(pinchwing_power_get(0) == PINCHWING_POWER_UNKNOWN);

    event.value = 0;
    receive_power(&event, NULL);
    assert(pinchwing_power_get(0) == 0); /* Empty is distinct from unavailable. */
    event.value = PINCHWING_POWER_UNKNOWN;
    receive_power(&event, NULL);
    assert(pinchwing_power_get(0) == PINCHWING_POWER_UNKNOWN);
    event.value = 100;
    now = UINT32_MAX - 1000;
    receive_power(&event, NULL);
    now += 4999;
    assert(pinchwing_power_get(0) == 100);
    now++;
    assert(pinchwing_power_get(0) == PINCHWING_POWER_UNKNOWN);
    puts("PASS: physical sides, unavailable/empty/full, stale charging, validation and timer wrap");

    /* Drive both real receiver implementations through their registered devices.
     * Motion, DPI and power share mouse_split without cross-updating state. */
    now += PINCHWING_POWER_STALE_MS;
    event = (struct input_event){
        .dev = DEVICE_DT_GET(DT_NODELABEL(mouse_split)),
        .type = INPUT_EV_MSC, .code = PINCHWING_INPUT_MSC_DPI, .value = 1600,
    };
    dispatch(&event);
    assert(pinchwing_dpi_get() == 1600);
    assert(pinchwing_power_get(1) == PINCHWING_POWER_UNKNOWN);
    event.code = PINCHWING_INPUT_MSC_POWER;
    event.value = 67;
    dispatch(&event);
    assert(pinchwing_power_get(1) == 67);
    assert(pinchwing_power_get(0) == PINCHWING_POWER_UNKNOWN);
    assert(pinchwing_dpi_get() == 1600);
    event.value = PINCHWING_POWER_USB;
    dispatch(&event);
    assert(pinchwing_power_get(1) == PINCHWING_POWER_USB);
    assert(pinchwing_dpi_get() == 1600);
    event.type = INPUT_EV_REL;
    event.code = 0; /* Mouse X */
    event.value = 10;
    event.sync = true;
    dispatch(&event);
    assert(pinchwing_power_get(1) == PINCHWING_POWER_USB);
    assert(pinchwing_dpi_get() == 1600);
    event.dev = DEVICE_DT_GET(DT_NODELABEL(power_left));
    event.type = INPUT_EV_MSC;
    event.code = PINCHWING_INPUT_MSC_POWER;
    event.value = 42;
    event.sync = false;
    dispatch(&event);
    assert(pinchwing_power_get(0) == 42);
    assert(pinchwing_power_get(1) == PINCHWING_POWER_USB);
    assert(pinchwing_dpi_get() == 1600);
    puts("PASS: shared right channel routes power/DPI independently and ignores optical motion");
#endif
    return 0;
}
