# Set default USB interface
PRODUCT_DEFAULT_PROPERTY_OVERRIDES += \
	persist.sys.usb.config=mtp,diag,serial_smd,serial_tty,rmnet_smd,mass_storage,serial_smd

PRODUCT_PROPERTY_OVERRIDES += \
       dalvik.vm.heapstartsize=5m \
       dalvik.vm.heapgrowthlimit=48m \
       dalvik.vm.heapsize=128m

PRODUCT_COPY_FILES += device/qcom/msm7627a/media/media_profiles_7627a.xml:system/etc/media_profiles.xml \
                      device/qcom/msm7627a/media/media_codecs_7627a.xml:system/etc/media_codecs.xml

DEVICE_PACKAGE_OVERLAYS := device/qcom/msm7627a/overlay

$(call inherit-product, device/qcom/common/common.mk)

#add more msm7627a packages
#DebugTools
DebugTools := DebugCtrl

#LogSystem
LogSystem := LogKit
LogSystem += logkit
LogSystem += SystemAgent
LogSystem += qlogd
LogSystem += qlog-conf.xml
LogSystem += diag_mdlog
LogSystem += rootagent

PACKAGES_FASTMMI =  mmi \
                    mmi_audio \
                    mmi_battery \
                    mmi_bt \
                    mmi_camera \
                    mmi_flashlight \
                    mmi_fm \
                    mmi_gps \
                    mmi_gsensor \
                    mmi_gyroscope \
                    mmi_headset \
                    mmi_keypadbacklight \
                    mmi_lcd \
                    mmi_led \
                    mmi_lsensor \
                    mmi_msensor \
                    mmi_psensor \
                    mmi_sdcard \
                    mmi_speaker \
                    mmi_touch \
                    mmi_touchpanel \
                    mmi_vibrator \
                    mmi_volume \
                    mmi_wifi \
                    mmi_sim \
                    fastmmi.cfg

PRODUCT_PACKAGES += $(PACKAGES_FASTMMI)

#QRDSensors
QRDSensors := sensors.$(TARGET_PRODUCT)
QRDSensors += sensors.msm7627a_sku7
QRDSensors += sensors.msm8x25q_skud
QRDSensors += libmllite
QRDSensors += libmlplatform
QRDSensors += libmplmpu
QRDSensors += akmdfs
PRODUCT_PACKAGES += $(QRDSensors)

PRODUCT_PACKAGES += FastBoot \
					RestoreAirplaneMode	\
					vold.fstab	\
					vold.emmc.fstab \
					wpa_cli		\
					wpa_supplicant  \
					wpa_supplicant.conf \
					hostapd_cli      \
					hostapd		\
					libecc		\
					libiwnwai_asue	\
					libsms4		\
					abtfilt		\
					fw-4		\
					bdata		\
					athtcmd_ram	\
					nullTestFlow	\
					athwlan		\
					utf		\
					cfg80211.ko	\
					ath6kl_sdio.ko	\
					athtestcmd

PRODUCT_PACKAGES += smlogserver
PRODUCT_PACKAGES += silent_profile
PRODUCT_PACKAGES += rmt_storage_recovery
PRODUCT_PACKAGES += nv_set
PRODUCT_PACKAGES += i2cdetect

PRODUCT_PACKAGES += $(LogSystem)
PRODUCT_PACKAGES += $(DebugTools)

PRODUCT_PACKAGES += dun-server
PRODUCT_PACKAGES += ftmdaemon_qca

PRODUCT_NAME := msm7627a
PRODUCT_DEVICE := msm7627a

#Bluetooth configuration files
PRODUCT_COPY_FILES += \
   system/bluetooth/data/main.le.conf:system/etc/bluetooth/main.conf
PRODUCT_PACKAGES += fstab.msm7627a
PRODUCT_PACKAGES += fstab.nand.msm7627a
