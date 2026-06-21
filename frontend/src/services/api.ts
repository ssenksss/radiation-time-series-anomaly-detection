import type { Measurement, ModelInfo, Summary } from '../types/api'

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

export function getModelInfo(): Promise<ModelInfo> {
    return request<ModelInfo>('/model-info')
}