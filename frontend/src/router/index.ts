import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'
import AnomaliesView from '../views/AnomaliesView.vue'
import DatasetView from '../views/DatasetView.vue'
import SettingsView from '../views/SettingsView.vue'

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: '/',
            name: 'dashboard',
            component: DashboardView,
        },
        {
            path: '/anomalies',
            name: 'anomalies',
            component: AnomaliesView,
        },
        {
            path: '/dataset',
            name: 'dataset',
            component: DatasetView,
        },
        {
            path: '/settings',
            name: 'settings',
            component: SettingsView,
        },
        {
            path: '/help',
            name: 'help',
            component: () => import('../views/HelpView.vue')
        },
    ],
})

export default router