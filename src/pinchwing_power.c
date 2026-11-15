/* SPDX-License-Identifier: MIT */
#include <zephyr/device.h>
#include <zephyr/input/input.h>
#include <zephyr/kernel.h>
#include <pinchwing_power.h>

#if !IS_ENABLED(CONFIG_ZMK_SPLIT_ROLE_CENTRAL)

#include <hal/nrf_power.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/init.h>
#include <zmk/split/peripheral.h>
#include <zmk/workqueue.h>

#if IS_ENABLED(CONFIG_SHIELD_PINCHWING_DONGLE_LEFT)
#define POWER_SPLIT DT_NODELABEL(power_left)
#else
/* Reuse the proven optical/DPI channel; no second GATT subscription on right. */
#define POWER_SPLIT DT_NODELABEL(mouse_split)
#endif

static const struct device *battery = DEVICE_DT_GET(DT_CHOSEN(zmk_battery));

static void announce(struct k_work *work);
K_WORK_DELAYABLE_DEFINE(power_work, announce);

static int read_power(void) {
    /* Read VBUS directly: USB data/HID is disabled on both halves. This also
     * detects charge-only cables without enabling or taking over the USB stack. */
    if (nrf_power_usbregstatus_vbusdet_get(NRF_POWER)) {
        return PINCHWING_POWER_USB;
    }

    struct sensor_value level;
    int value = PINCHWING_POWER_UNKNOWN;
    if (device_is_ready(battery) &&
        sensor_sample_fetch_chan(battery, SENSOR_CHAN_GAUGE_STATE_OF_CHARGE) == 0 &&
        sensor_channel_get(battery, SENSOR_CHAN_GAUGE_STATE_OF_CHARGE, &level) == 0 &&
        level.val1 >= 0 && level.val1 <= 100) {
        value = level.val1;
    }

    /* USB may have arrived during the ADC conversion. Never send its supply
     * voltage as a battery percentage, nor reuse ZMK's cached USB-era reading. */
    return nrf_power_usbregstatus_vbusdet_get(NRF_POWER) ? PINCHWING_POWER_USB : value;
}

static void announce(struct k_work *work) {
    ARG_UNUSED(work);
    const struct zmk_split_transport_peripheral_event event = {
        .type = ZMK_SPLIT_TRANSPORT_PERIPHERAL_EVENT_TYPE_INPUT_EVENT,
        .data.input_event = {
            .reg = DT_REG_ADDR(POWER_SPLIT),
            .type = INPUT_EV_MSC,
            .code = PINCHWING_INPUT_MSC_POWER,
            .value = read_power(),
            .sync = false,
        },
    };
    /* Direct transport avoids local input activity keeping the halves awake.
     * Repeat reports recover discovery, lost notifications, and dongle reboot.
     * The low-priority queue serializes ADC access with ZMK's battery worker. */
    (void)zmk_split_peripheral_report_event(&event);
    k_work_reschedule_for_queue(zmk_workqueue_lowprio_work_q(), &power_work,
                               K_MSEC(PINCHWING_POWER_REPORT_MS));
}

static int power_init(void) {
    k_work_schedule_for_queue(zmk_workqueue_lowprio_work_q(), &power_work,
                             K_MSEC(PINCHWING_POWER_REPORT_MS));
    return 0;
}

SYS_INIT(power_init, APPLICATION, CONFIG_APPLICATION_INIT_PRIORITY);

#else /* Dongle */

static struct k_spinlock power_lock;
static struct {
    int value;
    uint32_t received_at;
    bool received;
} reports[2];

static void receive_power(struct input_event *event, void *user_data) {
    unsigned int side = (uintptr_t)user_data;
    if (side >= ARRAY_SIZE(reports) || event->type != INPUT_EV_MSC ||
        event->code != PINCHWING_INPUT_MSC_POWER ||
        event->value < PINCHWING_POWER_UNKNOWN || event->value > PINCHWING_POWER_USB) {
        return;
    }
    k_spinlock_key_t key = k_spin_lock(&power_lock);
    reports[side].value = event->value;
    reports[side].received_at = k_uptime_get_32();
    reports[side].received = true;
    k_spin_unlock(&power_lock, key);
}

INPUT_CALLBACK_DEFINE_NAMED(DEVICE_DT_GET(DT_NODELABEL(power_left)), receive_power, (void *)0,
                            power_left);
INPUT_CALLBACK_DEFINE_NAMED(DEVICE_DT_GET(DT_NODELABEL(mouse_split)), receive_power, (void *)1,
                            power_right);

int pinchwing_power_get(unsigned int side) {
    if (side >= ARRAY_SIZE(reports)) {
        return PINCHWING_POWER_UNKNOWN;
    }
    k_spinlock_key_t key = k_spin_lock(&power_lock);
    int value = reports[side].received &&
                        (uint32_t)(k_uptime_get_32() - reports[side].received_at) <
                            PINCHWING_POWER_STALE_MS
                    ? reports[side].value : PINCHWING_POWER_UNKNOWN;
    k_spin_unlock(&power_lock, key);
    return value;
}

#endif
