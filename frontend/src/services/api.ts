import type { AppSettings, Measurement, ModelInfo, Summary } from '../types/api'

const API_BASE_URL = 'http://127.0.0.1:8000'

async function request<T>(path: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`)

    if (!response.ok) {
        throw new Error(`API request failed: ${path}`)
    }

    return response.json()
}

export function getMeasurements(limit = 1000): Promise<Measurement[]> {
    return request<Measurement[]>(`/measurements?limit=${limit}`)
}

export function getAnomalies(limit = 200): Promise<Measurement[]> {
    return request<Measurement[]>(`/anomalies?limit=${limit}`)
}

export function getSummary(): Promise<Summary> {
    return request<Summary>('/summary')
}

export function getModelInfo(
    modelA?: string,
    modelB?: string,
): Promise<ModelInfo> {
    const params = new URLSearchParams()

    if (modelA) {
        params.set('modelA', modelA)
    }

    if (modelB) {
        params.set('modelB', modelB)
    }

    const query = params.toString()

    return request<ModelInfo>(query ? `/model-info?${query}` : '/model-info')
}

export function getSettings(): Promise<AppSettings> {
    return request<AppSettings>('/settings')
}

export async function updateThreshold(threshold: number): Promise<AppSettings> {
    const response = await fetch(`${API_BASE_URL}/settings/threshold`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ threshold }),
    })

    if (!response.ok) {
        throw new Error('Failed to update threshold')
    }

    return response.json()
}

export async function updateActiveModel(activeModel: string): Promise<AppSettings> {
    const response = await fetch(`${API_BASE_URL}/settings/model`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ activeModel }),
    })

    if (!response.ok) {
        throw new Error('Failed to update active model')
    }

    return response.json()
}