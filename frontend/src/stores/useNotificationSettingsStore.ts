import { reactive } from 'vue'

export type AlertSeverity = 'Critical only' | 'High + Critical' | 'All anomalies'
export type NotificationFrequency = 'Immediate' | 'Daily summary'

export interface NotificationSettingsState {
    emailAlertsEnabled: boolean
    inAppAlertsEnabled: boolean
    alertEmail: string
    selectedAlertSeverity: AlertSeverity
    selectedNotificationFrequency: NotificationFrequency
}

const STORAGE_KEY = 'radiation-monitoring-notification-settings'

const notificationSettings = reactive<NotificationSettingsState>({
    emailAlertsEnabled: true,
    inAppAlertsEnabled: true,
    alertEmail: '',
    selectedAlertSeverity: 'Critical only',
    selectedNotificationFrequency: 'Immediate',
})

function loadNotificationSettings() {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return

    try {
        const parsed = JSON.parse(raw)

        notificationSettings.emailAlertsEnabled = parsed.emailAlertsEnabled ?? true
        notificationSettings.inAppAlertsEnabled = parsed.inAppAlertsEnabled ?? true
        notificationSettings.alertEmail = parsed.alertEmail ?? ''
        notificationSettings.selectedAlertSeverity = parsed.selectedAlertSeverity ?? 'Critical only'
        notificationSettings.selectedNotificationFrequency = parsed.selectedNotificationFrequency ?? 'Immediate'
    } catch (error) {
        console.error('Failed to restore notification settings:', error)
    }
}

function saveNotificationSettings() {
    localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
            emailAlertsEnabled: notificationSettings.emailAlertsEnabled,
            inAppAlertsEnabled: notificationSettings.inAppAlertsEnabled,
            alertEmail: notificationSettings.alertEmail,
            selectedAlertSeverity: notificationSettings.selectedAlertSeverity,
            selectedNotificationFrequency: notificationSettings.selectedNotificationFrequency,
        }),
    )
}

loadNotificationSettings()

export function useNotificationSettingsStore() {
    return {
        notificationSettings,
        saveNotificationSettings,
    }
}